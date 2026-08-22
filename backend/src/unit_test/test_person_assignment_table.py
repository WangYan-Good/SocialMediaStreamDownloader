import threading
import unittest

from backend.src.service.person_assignment import (
  MainAccountConflict,
  PersonAssignmentService,
)
from backend.src.database.table.person_identity import (
  AccountAttachedElsewhere,
  AssignmentConflict,
  DouyinPersonIdentityTable,
  AssignmentRaced,
  LastMainRemoval,
  MainAlreadyAssigned,
  NotAttached,
  PersonMissing,
  UnknownRole,
)


PLATFORM = "douyin"

##
## A staged deletion.  ``None`` cannot stand for it: the overlay has to be able
## to say "this transaction removed the row" distinctly from "this transaction
## has not touched the row", and a missing key already means the second.
##
_DELETED = object()


##
## >>============================= transaction fake =============================>>
##
##
## A stand-in that can actually be wrong.
##
## Asserting that ``assign_account`` was called proves nothing about whether the
## work it does is one transaction - which is the entire point of this method.
## So this fake keeps real rows, applies writes to a per-connection **overlay**
## and merges that overlay into the committed rows only on ``commit()``.  A test
## that injects a failure half way through therefore observes what a rollback
## really leaves behind, rather than a mock's recollection of the calls.
##
## Row locks are real ``threading.Lock`` objects held from the ``SELECT ... FOR
## UPDATE`` that took them until the transaction ends, so the concurrency test
## below exercises the same serialisation MySQL would provide rather than
## asserting that the words "FOR UPDATE" appear in a string.
##

class FakeDatabase:
  """The committed contents of the three tables this method touches."""

  def __init__(self):
    self.person = {}
    self.person_account = {}
    self.share_url = {}
    self.next_person_id = 1
    ##
    ## Set by the concurrency test to the number of racers.  Two transactions
    ## meeting here are guaranteed to be reading the person's main slot at the
    ## same moment - so if nothing holds them apart, they really do both see
    ## "no main", rather than only sometimes seeing it.
    ##
    self.barrier = None
    ##
    ## Armed only by the source-person race: it has to meet at the count read,
    ## not at the main read, and one barrier cannot serve both.
    ##
    self.count_barrier = None
    self._lock_table = {}
    self._lock_table_guard = threading.Lock()

  def row_lock(self, key):
    with self._lock_table_guard:
      if key not in self._lock_table:
        self._lock_table[key] = threading.Lock()
      return self._lock_table[key]

  def allocate_person_id(self) -> int:
    with self._lock_table_guard:
      new_id = self.next_person_id
      self.next_person_id += 1
      return new_id

  def main_of(self, person_id):
    for row in self.person_account.values():
      if row["person_id"] == person_id and row["role"] == "main":
        return row
    return None

  def accounts_of(self, person_id):
    return [
      row for row in self.person_account.values()
      if row["person_id"] == person_id
    ]


class FakeCursor:
  """Reads and writes the fake tables by recognising the statements sent."""

  def __init__(self, connection):
    self._connection = connection
    self.lastrowid = None
    self._pending = None

  ##
  ## Real rows are dicts, because the pool hands out pymysql's DictCursor.  An
  ## earlier fake in this suite returned tuples and hid that difference until
  ## every query failed on the real database.
  ##
  def fetchone(self):
    return self._pending

  def fetchall(self):
    return [] if self._pending is None else [self._pending]

  def __enter__(self):
    return self

  def __exit__(self, *unused):
    return False

  def execute(self, sql, params=None):
    connection = self._connection
    text = " ".join(sql.split())
    connection.calls.append((text, params))
    connection.fail_if_asked(text)

    if text.startswith("SELECT"):
      self._pending = self._select(text, params or ())
      return
    self._pending = None
    self._write(text, params or ())

  ##
  ## >>--------------------------- reads ---------------------------<<
  ##
  def _select(self, text, params):
    connection = self._connection

    if "COUNT(*)" in text and "FROM person_account" in text:
      ##
      ## Tested before the two lock reads below, because this statement also
      ## mentions ``person_account`` and ``person_id`` and would otherwise be
      ## answered by one of them.
      ##
      main_role, person_id = params
      rows = connection.accounts_of(person_id)
      connection.pause_counting()
      return {
        "account_count": len(rows),
        "main_count": sum(1 for row in rows if row["role"] == main_role),
      }

    if "FROM person WHERE person_id" in text:
      person_id = params[0]
      if "FOR UPDATE" in text:
        connection.lock(("person", person_id))
      row = connection.person(person_id)
      return None if row is None else dict(row)

    if "FROM person_account WHERE platform" in text:
      key = (params[0], params[1])
      if "FOR UPDATE" in text:
        connection.lock(("account", key))
      row = connection.account(key)
      return None if row is None else dict(row)

    if "FROM person_account WHERE person_id" in text and "role = 'main'" in text:
      person_id = params[0]
      row = connection.main_of(person_id)
      ##
      ## Held *after* the read, which is the whole point.  Two promotions that
      ## are not kept apart both reach this line having each read "no main", and
      ## both then go on to write one.  Pausing before the read instead would
      ## leave the interpreter free to run one of them from read to commit
      ## without interruption, and the race would never be observed.
      ##
      connection.pause()
      if row is not None and "FOR UPDATE" in text:
        ##
        ## The row that was read is the row that gets locked, which is what
        ## InnoDB does.  A person with no main has no row to lock - so the only
        ## thing serialising two requests that both want to become the main is
        ## the lock taken on the person itself.
        ##
        connection.lock(("account", (row["platform"], row["owner_user_id"])))
      return None if row is None else dict(row)

    if "FROM share_url WHERE owner_user_id" in text:
      row = connection.identity(params[0])
      return None if row is None else dict(row)

    raise AssertionError("fake cursor cannot read: {}".format(text))

  ##
  ## >>--------------------------- writes ---------------------------<<
  ##
  def _write(self, text, params):
    connection = self._connection

    if text.startswith("INSERT INTO share_url"):
      owner_user_id, sec_user_id, nickname = params
      stored = dict(connection.identity(owner_user_id) or {
        "owner_user_id": owner_user_id,
        "sec_user_id": None,
        "nickname": None,
        "directory_name": None,
      })
      if sec_user_id is not None:
        stored["sec_user_id"] = sec_user_id
      if nickname is not None:
        stored["nickname"] = nickname
      connection.stage_identity(owner_user_id, stored)
      return

    if text.startswith("INSERT INTO person ("):
      display_name, note = params
      person_id = connection.database.allocate_person_id()
      connection.stage_person(person_id, {
        "person_id": person_id,
        "display_name": display_name,
        "note": note,
      })
      self.lastrowid = person_id
      return

    if text.startswith("UPDATE person_account SET role"):
      role, platform, owner_user_id = params
      key = (platform, owner_user_id)
      stored = dict(connection.account(key))
      stored["role"] = role
      connection.stage_account(key, stored)
      return

    if text.startswith("INSERT INTO person_account"):
      platform, owner_user_id, person_id, role = params
      connection.stage_account((platform, owner_user_id), {
        "platform": platform,
        "owner_user_id": owner_user_id,
        "person_id": person_id,
        "role": role,
      })
      return

    if text.startswith("UPDATE share_url AS s"):
      ##
      ## Actually carried out, not just recorded.
      ##
      ## This is the statement the whole last-main rule exists because of: it
      ## copies the main account's folder onto every *other* account of the
      ## person, and nothing ever copies it back.  A fake that only noted the
      ## call could say "alignment happened" but never "and it wrote the wrong
      ## folder onto this row", which is the only form the damage actually
      ## takes.
      ##
      platform, person_id = params
      connection.aligned.append(params)
      main = connection.main_of(person_id)
      if main is None:
        ##
        ## No main to copy from.  A no-op rather than a blanking - copying "no
        ## folder" onto the siblings would move files that are filed correctly.
        ##
        return
      main_identity = connection.identity(main["owner_user_id"]) or {}
      folder = main_identity.get("directory_name")
      if not isinstance(folder, str) or not folder.strip():
        return
      for row in connection.accounts_of(person_id):
        if row["role"] == "main":
          continue
        stored = dict(connection.identity(row["owner_user_id"]) or {
          "owner_user_id": row["owner_user_id"],
          "sec_user_id": None,
          "nickname": None,
          "directory_name": None,
        })
        stored["directory_name"] = folder
        connection.stage_identity(row["owner_user_id"], stored)
      return

    if text.startswith("UPDATE person SET display_name"):
      ##
      ## Nothing in the assignment transaction sends this, and nothing should:
      ## renaming a person is PATCH /api/person/<id>.  It is understood here so
      ## that "a refresh does not rename the person" is a claim a mutation can
      ## actually break - a fake that simply refuses the statement would fail
      ## such a test with "cannot write", which proves nothing about the rule.
      ##
      display_name, person_id = params
      stored = dict(connection.person(person_id))
      stored["display_name"] = display_name
      connection.stage_person(person_id, stored)
      return

    if text.startswith("DELETE FROM person_account"):
      platform, owner_user_id = params
      connection.stage_account((platform, owner_user_id), _DELETED)
      return

    raise AssertionError("fake cursor cannot write: {}".format(text))


