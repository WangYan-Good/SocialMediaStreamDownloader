##>> Test
import os
import sys
sys.path.append(os.getcwd())
##<< Test

## <<Base>>
from dataclasses import dataclass
from typing import Any, Mapping, Optional

## <<Third-Part>>
from backend.src.database.query.sql_text import escape_like


##
## The library is a read model.  Nothing here writes: it reports what the
## downloader already recorded, joined to whichever creator and person that
## record belongs to.
##
## It deliberately answers "what did this program record", not "what is on the
## disk right now".  aweme_record keeps a save_dir and two counts but no file
## names, sizes or existence; live_record keeps no output path at all; and a
## recording_record path says where the recorder wrote, not whether the file
## still exists.  Asking the filesystem would be a different contract with a
## different security surface, so this layer never does.
##

##
## One platform is implemented.  Kept as a value rather than a free string so an
## unsupported one is refused rather than answered with an empty page - which
## reads as "nothing was downloaded" instead of "not supported".
##
PLATFORM = "douyin"

##
## What the downloader writes into aweme_record.  Mirrors the constants in
## douyin_aweme_external_info rather than inventing a third vocabulary.
##
AWEME_TYPES = ("video", "image")
SOURCES = ("api", "html")
RECORDING_PROTOCOLS = ("flv", "hls")

##
## Whether the recorded run saved everything it planned to.  A statement about
## the download record, never about files existing now.
##
COMPLETION_COMPLETE = "complete"
COMPLETION_PARTIAL = "partial"
COMPLETIONS = (COMPLETION_COMPLETE, COMPLETION_PARTIAL)

DEFAULT_PAGE_SIZE = 25
MAX_PAGE_SIZE = 100

##
## Sort keys accepted from the request, mapped to the column they may order by.
## The mapping is also the whitelist: nothing outside it ever reaches the SQL
## text, which is the only reason ORDER BY can be built by formatting at all.
##
POST_SORT_COLUMNS = {
  "downloaded_at": "a.downloaded_at",
  "create_time": "a.create_time",
  "nickname": "s.nickname",
  "aweme_id": "a.aweme_id",
}

LIVE_SORT_COLUMNS = {
  "observed_at": "lr.`now`",
  "start_time": "lr.start_time",
  "finish_time": "lr.finish_time",
  "nickname": "s.nickname",
}

RECORDING_SORT_COLUMNS = {
  "finished_at": "rr.finished_at",
  "started_at": "rr.started_at",
  "created_at": "rr.created_at",
  "title": "rr.title",
  "nickname": "s.nickname",
}


class LibraryFilterError(ValueError):
  """Raised when request supplied filter arguments cannot be normalised."""


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
    raise LibraryFilterError("{} must be an integer".format(key))


def _one_of(value: Optional[str], allowed: tuple, name: str) -> Optional[str]:
  if value is not None and value not in allowed:
    raise LibraryFilterError("{} must be one of {}".format(name, ", ".join(allowed)))
  return value


def _platform(source: Mapping[str, Any]) -> str:
  platform = _optional_text(source, "platform") or PLATFORM
  if platform != PLATFORM:
    raise LibraryFilterError("platform must be {}".format(PLATFORM))
  return platform


def _paging(source: Mapping[str, Any], page_size_limit: int) -> tuple:
  page = _optional_int(source, "page")
  page = 1 if page is None else page
  if page < 1:
    raise LibraryFilterError("page must be at least 1")

  requested = _optional_int(source, "page_size")
  requested = DEFAULT_PAGE_SIZE if requested is None else requested
  if requested < 1:
    raise LibraryFilterError("page_size must be at least 1")
  ##
  ## Clamped rather than refused: a caller asking for everything gets a large
  ## page instead of an error they cannot do anything about.
  ##
  return (page, min(requested, page_size_limit))


def _ordering(source: Mapping[str, Any], columns: dict, default_sort: str) -> tuple:
  sort = _optional_text(source, "sort") or default_sort
  if sort not in columns:
    raise LibraryFilterError("sort must be one of {}".format(", ".join(sorted(columns))))

  order = (_optional_text(source, "order") or "desc").lower()
  if order not in ("asc", "desc"):
    raise LibraryFilterError("order must be asc or desc")
  return (sort, order)


