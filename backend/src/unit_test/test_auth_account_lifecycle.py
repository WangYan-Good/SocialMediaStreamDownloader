import io
from types import SimpleNamespace
import unittest
from unittest.mock import Mock

from backend.src.auth.errors import UnknownUsername
from backend.src.auth.service import AuthenticationService
from backend.src.auth.credentials import verify_password


class LifecycleRepository:
  def __init__(self):
    self.user = {
      "user_id": 7,
      "username": "alice",
      "password_hash": "old-hash",
      "is_active": True,
      "role": "admin",
    }
    self.sessions = ["one", "two"]

  def find_user_by_username(self, username):
    return dict(self.user) if username == self.user["username"] else None

  def set_password_and_revoke_sessions(self, user_id, password_hash):
    if user_id != self.user["user_id"]:
      return False
    self.user["password_hash"] = password_hash
    self.sessions.clear()
    return True

  def disable_user_and_revoke_sessions(self, user_id):
    if user_id != self.user["user_id"]:
      return False
    self.user["is_active"] = False
    self.sessions.clear()
    return True

  def set_user_active(self, user_id, active):
    if user_id != self.user["user_id"]:
      return False
    self.user["is_active"] = active
    return True

  def delete_sessions_for_user(self, user_id):
    if user_id != self.user["user_id"]:
      return 0
    count = len(self.sessions)
    self.sessions.clear()
    return count


class AuthenticationAccountLifecycleTest(unittest.TestCase):
  def setUp(self):
    self.repository = LifecycleRepository()
    self.service = AuthenticationService(
      self.repository, session_ttl_seconds=3600
    )

  def test_password_reset_rehashes_and_revokes_every_session(self):
    user = self.service.set_password("ALICE", "new correct horse battery")

    self.assertEqual("alice", user.username)
    self.assertTrue(
      verify_password(
        self.repository.user["password_hash"], "new correct horse battery"
      )
    )
    self.assertEqual([], self.repository.sessions)

  def test_disable_revokes_sessions_and_enable_does_not_revive_them(self):
    disabled = self.service.disable_user("alice")
    self.assertFalse(self.repository.user["is_active"])
    self.assertEqual([], self.repository.sessions)

    enabled = self.service.enable_user("alice")
    self.assertTrue(self.repository.user["is_active"])
    self.assertEqual([], self.repository.sessions)
    self.assertEqual("alice", disabled.username)
    self.assertEqual("alice", enabled.username)

  def test_revoke_sessions_changes_no_account_property(self):
    before = dict(self.repository.user)

    user = self.service.revoke_all_sessions("alice")

    self.assertEqual(before, self.repository.user)
    self.assertEqual([], self.repository.sessions)
    self.assertEqual("admin", user.role)

  def test_every_lifecycle_operation_refuses_an_unknown_user(self):
    for operation in (
      lambda: self.service.set_password("nobody", "new correct horse battery"),
      lambda: self.service.disable_user("nobody"),
      lambda: self.service.enable_user("nobody"),
      lambda: self.service.revoke_all_sessions("nobody"),
    ):
      with self.subTest(operation=operation), self.assertRaises(UnknownUsername):
        operation()


class AuthenticationLifecycleCliTest(unittest.TestCase):
  def test_parser_exposes_lifecycle_without_a_password_argument(self):
    from backend.src.auth import cli

    parser = cli.build_parser()
    for argv in (
      ["set-password", "alice"],
      ["disable-user", "alice"],
      ["enable-user", "alice"],
      ["revoke-sessions", "alice"],
    ):
      with self.subTest(argv=argv):
        arguments = parser.parse_args(argv)
        self.assertEqual("alice", arguments.username)
        self.assertNotIn("password", vars(arguments))

  def test_set_password_prompts_twice_and_never_prints_the_secret(self):
    from backend.src.auth.cli import set_password_command

    secret = "new correct horse battery"
    output = io.StringIO()
    code = set_password_command(
      "alice",
      service_factory=lambda: AuthenticationService(
        self.repository, session_ttl_seconds=3600
      ),
      prompt=Mock(side_effect=[secret, secret]),
      out=output,
    )

    self.assertEqual(0, code)
    self.assertNotIn(secret, output.getvalue())
    self.assertNotIn("scrypt", output.getvalue())
    self.assertEqual([], self.repository.sessions)

  def test_cli_service_factory_initializes_schema_guard_before_runtime(self):
    from backend.src.auth.cli import build_cli_service_factory

    calls = []
    settings = {"database": {"enable": True}}
    service = object()
    factory = build_cli_service_factory(
      config_loader=lambda: calls.append("config") or settings,
      guard_initializer=lambda value: calls.append(("guard", value)),
      runtime_builder=lambda provider: calls.append(
        ("runtime", provider())
      )
      or SimpleNamespace(service=lambda: service),
    )

    self.assertIs(service, factory())
    self.assertEqual(
      ["config", ("guard", settings), ("runtime", settings)], calls
    )

  def setUp(self):
    self.repository = LifecycleRepository()


class TransactionCursor:
  def __init__(self, connection):
    self.connection = connection
    self.rowcount = 1
    self._selected = False

  def __enter__(self):
    return self

  def __exit__(self, *_args):
    return False

  def execute(self, statement, params):
    self.connection.statements.append((statement, params))
    if statement.startswith("SELECT user_id"):
      self._selected = True
    if self.connection.fail_delete and statement.startswith("DELETE"):
      raise RuntimeError("delete failed")

  def fetchone(self):
    return (7,) if self._selected else None


class TransactionConnection:
  def __init__(self, *, fail_delete=False):
    self.fail_delete = fail_delete
    self.statements = []
    self.commits = 0
    self.rollbacks = 0

  def __enter__(self):
    return self

  def __exit__(self, *_args):
    return False

  def cursor(self):
    return TransactionCursor(self)

  def commit(self):
    self.commits += 1

  def rollback(self):
    self.rollbacks += 1


class AuthenticationRepositoryLifecycleTransactionTest(unittest.TestCase):
  def repository(self, connection):
    from backend.src.auth.repository import AuthRepository

    database = SimpleNamespace(get_connection=lambda: connection)
    return AuthRepository(database)

  def test_password_update_and_session_revoke_share_one_transaction(self):
    connection = TransactionConnection()

    changed = self.repository(connection).set_password_and_revoke_sessions(
      7, "new-hash"
    )

    self.assertTrue(changed)
    self.assertEqual(1, connection.commits)
    self.assertEqual(0, connection.rollbacks)
    self.assertEqual(
      ["SELECT", "UPDATE", "DELETE"],
      [statement.split()[0] for statement, _ in connection.statements],
    )

  def test_disable_and_session_revoke_share_one_transaction(self):
    connection = TransactionConnection()

    changed = self.repository(connection).disable_user_and_revoke_sessions(7)

    self.assertTrue(changed)
    self.assertEqual(1, connection.commits)
    self.assertEqual(
      ["SELECT", "UPDATE", "DELETE"],
      [statement.split()[0] for statement, _ in connection.statements],
    )

  def test_failed_session_revoke_rolls_back_the_account_update(self):
    from backend.src.auth.errors import AuthUnavailable

    connection = TransactionConnection(fail_delete=True)

    with self.assertRaises(AuthUnavailable):
      self.repository(connection).disable_user_and_revoke_sessions(7)

    self.assertEqual(0, connection.commits)
    self.assertEqual(1, connection.rollbacks)


if __name__ == "__main__":
  unittest.main()
