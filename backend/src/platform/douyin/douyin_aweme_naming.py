##<<Base>>
import re

##<<Third-part>>
from backend.src.platform.douyin.douyin_aweme_external_info import (
  MEDIA_COVER,
  MEDIA_IMAGE,
  MEDIA_MUSIC,
  MEDIA_VIDEO,
)


##
## >>============================= one rule, two readers =============================>>
##
##
## How a downloaded file is recognised as belonging to a post.
##
## The downloader asks this to decide whether a file is already on disk and can
## be skipped.  Media asset discovery asks it to decide whether a file in a
## post's directory is that post's media.  They are the same question, and the
## day they answer it differently is the day the interface reports "no media"
## for a directory the downloader considers complete - or the other way round.
##
## So the rule lives here, in one place, with no database and no configuration
## behind it.  ``DouyinAwemeDownloader`` delegates to it; nothing about its
## behaviour changed when it moved.
##


def carries_aweme_id(file_name: str, aweme_id: str) -> bool:
  """Whether ``file_name`` names this post, on an underscore boundary.

  A plain substring test would let one id match inside a longer one - the id
  ``7657271784144009946`` appears inside ``9957657271784144009946`` - and skip a
  download because of an unrelated post's file.  Real ids are all 19 digits, so
  equal-length ids cannot nest and the bug would never fire on live data; that
  is a property of the data, not of the code, and not worth relying on.
  """
  if not file_name or not aweme_id:
    return False
  stem = file_name.rsplit(".", 1)[0]
  return aweme_id in stem.split("_")


##
## The stable tail of each media kind, exactly as douyin_aweme_external_info
## composes it.  A file is that kind when it carries the post's id *and* ends
## this way, which is what lets a name written by an older version - they used
## to carry the post's caption - still be recognised.
##
## Order matters. ``_cover.jpg`` and ``_01.jpg`` are both jpgs carrying the id,
## and only the tail separates them, so the named kinds are decided before the
## positional one.
##
_IMAGE_TAIL = re.compile(r"_\d{2}\.jpg$")


def post_media_kind(file_name: str, aweme_id: str):
  """Which kind of media this file is for this post, or None.

  None for everything else in the directory: ``info.txt``, a partial transfer,
  a file belonging to another post, a hidden file, anything whose extension
  this program never writes.  A directory listing is not a media list.
  """
  if not carries_aweme_id(file_name, aweme_id):
    return None

  ##
  ## Named kinds first - see the note above.
  ##
  if file_name.endswith("_" + MEDIA_COVER + ".jpg"):
    return MEDIA_COVER
  if file_name.endswith("_" + MEDIA_MUSIC + ".mp3"):
    return MEDIA_MUSIC
  if _IMAGE_TAIL.search(file_name):
    return MEDIA_IMAGE
  if file_name.endswith(".mp4"):
    return MEDIA_VIDEO
  return None


def image_position(file_name: str):
  """The position an image file records in its name, or None.

  Used only for ordering, so that image 2 follows image 1 rather than whatever
  order the filesystem happened to hand back.
  """
  found = _IMAGE_TAIL.search(file_name)
  if found is None:
    return None
  return int(found.group(0)[1:3])
