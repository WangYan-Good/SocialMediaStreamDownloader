##>> Test
import os
import sys
sys.path.append(os.getcwd())
##<< Test

## <<Base>>
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Mapping, Optional

## <<Third-Part>>
from backend.src.database.query.sql_text import escape_like
from backend.src.library.loglib import get_logger
from backend.src.library.safe_diagnostics import persistence_diagnostic


##
## room.status values carried over from the platform payload.
## 2 = broadcasting, 4 = finished.  Anything else (including NULL) is unknown.
##
LIVE_STATUS_LIVING = 2
LIVE_STATUS_ENDED = 4

##
## Sort keys accepted from the request, mapped to the column they may order by.
## The mapping is also the whitelist: nothing outside it ever reaches the SQL.
##
_SORT_COLUMNS = {
  "last_checked_at": "s.last_checked_at",
  "score": "f.score",
  "actived_count": "s.actived_count",
  "nickname": "s.nickname",
}

##
## "last seen live" windows offered by the UI.
##
_LAST_LIVE_WINDOWS = {
  "1h": timedelta(hours=1),
  "24h": timedelta(hours=24),
  "7d": timedelta(days=7),
  "30d": timedelta(days=30),
}
_LAST_LIVE_NEVER = "never"

_USER_STATUS_VALUES = ("正常", "已注销")

_SELECTED_COLUMNS = '''
      s.owner_user_id,
      s.sec_user_id,
      s.nickname,
      s.live_share_url,
      s.post_share_url,
      s.directory_name,
      s.user_status,
      s.actived_count,
      s.last_live_status,
      s.last_checked_at,
      s.last_room_id,
      f.score
'''

_FROM_AND_JOIN = '''
    FROM share_url s
    LEFT JOIN favorite_owner f
      ON f.owner_user_id = s.owner_user_id
     AND f.platform = %s
'''


class OwnerHistoryFilterError(ValueError):
  """Raised when request supplied filter arguments cannot be normalised."""


##
## Moved to a module of its own once the library query needed the same rule.
## Kept under the old private name here so nothing else in this file changed.
##
_escape_like = escape_like


def _optional_text(source: Mapping[str, Any], key: str) -> Optional[str]:
  raw = source.get(key)
  if raw is None:
    return None
  text = str(raw).strip()
  return text or None


def _optional_int(source: Mapping[str, Any], key: str) -> Optional[int]:
  raw = source.get(key)
  if raw is None or str(raw).strip() == "":
    return None
  try:
    return int(str(raw).strip())
  except (TypeError, ValueError):
    raise OwnerHistoryFilterError("{} must be an integer".format(key))


def _optional_bool(source: Mapping[str, Any], key: str) -> bool:
  raw = source.get(key)
  if raw is None:
    return False
  if isinstance(raw, bool):
    return raw
  return str(raw).strip().lower() in ("1", "true", "yes", "on")


