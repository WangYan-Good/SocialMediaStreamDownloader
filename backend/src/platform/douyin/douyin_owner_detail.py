##<<Base>>
from dataclasses import dataclass

##<<Third-part>>
from backend.src.library.baselib import get_dict_attr
from backend.src.platform.douyin.douyin_session import SessionExpired


class OwnerUnavailable(ValueError):
  """The payload carries no usable owner.

  A deleted or restricted account looks like this.  It is an ordinary answer
  about a link, not a failure of this program, so callers report it and move on.
  Distinct from ``SessionExpired``, which means *we* need a new cookie.
  """


@dataclass(frozen=True)
class OwnerDetail:
  sec_user_id: str
  uid: str
  nickname: str
  ##
  ## The handle a person types or shares - 抖音号.  Not always set.
  ##
  unique_id: str
  signature: str
  avatar_url: str
  follower_count: int
  following_count: int
  ##
  ## How many posts the platform says the owner has.  Compared against how many
  ## are recorded locally to answer "how much of this owner do I have".
  ##
  aweme_count: int
  total_favorited: int


def _first_http_url(url_list):
  if not isinstance(url_list, (list, tuple)):
    return ""
  for candidate in url_list:
    if isinstance(candidate, str) and candidate.strip().startswith("http"):
      return candidate.strip()
  return ""


def _text(value) -> str:
  return value.strip() if isinstance(value, str) else ""


def _count(value) -> int:
  ##
  ## Counts arrive as ints, but a missing one must read as 0 rather than crash a
  ## page render.
  ##
  if isinstance(value, bool) or not isinstance(value, int):
    return 0
  return value if value >= 0 else 0


def _avatar_url(user: dict) -> str:
  for path in (
    "$.avatar_larger.url_list",
    "$.avatar_medium.url_list",
    "$.avatar_thumb.url_list",
    "$.avatar_168x168.url_list",
  ):
    url = _first_http_url(get_dict_attr(user, path))
    if url:
      return url
  return ""


def build_owner_detail(payload, sec_user_id: str = None) -> OwnerDetail:
  """Turn a ``USER_DETAIL`` payload into the structure the UI consumes.

  Raises ``OwnerUnavailable`` when there is no owner in the payload.  Note that a
  dead session produces ``{"status_msg": "blocked", "user": {}}`` - that case is
  caught earlier by ``douyin_session.read_payload`` and raised as
  ``SessionExpired``, so an empty user reaching here really means the account is
  gone or restricted.
  """
  if not isinstance(payload, dict):
    raise OwnerUnavailable("owner payload is not an object")

  user = payload.get("user")
  if not isinstance(user, dict) or not user:
    raise OwnerUnavailable("owner payload carries no user")

  resolved_sec = _text(get_dict_attr(user, "$.sec_uid")) or _text(sec_user_id)
  uid = get_dict_attr(user, "$.uid")
  uid = str(uid).strip() if uid is not None else ""
  if not resolved_sec and not uid:
    raise OwnerUnavailable("owner payload carries no identity")

  return OwnerDetail(
    sec_user_id=resolved_sec,
    uid=uid,
    nickname=_text(get_dict_attr(user, "$.nickname")),
    unique_id=(
      _text(get_dict_attr(user, "$.unique_id"))
      or _text(get_dict_attr(user, "$.short_id"))
    ),
    signature=_text(get_dict_attr(user, "$.signature")),
    avatar_url=_avatar_url(user),
    follower_count=_count(get_dict_attr(user, "$.follower_count")),
    following_count=_count(get_dict_attr(user, "$.following_count")),
    aweme_count=_count(get_dict_attr(user, "$.aweme_count")),
    total_favorited=_count(get_dict_attr(user, "$.total_favorited")),
  )


def fetch_owner_detail(api, sec_user_id: str) -> OwnerDetail:
  """Fetch and parse one owner's profile.

  ``api`` is a ``DouyinOwnerApi``.  ``SessionExpired`` propagates: the caller must
  tell the user to refresh the cookie rather than show an empty profile.
  """
  if not isinstance(sec_user_id, str) or not sec_user_id.strip():
    raise ValueError("sec_user_id is required")
  payload = api.get(
    "$.USER_DETAIL",
    {
      "sec_user_id": sec_user_id.strip(),
      "publish_video_strategy_type": 2,
    },
  )
  return build_owner_detail(payload, sec_user_id=sec_user_id)
