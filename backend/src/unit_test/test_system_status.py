import unittest

from backend.src.database.schema_guard import GuardSnapshot, SchemaState
from backend.src.service.system_status import (
  DATABASE_STATE_MESSAGES,
  build_safe_config_snapshot,
  describe_database,
)


##
## The security boundary of the whole system page lives in this module.
##
## The configuration it is handed contains database credentials, cookies,
## tokens, proxies and absolute paths. The snapshot is built by naming every
## field that may leave the process, starting from an empty dictionary - never
## by copying the configuration and removing what looks secret, because that
## approach fails silently the first time somebody adds a field.
##


SECRETS = {
  "database": {
    "enable": True,
    "name": "SECRET_DB_NAME",
    "host": "SECRET_DB_HOST",
    "port": 33061,
    "username": "SECRET_DB_USER",
    "password": "SECRET_DB_PASSWORD",
  },
  "migrate": {
    "source_db_name": "SECRET_MIGRATE_NAME",
    "source_db_host": "SECRET_MIGRATE_HOST",
    "source_db_port": 33062,
    "source_db_username": "SECRET_MIGRATE_USER",
    "source_db_password": "SECRET_MIGRATE_PASSWORD",
  },
  "server": {
    "host": "SECRET_BIND_HOST",
    "port": 5000,
    "debug_mode": False,
  },
  "log": {
    "log_enable": True,
    "log_level": "INFO",
    "log_save": True,
    "log_file_path": "SECRET_LOG_PATH",
  },
  "download": {
    "save_path": "SECRET_SAVE_PATH",
    "folderize": True,
    "test_mode": False,
    "listening": False,
    "user_login": False,
    "max_threads": 4,
    "max_retry": 3,
    "save_response": False,
    "save_error_response": False,
    "tick_naming": True,
  },
  "history": {"page_size_limit": 10},
  "platform": {
    "douyin": {
      "api": {"DOUYIN_DOMAIN": "SECRET_API_DOMAIN"},
      "headers": {
        "post_info": {"Cookie": "SECRET_COOKIE", "User-Agent": "SECRET_UA"},
      },
      "login": {
        "msToken": "SECRET_TOKEN",
        "proxies": {"http": "SECRET_PROXY"},
      },
      "post": {
        "webid": "SECRET_WEBID",
        "verifyFp": "SECRET_FP",
        "a_bogus": "SECRET_BOGUS",
        "sec_uid": "SECRET_SEC_UID",
        "device_id": "SECRET_DEVICE",
      },
      "aweme": {
        "max_timeout": 30,
        "concurrency": 3,
        "html_fallback": True,
        "skip_downloaded": True,
        "video_quality": "highest",
        "media": {"video": True, "images": True, "music": True, "cover": True},
      },
      "owner": {
        "max_timeout": 30,
        "page_size": 18,
        "download_concurrency": 3,
        "max_pages": 100,
        "payload_retention_seconds": 900,
        "job_retention_seconds": 900,
      },
      "live": {
        "live_api": "SECRET_LIVE_API",
        "probe": {
          "max_batch_size": 10,
          "concurrency": 3,
          "cache_ttl_seconds": 60,
          "batch_retention_seconds": 600,
        },
      },
    }
  },
  ##
  ## Something nobody has written a rule about yet. A snapshot built by naming
  ## what is allowed omits this for free; one built by removing known secrets
  ## would carry it straight through.
  ##
  "future_feature": {"future_secret": "ULTRA_SECRET"},
}


def flatten(value):
  """Every string anywhere inside the snapshot."""
  found = []
  if isinstance(value, dict):
    for key, item in value.items():
      found.append(str(key))
      found.extend(flatten(item))
  elif isinstance(value, (list, tuple)):
    for item in value:
      found.extend(flatten(item))
  else:
    found.append(str(value))
  return found