@dataclass(frozen=True)
class LibraryPostFilter:
  """Normalised, already validated arguments for one page of downloaded posts."""

  platform: str = PLATFORM
  keyword: Optional[str] = None
  owner_user_id: Optional[str] = None
  person_id: Optional[int] = None
  aweme_type: Optional[str] = None
  completion: Optional[str] = None
  source: Optional[str] = None
  sort: str = "downloaded_at"
  order: str = "desc"
  page: int = 1
  page_size: int = DEFAULT_PAGE_SIZE

  @classmethod
  def from_mapping(
    cls,
    source: Mapping[str, Any],
    page_size_limit: int = MAX_PAGE_SIZE,
  ) -> "LibraryPostFilter":
    page, page_size = _paging(source, page_size_limit)
    sort, order = _ordering(source, POST_SORT_COLUMNS, "downloaded_at")

    return cls(
      platform=_platform(source),
      keyword=_optional_text(source, "q"),
      owner_user_id=_optional_text(source, "owner_user_id"),
      person_id=_optional_int(source, "person_id"),
      aweme_type=_one_of(_optional_text(source, "aweme_type"), AWEME_TYPES, "aweme_type"),
      completion=_one_of(
        _optional_text(source, "completion"), COMPLETIONS, "completion"
      ),
      source=_one_of(_optional_text(source, "source"), SOURCES, "source"),
      sort=sort,
      order=order,
      page=page,
      page_size=page_size,
    )


@dataclass(frozen=True)
class LibraryLiveFilter:
  """Normalised, already validated arguments for one page of live records.

  There is deliberately no "live now" filter.  Every row here is something that
  was observed at a point in the past; whether a room is broadcasting at this
  moment is only answerable by a probe, and offering the filter would invite the
  page to claim an answer it does not have.
  """

  platform: str = PLATFORM
  keyword: Optional[str] = None
  owner_user_id: Optional[str] = None
  person_id: Optional[int] = None
  sort: str = "observed_at"
  order: str = "desc"
  page: int = 1
  page_size: int = DEFAULT_PAGE_SIZE

  @classmethod
  def from_mapping(
    cls,
    source: Mapping[str, Any],
    page_size_limit: int = MAX_PAGE_SIZE,
  ) -> "LibraryLiveFilter":
    page, page_size = _paging(source, page_size_limit)
    sort, order = _ordering(source, LIVE_SORT_COLUMNS, "observed_at")

    return cls(
      platform=_platform(source),
      keyword=_optional_text(source, "q"),
      owner_user_id=_optional_text(source, "owner_user_id"),
      person_id=_optional_int(source, "person_id"),
      sort=sort,
      order=order,
      page=page,
      page_size=page_size,
    )


@dataclass(frozen=True)
class LibraryRecordingFilter:
  """Normalised arguments for persistent live recording resources."""

  platform: str = PLATFORM
  keyword: Optional[str] = None
  owner_user_id: Optional[str] = None
  protocol: Optional[str] = None
  sort: str = "finished_at"
  order: str = "desc"
  page: int = 1
  page_size: int = DEFAULT_PAGE_SIZE

  @classmethod
  def from_mapping(
    cls,
    source: Mapping[str, Any],
    page_size_limit: int = MAX_PAGE_SIZE,
  ) -> "LibraryRecordingFilter":
    page, page_size = _paging(source, page_size_limit)
    sort, order = _ordering(source, RECORDING_SORT_COLUMNS, "finished_at")

    return cls(
      platform=_platform(source),
      keyword=_optional_text(source, "q"),
      owner_user_id=_optional_text(source, "owner_user_id"),
      protocol=_one_of(
        _optional_text(source, "protocol"),
        RECORDING_PROTOCOLS,
        "protocol",
      ),
      sort=sort,
      order=order,
      page=page,
      page_size=page_size,
    )


