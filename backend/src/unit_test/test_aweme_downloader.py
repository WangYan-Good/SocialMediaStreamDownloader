import tempfile
import unittest
from datetime import datetime
from pathlib import Path
from threading import Event, Thread

from backend.src.platform.douyin import douyin_aweme_downloader as aweme_module
from backend.src.platform.douyin.douyin_aweme_downloader import (
  AWEME_PATH_SEGMENT,
  DouyinAwemeDownloader,
)
from backend.src.platform.douyin.douyin_aweme_external_info import (
  build_aweme_detail,
)
from backend.src.platform.douyin.douyin_aweme_resolver import AwemeResolution
from backend.src.unit_test.config_fixture import unified_config


AWEME_ID = "7123456789012345678"
CREATE_TIME = 1712484087
POST_URL = "https://www.douyin.com/video/" + AWEME_ID
OWNER_SEC_UID = "MS4wLjABAAAAGZkW5n1EHZD_TFyQ-QiaISBPemtKFxVVdhLSeoXhh-U"


def video_payload(**overrides):
  payload = {
    "aweme_id": AWEME_ID,
    "desc": "日落",
    "create_time": CREATE_TIME,
    "author": {
      "uid": "555",
      "sec_uid": "MS4wLjABAAAAsec",
      "nickname": "摄影师",
    },
    "video": {
      "play_addr": {"url_list": ["https://v.example.test/play.mp4"]},
      "cover": {"url_list": ["https://p.example.test/cover.jpeg"]},
    },
    "music": {"play_url": {"url_list": ["https://m.example.test/song.mp3"]}},
  }
  payload.update(overrides)
  return payload


def image_payload(image_count=3):
  payload = video_payload()
  payload.pop("video")
  payload["images"] = [
    {"url_list": ["https://p.example.test/img{}.webp".format(i)]}
    for i in range(1, image_count + 1)
  ]
  return payload


class StubResolver:
  """Stands in for the network-facing resolver."""

  def __init__(self, resolution):
    self._resolution = resolution
    self.calls = []

  def resolve(self, url, aweme_id=None):
    self.calls.append(url)
    return self._resolution

  def pause(self):
    return None


class RecordingDatabase:
  def __init__(self):
    self.owners = []
    self.records = []

  def get_aweme_record_table_tuple(self):
    return {
      key: None
      for key in (
        "platform",
        "aweme_id",
        "owner_user_id",
        "sec_user_id",
        "aweme_type",
        "desc",
        "create_time",
        "downloaded_at",
        "media_count",
        "saved_count",
        "save_dir",
        "source",
      )
    }

  def upsert_post_owner(self, record):
    self.owners.append(record)

  def upsert_aweme_record(self, record):
    self.records.append(record)


class AwemeDownloaderTestCase(unittest.TestCase):
  def setUp(self):
    self.fetched = []
    self.failures = {}
    self.skips = set()
    self._original_fetch = aweme_module.fetch_file
    aweme_module.fetch_file = self._fake_fetch
    self.addCleanup(self._restore_fetch)

  def _restore_fetch(self):
    aweme_module.fetch_file = self._original_fetch

  def _fake_fetch(self, url, save_path, file_name, **kwargs):
    self.fetched.append(
      {
        "url": url,
        "save_path": Path(save_path),
        "file_name": file_name,
        "kwargs": kwargs,
      }
    )
    if file_name in self.failures:
      raise self.failures[file_name]
    if file_name in self.skips:
      return None
    target = Path(save_path) / file_name
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(b"payload")
    return target

  def build(self, payload=None, save_path=None, database=None, **config_overrides):
    config = unified_config()
    config["download"]["test_mode"] = False
    config["download"]["user_login"] = False
    if save_path is not None:
      config["download"]["save_path"] = str(save_path)
    config["database"]["enable"] = database is not None
    for key, value in config_overrides.items():
      if key in config["download"]:
        config["download"][key] = value
      else:
        config["platform"]["douyin"]["aweme"][key] = value

    downloader = DouyinAwemeDownloader(config)
    detail = build_aweme_detail(
      payload if payload is not None else video_payload(),
      switches=config["platform"]["douyin"]["aweme"]["media"],
    )
    downloader.resolver = StubResolver(
      AwemeResolution(ok=True, aweme_id=detail.aweme_id, detail=detail)
    )
    if database is not None:
      downloader.database = database
      downloader._database_if_ready = lambda: database
      downloader._database_for_read = lambda: database
    else:
      downloader._database_if_ready = lambda: None
      downloader._database_for_read = lambda: None
    return downloader, detail