class SafeConfigSnapshotTest(unittest.TestCase):
  def test_no_secret_of_any_kind_survives(self):
    snapshot = build_safe_config_snapshot(SECRETS)

    for text in flatten(snapshot):
      self.assertNotIn("SECRET", text, "a secret reached the snapshot: {}".format(text))

  def test_a_field_nobody_wrote_a_rule_about_is_omitted(self):
    ##
    ## The difference between a whitelist and a blacklist, stated as a test.
    ##
    snapshot = build_safe_config_snapshot(SECRETS)

    self.assertNotIn("future_feature", snapshot)
    self.assertNotIn("ULTRA_SECRET", flatten(snapshot))

  def test_the_server_section_carries_only_the_debug_flag(self):
    snapshot = build_safe_config_snapshot(SECRETS)

    self.assertEqual({"debug_mode"}, set(snapshot["server"]))

  def test_the_database_credentials_never_appear(self):
    snapshot = build_safe_config_snapshot(SECRETS)
    text = flatten(snapshot)

    for forbidden in ("host", "port", "username", "password", "name"):
      self.assertNotIn(forbidden, text)

  def test_the_logging_summary_says_nothing_about_where_logs_live(self):
    snapshot = build_safe_config_snapshot(SECRETS)

    self.assertEqual({"enabled", "level", "save_enabled"}, set(snapshot["logging"]))
    self.assertNotIn("log_file_path", flatten(snapshot))

  def test_the_download_summary_omits_the_save_path(self):
    snapshot = build_safe_config_snapshot(SECRETS)

    self.assertEqual(
      {"test_mode", "folderize", "listening", "user_login"},
      set(snapshot["download"]),
    )

  def test_it_reports_the_values_that_are_allowed(self):
    snapshot = build_safe_config_snapshot(SECRETS)

    self.assertIs(False, snapshot["server"]["debug_mode"])
    self.assertEqual("INFO", snapshot["logging"]["level"])
    self.assertIs(True, snapshot["logging"]["save_enabled"])
    self.assertIs(False, snapshot["download"]["test_mode"])
    self.assertEqual(10, snapshot["history"]["page_size_limit"])
    self.assertEqual(3, snapshot["douyin"]["aweme"]["concurrency"])
    self.assertEqual("highest", snapshot["douyin"]["aweme"]["video_quality"])
    self.assertEqual(
      {"video": True, "images": True, "music": True, "cover": True},
      snapshot["douyin"]["aweme"]["media"],
    )
    self.assertEqual(18, snapshot["douyin"]["owner"]["page_size"])
    self.assertEqual(10, snapshot["douyin"]["live_probe"]["max_batch_size"])
    self.assertEqual(60, snapshot["douyin"]["live_probe"]["cache_ttl_seconds"])

  def test_the_shape_is_exactly_what_was_designed(self):
    ##
    ## Asserted as a whole, so a section added upstream cannot arrive here by
    ## accident - it has to be added to this test first.
    ##
    snapshot = build_safe_config_snapshot(SECRETS)

    self.assertEqual(
      {"server", "logging", "download", "history", "douyin"}, set(snapshot)
    )
    self.assertEqual({"aweme", "owner", "live_probe"}, set(snapshot["douyin"]))

  def test_a_missing_section_becomes_null_rather_than_an_error(self):
    ##
    ## The status page has to work on a partially configured server; that is
    ## precisely when somebody looks at it.
    ##
    snapshot = build_safe_config_snapshot({})

    self.assertIsNone(snapshot["server"]["debug_mode"])
    self.assertIsNone(snapshot["logging"]["level"])
    self.assertIsNone(snapshot["douyin"]["aweme"]["media"]["video"])

  def test_the_snapshot_does_not_track_later_edits_to_the_configuration(self):
    ##
    ## Copied, not referenced. A live reference would let anything that mutates
    ## the configuration mutate what the api reports.
    ##
    source = {"server": {"debug_mode": False}, "log": {"log_level": "INFO"}}
    snapshot = build_safe_config_snapshot(source)

    source["server"]["debug_mode"] = True
    source["log"]["log_level"] = "DEBUG"

    self.assertIs(False, snapshot["server"]["debug_mode"])
    self.assertEqual("INFO", snapshot["logging"]["level"])

  def test_nested_values_are_copied_too(self):
    media = {"video": True, "images": True, "music": True, "cover": True}
    source = {"platform": {"douyin": {"aweme": {"media": media}}}}
    snapshot = build_safe_config_snapshot(source)

    media["video"] = False

    self.assertIs(True, snapshot["douyin"]["aweme"]["media"]["video"])