@dataclass(frozen=True)
class LibraryPage:
  """One page of library rows plus the total the filters actually matched."""

  total: int
  page: int
  page_size: int
  items: tuple


##
## What one downloaded post looks like to the library.
##
## share_url carries the creator's display details and person_account carries
## the identity marking; both are LEFT joins because most downloaded accounts
## have neither a friendly name nor a person attached, and an inner join would
## quietly drop the majority of the library.
##
_POST_COLUMNS = '''
      a.platform,
      a.aweme_id,
      a.owner_user_id,
      a.sec_user_id,
      a.aweme_type,
      a.`desc`,
      a.create_time,
      a.downloaded_at,
      a.media_count,
      a.saved_count,
      a.save_dir,
      a.source,
      s.nickname,
      s.directory_name,
      pa.person_id,
      p.display_name AS person_display_name
'''

_POST_FROM = '''
    FROM aweme_record a
    LEFT JOIN share_url s
      ON s.owner_user_id = a.owner_user_id
    LEFT JOIN person_account pa
      ON pa.platform = a.platform
     AND pa.owner_user_id = a.owner_user_id
    LEFT JOIN person p
      ON p.person_id = pa.person_id
'''

_OWNED_POST_FROM = '''
    FROM aweme_record a
    JOIN app_user_aweme_record uar
      ON uar.platform = a.platform
     AND uar.aweme_id = a.aweme_id
    LEFT JOIN share_url s
      ON s.owner_user_id = a.owner_user_id
    LEFT JOIN person_account pa
      ON pa.platform = a.platform
     AND pa.owner_user_id = a.owner_user_id
    LEFT JOIN person p
      ON p.person_id = pa.person_id
'''

_GLOBAL_POST_SCOPE = object()

_RECORDING_COLUMNS = '''
      rr.recording_id,
      rr.app_user_id,
      rr.platform,
      rr.room_id,
      rr.owner_user_id,
      rr.title,
      rr.protocol,
      rr.output_path,
      rr.started_at,
      rr.finished_at,
      rr.source,
      rr.created_at,
      s.nickname,
      s.directory_name,
      pa.person_id,
      p.display_name AS person_display_name
'''

_RECORDING_FROM = '''
    FROM recording_record rr
    LEFT JOIN share_url s
      ON s.owner_user_id = rr.owner_user_id
    LEFT JOIN person_account pa
      ON pa.platform = rr.platform
     AND pa.owner_user_id = rr.owner_user_id
    LEFT JOIN person p
      ON p.person_id = pa.person_id
'''

_GLOBAL_RECORDING_SCOPE = object()


def _require_identifier(value, field: str) -> None:
  """Refuse anything that is not a positive integer identifier.

  ``type(...) is not int`` rather than isinstance: ``True`` is an ``int`` in
  Python, and a boolean reaching a WHERE clause binds as 1 and silently matches
  a real row.
  """
  if type(value) is not int or value < 1:
    raise ValueError("{} must be a positive integer".format(field))


class LibraryQuery:
  """Filtered, sorted, paginated views over what this program downloaded.

  Read only.  There is no write path here at all, deliberately: the library
  reports records, and every mutation of those records belongs to whichever
  service produced them.

  It also never touches the filesystem.  ``save_dir`` and ``output_path`` are
  strings the downloader wrote at the time; whether either location still holds
  anything is a question this layer cannot answer and does not pretend to.
  """

