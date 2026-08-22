##<<Base>>
import os
import unittest
import uuid

##<<Extension>>
import sqlalchemy as sa
from alembic import command
from sqlalchemy.exc import IntegrityError

##<<Third-part>>
from backend.src.database.migration import make_alembic_config
from backend.src.unit_test import no_network


##
## >>============================= why a real database =============================>>
##
##
## Everything in this file is MySQL-specific DDL.
##
## The constraint is a generated column plus a plain UNIQUE, because MySQL has
## no partial index - and "MySQL permits many NULLs in a unique index" is the
## entire mechanism.  A fake cursor cannot disagree with that, and SQLite would
## agree with it for different reasons and different syntax, so neither is
## evidence.  Only a real MySQL 8 can say whether this works.
##
## Skipped rather than failed when no database is reachable, so the ordinary
## unit run stays offline and fast; the skip is loud enough to notice in the
## summary, and the accompanying source-level tests in test_alembic_environment
## still hold the migration's shape either way.
##

DSN = os.environ.get("SMSD_TEST_MYSQL_DSN")

##
## Whether a caller has declared that these tests *must* run.
##
## Skipping is the right default: nobody should have to install MySQL to run
## the unit suite, and the constraint's shape is held by source-level tests
## either way.  But a skip that is invisible is a proof that quietly stopped
## happening, and this whole file exists because the behaviour it checks cannot
## be checked any other way.
##
## So CI sets this, and with it set a missing or unusable database is a failure
## rather than a silent pass.  Without it, nothing changes for anybody local.
##
REQUIRED = os.environ.get("SMSD_REQUIRE_MYSQL_TESTS") == "1"

if REQUIRED and not DSN:
  ##
  ## Raised during collection, on purpose: pytest reports it and exits non-zero.
  ## Answering with 21 skips and a green job is the one outcome this flag exists
  ## to prevent, and it is exactly what a mis-edited workflow would produce.
  ##
  raise RuntimeError(
    "SMSD_REQUIRE_MYSQL_TESTS=1 but SMSD_TEST_MYSQL_DSN is not set. "
    "These tests prove MySQL-specific DDL - a generated column, a unique index "
    "over it, and MySQL's many-NULLs rule - and nothing else in the suite can "
    "stand in for them. Either point SMSD_TEST_MYSQL_DSN at a MySQL 8 server "
    "or drop SMSD_REQUIRE_MYSQL_TESTS."
  )

MAIN_UNIQUE = "uq_person_account_main_person"

##
## Short, so an unreachable server fails the job in seconds rather than holding
## a runner until it times out.  Only ever used against a test database.
##
CONNECT_ARGS = {"connect_timeout": 5}


class RealDatabaseAllowed:
  """Lets this file - and only this file - reach a database.

  The suite blocks every outbound connection, because the traffic worth
  catching is the traffic nobody meant to send.  A connection asked for by name
  in an opt-in file is the opposite of that, and the socket layer cannot tell
  the two apart, so it is declared here instead of inferred.

  Restored in ``tearDownClass``, which runs whatever the tests did.
  """

  @classmethod
  def setUpClass(cls):
    no_network.permit_real_connections()
    super(RealDatabaseAllowed, cls).setUpClass()

  @classmethod
  def tearDownClass(cls):
    try:
      super(RealDatabaseAllowed, cls).tearDownClass()
    finally:
      no_network.restore_block()


def _config_for(database_name: str) -> dict:
  url = sa.engine.make_url(DSN)
  return {
    "database": {
      "host": url.host,
      "port": url.port or 3306,
      "username": url.username,
      "password": url.password,
      "name": database_name,
    }
  }