@dataclass(frozen=True)
class OwnerHistoryFilter:
  """Normalised, already validated filter arguments for one history page."""

  platform: str = "douyin"
  keyword: Optional[str] = None
  favorite_only: bool = False
  score_min: Optional[int] = None
  score_max: Optional[int] = None
  last_live_within: Optional[str] = None
  user_status: Optional[str] = None
  sort: str = "last_checked_at"
  order: str = "desc"
  page: int = 1
  page_size: int = 10

  @classmethod
  def from_mapping(
    cls,
    source: Mapping[str, Any],
    page_size_limit: int,
  ) -> "OwnerHistoryFilter":
    """Build a filter from raw request arguments.

    ``page_size_limit`` is a hard cap, not a default: a larger requested page is
    clamped rather than rejected, because the probe that follows a page runs one
    real network request per row.
    """
    if page_size_limit < 1:
      raise OwnerHistoryFilterError("page_size_limit must be at least 1")

    platform = _optional_text(source, "platform") or "douyin"

    score_min = _optional_int(source, "score_min")
    score_max = _optional_int(source, "score_max")
    for name, value in (("score_min", score_min), ("score_max", score_max)):
      if value is not None and not 0 <= value <= 100:
        raise OwnerHistoryFilterError("{} must be between 0 and 100".format(name))
    if score_min is not None and score_max is not None and score_min > score_max:
      raise OwnerHistoryFilterError("score_min must not exceed score_max")

    last_live_within = _optional_text(source, "last_live_within")
    if last_live_within is not None:
      if last_live_within not in _LAST_LIVE_WINDOWS and last_live_within != _LAST_LIVE_NEVER:
        raise OwnerHistoryFilterError(
          "last_live_within must be one of {}".format(
            ", ".join(sorted(_LAST_LIVE_WINDOWS) + [_LAST_LIVE_NEVER])
          )
        )

    user_status = _optional_text(source, "user_status")
    if user_status is not None and user_status not in _USER_STATUS_VALUES:
      raise OwnerHistoryFilterError(
        "user_status must be one of {}".format(", ".join(_USER_STATUS_VALUES))
      )

    sort = _optional_text(source, "sort") or "last_checked_at"
    if sort not in _SORT_COLUMNS:
      raise OwnerHistoryFilterError(
        "sort must be one of {}".format(", ".join(sorted(_SORT_COLUMNS)))
      )

    order = (_optional_text(source, "order") or "desc").lower()
    if order not in ("asc", "desc"):
      raise OwnerHistoryFilterError("order must be asc or desc")

    page = _optional_int(source, "page") or 1
    if page < 1:
      raise OwnerHistoryFilterError("page must be at least 1")

    requested_page_size = _optional_int(source, "page_size") or page_size_limit
    if requested_page_size < 1:
      raise OwnerHistoryFilterError("page_size must be at least 1")
    page_size = min(requested_page_size, page_size_limit)

    return cls(
      platform=platform,
      keyword=_optional_text(source, "q"),
      favorite_only=_optional_bool(source, "favorite"),
      score_min=score_min,
      score_max=score_max,
      last_live_within=last_live_within,
      user_status=user_status,
      sort=sort,
      order=order,
      page=page,
      page_size=page_size,
    )


@dataclass(frozen=True)
class OwnerHistoryPage:
  total: int
  page: int
  page_size: int
  items: tuple


class OwnerHistoryQuery:
  """Filtered, sorted, paginated view over previously downloaded owners.

  Every filter and sort key lives on ``share_url`` or ``favorite_owner``, so one
  page costs a single indexed join.  The live-status columns it reads are a cache
  of the last known status; deciding whether an owner is broadcasting *now* is the
  probe layer's job, never this one's.
  """

##
## >>============================= private method =============================>>
##
  def __init__(self, database, clock=datetime.now) -> None:
    if database is None:
      raise ValueError("database is required")
    self._database = database
    self._clock = clock

  def _conditions(self, owner_filter: OwnerHistoryFilter) -> tuple:
    clauses = list()
    params = list()

    if owner_filter.keyword is not None:
      clauses.append("s.nickname LIKE %s")
      params.append(_escape_like(owner_filter.keyword))

    if owner_filter.favorite_only is True:
      clauses.append("f.owner_user_id IS NOT NULL")

    if owner_filter.score_min is not None:
      clauses.append("f.score >= %s")
      params.append(owner_filter.score_min)

    if owner_filter.score_max is not None:
      clauses.append("f.score <= %s")
      params.append(owner_filter.score_max)

    if owner_filter.user_status is not None:
      clauses.append("s.user_status = %s")
      params.append(owner_filter.user_status)

    if owner_filter.last_live_within == _LAST_LIVE_NEVER:
      ##
      ## Never seen broadcasting: either never probed at all, or the newest known
      ## status was not "living".  Written NULL-safely on purpose.
      ##
      clauses.append(
        "(s.last_checked_at IS NULL"
        " OR s.last_live_status IS NULL"
        " OR s.last_live_status <> %s)"
      )
      params.append(LIVE_STATUS_LIVING)
    elif owner_filter.last_live_within is not None:
      cutoff = self._clock() - _LAST_LIVE_WINDOWS[owner_filter.last_live_within]
      clauses.append("s.last_live_status = %s AND s.last_checked_at >= %s")
      params.append(LIVE_STATUS_LIVING)
      params.append(cutoff)

    if not clauses:
      return ("", params)
    return ("    WHERE " + "\n      AND ".join(clauses) + "\n", params)