class FakeConnection:
  """One transaction: an overlay over the committed rows, plus its locks."""

  def __init__(self, database, fail_on=None):
    self.database = database
    self.calls = []
    self.aligned = []
    self.begins = 0
    self.commits = 0
    self.rollbacks = 0
    self._fail_on = fail_on
    self._overlay_person = {}
    self._overlay_account = {}
    self._overlay_identity = {}
    self._held = []

  ##
  ## >>--------------------------- dbapi ---------------------------<<
  ##
  def cursor(self):
    return FakeCursor(self)

  def begin(self):
    self.begins += 1

  def commit(self):
    self.commits += 1
    self.database.person.update(self._overlay_person)
    for key, row in self._overlay_account.items():
      if row is _DELETED:
        self.database.person_account.pop(key, None)
      else:
        self.database.person_account[key] = row
    self.database.share_url.update(self._overlay_identity)
    self._discard()

  def rollback(self):
    self.rollbacks += 1
    self._discard()

  def _discard(self):
    self._overlay_person = {}
    self._overlay_account = {}
    self._overlay_identity = {}
    while self._held:
      self._held.pop().release()

  def __enter__(self):
    return self

  def __exit__(self, *unused):
    ##
    ## Deliberately does *not* roll back.  The real pooled connection manager
    ## does, so leaving it out here means the atomicity tests are watching the
    ## rollback ``assign_account`` issues itself rather than one it inherits.
    ##
    return False

  ##
  ## >>--------------------------- state ---------------------------<<
  ##
  def fail_if_asked(self, text):
    if self._fail_on is not None and self._fail_on in text:
      raise RuntimeError("injected failure at: {}".format(self._fail_on))

  def pause_counting(self):
    """The same idea as ``pause``, at the read the source-person guard makes."""
    barrier = self.database.count_barrier
    if barrier is None:
      return
    try:
      barrier.wait(timeout=0.25)
    except threading.BrokenBarrierError:
      pass

  def pause(self):
    """Hold here until every racer has arrived, or until it is clear one cannot.

    A plain sleep made this a coin toss: whether the second transaction read
    before the first committed depended on how the interpreter felt.  The
    barrier removes the timing from the question entirely.

    When a lock *is* held the other racer never arrives, so the wait breaks on
    its timeout and this one carries on - which is exactly the serialised
    outcome being asserted.
    """
    barrier = self.database.barrier
    if barrier is None:
      return
    try:
      barrier.wait(timeout=0.25)
    except threading.BrokenBarrierError:
      pass

  def lock(self, key):
    lock = self.database.row_lock(key)
    lock.acquire()
    self._held.append(lock)

  def person(self, person_id):
    if person_id in self._overlay_person:
      return self._overlay_person[person_id]
    return self.database.person.get(person_id)

  def account(self, key):
    if key in self._overlay_account:
      staged = self._overlay_account[key]
      return None if staged is _DELETED else staged
    return self.database.person_account.get(key)

  def identity(self, owner_user_id):
    if owner_user_id in self._overlay_identity:
      return self._overlay_identity[owner_user_id]
    return self.database.share_url.get(owner_user_id)

  def main_of(self, person_id):
    for row in self.accounts_of(person_id):
      if row["role"] == "main":
        return row
    return None

  def accounts_of(self, person_id):
    """This person's accounts as *this transaction* sees them.

    Overlay first: a statement that has already staged a change must be able to
    read it back, exactly as it would inside a real transaction.
    """
    merged = dict(self.database.person_account)
    merged.update(self._overlay_account)
    return [
      row for row in merged.values()
      if row is not _DELETED and row["person_id"] == person_id
    ]

  def stage_person(self, person_id, row):
    self._overlay_person[person_id] = row

  def stage_account(self, key, row):
    self._overlay_account[key] = row
    self._enforce_one_main(row)

  def _enforce_one_main(self, written):
    """The unique index the schema now carries, checked the way MySQL checks it.

    Per statement, not per transaction. That distinction is the whole reason
    the assignment demotes the outgoing main *before* promoting the incoming
    one: both orders leave the same rows at COMMIT, but only one of them avoids
    a moment where two rows project the same person into ``main_person_id``.
    Without this the fake would happily accept the wrong order and the
    reordering would only be discovered against a real database.
    """
    if written is _DELETED or written["role"] != "main":
      return
    mains = [
      row for row in self.accounts_of(written["person_id"])
      if row["role"] == "main"
    ]
    if len(mains) > 1:
      import pymysql

      raise pymysql.err.IntegrityError(
        1062,
        "Duplicate entry '{}' for key "
        "'person_account.uq_person_account_main_person'".format(
          written["person_id"]
        ),
      )

  def stage_identity(self, owner_user_id, row):
    self._overlay_identity[owner_user_id] = row


def build_table(database=None, fail_on=None, write_ready=True):
  """A table wired to one fake transaction, with the write guard observable."""
  database = database if database is not None else FakeDatabase()
  connection = FakeConnection(database, fail_on=fail_on)
  table = DouyinPersonIdentityTable.__new__(DouyinPersonIdentityTable)
  table.get_connection = lambda: connection

  guard_calls = []

  def require_write_ready():
    guard_calls.append(len(connection.calls))
    if not write_ready:
      raise RuntimeError("schema is not write ready")

  table.require_write_ready = require_write_ready
  table.guard_calls = guard_calls
  return table, database, connection


def seed_person(database, person_id, display_name="现有的人", note=None):
  database.person[person_id] = {
    "person_id": person_id,
    "display_name": display_name,
    "note": note,
  }
  return person_id


def seed_account(database, owner_user_id, person_id, role, nickname=None,
                 directory_name=None):
  database.person_account[(PLATFORM, owner_user_id)] = {
    "platform": PLATFORM,
    "owner_user_id": owner_user_id,
    "person_id": person_id,
    "role": role,
  }
  database.share_url.setdefault(owner_user_id, {
    "owner_user_id": owner_user_id,
    "sec_user_id": None,
    "nickname": nickname,
    "directory_name": directory_name,
  })


##
## >>============================= creating a person =============================>>
##
class NewPersonAssignmentTest(unittest.TestCase):
  """Creating the person and attaching the account is one operation.

  Done as two calls it has a middle: a person exists, holds nothing, and
  whoever was going to attach the account has already failed.  Nobody ever goes
  back to clean those up, so the invariant has to be that they cannot happen.
  """

  def test_a_new_person_is_created_and_the_account_attached(self):
    table, database, _ = build_table()

    result = table.assign_account(
      owner_user_id="acc-1",
      role="main",
      display_name="张三",
    )

    self.assertTrue(result["created_person"])
    person_id = result["person_id"]
    self.assertEqual(database.person[person_id]["display_name"], "张三")
    self.assertEqual(
      database.person_account[(PLATFORM, "acc-1")]["person_id"], person_id
    )
    self.assertEqual(database.person_account[(PLATFORM, "acc-1")]["role"], "main")

  def test_a_new_person_may_hold_only_an_alt_account(self):
    """A person is allowed to have no main account.

    The first account somebody pastes is often the spare - that is *why* they
    are marking it - and forcing it to be the main one would record something
    the user did not say.
    """
    table, database, _ = build_table()

    result = table.assign_account(
      owner_user_id="acc-1", role="alt", display_name="张三"
    )

    person_id = result["person_id"]
    self.assertEqual(database.person_account[(PLATFORM, "acc-1")]["role"], "alt")
    self.assertIsNone(database.main_of(person_id))
    self.assertEqual(len(database.accounts_of(person_id)), 1)

  def test_a_new_person_may_hold_only_a_matrix_account(self):
    table, database, _ = build_table()

    result = table.assign_account(
      owner_user_id="acc-1", role="matrix", display_name="张三"
    )

    person_id = result["person_id"]
    self.assertEqual(
      database.person_account[(PLATFORM, "acc-1")]["role"], "matrix"
    )
    self.assertIsNone(database.main_of(person_id))

  def test_everything_lands_on_one_commit(self):
    table, _, connection = build_table()

    table.assign_account(
      owner_user_id="acc-1", role="main", display_name="张三"
    )

    self.assertEqual(connection.begins, 1)
    self.assertEqual(connection.commits, 1)
    self.assertEqual(connection.rollbacks, 0)

  def test_the_transaction_opens_before_the_first_statement(self):
    table, _, connection = build_table()

    ##
    ## ``begin`` is issued rather than relied on implicitly.  The pool hands out
    ## connections with autocommit off, so InnoDB would open one anyway - but a
    ## statement that ran before the transaction was demarcated would commit on
    ## its own the day that changes, and this is the one method where that would
    ## silently break the guarantee.
    ##
    self.assertEqual(connection.begins, 0)
    table.assign_account(
      owner_user_id="acc-1", role="main", display_name="张三"
    )
    self.assertGreaterEqual(len(connection.calls), 1)
    self.assertEqual(connection.begins, 1)

  def test_the_identity_is_recorded_for_an_account_never_downloaded(self):
    """``share_url`` has no row until something downloads.

    Without this the person page shows a bare id for an account somebody just
    marked, which is the whole reason marking by link exists.
    """
    table, database, _ = build_table()

    table.assign_account(
      owner_user_id="acc-1",
      role="alt",
      display_name="张三",
      sec_user_id="MS4wLjABAAAA",
      nickname="主播甲",
    )

    self.assertEqual(database.share_url["acc-1"]["nickname"], "主播甲")
    self.assertEqual(database.share_url["acc-1"]["sec_user_id"], "MS4wLjABAAAA")

  def test_the_recorded_folder_is_left_alone(self):
    """``directory_name`` belongs to the download paths, not to this one."""
    table, database, _ = build_table()
    database.share_url["acc-1"] = {
      "owner_user_id": "acc-1",
      "sec_user_id": None,
      "nickname": "旧昵称",
      "directory_name": "已经存在的目录",
    }

    table.assign_account(
      owner_user_id="acc-1", role="alt", display_name="张三", nickname="新昵称"
    )

    self.assertEqual(
      database.share_url["acc-1"]["directory_name"], "已经存在的目录"
    )

  def test_the_note_is_stored_with_the_new_person(self):
    table, database, _ = build_table()

    result = table.assign_account(
      owner_user_id="acc-1", role="alt", display_name="张三", note="备注"
    )

    self.assertEqual(database.person[result["person_id"]]["note"], "备注")


