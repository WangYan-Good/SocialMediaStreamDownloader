from threading import Lock

from backend.src.database.schema_guard import require_database_write_ready
from backend.src.database.table.recording_record import RecordingRecordTable
from backend.src.library.baselib import get_dict_attr
from backend.src.library.configlib import load_config


class RecordingNotPersistable(ValueError):
  """The download result does not prove that a media resource exists."""


class RecordingPersistenceUnavailable(RuntimeError):
  """The configured recording repository cannot be reached right now."""


def _optional_text(value):
  if value is None:
    return None
  if not isinstance(value, str):
    return str(value)
  text = value.strip()
  return text or None


class RecordingResourceService:
  """Validate a completed recording and lazily persist its resource facts."""

  def __init__(
    self,
    repository_provider=None,
    config_loader=load_config,
    database_factory=RecordingRecordTable,
  ) -> None:
    self._repository_provider = repository_provider
    self._config_loader = config_loader
    self._database_factory = database_factory
    self._lock = Lock()
    self._config = None
    self._repository_value = None

  def _repository(self):
    if self._repository_provider is not None:
      repository = self._repository_provider()
      if repository is None:
        raise RecordingPersistenceUnavailable(
          "recording repository is unavailable"
        )
      return repository

    with self._lock:
      if self._repository_value is not None:
        return self._repository_value
      if self._config is None:
        self._config = self._config_loader()
      settings = self._config
      if get_dict_attr(settings, "$.database.enable") is not True:
        raise RecordingPersistenceUnavailable(
          "recording persistence requires the database"
        )
      try:
        require_database_write_ready()
        self._repository_value = self._database_factory(
          host=get_dict_attr(settings, "$.database.host"),
          user=get_dict_attr(settings, "$.database.username"),
          passwd=get_dict_attr(settings, "$.database.password"),
          database=get_dict_attr(settings, "$.database.name"),
        )
      except Exception as e:
        raise RecordingPersistenceUnavailable(
          "recording repository is unavailable"
        ) from e
      return self._repository_value

  def record(
    self,
    result,
    *,
    app_user_id=None,
    platform: str,
    source: str,
    recovery_key=None,
  ) -> int:
    """Persist a real media result; never copy stream access credentials.

    ``recovery_key`` is optional and absent from every caller today: an
    ordinary recording is one execution and one resource, and passing nothing
    keeps exactly that behaviour. A future recovery replay supplies the key it
    journalled, which turns this into create-or-get so the same finished
    recording cannot be stored twice.

    Deliberately a parameter rather than a field on the result. The result
    describes what was captured; the recovery key describes an attempt to
    persist it, and folding the two together would put a persistence concern
    into the recording pipeline.
    """
    if result is None or result.recorded is not True:
      raise RecordingNotPersistable("result did not record media")
    if result.test_mode is True:
      raise RecordingNotPersistable("test mode produced no media resource")
    if not isinstance(result.output_path, str) or not result.output_path.strip():
      raise RecordingNotPersistable("recorded result has no output path")
    output_path = result.output_path
    if app_user_id is not None and (
      type(app_user_id) is not int or app_user_id < 1
    ):
      raise ValueError("app_user_id must be a positive integer or None")
    if not isinstance(platform, str) or not platform.strip():
      raise ValueError("platform is required")
    if not isinstance(source, str) or not source.strip():
      raise ValueError("source is required")

    record = {
      "app_user_id": app_user_id,
      "platform": platform.strip(),
      "room_id": _optional_text(result.room_id),
      "owner_user_id": _optional_text(result.owner_user_id),
      "title": _optional_text(getattr(result, "title", None)),
      "protocol": _optional_text(result.protocol),
      "output_path": output_path,
      "started_at": getattr(result, "started_at", None),
      "finished_at": getattr(result, "finished_at", None),
      "source": source.strip(),
    }
    return self._repository().create_recording(
      record,
      recovery_key=recovery_key,
    )


__all__ = [
  "RecordingNotPersistable",
  "RecordingPersistenceUnavailable",
  "RecordingResourceService",
]
