import tempfile
import unittest
from pathlib import Path

from backend.src.library.baselib import load_yml
from backend.src.platform.douyin import douyin_live_downloader as live_module
from backend.src.platform.douyin.douyin_live_prober import LiveProbeResult

PROJECT_ROOT = Path(__file__).resolve().parents[3]
CONFIG_EXAMPLE_PATH = PROJECT_ROOT / "docs" / "design" / "config.yml.example"

SHARE_URL = "https://v.douyin.com/example/"
STREAM_URL = "https://stream.example.test/live.flv?sign=SECRET&token=SECRET"


def live_config(test_mode=True):
  config = load_yml(CONFIG_EXAMPLE_PATH)
  config["database"]["enable"] = False
  config["download"]["test_mode"] = test_mode
  ##
  ## Both response dumps are off, and the save path points away from the
  ## checkout: these tests are about what ``run_with_result`` answers, and a
  ## test that leaves yml files inside the repository is a test with a side
  ## effect nobody asked for.
  ##
  config["download"]["save_response"] = False
  config["download"]["save_error_response"] = False
  config["download"]["save_path"] = tempfile.mkdtemp(prefix="live-result-test-")
  config["server"]["debug_mode"] = False
  return config


class LiveResponse:
  """The platform payload a probe carries, as far as this path reads it."""

  def __init__(self, flv=STREAM_URL, hls=None):
    self._payload = {
      "status_code": 0,
      "data": {
        "room": {
          "status": 2,
          "id": 998877,
          "owner_user_id": "owner-1",
          "owner": {"nickname": "Test Host", "sec_uid": "sec-1", "status": 1},
          "stream_url": {
            "flv_pull_url": {"FULL_HD1": flv, "HD1": None, "SD1": None, "SD2": None},
            "hls_pull_url_map": {
              "FULL_HD1": hls,
              "HD1": None,
              "SD1": None,
              "SD2": None,
            },
          },
        }
      },
    }

  def json(self):
    return self._payload


def probe_result(ok=True, room_status=2, response=None, error=None):
  live_response = response if response is not None else LiveResponse()
  return LiveProbeResult(
    url=SHARE_URL,
    ok=ok,
    room_status=room_status,
    owner_user_id="owner-1",
    room_id="998877",
    nickname="Test Host",
    directory_name="Test Host",
    error=error,
    payload=live_response.json(),
    share_info={},
    live_payload={},
    headers={},
    response=live_response,
  )


class StubProber:
  def __init__(self, result):
    self._result = result
    self.calls = []

  def probe(self, url):
    self.calls.append(url)
    return self._result


def build_downloader(probe, test_mode=True, download=None):
  downloader = live_module.DouyinLiveDownloader(live_config(test_mode=test_mode))
  downloader.prober = StubProber(probe)
  downloader.database = None
  recorded = []

  def capture(share_url, build, headers=None):
    recorded.append((share_url, build))
    if download is not None:
      return download(share_url, build)
    return None

  downloader.download_live_stream = capture
  return downloader, recorded


class LiveDownloadResultShapeTest(unittest.TestCase):
  def test_the_result_never_carries_a_stream_url(self):
    fields = set(live_module.LiveDownloadResult.__dataclass_fields__)

    ##
    ## A live stream url is signed: it carries ``sign`` and ``token`` query
    ## parameters that grant access.  It is used inside the downloader and must
    ## not survive into anything a browser can read, so it has no field here at
    ## all rather than being dropped later and relied upon to stay dropped.
    ##
    self.assertNotIn("stream_url", fields)
    self.assertNotIn("stream_name", fields)
    self.assertNotIn("headers", fields)
    self.assertNotIn("cookies", fields)