class SaveLayoutTest(AwemeDownloaderTestCase):
  def test_a_video_post_gets_its_own_folder(self):
    """Every post is archived as a unit.

    Even a single video post yields three files - video, audio track and cover -
    so filing them flat under the owner mixes several posts' pieces together.
    """
    with tempfile.TemporaryDirectory() as directory:
      downloader, detail = self.build(save_path=directory)

      result = downloader.run({"url": POST_URL})

      tick = datetime.fromtimestamp(CREATE_TIME).strftime("%Y%m%d%H%M%S")
      expected = (
        Path(directory)
        / "douyin"
        / AWEME_PATH_SEGMENT
        / detail.directory_name
        / "{}_{}".format(tick, AWEME_ID)
      )
      self.assertEqual(Path(result.save_dir), expected)
      self.assertEqual(
        {item["save_path"] for item in self.fetched},
        {expected},
      )

  def test_an_image_post_gets_its_own_folder_too(self):
    with tempfile.TemporaryDirectory() as directory:
      downloader, detail = self.build(
        payload=image_payload(3),
        save_path=directory,
      )

      result = downloader.run({"url": POST_URL})

      tick = datetime.fromtimestamp(CREATE_TIME).strftime("%Y%m%d%H%M%S")
      expected = (
        Path(directory)
        / "douyin"
        / AWEME_PATH_SEGMENT
        / detail.directory_name
        / "{}_{}".format(tick, AWEME_ID)
      )
      self.assertEqual(Path(result.save_dir), expected)

  def test_the_post_folder_is_named_from_stable_parts_only(self):
    """A re-run has to land in the same folder, so no caption and no now()."""
    with tempfile.TemporaryDirectory() as directory:
      downloader, detail = self.build(
        payload=video_payload(desc="会被改掉的文案"),
        save_path=directory,
      )

      first = downloader.build_save_dir(detail)
      second = downloader.build_save_dir(detail)

      self.assertEqual(first, second)
      self.assertNotIn("文案", first.name)
      self.assertEqual(
        first.name,
        "{}_{}".format(
          datetime.fromtimestamp(CREATE_TIME).strftime("%Y%m%d%H%M%S"),
          AWEME_ID,
        ),
      )

  def test_the_live_download_type_does_not_leak_into_the_path(self):
    """The path segment is a literal.

    $.platform.douyin.download.type is "live" process-wide, so reading it here
    would file posts under douyin/live/.
    """
    with tempfile.TemporaryDirectory() as directory:
      downloader, _ = self.build(save_path=directory)

      result = downloader.run({"url": POST_URL})

      self.assertIn("/douyin/aweme/", result.save_dir.replace("\\", "/"))
      self.assertNotIn("/douyin/live/", result.save_dir.replace("\\", "/"))

  def test_folderize_off_drops_the_owner_directory(self):
    with tempfile.TemporaryDirectory() as directory:
      downloader, detail = self.build(save_path=directory, folderize=False)

      result = downloader.run({"url": POST_URL})

      tick = datetime.fromtimestamp(CREATE_TIME).strftime("%Y%m%d%H%M%S")
      self.assertEqual(
        Path(result.save_dir),
        Path(directory)
        / "douyin"
        / AWEME_PATH_SEGMENT
        / "{}_{}".format(tick, AWEME_ID),
      )
      self.assertNotIn(detail.directory_name, result.save_dir)


class FetchPolicyTest(AwemeDownloaderTestCase):
  def test_files_are_fetched_with_skip_and_without_keeping_partials(self):
    """The post path needs the opposite of the live path on both settings."""
    with tempfile.TemporaryDirectory() as directory:
      downloader, _ = self.build(save_path=directory)

      downloader.run({"url": POST_URL})

      for item in self.fetched:
        with self.subTest(file_name=item["file_name"]):
          self.assertEqual(item["kwargs"]["on_exists"], "skip")
          self.assertIs(item["kwargs"]["keep_partial"], False)

  def test_every_media_item_is_fetched_in_order(self):
    with tempfile.TemporaryDirectory() as directory:
      downloader, detail = self.build(save_path=directory)

      result = downloader.run({"url": POST_URL})

      self.assertEqual(
        [item["file_name"] for item in self.fetched],
        [item.file_name for item in detail.media],
      )
      self.assertEqual(result.saved_count, detail.media_count)
      self.assertTrue(result.ok)

  def test_one_failed_file_does_not_stop_the_others(self):
    with tempfile.TemporaryDirectory() as directory:
      downloader, detail = self.build(save_path=directory)
      self.failures[detail.media[0].file_name] = OSError("connection reset")

      result = downloader.run({"url": POST_URL})

      self.assertTrue(result.ok)
      self.assertEqual(len(self.fetched), detail.media_count)
      self.assertEqual(result.saved_count, detail.media_count - 1)
      self.assertTrue(result.partial)

  def test_all_files_failing_still_reports_a_zero_save(self):
    with tempfile.TemporaryDirectory() as directory:
      downloader, detail = self.build(save_path=directory)
      for item in detail.media:
        self.failures[item.file_name] = OSError("connection reset")

      result = downloader.run({"url": POST_URL})

      self.assertEqual(result.saved_count, 0)
      self.assertFalse(result.partial)

  def test_a_file_already_on_disk_counts_as_saved(self):
    with tempfile.TemporaryDirectory() as directory:
      downloader, detail = self.build(save_path=directory)
      self.skips.add(detail.media[0].file_name)

      result = downloader.run({"url": POST_URL})

      self.assertEqual(result.saved_count, detail.media_count)

  def test_test_mode_skips_every_transfer(self):
    with tempfile.TemporaryDirectory() as directory:
      downloader, _ = self.build(save_path=directory, test_mode=True)

      result = downloader.run({"url": POST_URL})

      self.assertEqual(self.fetched, [])
      self.assertEqual(result.saved_count, 0)


