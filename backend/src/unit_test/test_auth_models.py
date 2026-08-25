##<<Base>>
import unittest

##<<Extension>>
import sqlalchemy as sa

##<<Third-part>>
from backend.src.database.orm.models import (
  MANAGED_TABLE_NAMES,
  AppUserModel,
  AuthSessionModel,
  Base,
  UserModel,
)


##
## >>============================= why a separate table =============================>>
##
##
## This repository already has a table called ``user``.  It is not an account
## anyone logs in with: it is a Douyin profile, with columns like
## ``fan_ticket_count``, ``hotsoon_verified`` and ``allow_be_located``, written
## from platform payloads.
##
## Putting a password on it would mean one row meaning two unrelated things -
## "a creator this program has downloaded from" and "somebody who may sign in" -
## and the first kind arrives automatically, from data this program does not
## control.  The application identity therefore gets its own table, and these
## tests exist mostly to keep that separation from eroding.
##


class TestApplicationUserIsNotThePlatformUser(unittest.TestCase):
  def test_the_platform_user_table_is_untouched_by_authentication(self):
    ##
    ## The whole reason app_user exists.  If a password ever appears here, the
    ## two concepts have been merged and a Douyin profile has become a login.
    ##
    columns = set(UserModel.__table__.columns.keys())

    for forbidden in ("password", "password_hash", "is_active", "username"):
      self.assertNotIn(forbidden, columns)

  def test_the_application_user_lives_in_its_own_table(self):
    self.assertEqual("app_user", AppUserModel.__tablename__)
    self.assertEqual("user", UserModel.__tablename__)

  def test_both_new_tables_are_managed_by_this_project(self):
    ##
    ## MANAGED_TABLE_NAMES is what alembic autogenerate and the start-up schema
    ## comparison both read.  A table missing from it is invisible to each: the
    ## comparison would not notice it drifting, and autogenerate would offer to
    ## drop it.
    ##
    self.assertIn("app_user", MANAGED_TABLE_NAMES)
    self.assertIn("auth_session", MANAGED_TABLE_NAMES)

  def test_both_new_tables_are_registered_on_the_shared_metadata(self):
    self.assertIn("app_user", Base.metadata.tables)
    self.assertIn("auth_session", Base.metadata.tables)


class TestApplicationUserShape(unittest.TestCase):
  def setUp(self):
    self.table = AppUserModel.__table__

  def test_it_carries_identity_status_and_role(self):
    ##
    ## Deliberately small.  A role column, an ownership column or an email is
    ## each a decision belonging to a later phase, and a column added "while we
    ## are here" is one that has to be migrated again once it turns out to be
    ## the wrong shape.
    ##
    self.assertEqual(
      {
        "user_id",
        "username",
        "password_hash",
        "role",
        "is_active",
        "created_at",
        "updated_at",
      },
      set(self.table.columns.keys()),
    )

  def test_it_stores_no_permission_or_ownership_model(self):
    columns = set(self.table.columns.keys())

    for later_phase in ("is_admin", "permissions", "scope"):
      self.assertNotIn(later_phase, columns)

  def test_role_has_a_safe_database_default_and_constraint(self):
    role = self.table.columns["role"]
    self.assertFalse(role.nullable)
    self.assertEqual("'user'", str(role.server_default.arg))
    checks = {
      constraint.name: str(constraint.sqltext)
      for constraint in self.table.constraints
      if isinstance(constraint, sa.CheckConstraint)
    }
    self.assertIn("ck_app_user_role", checks)
    self.assertIn("'user'", checks["ck_app_user_role"])
    self.assertIn("'admin'", checks["ck_app_user_role"])

  def test_the_username_is_unique(self):
    ##
    ## Enforced by the database rather than by a check-then-insert, which two
    ## concurrent creations can both pass.
    ##
    unique = {
      tuple(sorted(column.name for column in constraint.columns))
      for constraint in self.table.constraints
      if isinstance(constraint, sa.UniqueConstraint)
    }
    self.assertIn(("username",), unique)

  def test_the_password_column_is_named_for_what_it_holds(self):
    ##
    ## "password_hash", never "password".  The name is the reminder: a plaintext
    ## password has no column to be written into.
    ##
    self.assertIn("password_hash", self.table.columns)
    self.assertNotIn("password", self.table.columns)

  def test_a_hash_column_is_wide_enough_for_scrypt(self):
    ##
    ## Werkzeug's scrypt output is ~160 characters including its parameters and
    ## salt.  A column sized for bcrypt's 60 would truncate it, and a truncated
    ## hash silently never matches.
    ##
    self.assertGreaterEqual(self.table.columns["password_hash"].type.length, 255)

  def test_an_account_can_be_disabled_without_being_deleted(self):
    self.assertFalse(self.table.columns["is_active"].nullable)

  def test_the_identifier_is_not_the_username(self):
    ##
    ## Sessions and, later, ownership rows point at user_id.  A username that
    ## someone may want renamed is a poor thing to key foreign keys on.
    ##
    self.assertTrue(self.table.columns["user_id"].primary_key)
    self.assertFalse(self.table.columns["username"].primary_key)


class TestAuthSessionShape(unittest.TestCase):
  def setUp(self):
    self.table = AuthSessionModel.__table__

  def test_it_stores_a_hash_and_never_the_token(self):
    ##
    ## The single most important property in this file.
    ##
    ## The browser holds a random opaque token; the database holds only its
    ## SHA-256.  A column called ``token`` would mean that anyone who can read
    ## the table - a backup, a log of a query, a support session - can
    ## impersonate every signed-in user.
    ##
    columns = set(self.table.columns.keys())

    self.assertIn("token_hash", columns)
    for forbidden in ("token", "session_token", "raw_token", "secret"):
      self.assertNotIn(forbidden, columns)

  def test_role_is_not_cached_in_the_session(self):
    self.assertNotIn("role", self.table.columns)

  def test_the_token_hash_is_unique_so_a_lookup_is_exact(self):
    unique = {
      tuple(sorted(column.name for column in constraint.columns))
      for constraint in self.table.constraints
      if isinstance(constraint, sa.UniqueConstraint)
    }
    self.assertIn(("token_hash",), unique)

  def test_it_knows_who_it_belongs_to(self):
    foreign_keys = {
      (tuple(sorted(fk.column.name for fk in constraint.elements)), constraint.referred_table.name)
      for constraint in self.table.constraints
      if isinstance(constraint, sa.ForeignKeyConstraint)
    }
    self.assertIn((("user_id",), "app_user"), foreign_keys)

  def test_deleting_a_user_takes_their_sessions_with_them(self):
    ##
    ## Otherwise a deleted account leaves live sessions behind, and the row they
    ## point at is gone - which is either an orphan that still authenticates or
    ## a crash on every request, depending on how the join is written.
    ##
    constraint = next(
      one
      for one in self.table.constraints
      if isinstance(one, sa.ForeignKeyConstraint)
    )
    self.assertEqual("CASCADE", constraint.ondelete)

  def test_it_knows_when_it_stops_being_valid(self):
    self.assertIn("expires_at", self.table.columns)
    self.assertFalse(self.table.columns["expires_at"].nullable)

  def test_expiry_is_indexed_so_sweeping_is_cheap(self):
    indexed = {
      tuple(column.name for column in index.columns) for index in self.table.indexes
    }
    self.assertIn(("expires_at",), indexed)


if __name__ == "__main__":
  unittest.main()
