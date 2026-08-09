from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
import tempfile
from threading import Barrier, Event, Thread
from time import sleep
import unittest
from unittest import mock
from urllib.error import ContentTooShortError
from requests import exceptions

from backend.src.library.baselib import load_yml
from backend.src.platform.douyin import douyin_live_downloader as live_module
from backend.src.platform.douyin import douyin_api as api_module
from backend.src.platform.douyin.douyin_header import DouyinShareHeader
from backend.src.platform.douyin.hls_recorder import (
  FfmpegUnavailable,
  HlsDownloadError,
  HlsRecorder,
)
from backend.src.platform.douyin.douyin_live_external_info import LiveExternal


PROJECT_ROOT = Path(__file__).resolve().parents[3]
CONFIG_EXAMPLE_PATH = PROJECT_ROOT / "docs" / "design" / "config.yml.example"


def live_config():
  config = load_yml(CONFIG_EXAMPLE_PATH)
  config["database"]["enable"] = False
  config["download"]["test_mode"] = True
  config["server"]["debug_mode"] = False
  return config


class LiveStreamResponse:
  def __init__(self, *, flv, hls):
    self._payload = {
      "data": {
        "room": {
          "stream_url": {
            "flv_pull_url": flv,
            "hls_pull_url_map": hls,
          }
        }
      }
    }

  def json(self):
    return self._payload