class ExistingFileRecognitionTest(AwemeDownloaderTestCase):
  """A file this post already produced must be recognised even if renamed.

  The name carries the caption, which the poster can edit and which
  Names used to carry the post caption, so a file written by an earlier version
  has a different name for the same content.  Matching the whole name would miss
  it and fetch a second copy.
  """

  def test_a_file_named_by_the_old_scheme_is_not_downloaded_again(self):
    """File names used to end with the post caption.

    Those files are still this post's video, so they must be recognised rather
    than fetched again under the current name.
    """
    with tempfile.TemporaryDirectory() as directory:
      downloader, detail = self.build(save_path=directory)
      save_dir = downloader.build_save_dir(detail)
      save_dir.mkdir(parents=True, exist_ok=True)
      tick = datetime.fromtimestamp(CREATE_TIME).strftime("%Y%m%d%H%M%S")
      stale = save_dir / "{}_{}_很久以前的文案.mp4".format(tick, AWEME_ID)
      stale.write_bytes(b"already here")

      result = downloader.run({"url": POST_URL})

      self.assertEqual(
        [item["file_name"] for item in self.fetched],
        [
          item.file_name
          for item in detail.media
          if item.kind != "video"
        ],
      )
      self.assertEqual(result.saved_count, detail.media_count)
      self.assertEqual(stale.read_bytes(), b"already here")

  def test_another_posts_file_is_not_mistaken_for_this_one(self):
    with tempfile.TemporaryDirectory() as directory:
      downloader, detail = self.build(save_path=directory)
      save_dir = downloader.build_save_dir(detail)
      save_dir.mkdir(parents=True, exist_ok=True)
      (save_dir / "20240101000000_7000000000000000000_别人的作品.mp4").write_bytes(b"x")

      result = downloader.run({"url": POST_URL})

      self.assertEqual(len(self.fetched), detail.media_count)
      self.assertEqual(result.saved_count, detail.media_count)

  def test_a_cover_does_not_satisfy_an_image_and_the_reverse(self):
    """Both end in .jpg, so the marker has to keep them apart."""
    with tempfile.TemporaryDirectory() as directory:
      downloader, detail = self.build(
        payload=image_payload(2),
        save_path=directory,
      )
      save_dir = downloader.build_save_dir(detail)
      save_dir.mkdir(parents=True, exist_ok=True)
      tick = datetime.fromtimestamp(CREATE_TIME).strftime("%Y%m%d%H%M%S")
      (save_dir / "{}_{}_cover.jpg".format(tick, AWEME_ID)).write_bytes(b"x")

      downloader.run({"url": POST_URL})

      fetched = [item["file_name"] for item in self.fetched]
      self.assertIn("{}_{}_01.jpg".format(tick, AWEME_ID), fetched)
      self.assertIn("{}_{}_02.jpg".format(tick, AWEME_ID), fetched)

  def test_match_existing_needs_both_the_id_and_the_tail(self):
    downloader, detail = self.build()
    video = detail.media[0]

    self.assertIsNone(
      downloader.match_existing(["something_else.mp4"], AWEME_ID, video)
    )
    self.assertIsNone(
      downloader.match_existing(
        ["x_{}_y.mp3".format(AWEME_ID)],
        AWEME_ID,
        video,
      )
    )
    self.assertEqual(
      downloader.match_existing(
        ["x_{}_y.mp4".format(AWEME_ID)],
        AWEME_ID,
        video,
      ),
      "x_{}_y.mp4".format(AWEME_ID),
    )

  def test_a_missing_directory_yields_no_existing_names(self):
    with tempfile.TemporaryDirectory() as directory:
      downloader, _ = self.build(save_path=directory)

      self.assertEqual(
        downloader.existing_file_names(Path(directory) / "not-there"),
        [],
      )


class WritableNameTest(AwemeDownloaderTestCase):
  def test_a_long_caption_cannot_affect_the_file_names(self):
    """Captions are not part of file names, so they cannot overrun the limit.

    Written through the real filesystem rather than the fake fetcher, so the
    assertion is that the kernel accepts the name.
    """
    with tempfile.TemporaryDirectory() as directory:
      downloader, detail = self.build(
        payload=video_payload(desc="中" * 400),
        save_path=directory,
      )
      aweme_module.fetch_file = self._original_fetch
      save_dir = downloader.build_save_dir(detail)
      save_dir.mkdir(parents=True, exist_ok=True)

      for item in detail.media:
        with self.subTest(kind=item.kind):
          self.assertNotIn("中", item.file_name)
          target = save_dir / item.file_name
          target.write_bytes(b"payload")
          self.assertTrue(target.is_file())