##
## >>============================= private method =============================>>
##
  def __init__(self, database) -> None:
    if database is None:
      raise ValueError("database is required")
    self._database = database

  def _post_conditions(
    self,
    post_filter: LibraryPostFilter,
    app_user_id=_GLOBAL_POST_SCOPE,
  ) -> tuple:
    clauses = ["a.platform = %s"]
    params = [post_filter.platform]

    if app_user_id is not _GLOBAL_POST_SCOPE:
      clauses.append("uar.app_user_id = %s")
      params.append(app_user_id)

    if post_filter.keyword is not None:
      pattern = escape_like(post_filter.keyword)
      ##
      ## The four things somebody actually types: an id they copied, words they
      ## remember from the caption, the creator's name, or the person's.
      ##
      clauses.append(
        "(a.aweme_id LIKE %s"
        " OR a.`desc` LIKE %s"
        " OR s.nickname LIKE %s"
        " OR p.display_name LIKE %s)"
      )
      params.extend([pattern, pattern, pattern, pattern])

    if post_filter.owner_user_id is not None:
      clauses.append("a.owner_user_id = %s")
      params.append(post_filter.owner_user_id)

    if post_filter.person_id is not None:
      clauses.append("pa.person_id = %s")
      params.append(post_filter.person_id)

    if post_filter.aweme_type is not None:
      clauses.append("a.aweme_type = %s")
      params.append(post_filter.aweme_type)

    if post_filter.source is not None:
      clauses.append("a.source = %s")
      params.append(post_filter.source)

    if post_filter.completion == COMPLETION_PARTIAL:
      ##
      ## Fewer files landed than the run planned to fetch.  A statement about
      ## the record, not about the disk: nothing here checks whether the files
      ## that did land are still there.
      ##
      clauses.append("a.saved_count < a.media_count")
    elif post_filter.completion == COMPLETION_COMPLETE:
      clauses.append("a.saved_count >= a.media_count")

    return ("    WHERE " + "\n      AND ".join(clauses) + "\n", params)

