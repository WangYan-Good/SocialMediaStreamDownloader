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


##
## >>======================= persistence diagnostics =======================>>
##
##
## The same closed-field discipline as ``live_diagnostic``, applied to the layer
## that talks to MySQL.
##
## Persistence is where the raw values live. A record dict *is* the row, a
## parameter tuple *is* the row, a WHERE mapping *is* the identifiers somebody
## searched by, and a driver's exception message routinely carries the statement
## and the bound parameters that failed. Any of those interpolated into a log
## line writes the data into a file with none of the access rules the data
## itself has - and log files are rotated, shipped and read by people who could
## not read the row.
##
## DEBUG is not a lower standard here. ``$.log.level`` is operator-configurable,
## the bootstrap logger runs at DEBUG before any configuration is read, and a
## DEBUG line lands in exactly the same persisted file as an ERROR one.
##
## So the mitigation is not a scrubber. Truncating to 100 characters, replacing
## a known token or matching a secret-shaped regular expression are all
## after-the-fact cleanups of a value that should never have reached the
## formatter: they catch the leak somebody already thought of and miss the
## nickname, the share url and the driver message that arrive next. This
## function instead refuses to *accept* a raw value at all. Callers can only
## name fields whose rendering is defined below, and there is deliberately no
## mapping, ``**kwargs`` or free-text parameter, so a record, a params tuple or
## an exception message cannot be added by accident or by a later edit that
## looked harmless.
##
_PERSISTENCE_EVENTS = frozenset({
  "persistence_connection_failed",
  "persistence_connection_returned_failed",
  "persistence_delete_failed",
  "persistence_deleted",
  "persistence_duplicate_ignored",
  "persistence_empty_record",
  "persistence_import_failed",
  "persistence_initialisation_failed",
  "persistence_pool_ready",
  "persistence_registered",
  "persistence_schema_verification_failed",
  "persistence_table_absent",
  "persistence_table_create_failed",
  "persistence_table_created",
  "persistence_table_drop_refused",
  "persistence_table_dropped",
  "persistence_table_present",
  "persistence_unknown_table",
  "persistence_unregistered",
  "persistence_insert_failed",
  "persistence_inserted",
  "persistence_invalid_record",
  "persistence_lock_timeout",
  "persistence_lookup_failed",
  "persistence_missing_primary_key",
  "persistence_no_conditions",
  "persistence_no_update_fields",
  "persistence_query_failed",
  "persistence_queried",
  "persistence_record_absent",
  "persistence_registration_failed",
  "persistence_column_skipped",
  "persistence_schema_probe_failed",
  "persistence_statement_prepared",
  "persistence_table_dropped_failed",
  "persistence_unknown_identity",
  "persistence_update_failed",
  "persistence_updated",
})

##
## Operations, closed. A caller cannot invent one, so this can never become a
## place to smuggle a sentence.
##
_PERSISTENCE_OPERATIONS = frozenset({
  "delete",
  "drop",
  "insert",
  "query",
  "register",
  "update",
  "upsert",
})


def _safe_count(value) -> str:
  ##
  ## ``bool`` is an ``int`` in Python, and ``rows=True`` would render as 1 - a
  ## count nobody produced. Counts are also never negative except for the
  ## driver's "unknown" -1, which is reported as unknown rather than as a
  ## number.
  ##
  if type(value) is not int or value < 0:
    return UNKNOWN
  return str(value)


def _safe_flag(value) -> str:
  return "true" if value is True else "false" if value is False else UNKNOWN


def persistence_diagnostic(
  event: str,
  *,
  table=None,
  operation=None,
  identity=None,
  related_identity=None,
  rows=None,
  columns=None,
  changed=None,
  duplicate=None,
  found=None,
  error=None,
) -> str:
  """Build one closed-field diagnostic message for a persistence operation.

  Deliberately has no mapping or ``**kwargs`` escape hatch, and no field that
  renders arbitrary text. A record dict, a parameter tuple, a WHERE mapping, a
  share url or an exception message has no parameter to arrive through.

  ``identity`` and ``related_identity`` are for opaque platform identifiers -
  an owner id, a room id, an aweme id, a person id - and are rendered through
  the same strict identifier check the live diagnostics use. Anything that is
  not one, including every url and every free-text nickname or directory name,
  renders as ``unknown`` rather than as itself.
  """
  if event not in _PERSISTENCE_EVENTS:
    raise ValueError("unsupported persistence diagnostic event")

  fields = ["event={}".format(event)]
  if table is not None:
    fields.append("table={}".format(_safe_identifier(table)))
  if operation is not None:
    safe_operation = (
      operation if operation in _PERSISTENCE_OPERATIONS else UNKNOWN
    )
    fields.append("operation={}".format(safe_operation))
  if identity is not None:
    fields.append("identity={}".format(_safe_identifier(identity)))
  if related_identity is not None:
    fields.append("related_identity={}".format(_safe_identifier(related_identity)))
  if rows is not None:
    fields.append("rows={}".format(_safe_count(rows)))
  if columns is not None:
    fields.append("columns={}".format(_safe_count(columns)))
  if changed is not None:
    fields.append("changed={}".format(_safe_flag(changed)))
  if duplicate is not None:
    fields.append("duplicate={}".format(_safe_flag(duplicate)))
  if found is not None:
    fields.append("found={}".format(_safe_flag(found)))
  if error is not None:
    fields.append("error={}".format(_error_class(error)))
  return "persistence diagnostic " + " ".join(fields)