class DownloadDetailTest(AwemeDownloaderTestCase):
  """The entry point for a caller that already holds the post object.

  The owner browse path lists posts through USER_POST, whose items are the same
  shape POST_DETAIL returns, so it downloads a whole page without resolving
  anything.
  """

  def test_an_already_resolved_post_is_downloaded_without_resolving(self):
    with tempfile.TemporaryDirectory() as directory:
      downloader, detail = self.build(save_path=directory)
      ##
      ## a resolver that would fail if it were consulted
      ##
      downloader.resolver = StubResolver(
        AwemeResolution(ok=False, reason="must not be called")
      )

      result = downloader.download_detail(detail, POST_URL)

      self.assertTrue(result.ok)
      self.assertEqual(result.saved_count, detail.media_count)
      self.assertEqual(len(self.fetched), detail.media_count)
      self.assertEqual(downloader.resolver.calls, [])

  def test_a_long_profile_url_is_not_recorded(self):
    """The column holds the share link, and a long url is not one.

    ``https://www.douyin.com/user/<sec_user_id>`` can be rebuilt at any time from
    the ``sec_user_id`` sitting in the same row, so storing it keeps nothing that
    was not already there.  The short share link is the opposite: its code is
    opaque and issued by douyin, so if it is not kept it cannot be recovered -
    and it is the form that behaves like a real share when handed back.
    """
    with tempfile.TemporaryDirectory() as directory:
      database = RecordingDatabase()
      downloader, detail = self.build(save_path=directory, database=database)
      profile_url = "https://www.douyin.com/user/" + OWNER_SEC_UID

      downloader.download_detail(detail, profile_url)

      self.assertIsNone(database.owners[0]["post_share_url"])

  def test_a_long_profile_url_is_not_recorded_even_when_declared(self):
    """Declaring it an owner's does not make a long url a share link."""
    with tempfile.TemporaryDirectory() as directory:
      database = RecordingDatabase()
      downloader, detail = self.build(save_path=directory, database=database)
      profile_url = "https://www.douyin.com/user/" + OWNER_SEC_UID

      downloader.download_detail(detail, profile_url, owner_share_url=profile_url)

      self.assertIsNone(database.owners[0]["post_share_url"])

  def test_a_post_link_is_not_recorded_as_the_owners_profile(self):
    """A post link is not a profile link and must not take that column.

    Writing one there would overwrite a profile link that was already correct,
    and leave the column meaning two different things with no way to tell.
    """
    with tempfile.TemporaryDirectory() as directory:
      database = RecordingDatabase()
      downloader, detail = self.build(save_path=directory, database=database)

      downloader.download_detail(detail, "https://www.douyin.com/video/" + AWEME_ID)

      self.assertIsNone(database.owners[0]["post_share_url"])

  def test_an_unresolved_share_link_is_not_recorded_either(self):
    """A v.douyin.com link could be either kind; it is not evidence of a profile."""
    with tempfile.TemporaryDirectory() as directory:
      database = RecordingDatabase()
      downloader, detail = self.build(save_path=directory, database=database)

      downloader.download_detail(detail, "https://v.douyin.com/MqjfOkWSeG8/")

      self.assertIsNone(database.owners[0]["post_share_url"])

  def test_run_and_download_detail_produce_the_same_result(self):
    with tempfile.TemporaryDirectory() as directory:
      first, detail = self.build(save_path=directory)
      by_run = first.run({"url": POST_URL})

      second, _ = self.build(save_path=directory)
      by_detail = second.download_detail(detail, POST_URL)

      self.assertEqual(by_run.aweme_id, by_detail.aweme_id)
      self.assertEqual(by_run.save_dir, by_detail.save_dir)
      self.assertEqual(by_run.media_count, by_detail.media_count)
      ##
      ## the second call finds the first call's files, so it skips
      ##
      self.assertTrue(by_detail.skipped)


class PostNoteTest(AwemeDownloaderTestCase):
  """The caption lives beside the media, because it cannot live in the name.

  A folder called 20260701081200_7657271784144009946 tells a person nothing, and
  captions are barred from names: an author can edit one, which would rename the
  files and make the "already downloaded" check miss them.
  """

  def test_the_note_carries_the_caption_first(self):
    with tempfile.TemporaryDirectory() as directory:
      downloader, detail = self.build(
        payload=video_payload(desc="小鸟都粘我，你什么时候来粘我？"),
        save_path=directory,
      )

      result = downloader.run({"url": POST_URL})
      note = Path(result.save_dir) / "info.txt"

      self.assertTrue(note.is_file())
      body = note.read_text(encoding="utf-8")
      self.assertTrue(body.startswith("小鸟都粘我，你什么时候来粘我？"))
      self.assertIn(AWEME_ID, body)
      self.assertIn("视频", body)

  def test_a_post_without_a_caption_still_gets_a_note(self):
    with tempfile.TemporaryDirectory() as directory:
      downloader, _ = self.build(payload=video_payload(desc=""), save_path=directory)

      result = downloader.run({"url": POST_URL})
      body = (Path(result.save_dir) / "info.txt").read_text(encoding="utf-8")

      self.assertIn("（无文案）", body)

  def test_an_image_post_note_says_so(self):
    with tempfile.TemporaryDirectory() as directory:
      downloader, _ = self.build(payload=image_payload(3), save_path=directory)

      result = downloader.run({"url": POST_URL})
      body = (Path(result.save_dir) / "info.txt").read_text(encoding="utf-8")

      self.assertIn("图集", body)

  def test_a_folder_downloaded_before_notes_existed_gains_one(self):
    """This is the incremental case: nothing to fetch, but the note is missing."""
    with tempfile.TemporaryDirectory() as directory:
      downloader, detail = self.build(save_path=directory)
      save_dir = downloader.build_save_dir(detail)
      save_dir.mkdir(parents=True, exist_ok=True)
      for item in detail.media:
        (save_dir / item.file_name).write_bytes(b"already here")

      result = downloader.run({"url": POST_URL})

      self.assertTrue(result.skipped)
      self.assertEqual(self.fetched, [])
      self.assertTrue((save_dir / "info.txt").is_file())

  def test_an_edited_caption_updates_the_note(self):
    with tempfile.TemporaryDirectory() as directory:
      first, _ = self.build(payload=video_payload(desc="原来的文案"),
                            save_path=directory)
      result = first.run({"url": POST_URL})

      second, _ = self.build(payload=video_payload(desc="改过的文案"),
                             save_path=directory)
      second.run({"url": POST_URL})

      body = (Path(result.save_dir) / "info.txt").read_text(encoding="utf-8")
      self.assertTrue(body.startswith("改过的文案"))

  def test_the_note_is_not_mistaken_for_a_media_file(self):
    """It must not satisfy any media item's identity check."""
    with tempfile.TemporaryDirectory() as directory:
      downloader, detail = self.build(save_path=directory)
      downloader.run({"url": POST_URL})
      self.fetched.clear()

      again, _ = self.build(save_path=directory)
      result = again.run({"url": POST_URL})

      self.assertTrue(result.skipped)
      self.assertEqual(result.saved_count, detail.media_count)

  def test_test_mode_writes_no_note(self):
    with tempfile.TemporaryDirectory() as directory:
      downloader, detail = self.build(save_path=directory, test_mode=True)

      result = downloader.run({"url": POST_URL})

      self.assertFalse((Path(result.save_dir) / "info.txt").exists())


