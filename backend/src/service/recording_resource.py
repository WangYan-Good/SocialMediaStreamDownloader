from dataclasses import dataclass
from datetime import datetime
from threading import Lock
from typing import Optional

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


##
## Everything the database is told about one recording, already canonical.
##
## Lifted out of ``record`` so that the ordinary path and a future recovery
## replay cannot drift apart.  A replay reads a journal, not a
## ``LiveDownloadResult``; without this it would have to either fabricate a
## result object to reach ``record``, or carry a second copy of the validation
## and normalisation rules.  Both eventually disagree with the original.
##
## Frozen because it is handed to a journal writer and then to the database.
## If it could be adjusted in between, "what was journalled" and "what was
## stored" would become two different questions.
##
## ``recovery_key`` is deliberately absent: this describes the recording, and
## the key describes an attempt to persist it.  The same recording replayed
## under a different key is still this intent.
##
@dataclass(frozen=True)
class RecordingPersistenceIntent:
  app_user_id: Optional[int]
  platform: str
  room_id: Optional[str]
  owner_user_id: Optional[str]
  title: Optional[str]
  protocol: Optional[str]
  output_path: str
  started_at: Optional[datetime]
  finished_at: Optional[datetime]
  source: str

  def as_record(self) -> dict:
    """The row the repository writes, in its own vocabulary."""
    return {
      "app_user_id": self.app_user_id,
      "platform": self.platform,
      "room_id": self.room_id,
      "owner_user_id": self.owner_user_id,
      "title": self.title,
      "protocol": self.protocol,
      "output_path": self.output_path,
      "started_at": self.started_at,
      "finished_at": self.finished_at,
      "source": self.source,
    }


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

  ##
  ## Turn a finished recording into the exact facts the database will store.
  ##
  ## Every rule about what may be persisted lives here: whether the result
  ## proves media exists, what an owner id may be, how optional text is
  ## normalised, and which fields are carried at all.  ``record`` and any
  ## future replay both go through it, so neither can quietly canonicalise
  ## differently.
  ##
  def prepare(
    self,
    result,
    *,
    app_user_id=None,
    platform: str,
    source: str,
  ) -> RecordingPersistenceIntent:
    """Validate a completed recording; never copy stream access credentials."""
    if result is None or result.recorded is not True:
      raise RecordingNotPersistable("result did not record media")
    if result.test_mode is True:
      raise RecordingNotPersistable("test mode produced no media resource")
    if not isinstance(result.output_path, str) or not result.output_path.strip():
      raise RecordingNotPersistable("recorded result has no output path")
    if app_user_id is not None and (
      type(app_user_id) is not int or app_user_id < 1
    ):
      raise ValueError("app_user_id must be a positive integer or None")
    if not isinstance(platform, str) or not platform.strip():
      raise ValueError("platform is required")
    if not isinstance(source, str) or not source.strip():
      raise ValueError("source is required")

    return RecordingPersistenceIntent(
      app_user_id=app_user_id,
      platform=platform.strip(),
      room_id=_optional_text(result.room_id),
      owner_user_id=_optional_text(result.owner_user_id),
      title=_optional_text(getattr(result, "title", None)),
      protocol=_optional_text(result.protocol),
      ##
      ## Verbatim.  The recorder wrote this exact name - live files are renamed
      ## on collision - so normalising it would name a file nobody created.
      ##
      output_path=result.output_path,
      started_at=getattr(result, "started_at", None),
      finished_at=getattr(result, "finished_at", None),
      source=source.strip(),
    )

  ##
  ## The only thing that writes.  Given an intent, it is not this method's
  ## business where the intent came from - a live result or a replayed journal
  ## reach the same row.
  ##
  def record_prepared(
    self,
    intent: RecordingPersistenceIntent,
    *,
    recovery_key=None,
  ) -> int:
    return self._repository().create_recording(
      intent.as_record(),
      recovery_key=recovery_key,
    )

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

    Kept as the single-call convenience every existing caller already uses.
    It is now exactly ``prepare`` followed by ``record_prepared``, so there is
    no second path into the table.
    """
    intent = self.prepare(
      result,
      app_user_id=app_user_id,
      platform=platform,
      source=source,
    )
    return self.record_prepared(intent, recovery_key=recovery_key)


__all__ = [
  "RecordingNotPersistable",
  "RecordingPersistenceIntent",
  "RecordingPersistenceUnavailable",
  "RecordingResourceService",
]
