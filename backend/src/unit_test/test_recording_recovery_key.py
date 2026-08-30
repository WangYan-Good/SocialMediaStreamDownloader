##
## The identity that lets a recovery replay be idempotent.
##
## A future recovery journal will re-present the same finished recording after a
## crash: the journal is durable, the database insert may already have
## succeeded, and the process can die before the journal is acknowledged.  On
## restart the same entry is replayed.  Without a stable identity that the
## database itself enforces, that replay inserts a second row and one broadcast
## becomes two library resources.
##
## This is the identity, and nothing more.  It is not a token, not an API id,
## and not part of any digest a browser can see.  Phase 11B builds the journal
## that will generate these keys; production recordings still pass ``None``.
##
from pathlib import Path
import unittest

from backend.src.database.table.recording_record import (
  RecordingRecoveryConflict,
  canonical_recovery_key,
)

MIGRATION = (
  Path(__file__).resolve().parents[1]
  / "database"
  / "migration"
  / "versions"
  / "0011_recording_recovery_key.py"
)


class RecoveryKeyMigrationShapeTest(unittest.TestCase):
  """What the migration declares, read from its source.

  A real MySQL roundtrip proves it runs; this proves it says what it should
  before anybody runs it, including the parts a passing upgrade would not
  reveal - that nothing is backfilled, and that the column is nullable.
  """

  def setUp(self):
    self.source = MIGRATION.read_text(encoding="utf-8")

  def test_the_migration_exists(self):
    self.assertTrue(MIGRATION.is_file())

  def test_it_follows_the_current_head(self):
    self.assertIn('revision: str = "0011_recording_recovery_key"', self.source)
    self.assertIn(
      'down_revision: Union[str, None] = "0010_rbac_role_foundation"',
      self.source,
    )

  def test_it_adds_a_nullable_recovery_key(self):
    self.assertIn("recovery_key", self.source)
    self.assertIn("nullable=True", self.source)

  def test_it_adds_a_named_unique_constraint(self):
    self.assertIn("uq_recording_record_recovery_key", self.source)
    self.assertIn("unique=True", self.source)

  def test_it_does_not_backfill_historical_rows(self):
    ##
    ## Nothing on disk or in an existing row can establish a trustworthy
    ## recovery identity after the fact.  A synthesised one would be a
    ## fabricated fact that later replays could collide with.
    ##
    ## Asserted against the executable statements rather than the whole file:
    ## the prose above them is allowed to say "insert", the code is not.
    ##
    code = "\n".join(
      line for line in self.source.splitlines()
      if line.strip() and not line.strip().startswith("#")
    )
    body = code[code.index("def upgrade"):]
    for forbidden in ("op.execute", "op.bulk_insert", "UPDATE ", "INSERT "):
      self.assertNotIn(forbidden, body)

  def test_the_downgrade_removes_both_the_constraint_and_the_column(self):
    downgrade = self.source[self.source.index("def downgrade"):]
    ##
    ## Both halves: dropping the column alone would leave the index behind on
    ## some engines, and dropping the index alone would leave a column that a
    ## re-upgrade could not re-constrain.
    ##
    self.assertIn("drop_index", downgrade)
    self.assertIn("drop_column", downgrade)
    self.assertIn("RECOVERY_KEY_INDEX", downgrade)
    self.assertIn("recovery_key", downgrade)


class CanonicalRecoveryKeyTest(unittest.TestCase):
  """Exactly 32 lowercase hex characters, or nothing.

  Deliberately not forgiving.  A recovery key is compared against a database
  unique constraint, so ``ABC...`` and ``abc...`` being accepted as the same
  request but stored as different bytes would defeat the constraint that the
  whole design rests on.  Normalising here instead would hide a caller that is
  generating keys the wrong way.
  """

  def test_none_is_the_absence_of_a_recovery_identity(self):
    self.assertIsNone(canonical_recovery_key(None))

  def test_a_canonical_key_is_returned_unchanged(self):
    key = "0123456789abcdef0123456789abcdef"
    self.assertEqual(key, canonical_recovery_key(key))

  def test_every_lowercase_hex_digit_is_accepted(self):
    self.assertEqual("abcdef" * 5 + "ab", canonical_recovery_key("abcdef" * 5 + "ab"))
    self.assertEqual("0" * 32, canonical_recovery_key("0" * 32))
    self.assertEqual("f" * 32, canonical_recovery_key("f" * 32))

  def test_uppercase_is_refused_rather_than_lowered(self):
    with self.assertRaises(ValueError):
      canonical_recovery_key("0123456789ABCDEF0123456789abcdef")

  def test_whitespace_is_refused_rather_than_stripped(self):
    for value in (
      " 0123456789abcdef0123456789abcdef",
      "0123456789abcdef0123456789abcdef ",
      "0123456789abcdef0123456789abcde\n",
    ):
      with self.subTest(value=value):
        with self.assertRaises(ValueError):
          canonical_recovery_key(value)

  def test_the_wrong_length_is_refused(self):
    for value in ("", "0" * 31, "0" * 33, "0" * 64):
      with self.subTest(value=value):
        with self.assertRaises(ValueError):
          canonical_recovery_key(value)

  def test_non_hex_characters_are_refused(self):
    for value in ("g" * 32, "0123456789abcdef0123456789abcde-", "z" * 32):
      with self.subTest(value=value):
        with self.assertRaises(ValueError):
          canonical_recovery_key(value)

  def test_things_that_are_not_strings_are_refused(self):
    ##
    ## ``True`` is worth naming: it is an int, and an int that reaches a hex
    ## comparison silently would be a key nobody can reproduce.
    ##
    import uuid

    for value in (
      True,
      False,
      0,
      1,
      b"0123456789abcdef0123456789abcdef",
      uuid.UUID("01234567-89ab-cdef-0123-456789abcdef"),
      ["0" * 32],
    ):
      with self.subTest(value=repr(value)):
        with self.assertRaises((ValueError, TypeError)):
          canonical_recovery_key(value)

  def test_a_uuid_hex_string_is_the_intended_shape(self):
    ##
    ## ``uuid4().hex`` is 32 lowercase hex characters, which is what Phase 11B
    ## will produce.  Its dashed form is not.
    ##
    import uuid

    self.assertEqual(32, len(uuid.uuid4().hex))
    canonical_recovery_key(uuid.uuid4().hex)
    with self.assertRaises(ValueError):
      canonical_recovery_key(str(uuid.uuid4()))