@unittest.skipUnless(DSN, "set SMSD_TEST_MYSQL_DSN to run the MySQL constraint tests")
class PersonMainConstraintTest(RealDatabaseAllowed, unittest.TestCase):
  """The database's own refusal to hold two main accounts for one person."""

  @classmethod
  def setUpClass(cls):
    ##
    ## Chained, so the mixin gets to lift the network block before anything here
    ## tries to open a connection.
    ##
    super().setUpClass()
    cls.database_name = "smsd_test_{}".format(uuid.uuid4().hex[:12])
    cls.server = sa.create_engine(DSN, future=True, connect_args=CONNECT_ARGS)
    with cls.server.connect() as connection:
      connection.execute(
        sa.text(
          "CREATE DATABASE `{}` CHARACTER SET utf8mb4 "
          "COLLATE utf8mb4_0900_ai_ci".format(cls.database_name)
        )
      )
      connection.commit()
    cls.engine = sa.create_engine(
      "{}/{}".format(DSN.rstrip("/"), cls.database_name),
      future=True,
      connect_args=CONNECT_ARGS,
    )

  @classmethod
  def tearDownClass(cls):
    try:
      cls.engine.dispose()
      with cls.server.connect() as connection:
        connection.execute(
          sa.text("DROP DATABASE IF EXISTS `{}`".format(cls.database_name))
        )
        connection.commit()
      cls.server.dispose()
    finally:
      ##
      ## The block goes back on however the teardown went.
      ##
      super().tearDownClass()

  ##
  ## >>--------------------------- helpers ---------------------------<<
  ##
  def upgrade(self, revision: str = "head", engine=None, database_name=None):
    engine = engine if engine is not None else self.engine
    name = database_name if database_name is not None else self.database_name
    config = make_alembic_config(_config_for(name), name)
    config.attributes["engine"] = engine
    command.upgrade(config, revision)

  def downgrade(self, revision: str):
    config = make_alembic_config(_config_for(self.database_name), self.database_name)
    config.attributes["engine"] = self.engine
    command.downgrade(config, revision)

  def setUp(self):
    self.upgrade()
    with self.engine.connect() as connection:
      connection.execute(sa.text("DELETE FROM person_account"))
      connection.execute(sa.text("DELETE FROM person"))
      connection.commit()

  def person(self, person_id: int, name: str = "某人") -> int:
    with self.engine.connect() as connection:
      connection.execute(
        sa.text("INSERT INTO person (person_id, display_name) VALUES (:i, :n)"),
        {"i": person_id, "n": name},
      )
      connection.commit()
    return person_id

  def attach(self, owner_user_id: str, person_id: int, role: str):
    """Straight SQL, deliberately.

    The point of these tests is what happens to a write that never went near
    the service - a repair script, a console, a future code path that forgets.
    """
    with self.engine.connect() as connection:
      connection.execute(
        sa.text(
          "INSERT INTO person_account (platform, owner_user_id, person_id, role) "
          "VALUES ('douyin', :o, :p, :r)"
        ),
        {"o": owner_user_id, "p": person_id, "r": role},
      )
      connection.commit()

  def set_role(self, owner_user_id: str, role: str):
    with self.engine.connect() as connection:
      connection.execute(
        sa.text(
          "UPDATE person_account SET role = :r "
          "WHERE platform = 'douyin' AND owner_user_id = :o"
        ),
        {"r": role, "o": owner_user_id},
      )
      connection.commit()

  def move(self, owner_user_id: str, person_id: int, role: str):
    with self.engine.connect() as connection:
      connection.execute(
        sa.text(
          "UPDATE person_account SET person_id = :p, role = :r "
          "WHERE platform = 'douyin' AND owner_user_id = :o"
        ),
        {"p": person_id, "r": role, "o": owner_user_id},
      )
      connection.commit()

  def mains_of(self, person_id: int) -> int:
    with self.engine.connect() as connection:
      return connection.execute(
        sa.text(
          "SELECT COUNT(*) FROM person_account "
          "WHERE person_id = :p AND role = 'main'"
        ),
        {"p": person_id},
      ).scalar()

  ##
  ## >>--------------------------- the invariant ---------------------------<<
  ##
  def test_it_is_really_talking_to_mysql_8(self):
    """Otherwise every result below is about some other database.

    The major version only. ``mysql:8.0`` is a moving tag - the patch level
    changes whenever the image is rebuilt - and pinning one here would turn a
    routine base-image update into a red build for no reason.
    """
    self.assertEqual("mysql", self.engine.dialect.name)
    with self.engine.connect() as connection:
      version = connection.execute(sa.text("SELECT VERSION()")).scalar()
    self.assertTrue(
      str(version).startswith("8."),
      "these tests describe MySQL 8 behaviour, got {}".format(version),
    )

  def test_a_person_may_hold_no_main_at_all(self):
    """The first account somebody marks is often the spare - that is *why* they
    are marking it - so a person with no main is an ordinary, lasting state."""
    self.person(1)
    self.attach("acc-alt", 1, "alt")

    self.assertEqual(0, self.mains_of(1))

  def test_a_person_may_hold_one_main(self):
    self.person(1)
    self.attach("acc-main", 1, "main")

    self.assertEqual(1, self.mains_of(1))

  def test_a_second_main_is_refused_by_the_database(self):
    """The whole point of this migration.

    Nothing here goes through the service, so nothing here benefits from the
    transaction, the row lock or the conflict check. If this insert succeeds,
    the invariant is only a convention.
    """
    self.person(1)
    self.attach("acc-main", 1, "main")

    with self.assertRaises(IntegrityError) as caught:
      self.attach("acc-second", 1, "main")

    self.assertIn(MAIN_UNIQUE, str(caught.exception))
    self.assertEqual(1, self.mains_of(1))

  def test_each_person_gets_their_own_main(self):
    """The uniqueness is per person, not one main in the whole table."""
    for person_id in (1, 2, 3):
      self.person(person_id)
      self.attach("acc-main-{}".format(person_id), person_id, "main")

    self.assertEqual([1, 1, 1], [self.mains_of(i) for i in (1, 2, 3)])

  def test_a_person_may_hold_any_number_of_spares_and_matrix_accounts(self):
    """Only *main* is limited. Counting the others would be inventing a rule
    nobody asked for."""
    self.person(1)
    self.attach("acc-main", 1, "main")
    for index in range(5):
      self.attach("acc-alt-{}".format(index), 1, "alt")
      self.attach("acc-matrix-{}".format(index), 1, "matrix")

    with self.engine.connect() as connection:
      total = connection.execute(
        sa.text("SELECT COUNT(*) FROM person_account WHERE person_id = 1")
      ).scalar()
    self.assertEqual(11, total)

  ##
  ## >>--------------------------- role changes ---------------------------<<
  ##
  def test_promoting_a_spare_is_allowed_when_there_is_no_main(self):
    self.person(1)
    self.attach("acc-alt", 1, "alt")

    self.set_role("acc-alt", "main")

    self.assertEqual(1, self.mains_of(1))

  def test_promoting_a_spare_is_refused_when_a_main_already_exists(self):
    self.person(1)
    self.attach("acc-main", 1, "main")
    self.attach("acc-alt", 1, "alt")

    with self.assertRaises(IntegrityError):
      self.set_role("acc-alt", "main")

    self.assertEqual(1, self.mains_of(1))

  def test_demoting_the_main_is_always_allowed_by_the_database(self):
    """Zero mains is legal, so the database has nothing to say about it. What
    makes a careless demotion refuseable is the application's last-main rule,
    which is a different question and stays where it is."""
    self.person(1)
    self.attach("acc-main", 1, "main")

    self.set_role("acc-main", "alt")

    self.assertEqual(0, self.mains_of(1))

  def test_a_matrix_account_follows_the_same_rule(self):
    self.person(1)
    self.attach("acc-main", 1, "main")
    self.attach("acc-matrix", 1, "matrix")

    with self.assertRaises(IntegrityError):
      self.set_role("acc-matrix", "main")

  ##
  ## >>--------------------------- moves ---------------------------<<
  ##
  def test_an_account_may_move_in_as_the_main_of_a_person_who_has_none(self):
    self.person(1)
    self.person(2)
    self.attach("acc-1", 1, "alt")

    self.move("acc-1", 2, "main")

    self.assertEqual(1, self.mains_of(2))

  def test_an_account_may_not_move_in_as_a_second_main(self):
    self.person(1)
    self.person(2)
    self.attach("acc-1", 1, "alt")
    self.attach("acc-2", 2, "main")

    with self.assertRaises(IntegrityError):
      self.move("acc-1", 2, "main")

    self.assertEqual(1, self.mains_of(2))

  def test_replacing_a_main_succeeds_when_the_old_one_goes_first(self):
    """The order the assignment transaction already uses.

    UNIQUE is checked per statement, not per transaction, so promoting the new
    main before demoting the old one would collide even though the transaction
    as a whole is perfectly consistent. This is the test that would catch such
    a reordering.
    """
    self.person(1)
    self.attach("acc-old", 1, "main")
    self.attach("acc-new", 1, "alt")

    with self.engine.connect() as connection:
      connection.execute(
        sa.text(
          "UPDATE person_account SET role = 'alt' "
          "WHERE platform = 'douyin' AND owner_user_id = 'acc-old'"
        )
      )
      connection.execute(
        sa.text(
          "UPDATE person_account SET role = 'main' "
          "WHERE platform = 'douyin' AND owner_user_id = 'acc-new'"
        )
      )
      connection.commit()

    self.assertEqual(1, self.mains_of(1))
    with self.engine.connect() as connection:
      roles = dict(
        connection.execute(
          sa.text(
            "SELECT owner_user_id, role FROM person_account WHERE person_id = 1"
          )
        ).all()
      )
    self.assertEqual({"acc-old": "alt", "acc-new": "main"}, roles)

  def test_promoting_before_demoting_is_refused(self):
    """Stated as its own fact, so nobody 'simplifies' the transaction by
    swapping two statements that look independent."""
    self.person(1)
    self.attach("acc-old", 1, "main")
    self.attach("acc-new", 1, "alt")

    with self.assertRaises(IntegrityError):
      with self.engine.connect() as connection:
        connection.execute(
          sa.text(
            "UPDATE person_account SET role = 'main' "
            "WHERE platform = 'douyin' AND owner_user_id = 'acc-new'"
          )
        )
        connection.commit()

  ##
  ## >>--------------------------- deleting ---------------------------<<
  ##
  def test_removing_a_main_frees_the_slot(self):
    self.person(1)
    self.attach("acc-old", 1, "main")

    with self.engine.connect() as connection:
      connection.execute(
        sa.text("DELETE FROM person_account WHERE owner_user_id = 'acc-old'")
      )
      connection.commit()
    self.attach("acc-new", 1, "main")

    self.assertEqual(1, self.mains_of(1))