class DatabaseDescriptionTest(unittest.TestCase):
  def test_each_state_gets_its_own_public_sentence(self):
    for state in SchemaState:
      self.assertIn(state.value, DATABASE_STATE_MESSAGES)

  def test_a_ready_schema_is_write_ready(self):
    described = describe_database(
      enabled=True,
      snapshot=GuardSnapshot(state=SchemaState.READY, reason="ok", checked_at=1.0),
    )

    self.assertEqual("ready", described["state"])
    self.assertIs(True, described["write_ready"])
    self.assertIs(True, described["enabled"])

  def test_every_other_state_is_not_write_ready(self):
    for state in (SchemaState.UNAVAILABLE, SchemaState.BLOCKED, SchemaState.DISABLED):
      described = describe_database(
        enabled=True,
        snapshot=GuardSnapshot(state=state, reason="whatever", checked_at=1.0),
      )
      self.assertIs(False, described["write_ready"], state)

  def test_the_guards_own_reason_never_reaches_the_client(self):
    ##
    ## The reason is an internal sentence that may name a host or a revision.
    ## The api answers with a fixed message per state instead, so the guard's
    ## wording stays free to change without becoming a public contract.
    ##
    described = describe_database(
      enabled=True,
      snapshot=GuardSnapshot(
        state=SchemaState.UNAVAILABLE,
        reason="SECRET_DB_HOST=10.0.0.4 refused the connection",
        checked_at=1.0,
      ),
    )

    self.assertEqual("unavailable", described["state"])
    self.assertEqual(DATABASE_STATE_MESSAGES["unavailable"], described["message"])
    self.assertNotIn("SECRET_DB_HOST", str(described))
    self.assertNotIn("10.0.0.4", str(described))

  def test_the_monotonic_check_time_is_never_reported(self):
    ##
    ## checked_at is a monotonic clock reading. It means nothing to a browser,
    ## and showing it as a timestamp would be showing a wrong one.
    ##
    described = describe_database(
      enabled=True,
      snapshot=GuardSnapshot(state=SchemaState.READY, reason="ok", checked_at=98765.4),
    )

    self.assertNotIn("checked_at", described)
    self.assertNotIn("98765", str(described))

  def test_no_guard_at_all_is_unknown_rather_than_a_guess(self):
    described = describe_database(enabled=True, snapshot=None)

    self.assertEqual("unknown", described["state"])
    self.assertIs(False, described["write_ready"])
    self.assertEqual(DATABASE_STATE_MESSAGES["unknown"], described["message"])

  def test_a_disabled_database_is_reported_as_disabled(self):
    described = describe_database(
      enabled=False,
      snapshot=GuardSnapshot(state=SchemaState.DISABLED, reason="off", checked_at=1.0),
    )

    self.assertIs(False, described["enabled"])
    self.assertEqual("disabled", described["state"])

  def test_the_described_shape_is_exactly_four_fields(self):
    described = describe_database(
      enabled=True,
      snapshot=GuardSnapshot(state=SchemaState.READY, reason="ok", checked_at=1.0),
    )

    self.assertEqual({"enabled", "state", "write_ready", "message"}, set(described))

  def test_no_migration_revision_is_reported(self):
    described = describe_database(
      enabled=True,
      snapshot=GuardSnapshot(state=SchemaState.READY, reason="ok", checked_at=1.0),
    )
    text = str(described)

    for forbidden in ("revision", "head", "alembic"):
      self.assertNotIn(forbidden, text)