##
## >>============================= an existing person =============================>>
##
class ExistingPersonAssignmentTest(unittest.TestCase):
  def test_an_account_is_attached_to_an_existing_person(self):
    table, database, _ = build_table()
    seed_person(database, 12, display_name="李四")

    result = table.assign_account(
      owner_user_id="acc-2", role="main", person_id=12
    )

    self.assertFalse(result["created_person"])
    self.assertEqual(result["person_id"], 12)
    self.assertEqual(result["display_name"], "李四")
    self.assertEqual(database.person_account[(PLATFORM, "acc-2")]["role"], "main")

  def test_no_second_person_is_created(self):
    table, database, _ = build_table()
    seed_person(database, 12)

    table.assign_account(owner_user_id="acc-2", role="alt", person_id=12)

    self.assertEqual(list(database.person), [12])

  def test_every_role_is_accepted_for_an_existing_person(self):
    for role in ("main", "alt", "matrix"):
      table, database, _ = build_table()
      seed_person(database, 12)

      table.assign_account(owner_user_id="acc-2", role=role, person_id=12)

      self.assertEqual(
        database.person_account[(PLATFORM, "acc-2")]["role"], role
      )

  def test_the_sub_accounts_are_aligned_to_the_main_folder(self):
    """Their downloads all land in the main account's folder.

    Leaving each sub-account's own row saying something else would give the
    database two answers to one question.
    """
    table, database, connection = build_table()
    seed_person(database, 12)

    table.assign_account(owner_user_id="acc-2", role="alt", person_id=12)

    self.assertEqual(connection.aligned, [(PLATFORM, 12)])

  def test_the_alignment_happens_inside_the_same_transaction(self):
    table, database, connection = build_table()
    seed_person(database, 12)

    table.assign_account(owner_user_id="acc-2", role="alt", person_id=12)

    aligned_at = [
      index for index, (text, _) in enumerate(connection.calls)
      if text.startswith("UPDATE share_url AS s")
    ]
    self.assertEqual(len(aligned_at), 1)
    ##
    ## One commit, and it comes after the alignment: aligning in a second
    ## transaction would leave a window where the account is attached and the
    ## folder still says something else.
    ##
    self.assertEqual(connection.commits, 1)

  def test_the_same_account_and_role_again_changes_no_relationship(self):
    """Re-sending an assignment that already holds moves nothing.

    A browser retrying a request it never saw the answer to must not turn into
    a second, different state.  It does still refresh who the account is - see
    IdempotentIdentityRefreshTest for why those are two separate facts.
    """
    table, database, connection = build_table()
    seed_person(database, 12, display_name="李四")
    seed_account(database, "acc-2", 12, "alt")

    result = table.assign_account(
      owner_user_id="acc-2", role="alt", person_id=12
    )

    self.assertEqual(result["person_id"], 12)
    self.assertFalse(result["created_person"])
    self.assertEqual(
      database.person_account[(PLATFORM, "acc-2")]["role"], "alt"
    )
    self.assertEqual(list(database.person), [12])
    ##
    ## No attach, no role update, no person insert, no alignment.
    ##
    for text, _ in connection.calls:
      self.assertFalse(text.startswith("INSERT INTO person_account"))
      self.assertFalse(text.startswith("INSERT INTO person ("))
      self.assertFalse(text.startswith("UPDATE person_account"))
      self.assertFalse(text.startswith("UPDATE share_url AS s"))

  def test_a_role_change_within_one_person_is_applied(self):
    table, database, _ = build_table()
    seed_person(database, 12)
    seed_account(database, "acc-2", 12, "alt")

    table.assign_account(owner_user_id="acc-2", role="matrix", person_id=12)

    self.assertEqual(
      database.person_account[(PLATFORM, "acc-2")]["role"], "matrix"
    )


##
## >>============================= the write guard =============================>>
##
class WriteGuardTest(unittest.TestCase):
  def test_the_schema_guard_is_consulted_before_any_statement(self):
    table, _, connection = build_table()

    table.assign_account(
      owner_user_id="acc-1", role="main", display_name="张三"
    )

    self.assertEqual(table.guard_calls, [0])

  def test_a_blocked_schema_stops_the_assignment(self):
    table, database, connection = build_table(write_ready=False)

    with self.assertRaises(RuntimeError):
      table.assign_account(
        owner_user_id="acc-1", role="main", display_name="张三"
      )

    self.assertEqual(connection.calls, [])
    self.assertEqual(database.person, {})

  def test_an_unknown_role_is_refused_before_the_guard_or_any_sql(self):
    table, _, connection = build_table()

    with self.assertRaises(UnknownRole):
      table.assign_account(
        owner_user_id="acc-1", role="boss", display_name="张三"
      )

    self.assertEqual(connection.calls, [])


##
## >>============================= the account already belongs =============================>>
##
class AccountMoveTest(unittest.TestCase):
  """An account already under somebody else is never moved quietly.

  ``person_account`` is keyed on the account, so attaching it elsewhere really
  does take it away from whoever holds it - and their downloads change folder
  the moment it happens.  That is a decision, so it has to be asked for.
  """

  def test_moving_an_attached_account_is_refused_by_default(self):
    table, database, _ = build_table()
    seed_person(database, 7, display_name="原来的人")
    seed_person(database, 12, display_name="李四")
    seed_account(database, "acc-2", 7, "alt")

    with self.assertRaises(AccountAttachedElsewhere) as caught:
      table.assign_account(owner_user_id="acc-2", role="alt", person_id=12)

    self.assertEqual(caught.exception.person_id, 7)
    self.assertEqual(caught.exception.display_name, "原来的人")

  def test_a_refused_move_leaves_the_account_where_it_was(self):
    table, database, connection = build_table()
    seed_person(database, 7)
    seed_person(database, 12)
    seed_account(database, "acc-2", 7, "alt")

    with self.assertRaises(AccountAttachedElsewhere):
      table.assign_account(owner_user_id="acc-2", role="main", person_id=12)

    self.assertEqual(database.person_account[(PLATFORM, "acc-2")]["person_id"], 7)
    self.assertEqual(database.person_account[(PLATFORM, "acc-2")]["role"], "alt")
    self.assertEqual(connection.commits, 0)
    self.assertEqual(connection.rollbacks, 1)

  def test_a_refused_move_creates_no_person(self):
    """The conflict is found before the person is inserted, not after."""
    table, database, connection = build_table()
    seed_person(database, 7)
    seed_account(database, "acc-2", 7, "alt")

    with self.assertRaises(AccountAttachedElsewhere):
      table.assign_account(
        owner_user_id="acc-2", role="alt", display_name="新的人"
      )

    self.assertEqual(list(database.person), [7])
    inserts = [
      text for text, _ in connection.calls if text.startswith("INSERT INTO person (")
    ]
    self.assertEqual(inserts, [])

  def test_an_explicit_move_is_carried_out(self):
    table, database, connection = build_table()
    seed_person(database, 7, display_name="原来的人")
    seed_person(database, 12, display_name="李四")
    seed_account(database, "acc-2", 7, "alt")

    result = table.assign_account(
      owner_user_id="acc-2", role="matrix", person_id=12, allow_move=True
    )

    self.assertEqual(result["person_id"], 12)
    self.assertEqual(database.person_account[(PLATFORM, "acc-2")]["person_id"], 12)
    self.assertEqual(database.person_account[(PLATFORM, "acc-2")]["role"], "matrix")

  def test_an_explicit_move_is_one_transaction(self):
    """Detaching and re-attaching as two commits has a middle where the
    account belongs to nobody, and the downloads running at that moment file
    themselves somewhere else."""
    table, database, connection = build_table()
    seed_person(database, 7)
    seed_person(database, 12)
    seed_account(database, "acc-2", 7, "alt")

    table.assign_account(
      owner_user_id="acc-2", role="alt", person_id=12, allow_move=True
    )

    self.assertEqual(connection.begins, 1)
    self.assertEqual(connection.commits, 1)
    self.assertEqual(connection.rollbacks, 0)

  def test_an_account_moved_onto_a_brand_new_person_is_still_one_transaction(self):
    table, database, connection = build_table()
    seed_person(database, 7)
    seed_account(database, "acc-2", 7, "alt")

    result = table.assign_account(
      owner_user_id="acc-2",
      role="alt",
      display_name="新的人",
      allow_move=True,
    )

    self.assertTrue(result["created_person"])
    self.assertEqual(
      database.person_account[(PLATFORM, "acc-2")]["person_id"],
      result["person_id"],
    )
    self.assertEqual(connection.commits, 1)


