import unittest
from datetime import datetime

from backend.src.platform.douyin.douyin_aweme_external_info import (
  AWEME_TYPE_IMAGE,
  AWEME_TYPE_VIDEO,
  AwemeUnavailable,
  MEDIA_COVER,
  MEDIA_IMAGE,
  MEDIA_MUSIC,
  MEDIA_VIDEO,
  SOURCE_HTML,
  build_aweme_detail,
  detect_aweme_type,
  naming_tick,
  sanitize_text,
)
from backend.src.platform.douyin.douyin_live_external_info import LiveExternal


AWEME_ID = "7123456789012345678"
##
## 2024-04-07 18:01:27 local time
##
CREATE_TIME = 1712484087


def video_payload(**overrides):
  payload = {
    "aweme_id": AWEME_ID,
    "desc": "今天的日落",
    "create_time": CREATE_TIME,
    "author": {
      "uid": "1234567890",
      "sec_uid": "MS4wLjABAAAAsec",
      "nickname": "落日 摄影师",
    },
    "video": {
      "play_addr": {"url_list": ["https://v.example.test/play.mp4"]},
      "cover": {"url_list": ["https://p.example.test/cover.jpeg"]},
    },
    "music": {"play_url": {"url_list": ["https://m.example.test/song.mp3"]}},
  }
  payload.update(overrides)
  return payload


def image_payload(image_count=3, **overrides):
  payload = video_payload(**overrides)
  payload.pop("video", None)
  payload["images"] = [
    {"url_list": ["https://p.example.test/img{}.webp".format(i)]}
    for i in range(1, image_count + 1)
  ]
  return payload


class AwemeTypeDetectionTest(unittest.TestCase):
  def test_non_empty_images_means_image_post(self):
    self.assertEqual(detect_aweme_type(image_payload()), AWEME_TYPE_IMAGE)

  def test_absent_images_means_video_post(self):
    self.assertEqual(detect_aweme_type(video_payload()), AWEME_TYPE_VIDEO)

  def test_empty_image_list_means_video_post(self):
    self.assertEqual(
      detect_aweme_type(video_payload(images=[])),
      AWEME_TYPE_VIDEO,
    )

  def test_null_image_list_means_video_post(self):
    self.assertEqual(
      detect_aweme_type(video_payload(images=None)),
      AWEME_TYPE_VIDEO,
    )


class VideoPostMediaTest(unittest.TestCase):
  def test_video_post_yields_video_music_and_cover(self):
    detail = build_aweme_detail(video_payload())

    self.assertEqual(detail.aweme_type, AWEME_TYPE_VIDEO)
    self.assertEqual(
      [item.kind for item in detail.media],
      [MEDIA_VIDEO, MEDIA_MUSIC, MEDIA_COVER],
    )
    self.assertEqual(detail.media_count, 3)

  def test_video_file_name_is_the_tick_and_the_id(self):
    detail = build_aweme_detail(video_payload())
    video = detail.media[0]

    tick = naming_tick(datetime.fromtimestamp(CREATE_TIME))
    self.assertEqual(video.file_name, "{}_{}.mp4".format(tick, AWEME_ID))

  def test_music_and_cover_names_are_stable_suffixes(self):
    detail = build_aweme_detail(video_payload())
    tick = naming_tick(datetime.fromtimestamp(CREATE_TIME))

    self.assertEqual(
      detail.media[1].file_name,
      "{}_{}_music.mp3".format(tick, AWEME_ID),
    )
    self.assertEqual(
      detail.media[2].file_name,
      "{}_{}_cover.jpg".format(tick, AWEME_ID),
    )

  def test_dynamic_cover_is_used_when_the_static_cover_is_missing(self):
    payload = video_payload()
    payload["video"].pop("cover")
    payload["video"]["dynamic_cover"] = {
      "url_list": ["https://p.example.test/animated.webp"]
    }

    detail = build_aweme_detail(payload)
    cover = [i for i in detail.media if i.kind == MEDIA_COVER][0]

    self.assertEqual(cover.url, "https://p.example.test/animated.webp")

  def test_first_usable_mirror_is_chosen(self):
    payload = video_payload()
    payload["video"]["play_addr"]["url_list"] = [
      "",
      "   ",
      None,
      "ftp://v.example.test/nope.mp4",
      "https://v.example.test/second.mp4",
    ]

    detail = build_aweme_detail(payload)

    self.assertEqual(detail.media[0].url, "https://v.example.test/second.mp4")


