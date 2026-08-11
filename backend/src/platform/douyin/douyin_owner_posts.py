##<<Base>>
from dataclasses import dataclass, field

##<<Third-part>>
from backend.src.library.baselib import get_dict_attr
from backend.src.library.loglib import get_logger


##
## Cursor semantics: the platform hands back the cursor for the *next* page in
## ``max_cursor``, and ``has_more`` says whether asking again is worth it.  A
## first request starts at 0.  Verified over three pages: 19 + 18 + 18 items with
## no overlap between them.
##
FIRST_CURSOR = 0


@dataclass(frozen=True)
class OwnerPostPage:
  """One page of an owner's posts.

  ``payloads`` are the platform's own post objects, untouched.  They are the same
  shape ``POST_DETAIL`` returns, so ``build_aweme_detail`` consumes them directly
  and downloading a page costs no extra requests.
  """

  payloads: tuple = field(default_factory=tuple)
  next_cursor: int = FIRST_CURSOR
  has_more: bool = False

  @property
  def count(self) -> int:
    return len(self.payloads)


def _cursor(value) -> int:
  if isinstance(value, bool) or not isinstance(value, (int, float)):
    return FIRST_CURSOR
  return int(value)


def _has_more(value) -> bool:
  ##
  ## The platform sends 1/0 rather than true/false.
  ##
  if isinstance(value, bool):
    return value
  if isinstance(value, (int, float)):
    return int(value) == 1
  if isinstance(value, str):
    return value.strip() in ("1", "true", "True")
  return False


def build_post_page(payload) -> OwnerPostPage:
  """Turn a ``USER_POST`` payload into one page.

  An empty ``aweme_list`` is a valid answer here: an owner really can have no
  posts, and the pages after the last one are empty too.  The refusals that *look*
  like emptiness - empty body, ``status_msg: blocked``, a verification bundle -
  are caught upstream by ``douyin_session.read_payload``, so by the time a payload
  reaches this function an empty list means what it says.
  """
  if not isinstance(payload, dict):
    return OwnerPostPage()

  raw = payload.get("aweme_list")
  items = []
  for item in raw if isinstance(raw, list) else []:
    if not isinstance(item, dict):
      continue
    if not get_dict_attr(item, "$.aweme_id"):
      ##
      ## Without an id the item cannot be downloaded, deduplicated or recorded.
      ##
      continue
    items.append(item)

  return OwnerPostPage(
    payloads=tuple(items),
    next_cursor=_cursor(payload.get("max_cursor")),
    has_more=_has_more(payload.get("has_more")),
  )


def fetch_post_page(api, sec_user_id: str, cursor=FIRST_CURSOR, count=None):
  """Fetch one page of an owner's posts.

  ``api`` is a ``DouyinOwnerApi``.  ``SessionExpired`` propagates - the caller
  must say "log in again" rather than render an empty list.
  """
  if not isinstance(sec_user_id, str) or not sec_user_id.strip():
    raise ValueError("sec_user_id is required")
  page_size = count if count is not None else api.config.owner_page_size
  payload = api.get(
    "$.USER_POST",
    {
      "sec_user_id": sec_user_id.strip(),
      "max_cursor": _cursor(cursor),
      "count": page_size,
      "publish_video_strategy_type": 2,
    },
  )
  return build_post_page(payload)


def iter_all_posts(api, sec_user_id: str, max_pages=0, count=None):
  """Yield every post payload for one owner, walking the pages.

  ``max_pages`` of 0 means no cap.  Stops when the platform says there is no more,
  when a page comes back empty, or when a cursor repeats - the last of those
  guards against a cursor that never advances, which would otherwise loop forever.
  """
  cursor = FIRST_CURSOR
  seen_cursors = {cursor}
  seen_ids = set()
  page_index = 0

  while True:
    page = fetch_post_page(api, sec_user_id, cursor=cursor, count=count)
    page_index += 1

    for item in page.payloads:
      aweme_id = get_dict_attr(item, "$.aweme_id")
      if aweme_id in seen_ids:
        continue
      seen_ids.add(aweme_id)
      yield item

    if not page.has_more or page.count == 0:
      return
    if max_pages and page_index >= max_pages:
      get_logger().info(
        "owner {} stopped at the configured page cap of {}".format(
          sec_user_id,
          max_pages,
        )
      )
      return
    if page.next_cursor in seen_cursors:
      get_logger().warning(
        "owner {} returned a repeating cursor at page {}, stopping".format(
          sec_user_id,
          page_index,
        )
      )
      return
    seen_cursors.add(page.next_cursor)
    cursor = page.next_cursor