##
## >>============================= at most one main =============================>>
##
class MainAccountConflictTest(unittest.TestCase):
  """Zero or one main account per person.  Never two.

  Nothing in the schema forbids the second one, and the page that used to be
  the only guard is a browser - which cannot be one.  So this method is where
  the invariant actually lives.
  """

  def test_a_second_main_is_refused(self):
    table, database, _ = build_table()
    seed_person(database, 12)
    seed_account(database, "acc-1", 12, "main", nickname="主号")

    with self.assertRaises(MainAlreadyAssigned) as caught:
      table.assign_account(owner_user_id="acc-2", role="main", person_id=12)

    self.assertEqual(caught.exception.owner_user_id, "acc-1")
    self.assertEqual(caught.exception.nickname, "主号")

  def test_a_refused_second_main_writes_nothing(self):
    table, database, connection = build_table()
    seed_person(database, 12)
    seed_account(database, "acc-1", 12, "main")

    with self.assertRaises(MainAlreadyAssigned):
      table.assign_account(owner_user_id="acc-2", role="main", person_id=12)

    self.assertNotIn((PLATFORM, "acc-2"), database.person_account)
    self.assertNotIn("acc-2", database.share_url)
    self.assertEqual(database.main_of(12)["owner_user_id"], "acc-1")
    self.assertEqual(connection.commits, 0)

  def test_promoting_an_alt_of_the_same_person_still_hits_the_conflict(self):
    """A role change is not a way round the invariant."""
    table, database, _ = build_table()
    seed_person(database, 12)
    seed_account(database, "acc-1", 12, "main")
    seed_account(database, "acc-2", 12, "alt")

    with self.assertRaises(MainAlreadyAssigned):
      table.assign_account(owner_user_id="acc-2", role="main", person_id=12)

  def test_the_current_main_re_sent_as_main_is_not_a_conflict(self):
    table, database, _ = build_table()
    seed_person(database, 12)
    seed_account(database, "acc-1", 12, "main")

    result = table.assign_account(
      owner_user_id="acc-1", role="main", person_id=12
    )

    self.assertEqual(result["person_id"], 12)
    self.assertEqual(database.main_of(12)["owner_user_id"], "acc-1")

  def test_a_person_with_no_main_accepts_one(self):
    table, database, _ = build_table()
    seed_person(database, 12)
    seed_account(database, "acc-1", 12, "alt")

    table.assign_account(owner_user_id="acc-2", role="main", person_id=12)

    self.assertEqual(database.main_of(12)["owner_user_id"], "acc-2")

  def test_a_conflict_is_one_family_of_failure(self):
    """Both refusals answer 409, so a caller that only cares that the
    assignment was refused catches one thing."""
    self.assertTrue(issubclass(AccountAttachedElsewhere, AssignmentConflict))
    self.assertTrue(issubclass(MainAlreadyAssigned, AssignmentConflict))


##
## >>============================= replacing the main =============================>>
##
class ReplaceMainTest(unittest.TestCase):
  def test_the_old_main_is_demoted_and_the_new_one_promoted(self):
    table, database, _ = build_table()
    seed_person(database, 12)
    seed_account(database, "acc-1", 12, "main")

    table.assign_account(
      owner_user_id="acc-2", role="main", person_id=12, demote_main_to="alt"
    )

    self.assertEqual(database.person_account[(PLATFORM, "acc-1")]["role"], "alt")
    self.assertEqual(database.person_account[(PLATFORM, "acc-2")]["role"], "main")
    self.assertEqual(database.main_of(12)["owner_user_id"], "acc-2")

  def test_the_old_main_may_be_demoted_to_matrix(self):
    table, database, _ = build_table()
    seed_person(database, 12)
    seed_account(database, "acc-1", 12, "main")

    table.assign_account(
      owner_user_id="acc-2", role="main", person_id=12, demote_main_to="matrix"
    )

    self.assertEqual(
      database.person_account[(PLATFORM, "acc-1")]["role"], "matrix"
    )

  def test_the_replacement_is_one_transaction(self):
    table, database, connection = build_table()
    seed_person(database, 12)
    seed_account(database, "acc-1", 12, "main")

    table.assign_account(
      owner_user_id="acc-2", role="main", person_id=12, demote_main_to="alt"
    )

    self.assertEqual(connection.begins, 1)
    self.assertEqual(connection.commits, 1)

  def test_the_old_main_cannot_be_demoted_to_main(self):
    """Which would be the two-main state written out in full."""
    table, database, _ = build_table()
    seed_person(database, 12)
    seed_account(database, "acc-1", 12, "main")

    with self.assertRaises(UnknownRole):
      table.assign_account(
        owner_user_id="acc-2", role="main", person_id=12, demote_main_to="main"
      )

  def test_a_replacement_with_nothing_to_replace_simply_assigns(self):
    table, database, _ = build_table()
    seed_person(database, 12)

    table.assign_account(
      owner_user_id="acc-2", role="main", person_id=12, demote_main_to="alt"
    )

    self.assertEqual(database.main_of(12)["owner_user_id"], "acc-2")
    self.assertEqual(len(database.accounts_of(12)), 1)


##
## >>============================= the person must exist =============================>>
##
class MissingPersonTest(unittest.TestCase):
  def test_an_unknown_person_is_reported_rather_than_created(self):
    table, database, _ = build_table()

    with self.assertRaises(PersonMissing) as caught:
      table.assign_account(owner_user_id="acc-2", role="alt", person_id=999)

    self.assertEqual(caught.exception.person_id, 999)

  def test_an_unknown_person_leaves_nothing_behind(self):
    """Attaching first would hit the foreign key and answer 500, which tells
    the page nothing it can act on."""
    table, database, connection = build_table()

    with self.assertRaises(PersonMissing):
      table.assign_account(owner_user_id="acc-2", role="alt", person_id=999)

    self.assertEqual(database.person_account, {})
    self.assertEqual(database.share_url, {})
    self.assertEqual(connection.commits, 0)


##
## >>============================= losing the last main =============================>>
##
class LastMainRemovalTest(unittest.TestCase):
  """A person that has a main cannot quietly stop having one.

  Not symmetry for its own sake.  ``align_accounts_to_main`` copies the main's
  folder onto every *other* account of the person - its own row is excluded by
  ``sub.role <> 'main'`` - and nothing ever copies it back: the download path
  writes ``directory_name = COALESCE(directory_name, VALUES(directory_name))``,
  so a stored value wins forever.  Once a sibling has been aligned, the folder
  it used to file under is gone from the database.

  So when the last main goes away, ``find_person_folder`` starts answering
  ``None`` and those siblings fall back to "their own" recorded folder - which
  is now the *ex-main's* folder, with no person left to explain why.  That is
  not a state this program can get itself out of, so it is one it must not get
  into.
  """

  def build_person_with_sibling(self):
    database = FakeDatabase()
    seed_person(database, 12, display_name="李四")
    seed_account(database, "acc-main", 12, "main", nickname="主号")
    seed_account(database, "acc-alt", 12, "alt", nickname="小号")
    return database

  def test_demoting_the_only_main_of_a_person_with_siblings_is_refused(self):
    database = self.build_person_with_sibling()
    table, _, _ = build_table(database=database)

    with self.assertRaises(LastMainRemoval) as caught:
      table.assign_account(owner_user_id="acc-main", role="alt", person_id=12)

    self.assertEqual(caught.exception.person_id, 12)
    self.assertEqual(caught.exception.display_name, "李四")
    self.assertEqual(caught.exception.owner_user_id, "acc-main")
    self.assertEqual(caught.exception.nickname, "主号")

  def test_demoting_to_matrix_is_refused_the_same_way(self):
    database = self.build_person_with_sibling()
    table, _, _ = build_table(database=database)

    with self.assertRaises(LastMainRemoval):
      table.assign_account(owner_user_id="acc-main", role="matrix", person_id=12)

  def test_a_refused_demotion_writes_nothing(self):
    database = self.build_person_with_sibling()
    table, _, connection = build_table(database=database)

    with self.assertRaises(LastMainRemoval):
      table.assign_account(owner_user_id="acc-main", role="alt", person_id=12)

    self.assertEqual(
      database.person_account[(PLATFORM, "acc-main")]["role"], "main"
    )
    self.assertEqual(database.main_of(12)["owner_user_id"], "acc-main")
    self.assertEqual(connection.commits, 0)
    self.assertEqual(connection.rollbacks, 1)

  def test_moving_the_only_main_away_is_refused_even_with_allow_move(self):
    """``allow_move`` answers "may this account leave its person" - it does not
    answer "may that person be left with no main"."""
    database = self.build_person_with_sibling()
    seed_person(database, 20, display_name="王五")
    table, _, _ = build_table(database=database)

    with self.assertRaises(LastMainRemoval) as caught:
      table.assign_account(
        owner_user_id="acc-main", role="alt", person_id=20, allow_move=True
      )

    ##
    ## The person named is the one being harmed - the source - not the target.
    ##
    self.assertEqual(caught.exception.person_id, 12)
    self.assertEqual(caught.exception.display_name, "李四")

  def test_moving_the_only_main_away_as_a_main_is_refused_too(self):
    """The role it takes at its destination changes nothing about what the
    person it left behind is now missing."""
    database = self.build_person_with_sibling()
    seed_person(database, 20)
    table, _, _ = build_table(database=database)

    with self.assertRaises(LastMainRemoval):
      table.assign_account(
        owner_user_id="acc-main", role="main", person_id=20, allow_move=True
      )

  def test_a_refused_move_leaves_both_people_untouched(self):
    database = self.build_person_with_sibling()
    seed_person(database, 20)
    table, _, connection = build_table(database=database)

    with self.assertRaises(LastMainRemoval):
      table.assign_account(
        owner_user_id="acc-main", role="alt", person_id=20, allow_move=True
      )

    self.assertEqual(
      database.person_account[(PLATFORM, "acc-main")]["person_id"], 12
    )
    self.assertEqual(database.accounts_of(20), [])
    self.assertEqual(connection.commits, 0)

  def test_it_is_one_family_of_refusal_with_the_others(self):
    self.assertTrue(issubclass(LastMainRemoval, AssignmentConflict))