class ImagePostMediaTest(unittest.TestCase):
  def test_image_post_yields_one_item_per_image(self):
    detail = build_aweme_detail(image_payload(image_count=3))

    self.assertEqual(detail.aweme_type, AWEME_TYPE_IMAGE)
    self.assertTrue(detail.is_image_post)
    self.assertEqual(
      [item.kind for item in detail.media],
      [MEDIA_IMAGE, MEDIA_IMAGE, MEDIA_IMAGE, MEDIA_MUSIC],
    )

  def test_image_names_are_zero_padded_and_indexed_from_one(self):
    detail = build_aweme_detail(image_payload(image_count=2))
    tick = naming_tick(datetime.fromtimestamp(CREATE_TIME))

    self.assertEqual(
      [item.file_name for item in detail.media if item.kind == MEDIA_IMAGE],
      [
        "{}_{}_01.jpg".format(tick, AWEME_ID),
        "{}_{}_02.jpg".format(tick, AWEME_ID),
      ],
    )
    self.assertEqual(
      [item.index for item in detail.media if item.kind == MEDIA_IMAGE],
      [1, 2],
    )

  def test_unusable_image_entries_do_not_leave_gaps_in_the_numbering(self):
    payload = image_payload(image_count=3)
    payload["images"][1] = {"url_list": []}

    detail = build_aweme_detail(payload)
    images = [item for item in detail.media if item.kind == MEDIA_IMAGE]

    self.assertEqual([item.index for item in images], [1, 2])
    self.assertEqual(
      [item.url for item in images],
      [
        "https://p.example.test/img1.webp",
        "https://p.example.test/img3.webp",
      ],
    )

  def test_image_post_has_no_video_item(self):
    detail = build_aweme_detail(image_payload())

    self.assertEqual(
      [item for item in detail.media if item.kind == MEDIA_VIDEO],
      [],
    )


class MediaSwitchTest(unittest.TestCase):
  def test_video_only(self):
    detail = build_aweme_detail(
      video_payload(),
      switches={"video": True, "images": True, "music": False, "cover": False},
    )

    self.assertEqual([item.kind for item in detail.media], [MEDIA_VIDEO])
    self.assertEqual(detail.media_count, 1)

  def test_music_only_on_an_image_post(self):
    detail = build_aweme_detail(
      image_payload(),
      switches={"video": True, "images": False, "music": True, "cover": False},
    )

    self.assertEqual([item.kind for item in detail.media], [MEDIA_MUSIC])

  def test_cover_only(self):
    detail = build_aweme_detail(
      video_payload(),
      switches={"video": False, "images": False, "music": False, "cover": True},
    )

    self.assertEqual([item.kind for item in detail.media], [MEDIA_COVER])

  def test_media_count_reflects_the_switches_not_the_post(self):
    """media_count is what this run plans to fetch, not what the post holds."""
    payload = image_payload(image_count=9)

    everything = build_aweme_detail(payload)
    images_off = build_aweme_detail(
      payload,
      switches={"images": False, "music": True, "cover": True},
    )

    self.assertEqual(everything.media_count, 10)
    self.assertEqual(images_off.media_count, 1)

  def test_all_switches_off_is_reported_as_unavailable(self):
    with self.assertRaises(AwemeUnavailable):
      build_aweme_detail(
        video_payload(),
        switches={
          "video": False,
          "images": False,
          "music": False,
          "cover": False,
        },
      )

  def test_missing_switch_keys_default_to_enabled(self):
    detail = build_aweme_detail(video_payload(), switches={})

    self.assertEqual(
      [item.kind for item in detail.media],
      [MEDIA_VIDEO, MEDIA_MUSIC, MEDIA_COVER],
    )

  def test_non_true_switch_values_are_treated_as_off(self):
    detail = build_aweme_detail(
      video_payload(),
      switches={"video": True, "music": "yes", "cover": 1},
    )

    self.assertEqual([item.kind for item in detail.media], [MEDIA_VIDEO])