##
## >>============================= sub class method =============================>>
##
  def _posts(
    self,
    post_filter: LibraryPostFilter,
    from_sql: str,
    app_user_id=_GLOBAL_POST_SCOPE,
  ) -> LibraryPage:
    where_sql, params = self._post_conditions(
      post_filter,
      app_user_id=app_user_id,
    )

    count_sql = "SELECT COUNT(*) AS total\n" + from_sql + where_sql

    ##
    ## The sort key is a whitelist lookup, never the caller's string, which is
    ## the only reason this may be formatted into the statement at all.  The two
    ## trailing keys are the primary key: without them two rows sharing a
    ## timestamp can swap places between requests, so one is shown on both pages
    ## and another on neither.
    ##
    order_sql = "    ORDER BY {} {}, a.platform ASC, a.aweme_id ASC\n".format(
      POST_SORT_COLUMNS[post_filter.sort],
      "ASC" if post_filter.order == "asc" else "DESC",
    )
    page_sql = (
      "SELECT" + _POST_COLUMNS + from_sql + where_sql + order_sql
      + "    LIMIT %s OFFSET %s\n"
    )
    offset = (post_filter.page - 1) * post_filter.page_size

    with self._database.get_connection() as connector:
      with connector.cursor() as cursor:
        cursor.execute(count_sql, tuple(params))
        count_row = cursor.fetchone()
        total = 0 if count_row is None else int(count_row.get("total", 0))

        cursor.execute(page_sql, tuple(params + [post_filter.page_size, offset]))
        items = tuple(cursor.fetchall() or ())

    return LibraryPage(
      total=total,
      page=post_filter.page,
      page_size=post_filter.page_size,
      items=items,
    )

  def posts(self, post_filter: LibraryPostFilter) -> LibraryPage:
    """Return the global/Admin page, including historical unowned rows."""
    return self._posts(post_filter, _POST_FROM)

  def posts_for_user(
    self,
    app_user_id: int,
    post_filter: LibraryPostFilter,
  ) -> LibraryPage:
    """Return posts related to one server-selected application user."""
    if type(app_user_id) is not int or app_user_id < 1:
      raise ValueError("app_user_id must be a positive integer")
    return self._posts(
      post_filter,
      _OWNED_POST_FROM,
      app_user_id=app_user_id,
    )

  ##
  ## >>--------------------------- exact lookups ---------------------------<<
  ##
  ##
  ## One row, for the asset endpoints.
  ##
  ## Deliberately not "fetch a page and search it in Python": that reads rows
  ## nobody asked for, and it moves the ownership decision out of the statement
  ## and into a loop, where the next edit can quietly widen it. The scoped
  ## variants carry their constraint in the SQL for exactly that reason.
  ##
  ## Still database-only, like everything else in this class. Whether the files
  ## are still on disk is a different question, asked by a different module,
  ## after authorization has already succeeded.
  ##
  def post(self, platform: str, aweme_id: str):
    """One post, whoever owns it. Admin scope, including historical rows."""
    return self._one(
      "SELECT" + _POST_COLUMNS + _POST_FROM
      + "    WHERE a.platform = %s\n      AND a.aweme_id = %s\n    LIMIT 1\n",
      (platform, aweme_id),
    )

  def post_for_user(self, app_user_id: int, platform: str, aweme_id: str):
    """One post, only if this application user is related to it."""
    _require_identifier(app_user_id, "app_user_id")
    return self._one(
      "SELECT" + _POST_COLUMNS + _OWNED_POST_FROM
      + "    WHERE uar.app_user_id = %s\n"
        "      AND a.platform = %s\n"
        "      AND a.aweme_id = %s\n"
        "    LIMIT 1\n",
      (app_user_id, platform, aweme_id),
    )

  def recording(self, recording_id: int):
    """One recording, whoever owns it - including rows owned by nobody."""
    _require_identifier(recording_id, "recording_id")
    return self._one(
      "SELECT" + _RECORDING_COLUMNS + _RECORDING_FROM
      + "    WHERE rr.recording_id = %s\n    LIMIT 1\n",
      (recording_id,),
    )

  def recording_for_user(self, app_user_id: int, recording_id: int):
    """One recording, only if this application user owns it.

    A row with ``app_user_id IS NULL`` never matches: NULL is not equal to
    anything, which is the answer wanted here - historical recordings belong to
    nobody and so are nobody's to read.
    """
    _require_identifier(app_user_id, "app_user_id")
    _require_identifier(recording_id, "recording_id")
    return self._one(
      "SELECT" + _RECORDING_COLUMNS + _RECORDING_FROM
      + "    WHERE rr.recording_id = %s\n"
        "      AND rr.app_user_id = %s\n"
        "    LIMIT 1\n",
      (recording_id, app_user_id),
    )

  def _one(self, statement: str, params: tuple):
    with self._database.get_connection() as connector:
      with connector.cursor() as cursor:
        cursor.execute(statement, params)
        row = cursor.fetchone()
    return dict(row) if row else None

  def _recording_conditions(
    self,
    recording_filter: LibraryRecordingFilter,
    app_user_id=_GLOBAL_RECORDING_SCOPE,
  ) -> tuple:
    clauses = ["rr.platform = %s"]
    params = [recording_filter.platform]

    if app_user_id is not _GLOBAL_RECORDING_SCOPE:
      clauses.append("rr.app_user_id = %s")
      params.append(app_user_id)

    if recording_filter.keyword is not None:
      pattern = escape_like(recording_filter.keyword)
      clauses.append(
        "(rr.room_id LIKE %s"
        " OR rr.title LIKE %s"
        " OR s.nickname LIKE %s"
        " OR p.display_name LIKE %s)"
      )
      params.extend([pattern, pattern, pattern, pattern])

    if recording_filter.owner_user_id is not None:
      clauses.append("rr.owner_user_id = %s")
      params.append(recording_filter.owner_user_id)

    if recording_filter.protocol is not None:
      clauses.append("rr.protocol = %s")
      params.append(recording_filter.protocol)

    return ("    WHERE " + "\n      AND ".join(clauses) + "\n", params)

  def _recordings(
    self,
    recording_filter: LibraryRecordingFilter,
    app_user_id=_GLOBAL_RECORDING_SCOPE,
  ) -> LibraryPage:
    where_sql, params = self._recording_conditions(
      recording_filter,
      app_user_id=app_user_id,
    )
    count_sql = "SELECT COUNT(*) AS total\n" + _RECORDING_FROM + where_sql
    order_sql = "    ORDER BY {} {}, rr.recording_id ASC\n".format(
      RECORDING_SORT_COLUMNS[recording_filter.sort],
      "ASC" if recording_filter.order == "asc" else "DESC",
    )
    page_sql = (
      "SELECT" + _RECORDING_COLUMNS + _RECORDING_FROM + where_sql + order_sql
      + "    LIMIT %s OFFSET %s\n"
    )
    offset = (recording_filter.page - 1) * recording_filter.page_size

    with self._database.get_connection() as connector:
      with connector.cursor() as cursor:
        cursor.execute(count_sql, tuple(params))
        count_row = cursor.fetchone()
        total = 0 if count_row is None else int(count_row.get("total", 0))

        cursor.execute(
          page_sql,
          tuple(params + [recording_filter.page_size, offset]),
        )
        items = tuple(cursor.fetchall() or ())

    return LibraryPage(
      total=total,
      page=recording_filter.page,
      page_size=recording_filter.page_size,
      items=items,
    )

  def recordings(
    self,
    recording_filter: LibraryRecordingFilter,
  ) -> LibraryPage:
    """Return all persistent recording resources for a future Admin view."""
    return self._recordings(recording_filter)

  def recordings_for_user(
    self,
    app_user_id: int,
    recording_filter: LibraryRecordingFilter,
  ) -> LibraryPage:
    """Return persistent recordings owned by one server-selected user."""
    if type(app_user_id) is not int or app_user_id < 1:
      raise ValueError("app_user_id must be a positive integer")
    return self._recordings(recording_filter, app_user_id=app_user_id)

  def _rooms_for(self, cursor, rows) -> dict:
    """Look up the room metadata for one page of observations, in one query."""
    keys = [_room_key(row.get("observed_at"), row.get("room_id")) for row in rows]
    if not keys:
      return dict()

    ##
    ## Two plain IN lists rather than a row constructor.  Both are built only
    ## from %s placeholders, so nothing but bound values reaches the statement -
    ## the rule the sql construction invariant enforces across this package.
    ##
    ## The pair itself is matched afterwards, in Python: this may fetch a few
    ## rows whose (now, id) combination nobody asked for, and those simply never
    ## match a key and are dropped.  Both lists are at most one page long.
    ##
    observed = sorted({observed_at for observed_at, _ in keys})
    room_ids = sorted({room_id for _, room_id in keys})
    now_placeholders = ", ".join(["%s"] * len(observed))
    id_placeholders = ", ".join(["%s"] * len(room_ids))
    sql = (
      "SELECT rb.`now`, rb.id, rb.title, rb.status, rb.start_time\n"
      "    FROM room_base rb\n"
      "    WHERE rb.`now` IN ({})\n"
      "      AND rb.id IN ({})\n".format(now_placeholders, id_placeholders)
    )

    cursor.execute(sql, tuple(observed + room_ids))
    wanted = set(keys)
    rows = [
      row for row in (cursor.fetchall() or ())
      if _room_key(row.get("now"), row.get("id")) in wanted
    ]
    return _newest_rooms(rows)

  def lives(self, live_filter: LibraryLiveFilter) -> LibraryPage:
    """Return one page of recorded live observations plus the matching total.

    Exactly one item per ``live_record`` row, whatever room_base holds.
    """
    where_sql, params = _live_conditions(live_filter)

    count_sql = "SELECT COUNT(*) AS total\n" + _LIVE_FROM + where_sql

    sort_column = LIVE_SORT_COLUMNS[live_filter.sort]
    ##
    ## Every key column the sort did not already use, so two observations can
    ## never swap places between one page request and the next.
    ##
    tie_breakers = [one for one in _LIVE_KEY_COLUMNS if one != sort_column]
    order_sql = "    ORDER BY {} {}, {}\n".format(
      sort_column,
      "ASC" if live_filter.order == "asc" else "DESC",
      ", ".join("{} ASC".format(one) for one in tie_breakers),
    )
    page_sql = (
      "SELECT" + _LIVE_COLUMNS + _LIVE_FROM + where_sql + order_sql
      + "    LIMIT %s OFFSET %s\n"
    )
    offset = (live_filter.page - 1) * live_filter.page_size

    with self._database.get_connection() as connector:
      with connector.cursor() as cursor:
        cursor.execute(count_sql, tuple(params))
        count_row = cursor.fetchone()
        total = 0 if count_row is None else int(count_row.get("total", 0))

        cursor.execute(page_sql, tuple(params + [live_filter.page_size, offset]))
        rows = list(cursor.fetchall() or ())

        rooms = self._rooms_for(cursor, rows)

    ##
    ## Merged rather than joined, in the order the server produced the rows.
    ##
    items = list()
    for row in rows:
      room = rooms.get(_room_key(row.get("observed_at"), row.get("room_id")))
      item = dict(row)
      item["title"] = None if room is None else room.get("title")
      item["room_status"] = None if room is None else room.get("status")
      items.append(item)

    return LibraryPage(
      total=total,
      page=live_filter.page,
      page_size=live_filter.page_size,
      items=tuple(items),
    )