class LiveDownloaderPipelineTest(unittest.TestCase):
  def _run_live_pipeline_with_stream_urls(
    self,
    flv_urls,
    hls_urls,
    *,
    debug_mode=False,
    request_logger=None,
  ):
    config = live_config()
    config["server"]["debug_mode"] = debug_mode
    downloader = live_module.DouyinLiveDownloader(config)
    downloaded = []

    class FailingDatabase:
      def get_share_url_table_tuple(self):
        raise RuntimeError("database disconnected")

    class Response:
      def __init__(self, url, payload=None):
        self.url = url
        self.status_code = 200
        self._payload = payload

      def raise_for_status(self):
        return None

      def json(self):
        return self._payload

    downloader.database = FailingDatabase()
    responses = [
      Response(
        "https://live.douyin.com/douyin/webcast/reflow/123?sec_user_id=user"
      ),
      Response(
        "https://webcast.example.test/live-info",
        {
          "status_code": 0,
          "data": {
            "room": {
              "status": 2,
              "owner_user_id": "owner-1",
              "owner": {
                "nickname": "Test Host",
                "sec_uid": "sec-owner-1",
                "status": 1,
              },
              "stream_url": {
                "flv_pull_url": flv_urls,
                "hls_pull_url_map": hls_urls,
              },
            }
          },
        },
      ),
    ]
    original_request = live_module.request
    original_sleep = live_module.sleep
    original_get_logger = live_module.get_logger
    original_token_generator = DouyinShareHeader.create_douyin_msToken

    live_module.request = lambda *args, **kwargs: responses.pop(0)
    live_module.sleep = lambda *_args, **_kwargs: None
    if request_logger is not None:
      live_module.get_logger = lambda: request_logger
    downloader.download_live_stream = (
      lambda share_url, build, headers=None: downloaded.append((share_url, build))
    )
    DouyinShareHeader.create_douyin_msToken = lambda _header: ""
    try:
      downloader.run({"url": "https://v.douyin.com/example/"})
    finally:
      live_module.request = original_request
      live_module.sleep = original_sleep
      live_module.get_logger = original_get_logger
      DouyinShareHeader.create_douyin_msToken = original_token_generator
    self.assertEqual([], responses)
    self.assertEqual(1, len(downloaded))
    return downloaded[0][1]

  def test_default_douyin_api_uses_unified_config(self):
    config = live_config()
    config["platform"]["douyin"]["api"]["LIVE_DOMAIN"] = (
      "unified-live.example.test"
    )
    original_get_config = api_module.get_config
    api_module.get_config = lambda path: config["platform"]["douyin"]["api"]
    try:
      api = api_module.DouyinApi()
    finally:
      api_module.get_config = original_get_config

    self.assertEqual(
      api.get_config_dict_attr("$.LIVE_DOMAIN"),
      "unified-live.example.test",
    )

  def test_single_live_entry_passes_a_token_to_run(self):
    original_downloader = live_module.downloader
    received = []

    class Config:
      def get_config_dict_attr(self, attr):
        return False

    class Downloader:
      config = Config()

      def run(self, token):
        received.append(token)

    live_module.downloader = Downloader()
    try:
      live_module.download_single_live("https://example.test/live")
    finally:
      live_module.downloader = original_downloader

    self.assertEqual(received, [{"url": "https://example.test/live"}])

  def test_thread_limit_uses_unified_download_config(self):
    config = live_config()
    config["download"]["max_threads"] = 2
    downloader = live_module.DouyinLiveDownloader(config)
    downloader._actived_task_number = 2

    self.assertTrue(downloader.is_exceed_max_download_task())

  def test_unified_config_documents_hls_supervision_defaults(self):
    config = live_config()
    live_values = config["platform"]["douyin"]["live"]

    self.assertEqual(30, live_values.get("hls_stall_timeout"))
    self.assertEqual(5, live_values.get("hls_terminate_grace"))

  def test_zero_thread_limit_means_unlimited(self):
    config = live_config()
    config["download"]["max_threads"] = 0
    downloader = live_module.DouyinLiveDownloader(config)
    downloader._actived_task_number = 100

    self.assertFalse(downloader.is_exceed_max_download_task())

  def test_no_login_params_use_unified_live_config(self):
    config = live_config()
    downloader = live_module.DouyinLiveDownloader(config)
    downloader.header.init_share_live_header(False)
    downloader.header.create_douyin_msToken = lambda: "test-token"
    query_response = {
      "url": "https://live.douyin.com/douyin/webcast/reflow/123?sec_user_id=user",
      "path": "/douyin/webcast/reflow/123",
      "query": {"sec_user_id": ["user"]},
    }

    params = downloader.construct_live_params_no_login(query_response)

    self.assertEqual(params["type_id"], "0")
    self.assertEqual(params["live_id"], "1")
    self.assertEqual(params["room_id"], "123")
    self.assertEqual(params["sec_user_id"], "user")
    self.assertEqual(params["version_code"], "99.99.99")
    self.assertEqual(params["app_id"], "1128")
    self.assertEqual(params["msToken"], "test-token")
    self.assertTrue(params["verifyFp"])
    self.assertTrue(params["X-Bogus"])

  def test_run_in_test_mode_resolves_share_url_and_extracts_live_stream(self):
    config = live_config()
    downloader = live_module.DouyinLiveDownloader(config)
    downloaded = []

    class FailingDatabase:
      def get_share_url_table_tuple(self):
        raise RuntimeError("database disconnected")

    downloader.database = FailingDatabase()

    class Response:
      def __init__(self, url, payload=None):
        self.url = url
        self.status_code = 200
        self._payload = payload

      def raise_for_status(self):
        return None

      def json(self):
        return self._payload

    share_response = Response(
      "https://live.douyin.com/douyin/webcast/reflow/123?sec_user_id=user"
    )
    live_response = Response(
      "https://webcast.example.test/live-info",
      {
        "status_code": 0,
        "data": {
          "room": {
            "status": 2,
            "owner_user_id": "owner-1",
            "owner": {
              "nickname": "Test Host",
              "sec_uid": "sec-owner-1",
              "status": 1,
            },
            "stream_url": {
              "flv_pull_url": {
                "FULL_HD1": "https://stream.example.test/live.flv",
                "HD1": None,
                "SD1": None,
                "SD2": None,
              },
              "hls_pull_url_map": {
                "FULL_HD1": None,
                "HD1": None,
                "SD1": None,
                "SD2": None,
              },
            },
          }
        },
      },
    )
    responses = [share_response, live_response]
    original_request = live_module.request
    original_sleep = live_module.sleep
    original_token_generator = DouyinShareHeader.create_douyin_msToken

    def request(*args, **kwargs):
      return responses.pop(0)

    def capture_download(share_url, build, headers=None):
      downloaded.append((share_url, build))

    live_module.request = request
    live_module.sleep = lambda *_args, **_kwargs: None
    downloader.download_live_stream = capture_download
    DouyinShareHeader.create_douyin_msToken = lambda _header: ""
    try:
      downloader.run({"url": "https://v.douyin.com/example/"})
    finally:
      live_module.request = original_request
      live_module.sleep = original_sleep
      DouyinShareHeader.create_douyin_msToken = original_token_generator

    self.assertEqual(responses, [])
    self.assertEqual(len(downloaded), 1)
    share_url, build = downloaded[0]
    self.assertEqual(share_url, "https://v.douyin.com/example/")
    self.assertEqual(
      build["summary"]["stream_url"],
      "https://stream.example.test/live.flv",
    )
    self.assertEqual(build["summary"]["stream_name"], "live.flv")
    self.assertEqual(build["summary"]["nickname"], "Test Host")
    self.assertEqual(build["live_payload"]["msToken"], "")

  def test_run_summary_records_flv_protocol(self):
    build = self._run_live_pipeline_with_stream_urls(
      {
        "FULL_HD1": "https://stream.example.test/live.flv",
        "HD1": None,
        "SD1": None,
        "SD2": None,
      },
      {},
    )

    self.assertEqual("flv", build["summary"]["stream_protocol"])
    self.assertEqual("live.flv", build["summary"]["stream_name"])

  def test_run_summary_falls_back_to_hls_protocol(self):
    build = self._run_live_pipeline_with_stream_urls(
      {"FULL_HD1": None, "HD1": None, "SD1": None, "SD2": None},
      {
        "FULL_HD1": (
          "https://stream.example.test/stream-test/index.m3u8"
          "?sign=sensitive"
        ),
      },
    )

    self.assertEqual("hls", build["summary"]["stream_protocol"])
    self.assertEqual("stream-test.ts", build["summary"]["stream_name"])

  def test_run_debug_log_does_not_expose_signed_hls_url(self):
    messages = []
    stdout = StringIO()

    class RecordingLogger:
      def info(self, message):
        messages.append(str(message))

      def warning(self, message):
        messages.append(str(message))

      def error(self, message):
        messages.append(str(message))

    with redirect_stdout(stdout):
      self._run_live_pipeline_with_stream_urls(
        {"FULL_HD1": None},
        {
          "FULL_HD1": (
            "https://stream.example.test/stream-test/index.m3u8"
            "?sign=debug-signed-marker"
          ),
        },
        debug_mode=True,
        request_logger=RecordingLogger(),
      )

    self.assertNotIn("debug-signed-marker", "\n".join(messages))
    self.assertNotIn("debug-signed-marker", stdout.getvalue())

  def test_stream_extraction_rejects_hls_only_response(self):
    class Response:
      def json(self):
        return {
          "data": {
            "room": {
              "stream_url": {
                "flv_pull_url": {"FULL_HD1": None},
                "hls_pull_url_map": {
                  "FULL_HD1": "https://stream.example.test/live.m3u8"
                },
              }
            }
          }
        }

    with self.assertRaisesRegex(ValueError, "FLV"):
      LiveExternal().get_flv_pull_url(
        Response(),
        flv_clarity=1,
        hls_clarity=1,
      )

  def test_stream_extraction_falls_back_to_an_available_flv_quality(self):
    class Response:
      def json(self):
        return {
          "data": {
            "room": {
              "stream_url": {
                "flv_pull_url": {
                  "FULL_HD1": None,
                  "HD1": "https://stream.example.test/live_hd.flv",
                },
                "hls_pull_url_map": {},
              }
            }
          }
        }

    stream_url, stream_name = LiveExternal().get_flv_pull_url(
      Response(),
      flv_clarity=1,
      hls_clarity=1,
    )

    self.assertEqual(
      stream_url,
      "https://stream.example.test/live_hd.flv",
    )
    self.assertEqual(stream_name, "live_hd.flv")

  def test_live_source_prefers_any_flv_before_hls(self):
    source = LiveExternal().get_live_stream_source(
      LiveStreamResponse(
        flv={
          "FULL_HD1": None,
          "HD1": "https://stream.example.test/live_hd.flv",
        },
        hls={
          "FULL_HD1": "https://stream.example.test/stream-origin/index.m3u8",
        },
      ),
      flv_clarity=1,
      hls_clarity=1,
    )

    self.assertEqual("flv", source.protocol)
    self.assertEqual("https://stream.example.test/live_hd.flv", source.url)
    self.assertEqual("live_hd.flv", source.file_name)

  def test_live_source_falls_back_to_configured_hls_as_ts(self):
    source = LiveExternal().get_live_stream_source(
      LiveStreamResponse(
        flv={"FULL_HD1": None},
        hls={
          "HD1": (
            "https://stream.example.test/stream-hd/index.m3u8"
            "?sign=sensitive"
          ),
        },
      ),
      flv_clarity=1,
      hls_clarity=2,
    )

    self.assertEqual("hls", source.protocol)
    self.assertEqual("stream-hd.ts", source.file_name)

  def test_live_source_falls_back_to_an_available_hls_quality(self):
    source = LiveExternal().get_live_stream_source(
      LiveStreamResponse(
        flv={},
        hls={"SD1": "https://stream.example.test/live_sd.m3u8"},
      ),
      flv_clarity=1,
      hls_clarity=1,
    )

    self.assertEqual("hls", source.protocol)
    self.assertEqual("live_sd.ts", source.file_name)

  def test_live_source_rejects_response_without_flv_or_hls(self):
    with self.assertRaisesRegex(ValueError, "FLV or HLS"):
      LiveExternal().get_live_stream_source(
        LiveStreamResponse(flv={}, hls={}),
        flv_clarity=1,
        hls_clarity=1,
      )

  def test_live_source_skips_malformed_flv_before_valid_flv(self):
    source = LiveExternal().get_live_stream_source(
      LiveStreamResponse(
        flv={
          "FULL_HD1": "https://stream.example.test/no-media-suffix",
          "HD1": "https://stream.example.test/fallback.flv",
        },
        hls={},
      ),
      flv_clarity=1,
      hls_clarity=1,
    )

    self.assertEqual("flv", source.protocol)
    self.assertEqual("fallback.flv", source.file_name)

  def test_live_source_skips_unparseable_flv_before_valid_flv(self):
    source = LiveExternal().get_live_stream_source(
      LiveStreamResponse(
        flv={
          "FULL_HD1": "http://[broken/live.flv",
          "HD1": "https://stream.example.test/fallback.flv",
        },
        hls={},
      ),
      flv_clarity=1,
      hls_clarity=1,
    )

    self.assertEqual("flv", source.protocol)
    self.assertEqual("fallback.flv", source.file_name)

  def test_live_source_uses_hls_after_only_malformed_flv_candidates(self):
    source = LiveExternal().get_live_stream_source(
      LiveStreamResponse(
        flv={
          "FULL_HD1": "https://stream.example.test/no-media-suffix",
          "HD1": 42,
          "SD1": "   ",
        },
        hls={"FULL_HD1": "https://stream.example.test/live.m3u8"},
      ),
      flv_clarity=1,
      hls_clarity=1,
    )

    self.assertEqual("hls", source.protocol)
    self.assertEqual("live.ts", source.file_name)

  def test_live_source_skips_malformed_hls_before_valid_hls(self):
    source = LiveExternal().get_live_stream_source(
      LiveStreamResponse(
        flv={},
        hls={
          "FULL_HD1": "   ",
          "HD1": 42,
          "SD1": "https://stream.example.test/fallback.m3u8",
        },
      ),
      flv_clarity=1,
      hls_clarity=1,
    )

    self.assertEqual("hls", source.protocol)
    self.assertEqual("fallback.ts", source.file_name)

  def test_test_mode_skips_only_live_stream_data_download(self):
    config = live_config()
    config["download"]["test_mode"] = True
    config["download"]["tick_naming"] = False

    with tempfile.TemporaryDirectory() as temporary_directory:
      save_path = Path(temporary_directory) / "downloads"
      config["download"]["save_path"] = str(save_path)
      downloader = live_module.DouyinLiveDownloader(config)
      database_calls = []

      class RecordingDatabase:
        def is_owner_user_id_record_exist(self, owner_user_id):
          database_calls.append(owner_user_id)
          return False

      downloader.database = RecordingDatabase()
      build = {
        "summary": {
          "stream_url": "https://stream.example.test/live.flv",
          "stream_name": "live.flv",
          "directory_name": "Test_Host",
          "nickname": "Test Host",
        },
        "external_info": {
          "data": {"room": {"owner_user_id": "owner-1"}}
        },
      }

      downloader.download_live_stream(
        "https://v.douyin.com/example/",
        build,
      )

      stream_directory = save_path / "douyin" / "live" / "Test_Host"
      self.assertTrue(stream_directory.is_dir())
      self.assertFalse((stream_directory / "live.flv").exists())
      self.assertEqual(database_calls, ["owner-1"])
      self.assertEqual(downloader._actived_task_number, 0)

  def test_download_live_stream_writes_stream_bytes(self):
    config = live_config()
    config["download"]["test_mode"] = False
    config["download"]["tick_naming"] = False

    with tempfile.TemporaryDirectory() as temporary_directory:
      temporary_path = Path(temporary_directory)
      source_path = temporary_path / "source.flv"
      source_path.write_bytes(b"live-stream-bytes")
      save_path = temporary_path / "downloads"
      config["download"]["save_path"] = str(save_path)
      downloader = live_module.DouyinLiveDownloader(config)
      build = {
        "summary": {
          "stream_url": source_path.as_uri(),
          "stream_name": "stream.flv",
          "directory_name": "Test_Host",
          "nickname": "Test Host",
        },
        "external_info": {
          "data": {"room": {"owner_user_id": "owner-1"}}
        },
      }

      downloader.download_live_stream(
        "https://v.douyin.com/example/",
        build,
      )

      downloaded_path = (
        save_path / "douyin" / "live" / "Test_Host" / "stream.flv"
      )
      self.assertEqual(downloaded_path.read_bytes(), b"live-stream-bytes")

  def test_http_stream_write_uses_configured_headers(self):
    original_request = live_module.request
    original_urlretrieve = live_module.urlretrieve

    class StreamResponse:
      headers = {"Content-Length": "22"}

      def raise_for_status(self):
        return None

      def iter_content(self, chunk_size):
        yield b"http-live-stream-bytes"

    def stream_request(*args, **kwargs):
      if kwargs.get("headers", {}).get("X-Stream-Test") != "allowed":
        raise AssertionError("configured stream headers were not forwarded")
      if kwargs.get("timeout") != 10:
        raise AssertionError("configured stream timeout was not forwarded")
      if kwargs.get("proxies") != {"http": None, "https": None}:
        raise AssertionError("configured stream proxies were not forwarded")
      if kwargs.get("stream") is not True:
        raise AssertionError("HTTP live stream must use streaming mode")
      return StreamResponse()

    def reject_urlretrieve(*args, **kwargs):
      raise AssertionError("HTTP streams must use the requests transport")

    live_module.request = stream_request
    live_module.urlretrieve = reject_urlretrieve
    try:
      config = live_config()
      config["download"]["test_mode"] = False
      config["download"]["tick_naming"] = False
      with tempfile.TemporaryDirectory() as temporary_directory:
        save_path = Path(temporary_directory) / "downloads"
        config["download"]["save_path"] = str(save_path)
        downloader = live_module.DouyinLiveDownloader(config)
        downloader.header.set_header_dict_attr("$.X-Stream-Test", "allowed")
        build = {
          "summary": {
            "stream_url": "https://stream.example.test/live.flv",
            "stream_name": "stream.flv",
            "directory_name": "Test_Host",
            "nickname": "Test Host",
          },
          "external_info": {
            "data": {"room": {"owner_user_id": "owner-1"}}
          },
        }

        downloader.download_live_stream(
          "https://v.douyin.com/example/",
          build,
        )

        downloaded_path = (
          save_path / "douyin" / "live" / "Test_Host" / "stream.flv"
        )
        self.assertEqual(
          downloaded_path.read_bytes(),
          b"http-live-stream-bytes",
        )
    finally:
      live_module.request = original_request
      live_module.urlretrieve = original_urlretrieve

  def test_http_stream_timeout_preserves_downloaded_content_as_target_file(self):
    original_request = live_module.request

    class InterruptedStreamResponse:
      headers = {}

      def raise_for_status(self):
        return None

      def iter_content(self, chunk_size):
        yield b"downloaded-before-timeout"
        raise exceptions.ReadTimeout("live stream read timed out")

      def close(self):
        return None

    live_module.request = lambda *args, **kwargs: InterruptedStreamResponse()
    try:
      config = live_config()
      config["download"]["max_retry"] = 0
      downloader = live_module.DouyinLiveDownloader(config)
      with tempfile.TemporaryDirectory() as temporary_directory:
        with self.assertRaises(exceptions.ReadTimeout):
          downloader.auto_down(
            "https://stream.example.test/live.flv",
            temporary_directory,
            "stream.flv",
            0,
          )

        downloaded_path = Path(temporary_directory) / "stream.flv"
        self.assertTrue(downloaded_path.is_file())
        self.assertEqual(
          b"downloaded-before-timeout",
          downloaded_path.read_bytes(),
        )
    finally:
      live_module.request = original_request

  def test_hls_stream_uses_recorder_instead_of_flv_transport(self):
    config = live_config()
    config["download"]["test_mode"] = False
    config["download"]["tick_naming"] = False
    config["download"]["max_retry"] = 2
    config["platform"]["douyin"]["live"]["max_timeout"] = 7
    config["platform"]["douyin"]["live"]["hls_stall_timeout"] = 41
    config["platform"]["douyin"]["live"]["hls_terminate_grace"] = 2.5
    recorded = []

    class RecordingHlsRecorder:
      def record(self, url, output_path, **kwargs):
        recorded.append((url, output_path, kwargs))
        return output_path

    def reject_flv(*args, **kwargs):
      raise AssertionError("HLS sources must not use the FLV transport")

    with tempfile.TemporaryDirectory() as temporary_directory:
      config["download"]["save_path"] = temporary_directory
      downloader = live_module.DouyinLiveDownloader(config)
      downloader.hls_recorder = RecordingHlsRecorder()
      downloader.auto_down = reject_flv
      downloader.download_live_stream(
        "https://v.douyin.com/example/",
        {
          "summary": {
            "stream_url": "https://stream.example.test/index.m3u8?sign=sensitive",
            "stream_name": "stream-test.ts",
            "stream_protocol": "hls",
            "directory_name": "Test_Host",
            "nickname": "Test Host",
          },
          "external_info": {
            "data": {"room": {"owner_user_id": "owner-1"}}
          },
        },
      )

      expected_path = (
        Path(temporary_directory)
        / "douyin"
        / "live"
        / "Test_Host"
        / "stream-test.ts"
      )

    self.assertEqual(1, len(recorded))
    url, output_path, kwargs = recorded[0]
    self.assertEqual(
      "https://stream.example.test/index.m3u8?sign=sensitive",
      url,
    )
    self.assertEqual(expected_path, output_path)
    self.assertEqual(
      {
        "max_retry": 2,
        "io_timeout": 7,
        "stall_timeout": 41,
        "terminate_grace": 2.5,
      },
      {
        name: kwargs.get(name)
        for name in (
          "max_retry",
          "io_timeout",
          "stall_timeout",
          "terminate_grace",
        )
      },
    )
    self.assertEqual(downloader._actived_task_number, 0)

  def test_hls_stream_preserves_existing_recording_with_unique_name(self):
    config = live_config()
    config["download"]["test_mode"] = False
    config["download"]["tick_naming"] = False
    recorded_paths = []

    class RecordingHlsRecorder:
      def record(self, url, output_path, **kwargs):
        recorded_paths.append(output_path)
        output_path.write_bytes(b"new-recording")
        return output_path

    with tempfile.TemporaryDirectory() as temporary_directory:
      config["download"]["save_path"] = temporary_directory
      stream_directory = (
        Path(temporary_directory) / "douyin" / "live" / "Test_Host"
      )
      stream_directory.mkdir(parents=True)
      existing_path = stream_directory / "stream-test.ts"
      existing_path.write_bytes(b"existing-recording")
      downloader = live_module.DouyinLiveDownloader(config)
      downloader.hls_recorder = RecordingHlsRecorder()

      downloader.download_live_stream(
        "https://v.douyin.com/example/",
        {
          "summary": {
            "stream_url": "https://stream.example.test/index.m3u8",
            "stream_name": "stream-test.ts",
            "stream_protocol": "hls",
            "directory_name": "Test_Host",
            "nickname": "Test Host",
          },
          "external_info": {
            "data": {"room": {"owner_user_id": "owner-1"}}
          },
        },
      )

      self.assertEqual(b"existing-recording", existing_path.read_bytes())
      self.assertEqual(
        b"new-recording",
        (stream_directory / "re_0_stream-test.ts").read_bytes(),
      )

    self.assertEqual(
      [stream_directory / "re_0_stream-test.ts"],
      recorded_paths,
    )

  def test_hls_stream_uses_backward_compatible_supervision_defaults(self):
    config = live_config()
    config["download"]["test_mode"] = False
    config["download"]["tick_naming"] = False
    config["platform"]["douyin"]["live"]["max_timeout"] = 12
    live_config_values = config["platform"]["douyin"]["live"]
    live_config_values.pop("hls_stall_timeout", None)
    live_config_values.pop("hls_terminate_grace", None)
    recorded_kwargs = []

    class RecordingHlsRecorder:
      def record(self, url, output_path, **kwargs):
        recorded_kwargs.append(kwargs)
        return output_path

    with tempfile.TemporaryDirectory() as temporary_directory:
      config["download"]["save_path"] = temporary_directory
      downloader = live_module.DouyinLiveDownloader(config)
      downloader.hls_recorder = RecordingHlsRecorder()
      downloader.download_live_stream(
        "https://v.douyin.com/example/",
        {
          "summary": {
            "stream_url": "https://stream.example.test/index.m3u8",
            "stream_name": "stream-test.ts",
            "stream_protocol": "hls",
            "directory_name": "Test_Host",
            "nickname": "Test Host",
          },
          "external_info": {
            "data": {"room": {"owner_user_id": "owner-1"}}
          },
        },
      )

    self.assertEqual(1, len(recorded_kwargs))
    self.assertEqual(
      {
        "max_retry": config["download"]["max_retry"],
        "io_timeout": 12,
        "stall_timeout": 36,
        "terminate_grace": 5,
      },
      {
        name: recorded_kwargs[0].get(name)
        for name in (
          "max_retry",
          "io_timeout",
          "stall_timeout",
          "terminate_grace",
        )
      },
    )

  def test_concurrent_hls_streams_reserve_distinct_output_paths(self):
    config = live_config()
    config["download"]["test_mode"] = False
    config["download"]["tick_naming"] = False
    config["download"]["max_threads"] = 0
    recorder_barrier = Barrier(2)
    recorded_paths = []
    errors = []

    class BarrierRecorder:
      def record(self, url, output_path, **kwargs):
        recorded_paths.append(output_path)
        recorder_barrier.wait(timeout=2)
        output_path.write_bytes(b"recorded")
        return output_path

    def build():
      return {
        "summary": {
          "stream_url": "https://stream.example.test/index.m3u8",
          "stream_name": "stream-test.ts",
          "stream_protocol": "hls",
          "directory_name": "Test_Host",
          "nickname": "Test Host",
        },
        "external_info": {
          "data": {"room": {"owner_user_id": "owner-1"}}
        },
      }

    with tempfile.TemporaryDirectory() as temporary_directory:
      config["download"]["save_path"] = temporary_directory
      downloader = live_module.DouyinLiveDownloader(config)
      downloader.hls_recorder = BarrierRecorder()

      def download():
        try:
          downloader.download_live_stream(
            "https://v.douyin.com/example/",
            build(),
          )
        except Exception as exc:
          errors.append(exc)

      threads = [Thread(target=download), Thread(target=download)]
      for thread in threads:
        thread.start()
      for thread in threads:
        thread.join(timeout=3)

      stream_directory = (
        Path(temporary_directory) / "douyin" / "live" / "Test_Host"
      )
      self.assertEqual([], errors)
      self.assertTrue(all(not thread.is_alive() for thread in threads))
      self.assertEqual(
        {
          stream_directory / "stream-test.ts",
          stream_directory / "re_0_stream-test.ts",
        },
        set(recorded_paths),
      )

  def test_hls_stream_logs_do_not_expose_transport_credentials(self):
    sensitive_values = (
      "signed-url-marker",
      "cookie-marker",
      "proxy-marker",
    )
    messages = []

    class RecordingLogger:
      def info(self, message):
        messages.append(str(message))

      def warning(self, message):
        messages.append(str(message))

      def error(self, message):
        messages.append(str(message))

    class SuccessfulRecorder:
      def record(self, url, output_path, **kwargs):
        return output_path

    config = live_config()
    config["download"]["test_mode"] = False
    config["download"]["tick_naming"] = False
    config["platform"]["douyin"]["login"]["proxies"]["https"] = (
      "http://proxy-marker"
    )
    original_get_logger = live_module.get_logger
    live_module.get_logger = lambda: RecordingLogger()
    try:
      with tempfile.TemporaryDirectory() as temporary_directory:
        config["download"]["save_path"] = temporary_directory
        downloader = live_module.DouyinLiveDownloader(config)
        downloader.hls_recorder = SuccessfulRecorder()
        downloader.download_live_stream(
          "https://v.douyin.com/example/",
          {
            "summary": {
              "stream_url": (
                "https://stream.example.test/index.m3u8?signed-url-marker"
              ),
              "stream_name": "stream-test.ts",
              "stream_protocol": "hls",
              "directory_name": "Test_Host",
              "nickname": "Test Host",
            },
            "external_info": {
              "data": {"room": {"owner_user_id": "owner-1"}}
            },
          },
          headers={"Cookie": "cookie-marker"},
        )
    finally:
      live_module.get_logger = original_get_logger

    output = "\n".join(messages)
    for value in sensitive_values:
      self.assertNotIn(value, output)

  def test_hls_failure_propagates_and_releases_task_slot(self):
    expected_error = HlsDownloadError("sanitized HLS failure")
    reserved_paths = []
    partial_paths = []

    class FailingRecorder:
      def record(self, url, output_path, **kwargs):
        reserved_paths.append(output_path)
        partial_path = output_path.with_name(
          "{}.attempt-1.partial.ts".format(output_path.stem)
        )
        partial_path.write_bytes(b"preserved-partial")
        partial_paths.append(partial_path)
        raise expected_error

    config = live_config()
    config["download"]["test_mode"] = False
    config["download"]["tick_naming"] = False
    with tempfile.TemporaryDirectory() as temporary_directory:
      config["download"]["save_path"] = temporary_directory
      downloader = live_module.DouyinLiveDownloader(config)
      downloader.hls_recorder = FailingRecorder()
      with self.assertRaises(HlsDownloadError) as raised:
        downloader.download_live_stream(
          "https://v.douyin.com/example/",
          {
            "summary": {
              "stream_url": "https://stream.example.test/index.m3u8",
              "stream_name": "stream-test.ts",
              "stream_protocol": "hls",
              "directory_name": "Test_Host",
              "nickname": "Test Host",
            },
            "external_info": {
              "data": {"room": {"owner_user_id": "owner-1"}}
            },
          },
        )

      self.assertEqual(1, len(reserved_paths))
      self.assertFalse(reserved_paths[0].exists())
      self.assertEqual(1, len(partial_paths))
      self.assertEqual(b"preserved-partial", partial_paths[0].read_bytes())

    self.assertIs(expected_error, raised.exception)
    self.assertEqual(0, downloader._actived_task_number)

  def test_hls_cleanup_error_does_not_mask_recorder_error_or_leak_slot(self):
    for cleanup_failure in ("stat", "unlink"):
      with self.subTest(cleanup_failure=cleanup_failure):
        expected_error = HlsDownloadError(
          "sanitized recorder failure {}".format(cleanup_failure)
        )
        reserved_path = [None]
        real_stat = Path.stat
        real_unlink = Path.unlink

        class FailingRecorder:
          def record(self, url, output_path, **kwargs):
            reserved_path[0] = output_path
            raise expected_error

        def controlled_stat(path, *args, **kwargs):
          if cleanup_failure == "stat" and path == reserved_path[0]:
            raise OSError("reserved output stat failed")
          return real_stat(path, *args, **kwargs)

        def controlled_unlink(path, *args, **kwargs):
          if cleanup_failure == "unlink" and path == reserved_path[0]:
            raise PermissionError("reserved output unlink failed")
          return real_unlink(path, *args, **kwargs)

        config = live_config()
        config["download"]["test_mode"] = False
        config["download"]["tick_naming"] = False
        with tempfile.TemporaryDirectory() as temporary_directory:
          config["download"]["save_path"] = temporary_directory
          downloader = live_module.DouyinLiveDownloader(config)
          downloader.hls_recorder = FailingRecorder()
          caught = None
          with (
            mock.patch.object(Path, "stat", new=controlled_stat),
            mock.patch.object(Path, "unlink", new=controlled_unlink),
          ):
            try:
              downloader.download_live_stream(
                "https://v.douyin.com/example/",
                {
                  "summary": {
                    "stream_url": "https://stream.example.test/index.m3u8",
                    "stream_name": "stream-test.ts",
                    "stream_protocol": "hls",
                    "directory_name": "Test_Host",
                    "nickname": "Test Host",
                  },
                  "external_info": {
                    "data": {"room": {"owner_user_id": "owner-1"}}
                  },
                },
              )
            except BaseException as exc:
              caught = exc

          self.assertIs(expected_error, caught)
          self.assertEqual(0, downloader._actived_task_number)

  def test_missing_ffmpeg_does_not_leave_reserved_output(self):
    config = live_config()
    config["download"]["test_mode"] = False
    config["download"]["tick_naming"] = False
    with tempfile.TemporaryDirectory() as temporary_directory:
      config["download"]["save_path"] = temporary_directory
      downloader = live_module.DouyinLiveDownloader(config)
      downloader.hls_recorder = HlsRecorder(
        str(Path(temporary_directory) / "missing-ffmpeg")
      )
      with self.assertRaises(FfmpegUnavailable):
        downloader.download_live_stream(
          "https://v.douyin.com/example/",
          {
            "summary": {
              "stream_url": "https://stream.example.test/index.m3u8",
              "stream_name": "stream-test.ts",
              "stream_protocol": "hls",
              "directory_name": "Test_Host",
              "nickname": "Test Host",
            },
            "external_info": {
              "data": {"room": {"owner_user_id": "owner-1"}}
            },
          },
        )

      stream_directory = (
        Path(temporary_directory) / "douyin" / "live" / "Test_Host"
      )
      self.assertEqual([], list(stream_directory.iterdir()))

  def test_invalid_hls_headers_do_not_leave_reserved_output(self):
    config = live_config()
    config["download"]["test_mode"] = False
    config["download"]["tick_naming"] = False
    with tempfile.TemporaryDirectory() as temporary_directory:
      config["download"]["save_path"] = temporary_directory
      downloader = live_module.DouyinLiveDownloader(config)
      with self.assertRaisesRegex(ValueError, "CR or LF"):
        downloader.download_live_stream(
          "https://v.douyin.com/example/",
          {
            "summary": {
              "stream_url": "https://stream.example.test/index.m3u8",
              "stream_name": "stream-test.ts",
              "stream_protocol": "hls",
              "directory_name": "Test_Host",
              "nickname": "Test Host",
            },
            "external_info": {
              "data": {"room": {"owner_user_id": "owner-1"}}
            },
          },
          headers={"Cookie": "valid\r\nInjected: value"},
        )

      stream_directory = (
        Path(temporary_directory) / "douyin" / "live" / "Test_Host"
      )
      self.assertEqual([], list(stream_directory.iterdir()))

  def test_hls_test_mode_never_starts_recorder(self):
    class RejectingRecorder:
      def record(self, url, output_path, **kwargs):
        raise AssertionError("test mode must not start ffmpeg")

    config = live_config()
    config["download"]["test_mode"] = True
    config["download"]["tick_naming"] = False
    with tempfile.TemporaryDirectory() as temporary_directory:
      config["download"]["save_path"] = temporary_directory
      downloader = live_module.DouyinLiveDownloader(config)
      downloader.hls_recorder = RejectingRecorder()
      downloader.download_live_stream(
        "https://v.douyin.com/example/",
        {
          "summary": {
            "stream_url": "https://stream.example.test/index.m3u8",
            "stream_name": "stream-test.ts",
            "stream_protocol": "hls",
            "directory_name": "Test_Host",
            "nickname": "Test Host",
          },
          "external_info": {
            "data": {"room": {"owner_user_id": "owner-1"}}
          },
        },
      )

    self.assertEqual(0, downloader._actived_task_number)

  def test_stream_write_stops_after_configured_retries(self):
    config = live_config()
    config["download"]["max_retry"] = 2
    downloader = live_module.DouyinLiveDownloader(config)
    original_urlretrieve = live_module.urlretrieve
    attempts = []

    def fail_download(url, file_name):
      attempts.append((url, file_name))
      if len(attempts) > 3:
        raise AssertionError("download exceeded configured retry count")
      raise ContentTooShortError("incomplete stream", b"")

    live_module.urlretrieve = fail_download
    try:
      with self.assertRaises(ContentTooShortError):
        downloader.auto_down(
          "file:///tmp/live.flv",
          "/tmp",
          "live.flv",
          0,
        )
    finally:
      live_module.urlretrieve = original_urlretrieve

    self.assertEqual(len(attempts), 3)

  def test_stream_timeout_uses_configured_retry_limit(self):
    config = live_config()
    config["download"]["max_retry"] = 1
    downloader = live_module.DouyinLiveDownloader(config)
    original_urlretrieve = live_module.urlretrieve
    attempts = []

    def timeout_download(url, file_name):
      attempts.append((url, file_name))
      raise TimeoutError("stream timed out")

    live_module.urlretrieve = timeout_download
    try:
      with self.assertRaises(TimeoutError):
        downloader.auto_down(
          "file:///tmp/live.flv",
          "/tmp",
          "live.flv",
          0,
        )
    finally:
      live_module.urlretrieve = original_urlretrieve

    self.assertEqual(len(attempts), 2)

  def test_download_failure_is_propagated_and_releases_task_slot(self):
    config = live_config()
    config["download"]["test_mode"] = False
    config["download"]["tick_naming"] = False
    downloader = live_module.DouyinLiveDownloader(config)
    expected_error = exceptions.ConnectionError("stream disconnected")

    def fail_download(*args, **kwargs):
      raise expected_error

    downloader.auto_down = fail_download
    build = {
      "summary": {
        "stream_url": "https://stream.example.test/live.flv",
        "stream_name": "live.flv",
        "directory_name": "Test_Host",
        "nickname": "Test Host",
      },
      "external_info": {
        "data": {"room": {"owner_user_id": "owner-1"}}
      },
    }

    with tempfile.TemporaryDirectory() as temporary_directory:
      config["download"]["save_path"] = temporary_directory
      with self.assertRaises(exceptions.ConnectionError) as raised:
        downloader.download_live_stream(
          "https://v.douyin.com/example/",
          build,
        )

    self.assertIs(raised.exception, expected_error)
    self.assertEqual(downloader._actived_task_number, 0)

  def test_waiting_download_does_not_block_active_task_completion(self):
    config = live_config()
    config["download"]["max_threads"] = 1
    config["download"]["test_mode"] = True
    config["download"]["tick_naming"] = False
    downloader = live_module.DouyinLiveDownloader(config)
    downloader._actived_task_number = 1
    build = {
      "summary": {
        "stream_url": "https://stream.example.test/live.flv",
        "stream_name": "live.flv",
        "directory_name": "Test_Host",
        "nickname": "Test Host",
      },
      "external_info": {
        "data": {"room": {"owner_user_id": "owner-1"}}
      },
    }

    waiting_download = Thread(
      target=downloader.download_live_stream,
      args=("https://v.douyin.com/example/", build),
      daemon=True,
    )

    def complete_active_download():
      downloader.acquire()
      downloader._actived_task_number -= 1
      downloader.release()

    waiting_download.start()
    sleep(0.05)
    completion = Thread(target=complete_active_download, daemon=True)
    completion.start()
    waiting_download.join(timeout=0.5)
    completion.join(timeout=0.5)

    self.assertFalse(waiting_download.is_alive())
    self.assertFalse(completion.is_alive())

  def test_failed_hls_download_releases_single_slot_to_waiting_download(self):
    config = live_config()
    config["download"]["max_threads"] = 1
    config["download"]["test_mode"] = False
    config["download"]["tick_naming"] = False
    first_entered = Event()
    release_first = Event()
    second_entered = Event()
    recorder_calls = []
    errors = []
    expected_error = HlsDownloadError("bounded first HLS failure")

    class HandoffRecorder:
      def record(self, url, output_path, **kwargs):
        call_number = len(recorder_calls) + 1
        recorder_calls.append(call_number)
        if call_number == 1:
          first_entered.set()
          if not release_first.wait(timeout=1):
            raise AssertionError("first recorder call was not released")
          raise expected_error
        second_entered.set()
        output_path.write_bytes(b"second-complete")
        return output_path

    def build():
      return {
        "summary": {
          "stream_url": "https://stream.example.test/index.m3u8",
          "stream_name": "stream-test.ts",
          "stream_protocol": "hls",
          "directory_name": "Test_Host",
          "nickname": "Test Host",
        },
        "external_info": {
          "data": {"room": {"owner_user_id": "owner-1"}}
        },
      }

    with tempfile.TemporaryDirectory() as temporary_directory:
      config["download"]["save_path"] = temporary_directory
      downloader = live_module.DouyinLiveDownloader(config)
      downloader.hls_recorder = HandoffRecorder()

      def download():
        try:
          downloader.download_live_stream(
            "https://v.douyin.com/example/",
            build(),
          )
        except Exception as exc:
          errors.append(exc)

      first = Thread(target=download, daemon=True)
      second = Thread(target=download, daemon=True)
      first.start()
      self.assertTrue(first_entered.wait(timeout=1))
      second.start()
      self.assertFalse(second_entered.wait(timeout=0.1))
      release_first.set()
      first.join(timeout=2)
      second.join(timeout=2)

      self.assertFalse(first.is_alive())
      self.assertFalse(second.is_alive())
      self.assertTrue(second_entered.is_set())
      self.assertEqual([expected_error], errors)
      self.assertEqual([1, 2], recorder_calls)
      self.assertEqual(0, downloader._actived_task_number)

  def test_share_request_failure_is_not_masked_by_unbound_response(self):
    config = live_config()
    config["download"]["test_mode"] = False
    downloader = live_module.DouyinLiveDownloader(config)
    original_request = live_module.request

    def fail_request(*args, **kwargs):
      raise exceptions.ConnectionError("network unavailable")

    live_module.request = fail_request
    try:
      result = downloader.run({"url": "https://v.douyin.com/example/"})
    finally:
      live_module.request = original_request

    self.assertIsNone(result)

  def test_patrolman_entry_wraps_urls_as_tokens(self):
    original_downloader = live_module.downloader
    listener_items = []

    class Config:
      def get_config_dict_attr(self, attr):
        return False

    class Listener:
      def add_sub_task(self, item):
        listener_items.append(item)

      def is_patrolman_actived(self):
        return True

    class Downloader:
      config = Config()
      live_douyin_listener = Listener()

      def run(self, token):
        return token

    live_module.downloader = Downloader()
    try:
      live_module.download_multiple_live_with_patrolman([
        "https://example.test/live",
      ])
    finally:
      live_module.downloader = original_downloader

    self.assertEqual(
      listener_items[0]._args,
      ({"url": "https://example.test/live"},),
    )

  def test_live_test_entry_wraps_url_as_token(self):
    original_downloader = live_module.downloader
    received = []

    class Config:
      def get_config_dict_attr(self, attr):
        return False

    class Downloader:
      config = Config()

      def run(self, token):
        received.append(token)

    live_module.downloader = Downloader()
    try:
      live_module.download_live_test(["https://example.test/live"])
    finally:
      live_module.downloader = original_downloader

    self.assertEqual(received, [{"url": "https://example.test/live"}])


if __name__ == "__main__":
  unittest.main()