class LastMainGuardDoesNotOverreachTest(unittest.TestCase):
  """The guard protects an established folder relationship, nothing more.

  It is easy to write this rule as "a person must always have a main", and that
  rule would be wrong: the first account somebody pastes is often the spare, and
  a person who has never had a main has never had a folder copied off one.  The
  line is "do not take away the main that other accounts were aligned to", so
  everything on the other side of that line has to keep working.
  """

  def test_a_new_person_may_still_hold_only_an_alt(self):
    table, database, _ = build_table()

    result = table.assign_account(
      owner_user_id="acc-1", role="alt", display_name="张三"
    )

    self.assertIsNone(database.main_of(result["person_id"]))

  def test_a_new_person_may_still_hold_only_a_matrix(self):
    table, database, _ = build_table()

    result = table.assign_account(
      owner_user_id="acc-1", role="matrix", display_name="张三"
    )

    self.assertIsNone(database.main_of(result["person_id"]))

  def test_an_existing_person_with_no_main_may_still_take_an_alt(self):
    table, database, _ = build_table()
    seed_person(database, 12)
    seed_account(database, "acc-1", 12, "alt")

    table.assign_account(owner_user_id="acc-2", role="matrix", person_id=12)

    self.assertIsNone(database.main_of(12))
    self.assertEqual(len(database.accounts_of(12)), 2)

  def test_the_sole_account_of_a_person_may_be_demoted(self):
    """Nothing was ever aligned to it.

    ``align_accounts_to_main`` only writes rows with ``sub.role <> 'main'``, so
    a person holding one account has had no folder copied anywhere - not even
    onto that account itself.  Demoting it leaves its own recorded folder
    exactly as it was, which is where its downloads were already going.
    """
    table, database, _ = build_table()
    seed_person(database, 12)
    seed_account(database, "acc-only", 12, "main")

    table.assign_account(owner_user_id="acc-only", role="alt", person_id=12)

    self.assertEqual(
      database.person_account[(PLATFORM, "acc-only")]["role"], "alt"
    )
    self.assertIsNone(database.main_of(12))

  def test_the_sole_account_of_a_person_may_be_moved_away(self):
    table, database, _ = build_table()
    seed_person(database, 12)
    seed_person(database, 20)
    seed_account(database, "acc-only", 12, "main")

    table.assign_account(
      owner_user_id="acc-only", role="alt", person_id=20, allow_move=True
    )

    self.assertEqual(
      database.person_account[(PLATFORM, "acc-only")]["person_id"], 20
    )
    self.assertEqual(database.accounts_of(12), [])

  def test_demoting_an_account_that_is_not_the_main_is_untouched(self):
    table, database, _ = build_table()
    seed_person(database, 12)
    seed_account(database, "acc-main", 12, "main")
    seed_account(database, "acc-alt", 12, "alt")

    table.assign_account(owner_user_id="acc-alt", role="matrix", person_id=12)

    self.assertEqual(database.main_of(12)["owner_user_id"], "acc-main")
    self.assertEqual(
      database.person_account[(PLATFORM, "acc-alt")]["role"], "matrix"
    )

  def test_moving_a_sub_account_away_is_untouched(self):
    table, database, _ = build_table()
    seed_person(database, 12)
    seed_person(database, 20)
    seed_account(database, "acc-main", 12, "main")
    seed_account(database, "acc-alt", 12, "alt")

    table.assign_account(
      owner_user_id="acc-alt", role="alt", person_id=20, allow_move=True
    )

    self.assertEqual(database.main_of(12)["owner_user_id"], "acc-main")

  def test_a_person_left_with_another_main_is_untouched(self):
    """Rows written before this rule existed can hold two mains.

    Demoting one of them leaves a main behind, so the folder relationship the
    guard protects survives - and refusing would make the pre-existing mess
    impossible to clean up.
    """
    table, database, _ = build_table()
    seed_person(database, 12)
    seed_account(database, "acc-main", 12, "main")
    seed_account(database, "acc-second", 12, "main")
    seed_account(database, "acc-alt", 12, "alt")

    table.assign_account(owner_user_id="acc-second", role="alt", person_id=12)

    self.assertEqual(database.main_of(12)["owner_user_id"], "acc-main")

  def test_replace_main_is_not_blocked_by_the_guard(self):
    """The one legitimate way to change main.

    The old main is demoted and the new one promoted in the same transaction,
    so the person is never - not even between two statements - without one.
    """
    table, database, _ = build_table()
    seed_person(database, 12)
    seed_account(database, "acc-main", 12, "main")
    seed_account(database, "acc-alt", 12, "alt")

    table.assign_account(
      owner_user_id="acc-new", role="main", person_id=12, demote_main_to="alt"
    )

    self.assertEqual(database.main_of(12)["owner_user_id"], "acc-new")
    self.assertEqual(
      database.person_account[(PLATFORM, "acc-main")]["role"], "alt"
    )

  def test_re_sending_the_main_as_main_is_not_blocked(self):
    table, database, _ = build_table()
    seed_person(database, 12)
    seed_account(database, "acc-main", 12, "main")
    seed_account(database, "acc-alt", 12, "alt")

    table.assign_account(owner_user_id="acc-main", role="main", person_id=12)

    self.assertEqual(database.main_of(12)["owner_user_id"], "acc-main")


##
## >>============================= repeating an assignment =============================>>
##
class IdempotentIdentityRefreshTest(unittest.TestCase):
  """Repeating an assignment changes no relationship, and still refreshes who
  the account is.

  These are two different facts about two different tables, and collapsing them
  loses one.  "This account belongs to this person in this role" is already
  true, so re-asserting it must not move anything.  "This account is called X"
  came from a resolution made seconds ago and may well be newer than what
  ``share_url`` holds - a renamed owner, or an account marked by link before it
  had ever been downloaded and so never had a ``sec_user_id`` at all.

  Refusing to write the second because the first was unchanged is how a user
  ends up re-pasting a link, watching it succeed, and seeing the same stale
  nickname on the page.
  """

  def existing_relationship(self, nickname="旧昵称", sec_user_id=None):
    database = FakeDatabase()
    seed_person(database, 12, display_name="李四")
    seed_account(database, "acc-1", 12, "alt", nickname=nickname)
    database.share_url["acc-1"]["sec_user_id"] = sec_user_id
    return database

  def test_the_identity_is_refreshed(self):
    database = self.existing_relationship()
    table, _, _ = build_table(database=database)

    table.assign_account(
      owner_user_id="acc-1",
      role="alt",
      person_id=12,
      sec_user_id="new-sec",
      nickname="新昵称",
    )

    self.assertEqual(database.share_url["acc-1"]["nickname"], "新昵称")
    self.assertEqual(database.share_url["acc-1"]["sec_user_id"], "new-sec")

  def test_the_relationship_is_not_rewritten(self):
    database = self.existing_relationship()
    table, _, connection = build_table(database=database)

    table.assign_account(
      owner_user_id="acc-1", role="alt", person_id=12, nickname="新昵称"
    )

    ##
    ## The identity upsert, and nothing else.  No attach, no role update, no
    ## person insert, no demotion.
    ##
    writes = [
      text.split(" ")[0] + " " + text.split(" ")[2]
      for text, _ in connection.calls
      if text.startswith(("INSERT", "UPDATE"))
    ]
    self.assertEqual(writes, ["INSERT share_url"])

  def test_the_person_is_not_renamed_to_follow_the_nickname(self):
    """A person's name is theirs.  Somebody called the person 李四; the account
    changing its display name on douyin says nothing about that, and renaming
    is ``PATCH /api/person/<id>``.
    """
    database = self.existing_relationship()
    table, _, _ = build_table(database=database)

    table.assign_account(
      owner_user_id="acc-1", role="alt", person_id=12, nickname="新昵称"
    )

    self.assertEqual(database.person[12]["display_name"], "李四")

  def test_the_result_still_reports_the_relationship(self):
    database = self.existing_relationship()
    table, _, _ = build_table(database=database)

    result = table.assign_account(
      owner_user_id="acc-1", role="alt", person_id=12, nickname="新昵称"
    )

    self.assertEqual(result["person_id"], 12)
    self.assertEqual(result["role"], "alt")
    self.assertFalse(result["created_person"])
    self.assertEqual(result["display_name"], "李四")

  def test_a_missing_value_does_not_blank_what_is_stored(self):
    """The upsert coalesces, so a resolution that could not read a nickname
    leaves the stored one alone rather than erasing it."""
    database = self.existing_relationship(sec_user_id="old-sec")
    table, _, _ = build_table(database=database)

    table.assign_account(
      owner_user_id="acc-1", role="alt", person_id=12,
      sec_user_id=None, nickname=None,
    )

    self.assertEqual(database.share_url["acc-1"]["nickname"], "旧昵称")
    self.assertEqual(database.share_url["acc-1"]["sec_user_id"], "old-sec")

  def test_it_is_still_one_transaction(self):
    database = self.existing_relationship()
    table, _, connection = build_table(database=database)

    table.assign_account(
      owner_user_id="acc-1", role="alt", person_id=12, nickname="新昵称"
    )

    self.assertEqual(connection.begins, 1)
    self.assertEqual(connection.commits, 1)
    self.assertEqual(connection.rollbacks, 0)

  def test_a_failed_refresh_leaves_the_relationship_and_the_old_identity(self):
    """Nothing is half-applied, even when the only write is one statement."""
    database = self.existing_relationship(sec_user_id="old-sec")
    table, _, connection = build_table(
      database=database, fail_on="INSERT INTO share_url"
    )

    with self.assertRaises(RuntimeError):
      table.assign_account(
        owner_user_id="acc-1", role="alt", person_id=12,
        sec_user_id="new-sec", nickname="新昵称",
      )

    self.assertEqual(database.share_url["acc-1"]["nickname"], "旧昵称")
    self.assertEqual(database.share_url["acc-1"]["sec_user_id"], "old-sec")
    self.assertEqual(
      database.person_account[(PLATFORM, "acc-1")], {
        "platform": PLATFORM, "owner_user_id": "acc-1",
        "person_id": 12, "role": "alt",
      }
    )
    self.assertEqual(connection.commits, 0)
    self.assertEqual(connection.rollbacks, 1)

  def test_re_sending_a_main_refreshes_its_identity_too(self):
    database = FakeDatabase()
    seed_person(database, 12)
    seed_account(database, "acc-main", 12, "main", nickname="旧昵称")
    table, _, _ = build_table(database=database)

    table.assign_account(
      owner_user_id="acc-main", role="main", person_id=12, nickname="新昵称"
    )

    self.assertEqual(database.share_url["acc-main"]["nickname"], "新昵称")
    self.assertEqual(database.main_of(12)["owner_user_id"], "acc-main")