##
## One live observation, without any room metadata attached.
##
## room_base is deliberately absent from this statement.  It is keyed on
## (now, id, start_time), so one live_record can match several room rows, and a
## join would turn one observation into several library entries - a duplicate
## the pager cannot even count consistently, since the total comes from
## live_record while the items would not.  The room's title and status are
## fetched separately and merged afterwards.
##
_LIVE_COLUMNS = '''
      lr.`now`          AS observed_at,
      lr.platform,
      lr.room_id,
      lr.owner_user_id,
      lr.start_time,
      lr.finish_time,
      lr.status_code,
      s.nickname,
      s.directory_name,
      pa.person_id,
      p.display_name    AS person_display_name
'''

_LIVE_FROM = '''
    FROM live_record lr
    LEFT JOIN share_url s
      ON s.owner_user_id = lr.owner_user_id
    LEFT JOIN person_account pa
      ON pa.platform = lr.platform
     AND pa.owner_user_id = lr.owner_user_id
    LEFT JOIN person p
      ON p.person_id = pa.person_id
'''

##
## Every part of live_record's primary key, so a tie can always be broken.
##
_LIVE_KEY_COLUMNS = ("lr.`now`", "lr.platform", "lr.owner_user_id", "lr.room_id")


def _live_conditions(live_filter: LibraryLiveFilter) -> tuple:
  clauses = ["lr.platform = %s"]
  params = [live_filter.platform]

  if live_filter.keyword is not None:
    pattern = escape_like(live_filter.keyword)
    ##
    ## The title lives on room_base, and is matched with EXISTS rather than a
    ## join for the same reason the columns above avoid one: EXISTS answers
    ## yes or no once, however many snapshots the room has.
    ##
    clauses.append(
      "(lr.room_id LIKE %s"
      " OR s.nickname LIKE %s"
      " OR p.display_name LIKE %s"
      " OR EXISTS (SELECT 1 FROM room_base rb"
      " WHERE rb.id = lr.room_id AND rb.`now` = lr.`now`"
      " AND rb.title LIKE %s))"
    )
    params.extend([pattern, pattern, pattern, pattern])

  if live_filter.owner_user_id is not None:
    clauses.append("lr.owner_user_id = %s")
    params.append(live_filter.owner_user_id)

  if live_filter.person_id is not None:
    clauses.append("pa.person_id = %s")
    params.append(live_filter.person_id)

  return ("    WHERE " + "\n      AND ".join(clauses) + "\n", params)


def _room_key(observed_at, room_id) -> tuple:
  return (str(observed_at), str(room_id))


def _newest_rooms(rows) -> dict:
  """Collapse room snapshots to one per observation, newest start first.

  Several snapshots of the same room at the same instant are possible, and
  which one is shown must not depend on the order the database happened to
  return them.
  """
  newest = dict()
  for row in rows or ():
    key = _room_key(row.get("now"), row.get("id"))
    start = row.get("start_time")
    current = newest.get(key)
    if current is None:
      newest[key] = row
      continue
    current_start = current.get("start_time")
    if start is not None and (current_start is None or start > current_start):
      newest[key] = row
  return newest