class NamingTest(unittest.TestCase):
  def test_tick_is_the_publish_time_so_a_rerun_produces_the_same_name(self):
    first = build_aweme_detail(video_payload())
    second = build_aweme_detail(video_payload())

    self.assertEqual(
      first.media[0].file_name,
      second.media[0].file_name,
    )
    self.assertTrue(
      first.media[0].file_name.startswith(
        datetime.fromtimestamp(CREATE_TIME).strftime("%Y%m%d%H%M%S")
      )
    )

  def test_missing_publish_time_drops_the_prefix(self):
    detail = build_aweme_detail(video_payload(create_time=None))

    self.assertIsNone(detail.create_time)
    self.assertEqual(detail.media[0].file_name, "{}.mp4".format(AWEME_ID))

  def test_zero_publish_time_is_treated_as_missing(self):
    detail = build_aweme_detail(video_payload(create_time=0))

    self.assertIsNone(detail.create_time)

  def test_the_name_is_the_same_whatever_the_caption(self):
    tick = naming_tick(datetime.fromtimestamp(CREATE_TIME))
    expected = "{}_{}.mp4".format(tick, AWEME_ID)

    for caption in ("", "///", "日落", "a/b:c*d?e", None):
      with self.subTest(caption=caption):
        detail = build_aweme_detail(video_payload(desc=caption))
        self.assertEqual(detail.media[0].file_name, expected)


class FileNameContentTest(unittest.TestCase):
  """File names are built from identity parts only - never the caption.

  A caption is unbounded, editable by the poster, and would rename the file on a
  later run.  The post's own text is kept in aweme_record.desc instead.
  """

  def test_no_kind_of_file_name_contains_the_caption(self):
    caption = "会被写进文件名就错了"
    for payload in (
      video_payload(desc=caption),
      image_payload(image_count=2, desc=caption),
    ):
      detail = build_aweme_detail(payload)
      for item in detail.media:
        with self.subTest(kind=item.kind, index=item.index):
          self.assertNotIn(caption, item.file_name)
          self.assertNotIn("会被", item.file_name)

  def test_the_caption_is_still_recorded_on_the_detail(self):
    detail = build_aweme_detail(video_payload(desc="留在记录里"))

    self.assertEqual(detail.desc, "留在记录里")

  def test_a_very_long_caption_cannot_affect_the_name(self):
    """The filesystem counts bytes and a CJK character costs three.

    With the caption out of the name there is nothing left that can grow.
    """
    short = build_aweme_detail(video_payload(desc="短"))
    long = build_aweme_detail(video_payload(desc="中" * 4000))

    self.assertEqual(
      short.media[0].file_name,
      long.media[0].file_name,
    )
    self.assertLess(len(long.media[0].file_name.encode("utf-8")), 64)

  def test_every_name_stays_well_inside_the_component_limit(self):
    for payload in (video_payload(), image_payload(image_count=9)):
      detail = build_aweme_detail(payload)
      for item in detail.media:
        with self.subTest(kind=item.kind, index=item.index):
          self.assertLess(len(item.file_name.encode("utf-8")), 64)

  def test_names_are_pure_ascii_for_a_video_post(self):
    """Nothing but the tick, the id, a marker and an extension."""
    detail = build_aweme_detail(video_payload(desc="日落 🤨 #标签"))

    for item in detail.media:
      with self.subTest(kind=item.kind):
        self.assertTrue(item.file_name.isascii())


class MediaIdentityTest(unittest.TestCase):
  """The stable tail dedup matches on, so an edited caption cannot fool it."""

  def test_each_kind_carries_a_distinct_identity(self):
    detail = build_aweme_detail(video_payload())
    identities = {item.kind: item.identity for item in detail.media}

    self.assertEqual(identities[MEDIA_VIDEO], ".mp4")
    self.assertEqual(identities[MEDIA_MUSIC], "_music.mp3")
    self.assertEqual(identities[MEDIA_COVER], "_cover.jpg")

  def test_images_are_identified_by_their_position(self):
    detail = build_aweme_detail(image_payload(image_count=3))
    images = [item for item in detail.media if item.kind == MEDIA_IMAGE]

    self.assertEqual(
      [item.identity for item in images],
      ["_01.jpg", "_02.jpg", "_03.jpg"],
    )

  def test_every_file_name_ends_with_its_identity(self):
    for payload in (video_payload(), image_payload(image_count=2)):
      detail = build_aweme_detail(payload)
      for item in detail.media:
        with self.subTest(kind=item.kind, index=item.index):
          self.assertTrue(item.file_name.endswith(item.identity))

  def test_an_edited_caption_changes_nothing_about_the_file(self):
    """A poster editing their caption must not produce a second copy.

    With the caption out of the name, the name itself is unchanged - a stronger
    guarantee than matching on the identity tail alone.
    """
    first = build_aweme_detail(video_payload(desc="原来的文案"))
    second = build_aweme_detail(video_payload(desc="改过的文案完全不同"))

    self.assertEqual(first.media[0].file_name, second.media[0].file_name)
    self.assertEqual(first.media[0].identity, second.media[0].identity)

  def test_cover_and_image_identities_do_not_collide(self):
    """Both end in .jpg, so the marker has to separate them."""
    detail = build_aweme_detail(image_payload(image_count=1))
    by_kind = {item.kind: item for item in detail.media}
    image = by_kind[MEDIA_IMAGE]

    self.assertFalse(image.file_name.endswith("_cover.jpg"))


