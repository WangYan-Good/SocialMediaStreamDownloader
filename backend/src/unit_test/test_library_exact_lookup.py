##<<Base>>
import unittest

##<<Third-part>>
from backend.src.database.query.library import LibraryQuery


##
## >>============================= exact, and scoped =============================>>
##
##
## The asset endpoints need one row, not a page.
##
## Reaching it by asking for a page of a hundred and searching in Python would
## be wrong twice over: it fetches rows nobody asked for, and it moves the
## ownership decision out of the database and into the interpreter, where the
## next person to edit the loop can quietly widen it.
##
## So: one statement, bound parameters, and the ownership join present in the
## SQL itself for the user-scoped variants.
##


class FakeCursor:
  def __init__(self, rows):
    self._rows = list(rows)
    self.statements = []
    self.parameters = []

  def execute(self, statement, params=None):
    self.statements.append(statement)
    self.parameters.append(params)

  def fetchone(self):
    return self._rows.pop(0) if self._rows else None

  def fetchall(self):
    rows, self._rows = self._rows, []
    return rows

  def __enter__(self):
    return self

  def __exit__(self, *_):
    return False


class FakeConnection:
  def __init__(self, cursor):
    self._cursor = cursor

  def cursor(self):
    return self._cursor

  def __enter__(self):
    return self

  def __exit__(self, *_):
    return False


class FakeDatabase:
  def __init__(self, rows):
    self.cursor = FakeCursor(rows)

  def get_connection(self):
    return FakeConnection(self.cursor)


POST_ROW = {
  "platform": "douyin",
  "aweme_id": "7657271784144009946",
  "owner_user_id": "5885",
  "sec_user_id": "MS4w",
  "aweme_type": "video",
  "desc": "一条作品",
  "create_time": None,
  "downloaded_at": None,
  "media_count": 1,
  "saved_count": 1,
  "save_dir": "/downloads/creator",
  "source": "api",
  "nickname": "某位主播",
  "directory_name": "某位主播",
  "person_id": None,
  "person_display_name": None,
}

RECORDING_ROW = {
  "recording_id": 7,
  "app_user_id": 3,
  "platform": "douyin",
  "room_id": "123",
  "owner_user_id": "5885",
  "title": "晚间直播",
  "protocol": "flv",
  "output_path": "/downloads/creator/live.flv",
  "started_at": None,
  "finished_at": None,
  "source": "task",
  "created_at": None,
  "nickname": "某位主播",
  "directory_name": "某位主播",
  "person_id": None,
  "person_display_name": None,
}


class TestPostExactLookup(unittest.TestCase):
  def test_the_global_lookup_returns_the_row(self):
    database = FakeDatabase([POST_ROW])

    found = LibraryQuery(database).post("douyin", "7657271784144009946")

    self.assertIsNotNone(found)
    self.assertEqual("7657271784144009946", found["aweme_id"])
    self.assertEqual("/downloads/creator", found["save_dir"])

  def test_a_missing_row_is_none_rather_than_an_error(self):
    database = FakeDatabase([])

    self.assertIsNone(LibraryQuery(database).post("douyin", "nope"))

  def test_it_binds_its_parameters(self):
    ##
    ## Never formatted into the statement. The aweme id reaches this from a url
    ## segment, and the whole package holds this invariant.
    ##
    database = FakeDatabase([POST_ROW])

    LibraryQuery(database).post("douyin", "7657271784144009946")

    statement = database.cursor.statements[0]
    self.assertIn("%s", statement)
    self.assertNotIn("7657271784144009946", statement)
    self.assertEqual(("douyin", "7657271784144009946"), database.cursor.parameters[0])

  def test_it_asks_for_exactly_one_row(self):
    database = FakeDatabase([POST_ROW])

    LibraryQuery(database).post("douyin", "7657271784144009946")

    self.assertIn("LIMIT 1", database.cursor.statements[0])

  def test_the_user_lookup_joins_the_ownership_relation(self):
    ##
    ## The ownership decision belongs in the statement. A query that fetched
    ## the row and compared in Python would be one refactor away from
    ## forgetting to.
    ##
    database = FakeDatabase([POST_ROW])

    LibraryQuery(database).post_for_user(3, "douyin", "7657271784144009946")

    statement = database.cursor.statements[0]
    self.assertIn("app_user_aweme_record", statement)
    self.assertEqual(
      (3, "douyin", "7657271784144009946"), database.cursor.parameters[0]
    )

  def test_the_global_lookup_does_not_join_ownership(self):
    ##
    ## Admin sees historical rows that predate ownership and belong to nobody.
    ##
    database = FakeDatabase([POST_ROW])

    LibraryQuery(database).post("douyin", "7657271784144009946")

    self.assertNotIn("app_user_aweme_record", database.cursor.statements[0])

  def test_a_user_id_must_be_a_positive_integer(self):
    ##
    ## The same guard the paged variants carry: a string here would be bound as
    ## one and silently match nothing, which reads as "no such resource"
    ## instead of a programming error.
    ##
    database = FakeDatabase([POST_ROW])
    query = LibraryQuery(database)

    for bad in (0, -1, "3", None, True):
      with self.assertRaises(ValueError):
        query.post_for_user(bad, "douyin", "x")


class TestRecordingExactLookup(unittest.TestCase):
  def test_the_global_lookup_returns_the_row(self):
    database = FakeDatabase([RECORDING_ROW])

    found = LibraryQuery(database).recording(7)

    self.assertIsNotNone(found)
    self.assertEqual(7, found["recording_id"])
    self.assertEqual("/downloads/creator/live.flv", found["output_path"])

  def test_a_missing_row_is_none(self):
    self.assertIsNone(LibraryQuery(FakeDatabase([])).recording(999))

  def test_it_binds_its_parameters(self):
    database = FakeDatabase([RECORDING_ROW])

    LibraryQuery(database).recording(7)

    self.assertIn("%s", database.cursor.statements[0])
    self.assertEqual((7,), database.cursor.parameters[0])

  def test_the_user_lookup_constrains_the_owner_in_sql(self):
    database = FakeDatabase([RECORDING_ROW])

    LibraryQuery(database).recording_for_user(3, 7)

    statement = database.cursor.statements[0]
    self.assertIn("app_user_id", statement)
    self.assertEqual((7, 3), database.cursor.parameters[0])

  def test_the_global_lookup_reaches_recordings_owned_by_nobody(self):
    ##
    ## app_user_id IS NULL rows predate ownership. Admin can see them; a user
    ## never can, because the user statement compares the column to their id.
    ##
    database = FakeDatabase([dict(RECORDING_ROW, app_user_id=None)])

    found = LibraryQuery(database).recording(7)

    self.assertIsNotNone(found)
    self.assertNotIn("app_user_id = %s", database.cursor.statements[0])

  def test_a_recording_id_must_be_a_positive_integer(self):
    query = LibraryQuery(FakeDatabase([RECORDING_ROW]))

    for bad in (0, -1, "7", None, True):
      with self.assertRaises(ValueError):
        query.recording(bad)

  def test_a_user_id_must_be_a_positive_integer(self):
    query = LibraryQuery(FakeDatabase([RECORDING_ROW]))

    for bad in (0, -1, "3", None, True):
      with self.assertRaises(ValueError):
        query.recording_for_user(bad, 7)


if __name__ == "__main__":
  unittest.main()