@unittest.skipUnless(DSN, "set SMSD_TEST_MYSQL_DSN to run the MySQL constraint tests")
class PersonMainConstraintMigrationTest(RealDatabaseAllowed, unittest.TestCase):
  """What the migration does to a database that already has rows in it.

  A fresh schema is the easy case. The one worth testing is an existing install:
  it may hold exactly the state the new constraint forbids, and the migration
  has no business guessing which of two mains the user meant to keep.
  """

  BEFORE = "0005_drop_person_directory"

  def setUp(self):
    self.database_name = "smsd_mig_{}".format(uuid.uuid4().hex[:12])
    self.server = sa.create_engine(DSN, future=True, connect_args=CONNECT_ARGS)
    with self.server.connect() as connection:
      connection.execute(
        sa.text(
          "CREATE DATABASE `{}` CHARACTER SET utf8mb4 "
          "COLLATE utf8mb4_0900_ai_ci".format(self.database_name)
        )
      )
      connection.commit()
    self.engine = sa.create_engine(
      "{}/{}".format(DSN.rstrip("/"), self.database_name),
      future=True,
      connect_args=CONNECT_ARGS,
    )

  def tearDown(self):
    self.engine.dispose()
    with self.server.connect() as connection:
      connection.execute(
        sa.text("DROP DATABASE IF EXISTS `{}`".format(self.database_name))
      )
      connection.commit()
    self.server.dispose()

  def run_alembic(self, direction, revision):
    config = make_alembic_config(_config_for(self.database_name), self.database_name)
    config.attributes["engine"] = self.engine
    direction(config, revision)

  def upgrade(self, revision="head"):
    self.run_alembic(command.upgrade, revision)

  def downgrade(self, revision):
    self.run_alembic(command.downgrade, revision)

  def seed(self, rows):
    with self.engine.connect() as connection:
      for person_id in sorted({person_id for person_id, _, _ in rows}):
        connection.execute(
          sa.text("INSERT INTO person (person_id, display_name) VALUES (:i, :n)"),
          {"i": person_id, "n": "人物{}".format(person_id)},
        )
      for person_id, owner_user_id, role in rows:
        connection.execute(
          sa.text(
            "INSERT INTO person_account (platform, owner_user_id, person_id, role) "
            "VALUES ('douyin', :o, :p, :r)"
          ),
          {"o": owner_user_id, "p": person_id, "r": role},
        )
      connection.commit()

  def has_constraint(self) -> bool:
    with self.engine.connect() as connection:
      return bool(
        connection.execute(
          sa.text(
            "SELECT COUNT(*) FROM information_schema.STATISTICS "
            "WHERE TABLE_SCHEMA = :s AND TABLE_NAME = 'person_account' "
            "AND INDEX_NAME = :i"
          ),
          {"s": self.database_name, "i": MAIN_UNIQUE},
        ).scalar()
      )

  def has_column(self) -> bool:
    with self.engine.connect() as connection:
      return bool(
        connection.execute(
          sa.text(
            "SELECT COUNT(*) FROM information_schema.COLUMNS "
            "WHERE TABLE_SCHEMA = :s AND TABLE_NAME = 'person_account' "
            "AND COLUMN_NAME = 'main_person_id'"
          ),
          {"s": self.database_name},
        ).scalar()
      )

  def test_it_upgrades_an_empty_database(self):
    self.upgrade()

    self.assertTrue(self.has_column())
    self.assertTrue(self.has_constraint())

  def test_it_upgrades_a_database_that_already_has_ordinary_data(self):
    self.upgrade(self.BEFORE)
    self.seed([
      (1, "a-main", "main"),
      (1, "a-alt", "alt"),
      (1, "a-matrix", "matrix"),
      (2, "b-alt", "alt"),
      (3, "c-main", "main"),
    ])

    self.upgrade()

    self.assertTrue(self.has_constraint())

  def test_it_upgrades_a_person_who_has_no_main(self):
    self.upgrade(self.BEFORE)
    self.seed([(1, "a-alt", "alt"), (1, "a-matrix", "matrix")])

    self.upgrade()

    self.assertTrue(self.has_constraint())

  def test_it_refuses_a_database_that_already_holds_two_mains(self):
    """And says which people, so somebody can go and look.

    Not repaired automatically: which of two mains is the real one is a fact
    about the user's accounts that nothing here knows, and picking wrong is
    silent - the folder every other account of that person files under would
    move without anybody being told.
    """
    self.upgrade(self.BEFORE)
    self.seed([
      (1, "a-main", "main"),
      (1, "a-second", "main"),
      (2, "b-main", "main"),
      (3, "c-main", "main"),
      (3, "c-second", "main"),
    ])

    with self.assertRaises(Exception) as caught:
      self.upgrade()

    message = str(caught.exception)
    self.assertIn("1", message)
    self.assertIn("3", message)
    ##
    ## The untouched person is not named - nothing is wrong with them.
    ##
    self.assertNotIn("b-main", message)
    ##
    ## And nothing was changed on the way out.
    ##
    with self.engine.connect() as connection:
      remaining = connection.execute(
        sa.text("SELECT COUNT(*) FROM person_account WHERE role = 'main'")
      ).scalar()
    self.assertEqual(5, remaining)
    self.assertFalse(self.has_constraint())

  def test_downgrade_removes_the_constraint_and_the_column(self):
    self.upgrade()
    self.seed([(1, "a-main", "main"), (1, "a-alt", "alt")])

    self.downgrade(self.BEFORE)

    self.assertFalse(self.has_constraint())
    self.assertFalse(self.has_column())

  def test_downgrade_keeps_every_row(self):
    self.upgrade()
    self.seed([(1, "a-main", "main"), (1, "a-alt", "alt"), (2, "b-main", "main")])

    self.downgrade(self.BEFORE)

    with self.engine.connect() as connection:
      accounts = connection.execute(
        sa.text("SELECT COUNT(*) FROM person_account")
      ).scalar()
      people = connection.execute(sa.text("SELECT COUNT(*) FROM person")).scalar()
    self.assertEqual(3, accounts)
    self.assertEqual(2, people)

  def test_it_can_be_applied_again_after_a_downgrade(self):
    self.upgrade()
    self.downgrade(self.BEFORE)

    self.upgrade()

    self.assertTrue(self.has_constraint())
