import unittest

from backend.src.database.table.person_identity import (
  DouyinPersonIdentityTable,
)


##
## The same fakes the rest of the table tests use: the real pool hands out
## pymysql's DictCursor, so a fake returning tuples would hide every KeyError
## until the query met a real database.
##
class FakeCursor:
  def __init__(self):
    self.calls = []
    self.rows = []
    self.lastrowid = 7

  def execute(self, sql, params=None):
    self.calls.append((" ".join(sql.split()), params))

  def fetchall(self):
    return self.rows

  def fetchone(self):
    return self.rows[0] if self.rows else None

  def __enter__(self):
    return self

  def __exit__(self, *unused):
    return False


class FakeConnection:
  def __init__(self, cursor):
    self._cursor = cursor
    self.commits = 0

  def cursor(self):
    return self._cursor

  def commit(self):
    self.commits += 1

  def __enter__(self):
    return self

  def __exit__(self, *unused):
    return False


def build_table(rows=()):
  table = DouyinPersonIdentityTable.__new__(DouyinPersonIdentityTable)
  cursor = FakeCursor()
  cursor.rows = list(rows)
  connection = FakeConnection(cursor)
  table.get_connection = lambda: connection
  table.require_write_ready = lambda: None
  return table, cursor


##
## >>============================= the lookup =============================>>
##
class AccountAssignmentLookupTest(unittest.TestCase):
  """Who holds one particular account, asked by that account's own id.

  This is what lets the page say "you already added this" *before* the user
  fills in a form that would only be refused.  It is an identity question, not
  a search: the answer decides whether somebody is offered a "create a new
  person" button, so matching approximately would be worse than not asking.
  """

  def test_an_account_nobody_has_downloaded_is_unknown(self):
    """``share_url`` is the register of accounts this program has heard of.

    No row there means this account is genuinely new, which is the only state
    in which the full create-a-person flow is the right thing to offer.
    """
    table, _ = build_table(rows=[])

    self.assertIsNone(table.get_account_assignment("acc-9"))

  def test_a_known_account_nobody_marked_reports_no_person(self):
    """"Known" and "assigned" are different facts, and the page shows different
    things for them: an account downloaded a year ago but never marked is not a
    duplicate, it is an account waiting to be filed."""
    table, _ = build_table(
      rows=[
        {
          "owner_user_id": "acc-9",
          "sec_user_id": "MS4wLjABAAAA",
          "nickname": "程儿",
          "person_id": None,
          "role": None,
          "display_name": None,
        }
      ]
    )

    found = table.get_account_assignment("acc-9")

    self.assertEqual(found["owner_user_id"], "acc-9")
    self.assertEqual(found["nickname"], "程儿")
    self.assertIsNone(found["person_id"])
    self.assertIsNone(found["role"])

  def test_an_assigned_account_reports_its_person_and_role(self):
    table, _ = build_table(
      rows=[
        {
          "owner_user_id": "acc-9",
          "sec_user_id": "MS4wLjABAAAA",
          "nickname": "程儿",
          "person_id": 12,
          "role": "main",
          "display_name": "程儿",
        }
      ]
    )

    found = table.get_account_assignment("acc-9")

    self.assertEqual(found["person_id"], 12)
    self.assertEqual(found["role"], "main")
    self.assertEqual(found["display_name"], "程儿")

  def test_the_person_is_reported_by_id_even_when_names_collide(self):
    """Two different people may share a display name, and the row that decides
    ownership is the account's own - never a name that matched."""
    table, _ = build_table(
      rows=[
        {
          "owner_user_id": "acc-9",
          "sec_user_id": None,
          "nickname": "小明",
          "person_id": 2,
          "role": "alt",
          "display_name": "小明",
        }
      ]
    )

    self.assertEqual(table.get_account_assignment("acc-9")["person_id"], 2)

  def test_the_account_is_matched_exactly_rather_than_searched(self):
    """Stated against the sql.

    ``search_accounts`` exists next door and matches nicknames with LIKE.
    Reaching for it here would make "is this account already mine?" answerable
    by somebody else's similar nickname, and the answer decides whether a second
    person gets created.
    """
    table, cursor = build_table(rows=[])

    table.get_account_assignment("acc-9")

    sql, params = cursor.calls[0]
    self.assertNotIn("LIKE", sql)
    self.assertNotIn("nickname =", sql)
    self.assertIn("s.owner_user_id = %s", sql)
    self.assertEqual(params, ("douyin", "acc-9"))

  def test_the_account_id_is_bound_rather_than_interpolated(self):
    table, cursor = build_table(rows=[])

    table.get_account_assignment("'; DROP TABLE person; --")

    sql, params = cursor.calls[0]
    self.assertNotIn("DROP TABLE", sql)
    self.assertEqual(params[1], "'; DROP TABLE person; --")

  def test_only_the_three_identity_tables_are_read(self):
    """One row per account, guaranteed by what is *not* joined.

    ``person_account`` is keyed on the account and ``person`` on its id, so this
    can only ever answer with one row.  Joining works or collaborations - both
    of which multiply against an account - would turn one account into several
    and make a duplicate look like several duplicates.
    """
    table, cursor = build_table(rows=[])

    table.get_account_assignment("acc-9")

    sql, _ = cursor.calls[0]
    self.assertIn("share_url", sql)
    self.assertIn("person_account", sql)
    self.assertIn("person", sql)
    self.assertNotIn("aweme_record", sql)
    self.assertNotIn("live_record", sql)
    self.assertNotIn("person_collaboration", sql)

  def test_the_attachment_is_matched_on_platform_as_well(self):
    """``person_account`` is keyed on the pair.  Matching the id alone would
    read another platform's row for the same number."""
    table, cursor = build_table(rows=[])

    table.get_account_assignment("acc-9")

    sql, _ = cursor.calls[0]
    self.assertIn("pa.platform = %s", sql)

  def test_nothing_is_locked_because_nothing_is_written_on_this_answer(self):
    """A read for the page's benefit.  The assignment transaction discovers
    ownership again, under its own locks, and is the only thing allowed to
    decide anything on it."""
    table, cursor = build_table(rows=[])

    table.get_account_assignment("acc-9")

    sql, _ = cursor.calls[0]
    self.assertNotIn("FOR UPDATE", sql)

  def test_the_lookup_writes_nothing(self):
    table, cursor = build_table(rows=[])
    connection = table.get_connection()

    table.get_account_assignment("acc-9")

    self.assertEqual(connection.commits, 0)
    for sql, _ in cursor.calls:
      for statement in ("INSERT", "UPDATE", "DELETE"):
        self.assertNotIn(statement, sql)

  def test_a_blank_account_id_asks_nothing(self):
    """There is no account to ask about, and a query with an empty string would
    match whatever row happens to carry one."""
    table, cursor = build_table(rows=[])

    self.assertIsNone(table.get_account_assignment("   "))
    self.assertEqual(cursor.calls, [])

  def test_a_missing_account_id_asks_nothing(self):
    table, cursor = build_table(rows=[])

    self.assertIsNone(table.get_account_assignment(None))
    self.assertEqual(cursor.calls, [])

  def test_surrounding_space_is_trimmed_rather_than_queried(self):
    table, cursor = build_table(rows=[])

    table.get_account_assignment("  acc-9  ")

    _, params = cursor.calls[0]
    self.assertEqual(params[1], "acc-9")