##
## >>============================= unmarking an account =============================>>
##
class GuardedDetachTest(unittest.TestCase):
  """Detaching is the other way a person can lose its last main.

  Hardening only the assignment path would have been theatre: the person page
  has an "unmark" button next to every account, and it reaches the same rows by
  a shorter road.  So detaching answers to the same rule, decided in the same
  kind of transaction, with the person locked first.
  """

  def person_with_sibling(self):
    database = FakeDatabase()
    seed_person(database, 12, display_name="李四")
    seed_account(database, "acc-main", 12, "main", nickname="主号")
    seed_account(database, "acc-alt", 12, "alt", nickname="小号")
    return database

  def test_a_sub_account_is_detached(self):
    database = self.person_with_sibling()
    table, _, _ = build_table(database=database)

    table.detach_account_guarded(PLATFORM, "acc-alt")

    self.assertNotIn((PLATFORM, "acc-alt"), database.person_account)
    self.assertEqual(database.main_of(12)["owner_user_id"], "acc-main")

  def test_detaching_the_only_main_of_a_person_with_siblings_is_refused(self):
    database = self.person_with_sibling()
    table, _, _ = build_table(database=database)

    with self.assertRaises(LastMainRemoval) as caught:
      table.detach_account_guarded(PLATFORM, "acc-main")

    self.assertEqual(caught.exception.person_id, 12)
    self.assertEqual(caught.exception.display_name, "李四")
    self.assertEqual(caught.exception.owner_user_id, "acc-main")

  def test_a_refused_detach_leaves_the_row_in_place(self):
    database = self.person_with_sibling()
    table, _, connection = build_table(database=database)

    with self.assertRaises(LastMainRemoval):
      table.detach_account_guarded(PLATFORM, "acc-main")

    self.assertIn((PLATFORM, "acc-main"), database.person_account)
    self.assertEqual(connection.commits, 0)
    self.assertEqual(connection.rollbacks, 1)

  def test_the_sole_account_of_a_person_may_be_detached(self):
    """Nothing was aligned to it, so unmarking it puts the account back exactly
    where it already was - which is what unmarking is supposed to mean."""
    database = FakeDatabase()
    seed_person(database, 12)
    seed_account(database, "acc-only", 12, "main")
    table, _, _ = build_table(database=database)

    table.detach_account_guarded(PLATFORM, "acc-only")

    self.assertEqual(database.accounts_of(12), [])

  def test_detaching_a_main_that_is_not_the_last_is_allowed(self):
    database = self.person_with_sibling()
    seed_account(database, "acc-second", 12, "main")
    table, _, _ = build_table(database=database)

    table.detach_account_guarded(PLATFORM, "acc-second")

    self.assertEqual(database.main_of(12)["owner_user_id"], "acc-main")

  def test_detaching_an_account_nobody_marked_says_so(self):
    """Rather than reporting a success that removed nothing - which is how a
    page ends up showing an account as unmarked when it never was."""
    table, database, _ = build_table()

    with self.assertRaises(NotAttached):
      table.detach_account_guarded(PLATFORM, "acc-unknown")

  def test_the_person_is_locked_before_the_account(self):
    """The same order the assignment takes them in.

    This test used to assert the opposite, and the opposite was a bug: detach
    locked the account to find out which person to lock, giving it the order
    account -> person while every assignment takes person -> account.  Two
    requests on the same pair of rows would each have held what the other was
    waiting for.

    The account is still *read* first - it is what names the person - but that
    read takes no lock, and the account is locked afterwards and re-checked.
    """
    database = self.person_with_sibling()
    table, _, connection = build_table(database=database)

    table.detach_account_guarded(PLATFORM, "acc-alt")

    order = [
      "person" if "FROM person WHERE person_id" in text else "account"
      for text, _ in connection.calls
      if "FOR UPDATE" in text
    ]
    self.assertEqual(order, ["person", "account"])

  def test_an_account_that_moves_mid_detach_is_refused_rather_than_guessed(self):
    """The window the unlocked discovery read leaves open.

    Whoever moved it holds locks this transaction does not, so carrying on would
    decide the last-main question against a person nobody here is holding still.
    """
    database = self.person_with_sibling()
    seed_person(database, 20)
    table, _, connection = build_table(database=database)

    real_execute = FakeCursor.execute
    moved = []

    def execute(self, sql, params=None):
      real_execute(self, sql, params)
      ##
      ## Simulate another transaction committing a move in the gap between the
      ## discovery read and the lock.
      ##
      if "FROM person WHERE person_id" in " ".join(sql.split()) and not moved:
        moved.append(True)
        database.person_account[(PLATFORM, "acc-alt")]["person_id"] = 20

    FakeCursor.execute = execute
    try:
      with self.assertRaises(AssignmentRaced):
        table.detach_account_guarded(PLATFORM, "acc-alt")
    finally:
      FakeCursor.execute = real_execute

    self.assertIn((PLATFORM, "acc-alt"), database.person_account)
    self.assertEqual(connection.commits, 0)

  def test_the_write_guard_is_consulted(self):
    database = self.person_with_sibling()
    table, _, connection = build_table(database=database, write_ready=False)

    with self.assertRaises(RuntimeError):
      table.detach_account_guarded(PLATFORM, "acc-alt")

    self.assertEqual(connection.calls, [])
    self.assertIn((PLATFORM, "acc-alt"), database.person_account)

  def test_it_is_one_transaction(self):
    database = self.person_with_sibling()
    table, _, connection = build_table(database=database)

    table.detach_account_guarded(PLATFORM, "acc-alt")

    self.assertEqual(connection.begins, 1)
    self.assertEqual(connection.commits, 1)


##
## >>============================= the database's own refusal =============================>>
##
class DatabaseMainConstraintTest(unittest.TestCase):
  """What happens when the schema, not this method, is the one that says no.

  The transaction below already refuses a second main, so in normal running the
  unique index never fires.  It fires for the writes this method did not make -
  and for anything that manages to slip past the checks - and when it does, the
  user should still get the sentence that explains their situation rather than
  "server error".

  Classified by the index's own name, which is ours and stable.  Not by the
  driver's message text: that is English prose written by MySQL, it differs
  between versions, and a business decision taken by matching on it would break
  silently the day it was reworded.
  """

  DUPLICATE_KEY = 1062

  def failing_table(self, errno, message):
    import pymysql

    table, database, connection = build_table()
    seed_person(database, 12)

    real_execute = FakeCursor.execute

    def execute(cursor, sql, params=None):
      if " ".join(sql.split()).startswith("INSERT INTO person_account"):
        raise pymysql.err.IntegrityError(errno, message)
      real_execute(cursor, sql, params)

    FakeCursor.execute = execute
    self.addCleanup(setattr, FakeCursor, "execute", real_execute)
    return table, database, connection

  def test_a_duplicate_main_from_the_database_reads_as_a_main_conflict(self):
    table, _, connection = self.failing_table(
      self.DUPLICATE_KEY,
      "Duplicate entry '12' for key "
      "'person_account.uq_person_account_main_person'",
    )

    with self.assertRaises(MainAlreadyAssigned):
      table.assign_account(owner_user_id="acc-2", role="main", person_id=12)

    self.assertEqual(connection.rollbacks, 1)

  def test_it_says_nothing_it_does_not_know(self):
    """The transaction is gone, so which account holds the main cannot be read.

    Reported as absent rather than guessed: the page shows the plain refusal and
    offers no "replace the main" button, because it has nothing to replace
    against.
    """
    table, _, _ = self.failing_table(
      self.DUPLICATE_KEY,
      "Duplicate entry '12' for key "
      "'person_account.uq_person_account_main_person'",
    )

    with self.assertRaises(MainAlreadyAssigned) as caught:
      table.assign_account(owner_user_id="acc-2", role="main", person_id=12)

    self.assertIsNone(caught.exception.owner_user_id)
    self.assertIsNone(caught.exception.nickname)

  def test_a_duplicate_on_a_different_key_is_not_a_main_conflict(self):
    """The primary key fires 1062 too.  Reading every duplicate as "this person
    already has a main" would explain the wrong thing."""
    import pymysql

    table, _, _ = self.failing_table(
      self.DUPLICATE_KEY,
      "Duplicate entry 'douyin-acc-2' for key 'person_account.PRIMARY'",
    )

    with self.assertRaises(pymysql.err.IntegrityError):
      table.assign_account(owner_user_id="acc-2", role="main", person_id=12)

  def test_another_integrity_failure_is_not_reinterpreted(self):
    """A foreign key violation is not a main conflict, and pretending otherwise
    would send somebody looking at the wrong thing."""
    import pymysql

    table, _, _ = self.failing_table(
      1452, "Cannot add or update a child row: a foreign key constraint fails"
    )

    with self.assertRaises(pymysql.err.IntegrityError):
      table.assign_account(owner_user_id="acc-2", role="main", person_id=12)

  def test_the_failure_is_never_swallowed(self):
    """However it is classified, it is still a failure - nothing may report the
    assignment as done."""
    table, database, connection = self.failing_table(
      self.DUPLICATE_KEY,
      "Duplicate entry '12' for key "
      "'person_account.uq_person_account_main_person'",
    )

    with self.assertRaises(Exception):
      table.assign_account(owner_user_id="acc-2", role="main", person_id=12)

    self.assertEqual(connection.commits, 0)
    self.assertEqual(database.person_account, {})


