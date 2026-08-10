##<<Base>>
from dataclasses import dataclass, field
from datetime import datetime
from urllib.parse import urlparse

##<<Third-part>>
from backend.src.library.baselib import get_dict_attr
from backend.src.platform.douyin.douyin_live_external_info import LiveExternal


##
## Nickname sanitising has to be the *same* rule the live path uses.  A live
## download writes share_url.directory_name through LiveExternal._replaceT, so a
## second rule here would give one owner two folders.  The method does not touch
## instance state, so one shared instance is enough.
##
_SANITIZER = LiveExternal()

MEDIA_VIDEO = "video"
MEDIA_IMAGE = "image"
MEDIA_MUSIC = "music"
MEDIA_COVER = "cover"

AWEME_TYPE_VIDEO = "video"
AWEME_TYPE_IMAGE = "image"

SOURCE_API = "api"
SOURCE_HTML = "html"

DEFAULT_MEDIA_SWITCHES = {
  MEDIA_VIDEO: True,
  "images": True,
  MEDIA_MUSIC: True,
  MEDIA_COVER: True,
}

##
## File names are built from identity parts only - no caption - so they stay well
## inside the filesystem's 255-byte per-component limit without any trimming.
## Directory names still need that care, because they come from nicknames; see
## douyin_owner_directory.fit_directory_name.
##

##
## Extensions are fixed per media kind rather than taken from the url: these
## addresses carry signed query strings and often no usable suffix at all.
##
_EXTENSIONS = {
  MEDIA_VIDEO: ".mp4",
  MEDIA_IMAGE: ".jpg",
  MEDIA_MUSIC: ".mp3",
  MEDIA_COVER: ".jpg",
}


class AwemeUnavailable(ValueError):
  """The payload does not describe a downloadable post.

  Deleted, private and follower-only posts land here.  That is an ordinary
  outcome of asking about a link, not a failure of this program, so the caller
  reports it and moves on.
  """


@dataclass(frozen=True)
class MediaItem:
  kind: str
  url: str
  file_name: str
  ##
  ## The part of ``file_name`` that cannot drift, used together with the aweme id
  ## to recognise a file this post already produced.  Matching the whole name
  ## would tie dedup to the exact naming scheme, so a file written by an earlier
  ## version - names used to carry the post caption - would go unrecognised and be
  ## fetched a second time under the new name.
  ##
  identity: str = ""
  index: int = None


@dataclass(frozen=True)
class AwemeDetail:
  aweme_id: str
  aweme_type: str
  desc: str
  create_time: datetime
  owner_user_id: str
  sec_user_id: str
  nickname: str
  directory_name: str
  media: tuple = field(default_factory=tuple)
  source: str = SOURCE_API

  @property
  def media_count(self) -> int:
    """How many files this run plans to fetch.

    Driven by the media switches, so it is not a count of what the post
    objectively contains.
    """
    return len(self.media)

  @property
  def is_image_post(self) -> bool:
    return self.aweme_type == AWEME_TYPE_IMAGE


def sanitize_text(value, replace: str = None):
  """Strip characters that cannot appear in a file or directory name."""
  return _SANITIZER._replaceT(value, replace=replace)


def _first_http_url(url_list):
  """Return the first usable mirror from a platform url list."""
  if not isinstance(url_list, (list, tuple)):
    return None
  for candidate in url_list:
    if not isinstance(candidate, str) or not candidate.strip():
      continue
    if urlparse(candidate.strip()).scheme in ("http", "https"):
      return candidate.strip()
  return None


def _create_time(payload):
  """Convert the unix ``create_time`` to a datetime, or ``None``."""
  raw = get_dict_attr(payload, "$.create_time")
  if not isinstance(raw, int) or isinstance(raw, bool) or raw <= 0:
    return None
  try:
    return datetime.fromtimestamp(raw)
  except (OverflowError, OSError, ValueError):
    return None


def naming_tick(create_time) -> str:
  """Return the file-name prefix for a post.

  Deliberately the post's own publish time rather than ``now()``: the name has
  to come out the same on a re-run, or the "already downloaded" check can never
  recognise its own files.  Missing publish time means no prefix.
  """
  if create_time is None:
    return ""
  return create_time.strftime("%Y%m%d%H%M%S")


def _compose_name(parts, extension: str) -> str:
  """Build a file name from identity parts only.

  Every part here is fixed-width by construction - a 14-character tick, a 19-digit
  aweme id, a short media marker - so the result cannot approach the filesystem's
  per-component byte limit and needs no trimming.  Captions are deliberately kept
  out of file names; the post's own text lives in ``aweme_record.desc``.
  """
  return "_".join([part for part in parts if part]) + extension


def _enabled(switches, key: str) -> bool:
  if not isinstance(switches, dict):
    return bool(DEFAULT_MEDIA_SWITCHES.get(key, True))
  return switches.get(key, DEFAULT_MEDIA_SWITCHES.get(key, True)) is True


def _video_item(payload, aweme_id, tick):
  url = _first_http_url(get_dict_attr(payload, "$.video.play_addr.url_list"))
  if url is None:
    return None
  return MediaItem(
    kind=MEDIA_VIDEO,
    url=url,
    file_name=_compose_name(
      (tick, aweme_id),
      _EXTENSIONS[MEDIA_VIDEO],
    ),
    ##
    ## a post has one video, so the extension alone separates it from the other
    ## kinds - and it still matches a name written when captions were included
    ##
    identity=_EXTENSIONS[MEDIA_VIDEO],
  )