class RecoveryConflictTypeTest(unittest.TestCase):
  def test_a_recovery_conflict_is_not_silently_a_success(self):
    ##
    ## One recovery identity must name one media resource. Being handed the
    ## same key for a different recording is a bug in the caller or a corrupted
    ## journal, and returning the existing id would quietly attach a new
    ## recording's identity to old bytes.
    ##
    self.assertTrue(issubclass(RecordingRecoveryConflict, Exception))


class RecoveryKeyIsNotExposedTest(unittest.TestCase):
  """The recovery key never reaches a browser.

  It is a persistence identity, not a capability: knowing it grants nothing,
  and it has no meaning to a user.  Something with no reason to be in a
  response is something that should not be in one - every field a page can see
  is a field that has to stay correct forever.
  """

  def test_the_library_recording_query_does_not_select_it(self):
    ##
    ## Recovery lookups live in the repository. If the ordinary listing started
    ## carrying the column it would end up in serialisation by accident.
    ##
    source = (
      Path(__file__).resolve().parents[1]
      / "database" / "query" / "library.py"
    ).read_text(encoding="utf-8")
    self.assertNotIn("recovery_key", source)

  def test_the_media_asset_layer_does_not_know_about_it(self):
    for module in ("media_asset.py", "media_range.py"):
      source = (
        Path(__file__).resolve().parents[1] / "service" / module
      ).read_text(encoding="utf-8")
      with self.subTest(module=module):
        self.assertNotIn("recovery_key", source)

  def test_no_web_route_mentions_it(self):
    web = Path(__file__).resolve().parents[1] / "web"
    for module in sorted(web.glob("*.py")):
      with self.subTest(module=module.name):
        self.assertNotIn(
          "recovery_key", module.read_text(encoding="utf-8")
        )

  def test_the_recording_task_generates_a_key_but_never_publishes_it(self):
    ##
    ## Superseded on purpose. Phase 11B-0 asserted the opposite - that
    ## production generated no key at all - because the primitive existed with
    ## nothing to use it. Phase 11B wired the journal in, so the persistence
    ## boundary now mints exactly one key per recording.
    ##
    ## What survives from that original assertion is the half that still
    ## matters: the key is a persistence identity, so it must never reach the
    ## metadata a browser reads. That is asserted against the serialiser rather
    ## than the whole module, since the module is now entitled to mention it.
    ##
    source = (
      Path(__file__).resolve().parents[1]
      / "service" / "live_recording_task.py"
    ).read_text(encoding="utf-8")
    self.assertIn("recovery_key", source)

    metadata = source[source.index("def _result_metadata"):]
    metadata = metadata[:metadata.index("\n  def ")]
    self.assertNotIn("recovery", metadata)
    self.assertNotIn("journal", metadata)


class AssetIdentityUnaffectedTest(unittest.TestCase):
  """Phase 10A asset ids are unchanged by the existence of a recovery key."""

  def test_recording_asset_ids_keep_their_golden_digests(self):
    ##
    ## Golden values, not recomputed expectations: an id that changed would
    ## silently invalidate every download and preview URL a browser is holding.
    ##
    from backend.src.service.media_asset import asset_id_for

    ##
    ## Literal digests captured from the code as it stands. Recomputing the
    ## expectation with the same function would agree with any change,
    ## including one that silently invalidated every download and preview URL a
    ## browser is currently holding.
    ##
    self.assertEqual(
      "1d65260b7f1c0d9afc3280156e424c529d33e5d5c284874eeff3625880abe3c2",
      asset_id_for("recording", (7,), "live.mp4"),
    )
    self.assertEqual(
      "efb8931269b5fd931f9b5275896d1359dbe661643d10866b573fe14bc2d2acb3",
      asset_id_for("recording", (7,), "live.ts"),
    )
    self.assertEqual(
      "2316dba3fcc53a9bfcc3c29ba86780cd11b01c840b1d5db936d5aa982d3fae9f",
      asset_id_for("recording", (8,), "live.mp4"),
    )

  def test_the_asset_id_material_has_not_gained_a_field(self):
    source = (
      Path(__file__).resolve().parents[1] / "service" / "media_asset.py"
    ).read_text(encoding="utf-8")
    body = source[source.index("def asset_id_for"):]
    body = body[:body.index("\ndef ")]
    self.assertIn("resource_kind", body)
    self.assertIn("file_name", body)
    self.assertNotIn("recovery", body)


if __name__ == "__main__":
  unittest.main()