##
## >>============================= sub class method =============================>>
##
  def search(self, owner_filter: OwnerHistoryFilter) -> OwnerHistoryPage:
    """Return one page of owners plus the total matching count."""
    where_sql, where_params = self._conditions(owner_filter)
    ##
    ## The platform parameter belongs to the JOIN, so it always leads the list.
    ##
    params = [owner_filter.platform] + where_params

    count_sql = "SELECT COUNT(*) AS total\n" + _FROM_AND_JOIN + where_sql

    ##
    ## Sorting on last_checked_at ASC puts never-probed owners first: an owner we
    ## have never checked is the most overdue one, which is what "最久未下载" means.
    ## owner_user_id breaks ties so pagination stays stable across requests.
    ##
    order_sql = "    ORDER BY {} {}, s.owner_user_id ASC\n".format(
      _SORT_COLUMNS[owner_filter.sort],
      "ASC" if owner_filter.order == "asc" else "DESC",
    )
    page_sql = (
      "SELECT" + _SELECTED_COLUMNS + _FROM_AND_JOIN + where_sql + order_sql
      + "    LIMIT %s OFFSET %s\n"
    )
    offset = (owner_filter.page - 1) * owner_filter.page_size

    with self._database.get_connection() as connector:
      with connector.cursor() as cursor:
        cursor.execute(count_sql, tuple(params))
        count_row = cursor.fetchone()
        total = 0 if count_row is None else int(count_row.get("total", 0))

        cursor.execute(
          page_sql, tuple(params + [owner_filter.page_size, offset])
        )
        items = tuple(cursor.fetchall() or ())

    return OwnerHistoryPage(
      total=total,
      page=owner_filter.page,
      page_size=owner_filter.page_size,
      items=items,
    )

  def sessions(
    self,
    owner_user_id: str,
    platform: str = "douyin",
    limit: int = 20,
  ) -> tuple:
    """Return recent live sessions recorded for one owner, newest first.

    ``live_record`` and ``room_base`` are joined on the room id, which is
    VARCHAR(200) on both sides, so this join stays index eligible.  Joining
    ``room_base`` on owner id instead would cast BIGINT against VARCHAR and lose
    every index.
    """
    if owner_user_id is None or str(owner_user_id).strip() == "":
      raise ValueError("owner_user_id is required")
    if limit < 1:
      raise ValueError("limit must be at least 1")

    sql = '''
          SELECT lr.`now`        AS observed_at,
                 lr.room_id      AS room_id,
                 lr.start_time   AS start_time,
                 lr.finish_time  AS finish_time,
                 lr.status_code  AS status_code,
                 rb.title        AS title,
                 rb.status       AS room_status
          FROM live_record lr
          LEFT JOIN room_base rb
            ON rb.id = lr.room_id
           AND rb.`now` = lr.`now`
          WHERE lr.owner_user_id = %s
            AND lr.platform = %s
          ORDER BY lr.`now` DESC
          LIMIT %s
          '''
    with self._database.get_connection() as connector:
      with connector.cursor() as cursor:
        cursor.execute(sql, (str(owner_user_id), platform, limit))
        return tuple(cursor.fetchall() or ())

  def live_share_urls(self, owner_user_ids, platform: str = "douyin") -> dict:
    """Return ``{owner_user_id: live_share_url}`` for the given owners.

    The probe layer needs the share url that belongs to each requested owner and
    must not trust one supplied by the client.
    """
    identifiers = [str(item) for item in (owner_user_ids or ()) if str(item).strip()]
    if not identifiers:
      return dict()

    placeholders = ", ".join(["%s"] * len(identifiers))
    sql = '''
          SELECT owner_user_id,
                 live_share_url,
                 nickname,
                 last_live_status,
                 last_checked_at,
                 last_room_id
          FROM share_url
          WHERE owner_user_id IN ({})
          '''.format(placeholders)
    with self._database.get_connection() as connector:
      with connector.cursor() as cursor:
        cursor.execute(sql, tuple(identifiers))
        rows = cursor.fetchall() or ()

    resolved = dict()
    for row in rows:
      resolved[str(row.get("owner_user_id"))] = row
    missing = [item for item in identifiers if item not in resolved]
    if missing:
      get_logger().warning(
        persistence_diagnostic(
          "persistence_unknown_identity",
          table="share_url",
          operation="query",
          ##
          ## How many were unresolved, never which. The identifiers are the
          ## accounts somebody asked about.
          ##
          rows=len(missing),
          found=False,
        )
      )
    return resolved