class UnresolvableLinkTest(AwemeDownloaderTestCase):
  def test_an_unresolved_link_is_reported_without_fetching(self):
    downloader, _ = self.build()
    downloader.resolver = StubResolver(
      AwemeResolution(ok=False, aweme_id=AWEME_ID, reason="post was removed")
    )

    result = downloader.run({"url": POST_URL})

    self.assertFalse(result.ok)
    self.assertEqual(result.reason, "post was removed")
    self.assertEqual(self.fetched, [])

  def test_a_token_without_a_url_is_a_programming_error(self):
    downloader, _ = self.build()

    with self.assertRaises(ValueError):
      downloader.run({"score": 5})
    with self.assertRaises(ValueError):
      downloader.run({"url": "   "})


class DedupTest(AwemeDownloaderTestCase):
  """Disk decides what still needs fetching, not the recorded counts."""

  def _fill(self, downloader, detail):
    save_dir = downloader.build_save_dir(detail)
    save_dir.mkdir(parents=True, exist_ok=True)
    for item in detail.media:
      (save_dir / item.file_name).write_bytes(b"already here")
    return save_dir

  def test_a_post_whose_files_are_all_present_fetches_nothing(self):
    with tempfile.TemporaryDirectory() as directory:
      downloader, detail = self.build(save_path=directory)
      self._fill(downloader, detail)

      result = downloader.run({"url": POST_URL})

      self.assertTrue(result.ok)
      self.assertTrue(result.skipped)
      self.assertEqual(self.fetched, [])
      self.assertEqual(result.saved_count, detail.media_count)

  def test_a_post_with_no_files_on_disk_fetches_everything(self):
    with tempfile.TemporaryDirectory() as directory:
      downloader, detail = self.build(save_path=directory)

      result = downloader.run({"url": POST_URL})

      self.assertFalse(result.skipped)
      self.assertEqual(len(self.fetched), detail.media_count)

  def test_only_the_missing_files_are_fetched(self):
    with tempfile.TemporaryDirectory() as directory:
      downloader, detail = self.build(save_path=directory)
      save_dir = downloader.build_save_dir(detail)
      save_dir.mkdir(parents=True, exist_ok=True)
      (save_dir / detail.media[0].file_name).write_bytes(b"already here")

      result = downloader.run({"url": POST_URL})

      self.assertEqual(
        [item["file_name"] for item in self.fetched],
        [item.file_name for item in detail.media[1:]],
      )
      self.assertEqual(result.saved_count, detail.media_count)
      self.assertFalse(result.skipped)

  def test_dedup_works_without_a_database(self):
    """Disk-based dedup keeps working when persistence is switched off."""
    with tempfile.TemporaryDirectory() as directory:
      downloader, detail = self.build(save_path=directory, database=None)
      self._fill(downloader, detail)

      result = downloader.run({"url": POST_URL})

      self.assertTrue(result.skipped)
      self.assertEqual(self.fetched, [])

  def test_a_missing_record_does_not_cause_a_re_download(self):
    """The record is an outcome log, not the dedup authority.

    A payload that omitted one file would otherwise record a complete count and
    permanently suppress that file; and a record removed by hand would cause a
    full re-download of files that are already there.
    """
    with tempfile.TemporaryDirectory() as directory:
      database = RecordingDatabase()
      downloader, detail = self.build(save_path=directory, database=database)
      self._fill(downloader, detail)

      result = downloader.run({"url": POST_URL})

      self.assertEqual(self.fetched, [])
      self.assertEqual(len(database.records), 1)
      self.assertEqual(result.saved_count, detail.media_count)

  def test_dedup_can_be_switched_off(self):
    with tempfile.TemporaryDirectory() as directory:
      downloader, detail = self.build(
        save_path=directory,
        skip_downloaded=False,
      )
      self._fill(downloader, detail)

      result = downloader.run({"url": POST_URL})

      self.assertFalse(result.skipped)
      self.assertEqual(len(self.fetched), detail.media_count)

  def test_switching_dedup_off_overwrites_instead_of_skipping(self):
    with tempfile.TemporaryDirectory() as directory:
      downloader, detail = self.build(
        save_path=directory,
        skip_downloaded=False,
      )
      self._fill(downloader, detail)

      downloader.run({"url": POST_URL})

      for item in self.fetched:
        with self.subTest(file_name=item["file_name"]):
          self.assertEqual(item["kwargs"]["on_exists"], "overwrite")


