from collections.abc import Mapping
from pathlib import Path
import subprocess


class HlsDownloadError(RuntimeError):
  pass


class FfmpegUnavailable(HlsDownloadError):
  pass


class HlsRecorder:
  def __init__(self, ffmpeg_path="ffmpeg", runner=subprocess.run):
    self.ffmpeg_path = ffmpeg_path
    self.runner = runner

  @staticmethod
  def _header_block(headers):
    if headers is None:
      return None
    if not isinstance(headers, Mapping):
      raise TypeError("HLS headers must be a mapping")
    lines = []
    for name, value in headers.items():
      if value is None or value == "":
        continue
      name = str(name)
      value = str(value)
      if "\r" in name or "\n" in name or "\r" in value or "\n" in value:
        raise ValueError("HLS headers must not contain CR or LF")
      lines.append("{}: {}\r\n".format(name, value))
    return "".join(lines) or None

  @staticmethod
  def _proxy(proxies):
    if proxies is None:
      return None
    if not isinstance(proxies, Mapping):
      raise TypeError("HLS proxies must be a mapping")
    return proxies.get("https") or proxies.get("http")

  def _command(self, url, output_path, headers, proxies):
    command = [
      self.ffmpeg_path,
      "-nostdin",
      "-hide_banner",
      "-nostats",
      "-loglevel",
      "error",
      "-y",
    ]
    header_block = self._header_block(headers)
    if header_block is not None:
      command.extend(["-headers", header_block])
    proxy = self._proxy(proxies)
    if proxy:
      command.extend(["-http_proxy", str(proxy)])
    command.extend([
      "-i",
      str(url),
      "-c",
      "copy",
      "-f",
      "mpegts",
      str(output_path),
    ])
    return command

  def record(
    self,
    url,
    output_path,
    *,
    headers=None,
    proxies=None,
    max_retry=0,
  ):
    if type(max_retry) is not int or max_retry < 0:
      raise ValueError("HLS max_retry must be a non-negative integer")
    destination = Path(output_path)
    command = self._command(url, destination, headers, proxies)
    for _attempt in range(max_retry + 1):
      try:
        result = self.runner(
          command,
          stdout=subprocess.DEVNULL,
          stderr=subprocess.DEVNULL,
          shell=False,
        )
      except OSError as exc:
        raise FfmpegUnavailable(
          "ffmpeg executable is required for HLS download"
        ) from exc
      if result.returncode == 0:
        return destination
    raise HlsDownloadError(
      "ffmpeg HLS recording failed after {} attempts".format(max_retry + 1)
    )


__all__ = [
  "FfmpegUnavailable",
  "HlsDownloadError",
  "HlsRecorder",
]