##
## >>============================= lock order =============================>>
##
class LockOrderTest(unittest.TestCase):
  """Every path takes the person before the account.  Always that way round.

  Two transactions taking one pair of locks in opposite orders is a deadlock,
  and it does not announce itself in testing - it needs two requests to arrive
  at the same instant on the same rows.  So the order is asserted rather than
  observed.

  Detaching is the awkward one: the account row is what says *which* person to
  lock, so it has to be read first.  It is read without a lock, the person is
  locked on the strength of it, and then the account is locked and re-checked -
  which is what makes the unlocked read safe to have made.
  """

  def locking_order(self, connection):
    return [
      "person" if "FROM person WHERE person_id" in text else "account"
      for text, _ in connection.calls
      if "FOR UPDATE" in text
    ]

  def test_an_assignment_locks_the_person_first(self):
    table, database, connection = build_table()
    seed_person(database, 12)

    table.assign_account(owner_user_id="acc-2", role="alt", person_id=12)

    self.assertEqual(self.locking_order(connection)[0], "person")

  def test_a_detach_locks_the_person_first(self):
    database = FakeDatabase()
    seed_person(database, 12)
    seed_account(database, "acc-main", 12, "main")
    seed_account(database, "acc-alt", 12, "alt")
    table, _, connection = build_table(database=database)

    table.detach_account_guarded(PLATFORM, "acc-alt")

    self.assertEqual(self.locking_order(connection)[0], "person")

  def test_a_detach_discovers_the_person_without_locking(self):
    """The read that decides which person to lock cannot itself be a lock -
    that is the cycle this whole ordering exists to avoid."""
    database = FakeDatabase()
    seed_person(database, 12)
    seed_account(database, "acc-main", 12, "main")
    seed_account(database, "acc-alt", 12, "alt")
    table, _, connection = build_table(database=database)

    table.detach_account_guarded(PLATFORM, "acc-alt")

    first = connection.calls[0][0]
    self.assertIn("FROM person_account", first)
    self.assertNotIn("FOR UPDATE", first)

  def test_a_detach_locks_the_account_after_the_person(self):
    database = FakeDatabase()
    seed_person(database, 12)
    seed_account(database, "acc-main", 12, "main")
    seed_account(database, "acc-alt", 12, "alt")
    table, _, connection = build_table(database=database)

    table.detach_account_guarded(PLATFORM, "acc-alt")

    self.assertEqual(self.locking_order(connection), ["person", "account"])

  def test_a_move_locks_the_person_it_takes_the_account_from(self):
    """The source person's account counts decide whether the move is allowed,
    and a count read without that person's lock is a guess about a moment that
    has already passed."""
    database = FakeDatabase()
    seed_person(database, 12)
    seed_person(database, 20)
    seed_account(database, "acc-1", 12, "alt")
    table, _, connection = build_table(database=database)

    table.assign_account(
      owner_user_id="acc-1", role="alt", person_id=20, allow_move=True
    )

    locked = [
      params[0] for text, params in connection.calls
      if "FROM person WHERE person_id" in text and "FOR UPDATE" in text
    ]
    self.assertIn(12, locked)
    self.assertIn(20, locked)

  def test_two_people_are_locked_in_a_fixed_order(self):
    """Ascending id, whichever of the two the request happens to name.

    A move locks two people.  If one request took them target-first and another
    took them source-first, two moves swapping a pair of accounts would deadlock
    against each other.
    """
    for target, source in ((20, 12), (12, 20)):
      database = FakeDatabase()
      seed_person(database, 12)
      seed_person(database, 20)
      seed_account(database, "acc-1", source, "alt")
      table, _, connection = build_table(database=database)

      table.assign_account(
        owner_user_id="acc-1", role="alt", person_id=target, allow_move=True
      )

      locked = [
        params[0] for text, params in connection.calls
        if "FROM person WHERE person_id" in text and "FOR UPDATE" in text
      ]
      self.assertEqual(locked, sorted(locked))


class ConcurrentMoveOfALastMainTest(unittest.TestCase):
  """Moving a person's only main away, while somebody attaches to that person.

  Without the source person's lock both transactions read a world in which the
  other has not happened: the move sees one account and lets the main go, the
  attach sees a main and aligns the new account onto its folder.  Both commit,
  and the person is left holding an account that files under a folder belonging
  to somebody who is no longer theirs - the exact state the guard exists to
  prevent, reached by two operations that were each individually allowed.
  """

  def test_no_account_is_left_filing_under_a_main_that_left(self):
    """The only outcome that is actually forbidden.

    A person ending up with just an alt is fine - that is the ordinary
    alt-only person.  What must never happen is an account carrying a folder
    that was copied off a main which then walked away: the folder it used to
    have is gone from the database, so nothing can put it back.

    Both interleavings are acceptable on their own.  Either the attach happens
    first and the move is refused because the person now has two accounts, or
    the move happens first and the attach aligns nothing because there is no
    main left.  It is the overlap that is not.
    """
    database = FakeDatabase()
    database.count_barrier = threading.Barrier(2)
    seed_person(database, 12, display_name="李四")
    seed_person(database, 20, display_name="王五")
    seed_account(
      database, "acc-main", 12, "main", directory_name="主号目录"
    )
    database.share_url["acc-new"] = {
      "owner_user_id": "acc-new",
      "sec_user_id": None,
      "nickname": None,
      "directory_name": "新号自己的目录",
    }

    def move_the_main():
      table, _, _ = build_table(database=database)
      try:
        table.assign_account(
          owner_user_id="acc-main", role="alt", person_id=20, allow_move=True
        )
      except AssignmentConflict:
        pass

    def attach_a_sibling():
      table, _, _ = build_table(database=database)
      try:
        table.assign_account(owner_user_id="acc-new", role="alt", person_id=12)
      except AssignmentConflict:
        pass

    threads = [
      threading.Thread(target=move_the_main),
      threading.Thread(target=attach_a_sibling),
    ]
    for thread in threads:
      thread.start()
    for thread in threads:
      thread.join(timeout=10)

    aligned_onto_the_main = (
      database.share_url["acc-new"]["directory_name"] == "主号目录"
    )
    if aligned_onto_the_main:
      main = database.main_of(12)
      self.assertIsNotNone(
        main,
        "acc-new was aligned onto 主号目录 and then person 12 lost that main - "
        "its own folder is now unrecoverable",
      )
      self.assertEqual(main["owner_user_id"], "acc-main")


