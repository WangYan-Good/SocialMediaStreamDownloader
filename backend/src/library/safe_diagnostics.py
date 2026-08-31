import re
from urllib.parse import urlsplit


UNKNOWN = "unknown"

_HOST = re.compile(r"[A-Za-z0-9.:-]{1,253}\Z")
_IDENTIFIER = re.compile(r"[A-Za-z0-9_-]{1,128}\Z")
_PROTOCOLS = frozenset({"flv", "hls"})
_LIVE_EVENTS = frozenset({
  "download_retry",
  "live_download_failed",
  "live_info_failed",
  "live_info_request",
  "live_info_response",
  "live_params_constructed",
  "live_query_rejected",
  "live_recovery_ack_failed",
  "live_recovery_handoff_failed",
  "live_recording_cancelled",
  "live_recording_failed",
  "live_recording_persistence_failed",
  "live_response_parse_failed",
  "share_url_failed",
  "share_url_parse_failed",
  "share_url_request",
  "stream_selection_failed",
})


def safe_url_host(url) -> str:
  """Return only a syntactically safe hostname, never any other URL part."""
  try:
    text = str(url)
    if any(ord(character) < 32 or ord(character) == 127 for character in text):
      return UNKNOWN
    parsed = urlsplit(text)
    ## Accessing port is the standard parser's delayed validation for malformed
    ## authorities such as ``:not-a-number``. It is deliberately checked even
    ## though diagnostics never render the port.
    parsed.port
    host = parsed.hostname
  except (TypeError, ValueError):
    return UNKNOWN
  if host is None or _HOST.fullmatch(host) is None:
    return UNKNOWN
  return host.lower()


def _safe_identifier(value) -> str:
  text = str(value)
  return text if _IDENTIFIER.fullmatch(text) is not None else UNKNOWN


def _error_class(error) -> str:
  if isinstance(error, type) and issubclass(error, BaseException):
    return error.__name__
  if isinstance(error, BaseException):
    return type(error).__name__
  return UNKNOWN


def live_diagnostic(
  event: str,
  *,
  url=None,
  status=None,
  room_id=None,
  protocol=None,
  error=None,
  state=None,
) -> str:
  """Build one closed-field diagnostic message for live operations.

  This function deliberately has no mapping/kwargs escape hatch. Callers can
  only name fields whose rendering is defined here, so a header, params dict,
  signed query or exception message cannot be added by accident.
  """
  if event not in _LIVE_EVENTS:
    raise ValueError("unsupported live diagnostic event")

  fields = ["event={}".format(event)]
  if url is not None:
    fields.append("host={}".format(safe_url_host(url)))
  if status is not None:
    safe_status = (
      status if type(status) is int and 100 <= status <= 599 else UNKNOWN
    )
    fields.append("status={}".format(safe_status))
  if room_id is not None:
    fields.append("room_id={}".format(_safe_identifier(room_id)))
  if protocol is not None:
    safe_protocol = protocol if protocol in _PROTOCOLS else UNKNOWN
    fields.append("protocol={}".format(safe_protocol))
  if error is not None:
    fields.append("error={}".format(_error_class(error)))
  if state is not None:
    fields.append("state={}".format("true" if state is True else "false"))
  return "live diagnostic " + " ".join(fields)