class PersistenceTest(AwemeDownloaderTestCase):
  def test_the_owner_row_records_identity_but_not_a_post_link(self):
    with tempfile.TemporaryDirectory() as directory:
      database = RecordingDatabase()
      downloader, detail = self.build(save_path=directory, database=database)

      downloader.run({"url": POST_URL})

      self.assertEqual(len(database.owners), 1)
      owner = database.owners[0]
      self.assertEqual(owner["owner_user_id"], detail.owner_user_id)
      self.assertEqual(owner["directory_name"], detail.directory_name)
      ##
      ## POST_URL is a post link, so it is not the owner's profile link
      ##
      self.assertIsNone(owner["post_share_url"])
      ##
      ## live_share_url and actived_count belong to the live path
      ##
      self.assertNotIn("live_share_url", owner)
      self.assertNotIn("actived_count", owner)

  def test_the_owner_share_link_is_recorded_when_the_browse_path_supplies_it(self):
    """The pasted profile link is stored verbatim, short form and all.

    ``live_share_url`` holds exactly this shape - 1785 rows of
    ``https://v.douyin.com/<code>/`` and not one long url - and reading a link
    back out to re-download has to give douyin the form it expects.

    It cannot be recognised from the string: an owner share link and a post
    share link are both ``v.douyin.com/<code>/``.  Only the caller knows which
    one it followed, so only the caller may declare it.
    """
    owner_link = "https://v.douyin.com/Gv2snnrMBCs/"
    with tempfile.TemporaryDirectory() as directory:
      database = RecordingDatabase()
      downloader, detail = self.build(save_path=directory, database=database)

      downloader.download_detail(detail, POST_URL, owner_share_url=owner_link)

      self.assertEqual(database.owners[0]["post_share_url"], owner_link)

  def test_a_post_link_is_still_never_written_into_the_owner_column(self):
    """Without that declaration nothing is assumed - the old guard stands."""
    with tempfile.TemporaryDirectory() as directory:
      database = RecordingDatabase()
      downloader, detail = self.build(save_path=directory, database=database)

      downloader.download_detail(detail, "https://v.douyin.com/aPostLink/")

      self.assertIsNone(database.owners[0]["post_share_url"])

  def test_a_blank_owner_share_link_records_nothing(self):
    """An empty string must not overwrite a link already on the row."""
    with tempfile.TemporaryDirectory() as directory:
      database = RecordingDatabase()
      downloader, detail = self.build(save_path=directory, database=database)

      downloader.download_detail(detail, POST_URL, owner_share_url="")

      self.assertIsNone(database.owners[0]["post_share_url"])

  def test_the_record_captures_counts_source_and_directory(self):
    with tempfile.TemporaryDirectory() as directory:
      database = RecordingDatabase()
      downloader, detail = self.build(save_path=directory, database=database)

      result = downloader.run({"url": POST_URL})

      self.assertEqual(len(database.records), 1)
      record = database.records[0]
      self.assertEqual(record["platform"], "douyin")
      self.assertEqual(record["aweme_id"], AWEME_ID)
      self.assertEqual(record["media_count"], detail.media_count)
      self.assertEqual(record["saved_count"], result.saved_count)
      self.assertEqual(record["save_dir"], result.save_dir)
      self.assertEqual(record["source"], detail.source)
      self.assertEqual(record["aweme_type"], detail.aweme_type)
      self.assertIsInstance(record["downloaded_at"], datetime)

  def test_a_partial_download_is_recorded_as_partial(self):
    with tempfile.TemporaryDirectory() as directory:
      database = RecordingDatabase()
      downloader, detail = self.build(save_path=directory, database=database)
      self.failures[detail.media[0].file_name] = OSError("reset")

      downloader.run({"url": POST_URL})

      record = database.records[0]
      self.assertLess(record["saved_count"], record["media_count"])

  def test_files_are_still_downloaded_when_the_database_is_absent(self):
    with tempfile.TemporaryDirectory() as directory:
      downloader, detail = self.build(save_path=directory, database=None)

      result = downloader.run({"url": POST_URL})

      self.assertTrue(result.ok)
      self.assertEqual(result.saved_count, detail.media_count)

  def test_a_failing_database_does_not_lose_the_files(self):
    class BrokenDatabase(RecordingDatabase):
      def upsert_post_owner(self, record):
        raise RuntimeError("database went away")

    with tempfile.TemporaryDirectory() as directory:
      downloader, detail = self.build(
        save_path=directory,
        database=BrokenDatabase(),
      )

      result = downloader.run({"url": POST_URL})

      self.assertTrue(result.ok)
      self.assertEqual(result.saved_count, detail.media_count)


class AwemeIdBoundaryTest(unittest.TestCase):
  """The id must match on a boundary, not as a bare substring."""

  def test_a_shorter_id_does_not_match_inside_a_longer_one(self):
    self.assertFalse(
      DouyinAwemeDownloader.carries_aweme_id(
        "20240101000000_9957657271784144009946_x.mp4",
        "7657271784144009946",
      )
    )

  def test_the_id_matches_between_underscores(self):
    self.assertTrue(
      DouyinAwemeDownloader.carries_aweme_id(
        "20240101000000_7657271784144009946_x.mp4",
        "7657271784144009946",
      )
    )

  def test_the_id_matches_without_a_tick_prefix(self):
    self.assertTrue(
      DouyinAwemeDownloader.carries_aweme_id(
        "7657271784144009946_cover.jpg",
        "7657271784144009946",
      )
    )

  def test_the_id_matches_as_the_whole_stem(self):
    self.assertTrue(
      DouyinAwemeDownloader.carries_aweme_id(
        "7657271784144009946.mp4",
        "7657271784144009946",
      )
    )

  def test_an_id_glued_to_other_digits_does_not_match(self):
    self.assertFalse(
      DouyinAwemeDownloader.carries_aweme_id(
        "7657271784144009946123_cover.jpg",
        "7657271784144009946",
      )
    )

  def test_missing_input_does_not_match(self):
    self.assertFalse(DouyinAwemeDownloader.carries_aweme_id("", "1"))
    self.assertFalse(DouyinAwemeDownloader.carries_aweme_id("a_1.mp4", ""))

  def test_a_neighbouring_posts_file_is_not_claimed(self):
    with tempfile.TemporaryDirectory() as directory:
      ##
      ## a longer id that contains this post's id as a substring
      ##
      self.assertFalse(
        DouyinAwemeDownloader.carries_aweme_id(
          "20240101000000_995{}_x.mp4".format(AWEME_ID),
          AWEME_ID,
        )
      )