##
## >>============================= atomicity =============================>>
##
class AtomicityTest(unittest.TestCase):
  """What a failure half way through is allowed to leave behind: nothing.

  These are the tests the fake exists for.  Each injects a failure at a named
  statement and then reads the committed rows, so what is being checked is the
  state a rollback really leaves rather than which calls were made.
  """

  def test_a_failure_attaching_the_account_creates_no_person(self):
    table, database, connection = build_table(fail_on="INSERT INTO person_account")

    with self.assertRaises(RuntimeError):
      table.assign_account(
        owner_user_id="acc-1", role="main", display_name="张三"
      )

    self.assertEqual(database.person, {})
    self.assertEqual(database.person_account, {})
    self.assertEqual(database.share_url, {})
    self.assertEqual(connection.commits, 0)
    self.assertEqual(connection.rollbacks, 1)

  def test_a_failure_attaching_leaves_no_identity_row_either(self):
    """The identity is written first, so it is the one most likely to survive
    a partial write - and an identity row for an account nobody ended up
    marking is exactly the litter this method exists to avoid."""
    table, database, connection = build_table(fail_on="INSERT INTO person_account")

    with self.assertRaises(RuntimeError):
      table.assign_account(
        owner_user_id="acc-1",
        role="alt",
        display_name="张三",
        nickname="主播甲",
      )

    self.assertNotIn("acc-1", database.share_url)

  def test_a_failure_aligning_undoes_the_attachment(self):
    table, database, connection = build_table(fail_on="UPDATE share_url AS s")

    with self.assertRaises(RuntimeError):
      table.assign_account(
        owner_user_id="acc-1", role="main", display_name="张三"
      )

    self.assertEqual(database.person, {})
    self.assertEqual(database.person_account, {})

  def test_a_failure_promoting_the_new_main_does_not_demote_the_old_one(self):
    """Half a replacement is worse than none: the person is left with no main
    at all, and every download of theirs changes folder."""
    table, database, connection = build_table(fail_on="INSERT INTO person_account")
    seed_person(database, 12)
    seed_account(database, "acc-1", 12, "main")

    with self.assertRaises(RuntimeError):
      table.assign_account(
        owner_user_id="acc-2", role="main", person_id=12, demote_main_to="alt"
      )

    self.assertEqual(database.person_account[(PLATFORM, "acc-1")]["role"], "main")
    self.assertNotIn((PLATFORM, "acc-2"), database.person_account)
    self.assertEqual(database.main_of(12)["owner_user_id"], "acc-1")

  def test_a_failure_demoting_the_old_main_does_not_promote_the_new_one(self):
    """The other half.  Both applied would be two mains - the one state this
    whole method exists to make impossible."""
    table, database, connection = build_table(
      fail_on="UPDATE person_account SET role"
    )
    seed_person(database, 12)
    seed_account(database, "acc-1", 12, "main")

    with self.assertRaises(RuntimeError):
      table.assign_account(
        owner_user_id="acc-2", role="main", person_id=12, demote_main_to="alt"
      )

    mains = [
      row for row in database.person_account.values()
      if row["person_id"] == 12 and row["role"] == "main"
    ]
    self.assertEqual(len(mains), 1)
    self.assertEqual(mains[0]["owner_user_id"], "acc-1")

  def test_a_failure_moving_an_account_leaves_it_with_its_first_person(self):
    table, database, connection = build_table(fail_on="UPDATE share_url AS s")
    seed_person(database, 7)
    seed_person(database, 12)
    seed_account(database, "acc-2", 7, "alt")

    with self.assertRaises(RuntimeError):
      table.assign_account(
        owner_user_id="acc-2", role="alt", person_id=12, allow_move=True
      )

    self.assertEqual(database.person_account[(PLATFORM, "acc-2")]["person_id"], 7)

  def test_nothing_is_committed_before_the_end(self):
    """A commit in the middle would make every rollback above a lie."""
    table, database, connection = build_table()
    seed_person(database, 12)
    seed_account(database, "acc-1", 12, "main")

    table.assign_account(
      owner_user_id="acc-2", role="main", person_id=12, demote_main_to="alt"
    )

    ##
    ## Five writes - identity, demote, attach, align - under exactly one commit.
    ##
    writes = [
      text for text, _ in connection.calls
      if text.startswith(("INSERT", "UPDATE"))
    ]
    self.assertGreater(len(writes), 1)
    self.assertEqual(connection.commits, 1)

  def test_the_rollback_is_issued_by_this_method(self):
    """Not left to the pooled connection manager.

    The transaction is opened here, so it is closed here too - a caller that
    reaches for the connection differently one day must not silently lose the
    only thing keeping these rows consistent.
    """
    table, database, connection = build_table(fail_on="INSERT INTO person_account")

    with self.assertRaises(RuntimeError):
      table.assign_account(
        owner_user_id="acc-1", role="main", display_name="张三"
      )

    self.assertEqual(connection.rollbacks, 1)


##
## >>============================= locking =============================>>
##
class LockingTest(unittest.TestCase):
  """What the statements have to take, so the checks above mean something.

  Every conflict this method reports is decided by reading a row and then
  writing based on what it said.  Read without a lock, that is a guess about a
  moment that has already passed.
  """

  def test_the_target_person_is_locked_before_anything_is_decided(self):
    table, database, connection = build_table()
    seed_person(database, 12)

    table.assign_account(owner_user_id="acc-2", role="main", person_id=12)

    locking = [
      (text, params) for text, params in connection.calls
      if "FROM person WHERE person_id" in text and "FOR UPDATE" in text
    ]
    self.assertEqual(len(locking), 1)
    self.assertEqual(locking[0][1], (12,))

  def test_the_accounts_current_attachment_is_locked(self):
    table, database, connection = build_table()
    seed_person(database, 12)

    table.assign_account(owner_user_id="acc-2", role="alt", person_id=12)

    locking = [
      (text, params) for text, params in connection.calls
      if "FROM person_account WHERE platform" in text and "FOR UPDATE" in text
    ]
    self.assertEqual(len(locking), 1)
    self.assertEqual(locking[0][1], (PLATFORM, "acc-2"))

  def test_the_current_main_is_locked(self):
    table, database, connection = build_table()
    seed_person(database, 12)
    seed_account(database, "acc-1", 12, "main")

    with self.assertRaises(MainAlreadyAssigned):
      table.assign_account(owner_user_id="acc-2", role="main", person_id=12)

    locking = [
      text for text, _ in connection.calls
      if "FROM person_account WHERE person_id" in text
      and "role = 'main'" in text
      and "FOR UPDATE" in text
    ]
    self.assertEqual(len(locking), 1)

  def test_the_person_is_locked_before_the_account(self):
    """One order, everywhere.  Two requests taking the same two locks in
    opposite orders is a deadlock, and this method is the only thing that takes
    them."""
    table, database, connection = build_table()
    seed_person(database, 12)

    table.assign_account(owner_user_id="acc-2", role="main", person_id=12)

    order = [
      "person" if "FROM person WHERE person_id" in text else "account"
      for text, _ in connection.calls
      if "FOR UPDATE" in text
    ]
    self.assertEqual(order[0], "person")


class ConcurrentMainAssignmentTest(unittest.TestCase):
  """Two requests, one person, two different accounts, both asking for main.

  Read-then-write without a lock is the classic way to end up with two: both
  transactions see no main, and both insert one.  The fake holds its row locks
  from the ``SELECT ... FOR UPDATE`` that took them until the transaction ends,
  so this exercises the serialisation rather than asserting on a string.

  What this proves is the control flow, *given* those semantics; that MySQL
  provides them for ``SELECT ... FOR UPDATE`` under InnoDB is assumed, not
  tested here.
  """

  def _promote(self, database, owner_user_id, results, errors):
    table, _, connection = build_table(database=database)
    try:
      results.append(
        table.assign_account(
          owner_user_id=owner_user_id, role="main", person_id=12
        )
      )
    except AssignmentConflict as e:
      errors.append(e)

  def test_only_one_of_two_concurrent_promotions_succeeds(self):
    database = FakeDatabase()
    database.barrier = threading.Barrier(2)
    seed_person(database, 12)
    results = []
    errors = []

    threads = [
      threading.Thread(
        target=self._promote, args=(database, owner, results, errors)
      )
      for owner in ("acc-1", "acc-2")
    ]
    for thread in threads:
      thread.start()
    for thread in threads:
      thread.join(timeout=10)

    self.assertEqual(len(results), 1)
    self.assertEqual(len(errors), 1)
    self.assertIsInstance(errors[0], MainAlreadyAssigned)

  def _promote_known(self, database, owner_user_id, results, errors):
    """The legacy route's path: no receipt, no identity, same transaction."""
    table, _, _ = build_table(database=database)
    service = PersonAssignmentService(
      resolve_service=None,
      table_factory=lambda: table,
      identity_reader=None,
    )
    try:
      results.append(
        service.assign_known_account(
          owner_user_id=owner_user_id, person_id=12, role="main"
        )
      )
    except MainAccountConflict as e:
      errors.append(e)

  def test_the_older_endpoints_cannot_race_a_second_main_in_either(self):
    """Two known accounts, one person, both asking to be the main.

    Worth its own test rather than trusting that "it is the same transaction":
    the point of this step was that the older endpoints stopped having their own
    write path, and if one of them ever grows one again this is what notices.
    """
    database = FakeDatabase()
    database.barrier = threading.Barrier(2)
    seed_person(database, 12)
    for owner in ("acc-1", "acc-2"):
      database.share_url[owner] = {
        "owner_user_id": owner, "sec_user_id": None,
        "nickname": None, "directory_name": None,
      }
    results = []
    errors = []

    threads = [
      threading.Thread(
        target=self._promote_known, args=(database, owner, results, errors)
      )
      for owner in ("acc-1", "acc-2")
    ]
    for thread in threads:
      thread.start()
    for thread in threads:
      thread.join(timeout=10)

    self.assertEqual(len(results), 1)
    self.assertEqual(len(errors), 1)
    mains = [
      row for row in database.person_account.values()
      if row["person_id"] == 12 and row["role"] == "main"
    ]
    self.assertEqual(len(mains), 1)

  def test_the_person_ends_with_exactly_one_main(self):
    database = FakeDatabase()
    database.barrier = threading.Barrier(2)
    seed_person(database, 12)
    results = []
    errors = []

    threads = [
      threading.Thread(
        target=self._promote, args=(database, owner, results, errors)
      )
      for owner in ("acc-1", "acc-2")
    ]
    for thread in threads:
      thread.start()
    for thread in threads:
      thread.join(timeout=10)

    mains = [
      row for row in database.person_account.values()
      if row["person_id"] == 12 and row["role"] == "main"
    ]
    self.assertEqual(len(mains), 1)


if __name__ == "__main__":
  unittest.main()