##
## >>============================= grain =============================>>
##
class ListingGrainTest(unittest.TestCase):
  """One row per thing, so no page has to de-duplicate what it is given.

  A Vue ``Set`` over these lists would have to pick a key, and every key that
  looks convenient is wrong: two people may share a display name, and two
  accounts may share a nickname.  So the grain is settled here, in the query.
  """

  def test_the_person_listing_reports_each_person_once(self):
    """It joins ``person_account`` twice - once to count, once to find the main
    account's folder - so without the grouping a person with three accounts
    would appear three times."""
    table, cursor = build_table(rows=[])

    table.list_persons()

    sql, _ = cursor.calls[0]
    self.assertIn("GROUP BY p.person_id", sql)

  def test_the_account_search_reports_each_account_once(self):
    """``share_url`` is keyed on the account and ``person_account`` on the
    platform pair, so the join can only match one attachment."""
    table, cursor = build_table(rows=[])

    table.search_accounts("程")

    sql, _ = cursor.calls[0]
    self.assertIn("pa.owner_user_id = s.owner_user_id", sql)
    self.assertIn("pa.platform = %s", sql)
    self.assertNotIn("aweme_record", sql)
    self.assertNotIn("person_collaboration", sql)

  def test_a_persons_accounts_are_listed_once_each(self):
    """One row per ``person_account`` row, which is one row per account.  A
    join onto the works or the recordings would report an account once per
    file it has produced."""
    table, cursor = build_table(rows=[])

    table.list_person_accounts(12)

    sql, _ = cursor.calls[0]
    self.assertNotIn("aweme_record", sql)
    self.assertNotIn("live_record", sql)
    self.assertNotIn("person_collaboration", sql)


if __name__ == "__main__":
  unittest.main()