class DirectoryNameTest(unittest.TestCase):
  def test_directory_name_matches_the_live_path_rule(self):
    """One owner must not end up with two folders.

    The live download writes share_url.directory_name with
    LiveExternal._replaceT, so the post path has to produce the same string.
    """
    nickname = "落日 摄影师/2024"
    detail = build_aweme_detail(
      video_payload(
        author={
          "uid": "1",
          "sec_uid": "MS4w",
          "nickname": nickname,
        }
      )
    )

    self.assertEqual(
      detail.directory_name,
      LiveExternal()._replaceT(nickname),
    )

  def test_sanitize_text_is_the_shared_rule(self):
    self.assertEqual(
      sanitize_text("a b/c"),
      LiveExternal()._replaceT("a b/c"),
    )

  def test_missing_nickname_yields_an_empty_directory_name(self):
    detail = build_aweme_detail(
      video_payload(author={"uid": "1", "sec_uid": "MS4w"})
    )

    self.assertEqual(detail.directory_name, "")
    self.assertEqual(detail.nickname, "")


class UnavailablePostTest(unittest.TestCase):
  def test_empty_payload(self):
    with self.assertRaises(AwemeUnavailable):
      build_aweme_detail({})

  def test_non_mapping_payload(self):
    with self.assertRaises(AwemeUnavailable):
      build_aweme_detail(None)

  def test_payload_without_an_id_and_without_a_fallback(self):
    payload = video_payload()
    payload.pop("aweme_id")

    with self.assertRaises(AwemeUnavailable):
      build_aweme_detail(payload)

  def test_id_falls_back_to_the_one_taken_from_the_url(self):
    payload = video_payload()
    payload.pop("aweme_id")

    detail = build_aweme_detail(payload, aweme_id=AWEME_ID)

    self.assertEqual(detail.aweme_id, AWEME_ID)

  def test_payload_exposing_no_media_is_unavailable(self):
    payload = {
      "aweme_id": AWEME_ID,
      "desc": "blocked",
      "author": {"uid": "1", "sec_uid": "MS4w", "nickname": "someone"},
    }

    with self.assertRaises(AwemeUnavailable):
      build_aweme_detail(payload)


class OwnerAndSourceTest(unittest.TestCase):
  def test_owner_fields_are_carried_through(self):
    detail = build_aweme_detail(video_payload())

    self.assertEqual(detail.owner_user_id, "1234567890")
    self.assertEqual(detail.sec_user_id, "MS4wLjABAAAAsec")
    self.assertEqual(detail.nickname, "落日 摄影师")

  def test_numeric_owner_id_is_normalised_to_text(self):
    """share_url.owner_user_id is VARCHAR, so the id has to arrive as text."""
    detail = build_aweme_detail(
      video_payload(
        author={"uid": 1234567890, "sec_uid": "MS4w", "nickname": "n"}
      )
    )

    self.assertEqual(detail.owner_user_id, "1234567890")

  def test_source_is_recorded(self):
    detail = build_aweme_detail(video_payload(), source=SOURCE_HTML)

    self.assertEqual(detail.source, SOURCE_HTML)

  def test_detail_is_immutable(self):
    detail = build_aweme_detail(video_payload())

    with self.assertRaises(Exception):
      detail.aweme_id = "other"


if __name__ == "__main__":
  unittest.main()