class LiveRunResultTest(unittest.TestCase):
  def test_a_confirmed_room_records_and_reports_success(self):
    downloader, recorded = build_downloader(probe_result(), test_mode=False)

    result = downloader.run_with_result({"url": SHARE_URL})

    self.assertIs(True, result.ok)
    self.assertIs(True, result.recorded)
    self.assertIs(False, result.test_mode)
    self.assertEqual(2, result.room_status)
    self.assertEqual(1, len(recorded))

  def test_a_successful_recording_describes_the_room(self):
    downloader, recorded = build_downloader(probe_result(), test_mode=False)

    result = downloader.run_with_result({"url": SHARE_URL})

    self.assertEqual("998877", result.room_id)
    self.assertEqual("owner-1", result.owner_user_id)
    self.assertEqual("Test Host", result.nickname)
    self.assertEqual("flv", result.protocol)
    self.assertIsNone(result.reason)

  def test_the_written_path_comes_from_the_downloader(self):
    downloader, recorded = build_downloader(
      probe_result(),
      test_mode=False,
      download=lambda share_url, build: Path("/media/douyin/live/re_1_live.flv"),
    )

    result = downloader.run_with_result({"url": SHARE_URL})

    ##
    ## Reported rather than reconstructed.  Live files are renamed on collision -
    ## ``re_1_`` here - so a path rebuilt from the stream name would name a file
    ## that does not exist.
    ##
    self.assertEqual("/media/douyin/live/re_1_live.flv", result.output_path)

  def test_test_mode_completes_without_claiming_a_recording(self):
    downloader, recorded = build_downloader(probe_result(), test_mode=True)

    result = downloader.run_with_result({"url": SHARE_URL})

    ##
    ## Every stage but the media transfer ran, so the attempt succeeded; saying
    ## ``recorded`` would claim a file that was never written.
    ##
    self.assertIs(True, result.ok)
    self.assertIs(False, result.recorded)
    self.assertIs(True, result.test_mode)
    self.assertIsNone(result.output_path)

  def test_a_probe_that_failed_stops_before_any_recording(self):
    downloader, recorded = build_downloader(
      probe_result(ok=False, room_status=None, error="请求超时"), test_mode=False
    )

    result = downloader.run_with_result({"url": SHARE_URL})

    self.assertIs(False, result.ok)
    self.assertIs(False, result.recorded)
    self.assertEqual([], recorded)
    self.assertTrue(result.reason)

  def test_a_room_that_is_not_live_is_not_a_recording(self):
    downloader, recorded = build_downloader(
      probe_result(room_status=4), test_mode=False
    )

    result = downloader.run_with_result({"url": SHARE_URL})

    ##
    ## Distinguishable from a probe failure, which is the whole reason this
    ## result exists: both used to be a bare ``None``.
    ##
    self.assertIs(False, result.ok)
    self.assertIs(False, result.recorded)
    self.assertEqual(4, result.room_status)
    self.assertEqual("Test Host", result.nickname)
    self.assertEqual([], recorded)

  def test_offline_and_probe_failure_are_told_apart(self):
    """The distinction this whole result type exists for.

    Both used to be a bare ``None``.  They agree on what matters to a caller -
    nothing was recorded - and disagree on why, which is exactly what could not
    be expressed before.
    """
    offline, unused = build_downloader(probe_result(room_status=4), test_mode=False)
    broken, unused_too = build_downloader(
      probe_result(ok=False, room_status=None, error="请求超时"), test_mode=False
    )

    offline_result = offline.run_with_result({"url": SHARE_URL})
    broken_result = broken.run_with_result({"url": SHARE_URL})

    ##
    ## Neither is a recording, and neither may pass as one.
    ##
    for result in (offline_result, broken_result):
      self.assertIs(False, result.ok)
      self.assertIs(False, result.recorded)
      self.assertIsNone(result.output_path)
      self.assertTrue(result.reason)

    ##
    ## And they are still distinguishable: the room answered "not broadcasting",
    ## while the other was never successfully asked.
    ##
    self.assertNotEqual(offline_result.reason, broken_result.reason)
    self.assertEqual(4, offline_result.room_status)
    self.assertIsNone(broken_result.room_status)

  def test_no_unrecorded_ending_can_pass_as_a_recording(self):
    ##
    ## Swept together so a new early-return cannot quietly join the list without
    ## being held to the same rule.
    ##
    endings = {
      "offline": probe_result(room_status=4),
      "probe failed": probe_result(ok=False, room_status=None, error="请求超时"),
    }
    for label, probe in endings.items():
      with self.subTest(ending=label):
        downloader, recorded = build_downloader(probe, test_mode=False)

        result = downloader.run_with_result({"url": SHARE_URL})

        self.assertIs(False, result.ok)
        self.assertIs(False, result.recorded)
        self.assertIs(False, result.test_mode)
        self.assertEqual([], recorded)

  def test_a_room_without_a_usable_stream_is_not_a_success(self):
    downloader, recorded = build_downloader(
      probe_result(response=LiveResponse(flv=None, hls=None)), test_mode=False
    )

    with self.assertRaises(Exception):
      downloader.run_with_result({"url": SHARE_URL})

  def test_a_crashing_download_still_propagates(self):
    def explode(share_url, build):
      raise RuntimeError("stream reset")

    downloader, recorded = build_downloader(
      probe_result(), test_mode=False, download=explode
    )

    ##
    ## Unchanged from before this result existed: the thread running a recording
    ## sees the same exception it always did.
    ##
    with self.assertRaises(RuntimeError):
      downloader.run_with_result({"url": SHARE_URL})

  def test_a_missing_url_is_still_a_programming_error(self):
    downloader, recorded = build_downloader(probe_result())

    with self.assertRaises(ValueError):
      downloader.run_with_result({})


class LiveRunLegacyContractTest(unittest.TestCase):
  """``run`` keeps answering the way every existing caller expects."""

  def test_run_still_answers_with_nothing(self):
    downloader, recorded = build_downloader(probe_result(), test_mode=False)

    self.assertIsNone(downloader.run({"url": SHARE_URL}))

  def test_run_still_does_the_work(self):
    downloader, recorded = build_downloader(probe_result(), test_mode=False)

    downloader.run({"url": SHARE_URL})

    self.assertEqual(1, len(recorded))

  def test_run_still_swallows_what_it_used_to_swallow(self):
    downloader, recorded = build_downloader(
      probe_result(ok=False, room_status=None, error="请求超时"), test_mode=False
    )

    self.assertIsNone(downloader.run({"url": SHARE_URL}))

  def test_run_still_raises_what_it_used_to_raise(self):
    def explode(share_url, build):
      raise RuntimeError("stream reset")

    downloader, recorded = build_downloader(
      probe_result(), test_mode=False, download=explode
    )

    with self.assertRaises(RuntimeError):
      downloader.run({"url": SHARE_URL})


if __name__ == "__main__":
  unittest.main()