class OwnerDirectoryTest(AwemeDownloaderTestCase):
  """One folder per owner, even after the owner renames themselves."""

  class DirectoryDatabase(RecordingDatabase):
    def __init__(self, recorded=None, failure=None, owners=1):
      super().__init__()
      self.recorded = recorded
      self.failure = failure
      self.owners = owners
      self.lookups = []
      self.counted = []

    def find_owner_directory_name(self, owner_user_id):
      self.lookups.append(owner_user_id)
      if self.failure is not None:
        raise self.failure
      return self.recorded

    def count_owners_using_directory_name(self, directory_name):
      self.counted.append(directory_name)
      return self.owners

  def test_the_recorded_folder_wins_over_a_new_nickname(self):
    """A renamed owner keeps their original folder.

    Otherwise this post's earlier files, sitting under the old name, would stop
    being found and the post would download a second time.
    """
    with tempfile.TemporaryDirectory() as directory:
      database = self.DirectoryDatabase(recorded="旧的目录名")
      downloader, detail = self.build(save_path=directory, database=database)

      result = downloader.run({"url": POST_URL})

      self.assertEqual(Path(result.save_dir).parent.name, "旧的目录名")
      self.assertNotEqual(Path(result.save_dir).parent.name, detail.directory_name)
      self.assertEqual(database.lookups, [detail.owner_user_id])

  def test_the_nickname_is_used_when_the_owner_is_new(self):
    with tempfile.TemporaryDirectory() as directory:
      database = self.DirectoryDatabase(recorded=None)
      downloader, detail = self.build(save_path=directory, database=database)

      result = downloader.run({"url": POST_URL})

      self.assertEqual(Path(result.save_dir).parent.name, detail.directory_name)

  def test_the_nickname_is_used_when_the_database_is_absent(self):
    with tempfile.TemporaryDirectory() as directory:
      downloader, detail = self.build(save_path=directory, database=None)

      result = downloader.run({"url": POST_URL})

      self.assertEqual(Path(result.save_dir).parent.name, detail.directory_name)

  def test_a_failing_lookup_falls_back_to_the_nickname(self):
    """A database problem must not stop the download, matching the live path."""
    with tempfile.TemporaryDirectory() as directory:
      database = self.DirectoryDatabase(failure=RuntimeError("gone"))
      downloader, detail = self.build(save_path=directory, database=database)

      result = downloader.run({"url": POST_URL})

      self.assertTrue(result.ok)
      self.assertEqual(Path(result.save_dir).parent.name, detail.directory_name)

  def test_an_image_post_nests_under_the_recorded_folder(self):
    with tempfile.TemporaryDirectory() as directory:
      database = self.DirectoryDatabase(recorded="旧的目录名")
      downloader, _ = self.build(
        payload=image_payload(2),
        save_path=directory,
        database=database,
      )

      result = downloader.run({"url": POST_URL})

      ##
      ## owner folder, then the post's own folder inside it
      ##
      self.assertEqual(Path(result.save_dir).parent.name, "旧的目录名")
      self.assertTrue(Path(result.save_dir).name.endswith(AWEME_ID))


class SharedNicknameTest(AwemeDownloaderTestCase):
  """Douyin lets different accounts hold the same nickname.

  Measured on this database: 39 folder names cover more than one owner.  A folder
  named after the nickname alone would mix those accounts' files together.
  """

  def test_a_shared_folder_name_gains_the_owner_id(self):
    with tempfile.TemporaryDirectory() as directory:
      database = OwnerDirectoryTest.DirectoryDatabase(owners=2)
      downloader, detail = self.build(save_path=directory, database=database)

      result = downloader.run({"url": POST_URL})

      self.assertEqual(
        Path(result.save_dir).parent.name,
        "{}_{}".format(detail.directory_name, detail.owner_user_id),
      )

  def test_a_folder_used_by_one_owner_is_left_alone(self):
    with tempfile.TemporaryDirectory() as directory:
      database = OwnerDirectoryTest.DirectoryDatabase(owners=1)
      downloader, detail = self.build(save_path=directory, database=database)

      result = downloader.run({"url": POST_URL})

      self.assertEqual(Path(result.save_dir).parent.name, detail.directory_name)

  def test_the_discriminator_applies_to_every_owner_in_the_group(self):
    """Including whoever was downloaded first.

    Otherwise the layout would depend on download order: one owner would hold the
    bare folder and the rest would be suffixed.
    """
    with tempfile.TemporaryDirectory() as directory:
      database = OwnerDirectoryTest.DirectoryDatabase(
        recorded="共用的名字",
        owners=3,
      )
      downloader, detail = self.build(save_path=directory, database=database)

      result = downloader.run({"url": POST_URL})

      self.assertEqual(
        Path(result.save_dir).parent.name,
        "共用的名字_{}".format(detail.owner_user_id),
      )
      self.assertEqual(database.counted, ["共用的名字"])

  def test_two_owners_sharing_a_nickname_get_separate_folders(self):
    with tempfile.TemporaryDirectory() as directory:
      first_dir = None
      for owner in ("111111", "222222"):
        database = OwnerDirectoryTest.DirectoryDatabase(owners=2)
        downloader, _ = self.build(
          payload=video_payload(
            author={"uid": owner, "sec_uid": "MS4w", "nickname": "同名主播"}
          ),
          save_path=directory,
          database=database,
        )
        result = downloader.run({"url": POST_URL})
        if first_dir is None:
          first_dir = result.save_dir
        else:
          self.assertNotEqual(first_dir, result.save_dir)
          self.assertTrue(Path(result.save_dir).parent.name.endswith("_222222"))
          self.assertTrue(Path(first_dir).parent.name.endswith("_111111"))

  def test_a_post_without_an_owner_id_writes_no_owner_row(self):
    """share_url is keyed on the owner id, and the platform sometimes omits it.

    A blank key produces a row nothing can match, and counting it as an owner made
    a folder look shared - which suppressed the discriminator for the one real
    account using it.  The post record is still written; it is keyed on the post.
    """
    with tempfile.TemporaryDirectory() as directory:
      database = RecordingDatabase()
      downloader, _ = self.build(
        payload=video_payload(author={"sec_uid": "MS4w", "nickname": "无 id"}),
        save_path=directory,
        database=database,
      )

      result = downloader.run({"url": POST_URL})

      self.assertTrue(result.ok)
      self.assertEqual(database.owners, [])
      self.assertEqual(len(database.records), 1)
      self.assertIsNone(database.records[0]["owner_user_id"])

  def test_a_failing_count_falls_back_to_the_nickname(self):
    class CountFails(OwnerDirectoryTest.DirectoryDatabase):
      def count_owners_using_directory_name(self, directory_name):
        raise RuntimeError("gone")

    with tempfile.TemporaryDirectory() as directory:
      downloader, detail = self.build(
        save_path=directory,
        database=CountFails(),
      )

      result = downloader.run({"url": POST_URL})

      self.assertTrue(result.ok)
      self.assertEqual(Path(result.save_dir).parent.name, detail.directory_name)


