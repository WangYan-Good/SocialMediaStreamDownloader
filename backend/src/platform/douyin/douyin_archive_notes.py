##<<Base>>
import os
from datetime import datetime
from pathlib import Path

##<<Third-part>>
from backend.src.library.loglib import get_logger


##
## Plain-text notes written beside the downloaded files.
##
## Captions are deliberately not part of file or folder names - a caption can be
## edited by its author, has no length limit, and putting it in a name would make
## the "already downloaded" check miss its own files.  But a folder called
## ``20260701081200_7657271784144009946`` tells a person nothing, so the caption
## is kept next to the media instead.
##
## Text rather than yaml on purpose: the point is that a person can see what a
## folder holds at a glance, and a file manager will preview the first line.
##

POST_NOTE_NAME = "info.txt"
OWNER_NOTE_NAME = "owner.txt"
OWNER_AVATAR_NAME = "avatar.jpg"

_TYPE_NAMES = {"video": "视频", "image": "图集"}


def _format_time(value) -> str:
  if not isinstance(value, datetime):
    return "未知"
  return value.strftime("%Y-%m-%d %H:%M:%S")


def _write_text(path: Path, text: str) -> bool:
  """Write ``text`` to ``path``.  Returns whether it landed.

  A note is a convenience, never the product: if it cannot be written the
  download it accompanies still counts as done.
  """
  try:
    os.makedirs(path.parent, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return True
  except OSError as e:
    get_logger().warning("could not write {}: {}".format(path, e))
    return False


def post_note_text(detail) -> str:
  """The caption first, then the facts that identify the post."""
  caption = (detail.desc or "").strip() or "（无文案）"
  lines = [
    caption,
    "",
    "作品 ID  : {}".format(detail.aweme_id),
    "类型     : {}".format(_TYPE_NAMES.get(detail.aweme_type, detail.aweme_type)),
    "发布时间 : {}".format(_format_time(detail.create_time)),
    "主播     : {}".format(detail.nickname or "未知"),
    "文件数   : {}".format(detail.media_count),
  ]
  return "\n".join(lines) + "\n"


def write_post_note(save_dir, detail) -> bool:
  """Write the caption note into one post's folder.

  Written on every run, not only the first.  That is what backfills a folder
  downloaded before notes existed, and what picks up an edited caption.  It costs
  a few hundred bytes and no platform request.
  """
  return _write_text(Path(save_dir) / POST_NOTE_NAME, post_note_text(detail))


def owner_note_text(owner, collected_at=None) -> str:
  """The owner's card as text, with the moment it was taken.

  The counts are a snapshot: follower numbers move constantly, so the note says
  when it was read rather than pretending to be current.
  """
  moment = collected_at if collected_at is not None else datetime.now()
  lines = [
    owner.nickname or "未知",
  ]
  if owner.unique_id:
    lines.append("@{}".format(owner.unique_id))
  lines.extend([
    "",
    "签名     : {}".format((owner.signature or "").strip() or "（无）"),
    "粉丝     : {}".format(owner.follower_count),
    "关注     : {}".format(owner.following_count),
    "作品     : {}".format(owner.aweme_count),
    "获赞     : {}".format(owner.total_favorited),
    "sec_uid  : {}".format(owner.sec_user_id),
    "uid      : {}".format(owner.uid),
    "",
    "采集时间 : {}".format(_format_time(moment)),
  ])
  return "\n".join(lines) + "\n"


def write_owner_note(owner_dir, owner, collected_at=None) -> bool:
  """Write the owner's card into their folder, replacing any earlier one."""
  return _write_text(
    Path(owner_dir) / OWNER_NOTE_NAME,
    owner_note_text(owner, collected_at=collected_at),
  )