def _image_items(payload, aweme_id, tick):
  images = get_dict_attr(payload, "$.images")
  if not isinstance(images, (list, tuple)):
    return []
  items = []
  position = 0
  for image in images:
    if not isinstance(image, dict):
      continue
    url = _first_http_url(image.get("url_list"))
    if url is None:
      continue
    ##
    ## the index numbers what was actually collected, so a skipped entry does
    ## not leave a gap in the file names
    ##
    position += 1
    marker = "{:02d}".format(position)
    items.append(
      MediaItem(
        kind=MEDIA_IMAGE,
        url=url,
        file_name=_compose_name(
          (tick, aweme_id, marker),
          _EXTENSIONS[MEDIA_IMAGE],
        ),
        identity="_" + marker + _EXTENSIONS[MEDIA_IMAGE],
        index=position,
      )
    )
  return items


def _music_item(payload, aweme_id, tick):
  url = _first_http_url(get_dict_attr(payload, "$.music.play_url.url_list"))
  if url is None:
    return None
  return MediaItem(
    kind=MEDIA_MUSIC,
    url=url,
    file_name=_compose_name(
      (tick, aweme_id, MEDIA_MUSIC),
      _EXTENSIONS[MEDIA_MUSIC],
    ),
    identity="_" + MEDIA_MUSIC + _EXTENSIONS[MEDIA_MUSIC],
  )


def _cover_item(payload, aweme_id, tick):
  url = _first_http_url(get_dict_attr(payload, "$.video.cover.url_list"))
  if url is None:
    url = _first_http_url(
      get_dict_attr(payload, "$.video.dynamic_cover.url_list")
    )
  if url is None:
    return None
  return MediaItem(
    kind=MEDIA_COVER,
    url=url,
    file_name=_compose_name(
      (tick, aweme_id, MEDIA_COVER),
      _EXTENSIONS[MEDIA_COVER],
    ),
    identity="_" + MEDIA_COVER + _EXTENSIONS[MEDIA_COVER],
  )


def detect_aweme_type(payload) -> str:
  """Image posts are the ones carrying a non-empty ``images`` list.

  The payload decides, not the url: a ``/note/`` link can serve a video and a
  ``/video/`` link can serve an image post.
  """
  images = get_dict_attr(payload, "$.images")
  if isinstance(images, (list, tuple)) and len(images) > 0:
    return AWEME_TYPE_IMAGE
  return AWEME_TYPE_VIDEO


def build_media(payload, aweme_type, aweme_id, tick, switches):
  """Return the media files to fetch, in download order."""
  items = []
  if aweme_type == AWEME_TYPE_IMAGE:
    if _enabled(switches, "images"):
      items.extend(_image_items(payload, aweme_id, tick))
  else:
    if _enabled(switches, MEDIA_VIDEO):
      video = _video_item(payload, aweme_id, tick)
      if video is not None:
        items.append(video)

  if _enabled(switches, MEDIA_MUSIC):
    music = _music_item(payload, aweme_id, tick)
    if music is not None:
      items.append(music)

  if _enabled(switches, MEDIA_COVER):
    cover = _cover_item(payload, aweme_id, tick)
    if cover is not None:
      items.append(cover)

  return tuple(items)


def build_aweme_detail(
  payload,
  aweme_id: str = None,
  switches: dict = None,
  source: str = SOURCE_API,
) -> AwemeDetail:
  """Turn a platform post payload into the structure the downloader consumes.

  ``payload`` is the post object itself (``aweme_detail`` in the API response),
  already unwrapped by the resolver, so both the API and the HTML fallback reach
  this function with the same shape.

  Raises ``AwemeUnavailable`` when the payload carries no post or no id: that is
  what a deleted or private link looks like.
  """
  if not isinstance(payload, dict) or not payload:
    raise AwemeUnavailable("post payload is empty")

  resolved_id = get_dict_attr(payload, "$.aweme_id")
  if not isinstance(resolved_id, str) or not resolved_id.strip():
    resolved_id = aweme_id
  if not isinstance(resolved_id, str) or not resolved_id.strip():
    raise AwemeUnavailable("post payload carries no aweme id")
  resolved_id = resolved_id.strip()

  aweme_type = detect_aweme_type(payload)
  create_time = _create_time(payload)
  tick = naming_tick(create_time)
  ##
  ## Kept for the record only.  Captions are not part of file names: the poster can
  ## edit one, which would rename the file and make dedup miss it, and a caption is
  ## unbounded while a path component is not.
  ##
  desc = get_dict_attr(payload, "$.desc")
  desc = desc if isinstance(desc, str) else ""

  nickname = get_dict_attr(payload, "$.author.nickname")
  nickname = nickname if isinstance(nickname, str) else ""
  owner_user_id = get_dict_attr(payload, "$.author.uid")
  sec_user_id = get_dict_attr(payload, "$.author.sec_uid")

  media = build_media(
    payload,
    aweme_type,
    resolved_id,
    tick,
    switches,
  )
  if not media:
    raise AwemeUnavailable(
      "post {} exposes no downloadable media".format(resolved_id)
    )

  return AwemeDetail(
    aweme_id=resolved_id,
    aweme_type=aweme_type,
    desc=desc,
    create_time=create_time,
    owner_user_id=str(owner_user_id) if owner_user_id is not None else "",
    sec_user_id=sec_user_id if isinstance(sec_user_id, str) else "",
    nickname=nickname,
    directory_name=sanitize_text(nickname) if nickname else "",
    media=media,
    source=source,
  )