##
## Folder naming itself is covered by test_owner_directory; the policy is shared
## with the live path and lives in douyin_owner_directory.
##


class PostLockTest(unittest.TestCase):
  """Same post, two workers: reading and writing the folder must not interleave."""

  def test_the_same_post_is_serialised(self):
    locks = aweme_module.PostLocks()
    order = []
    first_inside = Event()
    release_first = Event()

    def worker_one():
      with locks.hold("A"):
        order.append("one-in")
        first_inside.set()
        release_first.wait(2)
        order.append("one-out")

    def worker_two():
      first_inside.wait(2)
      with locks.hold("A"):
        order.append("two-in")

    threads = [Thread(target=worker_one), Thread(target=worker_two)]
    for thread in threads:
      thread.start()
    first_inside.wait(2)
    ##
    ## worker two is now blocked on the same key
    ##
    self.assertEqual(order, ["one-in"])
    release_first.set()
    for thread in threads:
      thread.join(2)

    self.assertEqual(order, ["one-in", "one-out", "two-in"])

  def test_different_posts_do_not_block_each_other(self):
    locks = aweme_module.PostLocks()
    inside = Event()
    done = Event()

    def holder():
      with locks.hold("A"):
        inside.set()
        done.wait(2)

    thread = Thread(target=holder)
    thread.start()
    inside.wait(2)
    try:
      with locks.hold("B"):
        entered_b = True
    finally:
      done.set()
      thread.join(2)

    self.assertTrue(entered_b)

  def test_entries_are_dropped_when_released(self):
    """A long-running server must not keep one lock per post it has ever seen."""
    locks = aweme_module.PostLocks()

    for index in range(50):
      with locks.hold("post-{}".format(index)):
        self.assertEqual(locks.tracked(), 1)

    self.assertEqual(locks.tracked(), 0)

  def test_an_entry_survives_while_another_holder_waits(self):
    locks = aweme_module.PostLocks()
    inside = Event()
    done = Event()

    def holder():
      with locks.hold("A"):
        inside.set()
        done.wait(2)

    thread = Thread(target=holder)
    thread.start()
    inside.wait(2)
    try:
      self.assertEqual(locks.tracked(), 1)
    finally:
      done.set()
      thread.join(2)

    self.assertEqual(locks.tracked(), 0)

  def test_the_lock_is_released_when_the_body_raises(self):
    locks = aweme_module.PostLocks()

    with self.assertRaises(ValueError):
      with locks.hold("A"):
        raise ValueError("boom")

    self.assertEqual(locks.tracked(), 0)
    ##
    ## still acquirable
    ##
    with locks.hold("A"):
      pass


class ExecutorTest(unittest.TestCase):
  def tearDown(self):
    aweme_module.shutdown_aweme_downloads()

  def test_the_post_pool_is_not_the_live_or_probe_pool(self):
    """Its own pool on purpose; a shared one would let paths stall each other."""
    aweme_module.shutdown_aweme_downloads()
    executor = aweme_module.get_aweme_executor(3)

    self.assertEqual(executor._max_workers, 3)
    self.assertIs(aweme_module.get_aweme_executor(3), executor)

  def test_an_invalid_worker_count_falls_back_to_a_safe_default(self):
    aweme_module.shutdown_aweme_downloads()

    self.assertEqual(aweme_module.get_aweme_executor(0)._max_workers, 3)

  def test_shutdown_releases_the_pool(self):
    aweme_module.shutdown_aweme_downloads()
    first = aweme_module.get_aweme_executor(2)
    aweme_module.shutdown_aweme_downloads()
    second = aweme_module.get_aweme_executor(2)

    self.assertIsNot(first, second)

  def test_submitting_no_tokens_does_nothing(self):
    self.assertEqual(aweme_module.download_multiple_aweme([]), [])


if __name__ == "__main__":
  unittest.main()
