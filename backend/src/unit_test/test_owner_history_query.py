import unittest
from datetime import datetime, timedelta

from backend.src.database.query.owner_history import (
  LIVE_STATUS_LIVING,
  OwnerHistoryFilter,
  OwnerHistoryFilterError,
  OwnerHistoryQuery,
)


class FakeCursor:
  def __init__(self, results):
    self._results = results
    self.executed = []

  def execute(self, sql, params=None):
    self.executed.append((sql, params))

  def fetchone(self):
    return self._results.pop(0) if self._results else None

  def fetchall(self):
    return self._results.pop(0) if self._results else []

  def __enter__(self):
    return self

  def __exit__(self, *unused):
    return False


class FakeConnection:
  def __init__(self, cursor):
    self._cursor = cursor

  def cursor(self):
    return self._cursor

  def __enter__(self):
    return self

  def __exit__(self, *unused):
    return False


class FakeDatabase:
  def __init__(self, results):
    self.cursor = FakeCursor(results)

  def get_connection(self):
    return FakeConnection(self.cursor)


class OwnerHistoryFilterTest(unittest.TestCase):
  def test_page_size_is_clamped_to_the_limit_rather_than_rejected(self):
    owner_filter = OwnerHistoryFilter.from_mapping({"page_size": "999"}, 10)

    self.assertEqual(10, owner_filter.page_size)

  def test_missing_page_size_defaults_to_the_limit(self):
    self.assertEqual(10, OwnerHistoryFilter.from_mapping({}, 10).page_size)

  def test_sort_is_restricted_to_the_whitelist(self):
    with self.assertRaises(OwnerHistoryFilterError):
      OwnerHistoryFilter.from_mapping({"sort": "owner_user_id; DROP TABLE"}, 10)

  def test_order_is_restricted_to_asc_or_desc(self):
    with self.assertRaises(OwnerHistoryFilterError):
      OwnerHistoryFilter.from_mapping({"order": "sideways"}, 10)

  def test_score_bounds_are_validated(self):
    with self.assertRaises(OwnerHistoryFilterError):
      OwnerHistoryFilter.from_mapping({"score_min": "101"}, 10)
    with self.assertRaises(OwnerHistoryFilterError):
      OwnerHistoryFilter.from_mapping({"score_min": "80", "score_max": "20"}, 10)

  def test_unknown_last_live_window_is_rejected(self):
    with self.assertRaises(OwnerHistoryFilterError):
      OwnerHistoryFilter.from_mapping({"last_live_within": "3y"}, 10)

  def test_unknown_user_status_is_rejected(self):
    with self.assertRaises(OwnerHistoryFilterError):
      OwnerHistoryFilter.from_mapping({"user_status": "unknown"}, 10)

  def test_non_integer_page_is_reported_as_a_filter_error(self):
    with self.assertRaises(OwnerHistoryFilterError):
      OwnerHistoryFilter.from_mapping({"page": "second"}, 10)


class OwnerHistoryConditionTest(unittest.TestCase):
  def setUp(self):
    self.clock = lambda: datetime(2026, 8, 10, 12, 0, 0)
    self.query = OwnerHistoryQuery(FakeDatabase([]), clock=self.clock)

  def test_keyword_is_bound_as_a_parameter_with_escaped_wildcards(self):
    owner_filter = OwnerHistoryFilter.from_mapping({"q": "50%_a\\b"}, 10)

    clause, params = self.query._conditions(owner_filter)

    self.assertIn("s.nickname LIKE %s", clause)
    self.assertEqual(["%50\\%\\_a\\\\b%"], params)

  def test_last_live_window_requires_a_living_status_and_a_recent_timestamp(self):
    owner_filter = OwnerHistoryFilter.from_mapping({"last_live_within": "24h"}, 10)

    clause, params = self.query._conditions(owner_filter)

    self.assertIn("s.last_live_status = %s AND s.last_checked_at >= %s", clause)
    self.assertEqual(LIVE_STATUS_LIVING, params[0])
    self.assertEqual(self.clock() - timedelta(hours=24), params[1])

  def test_never_seen_live_is_written_null_safely(self):
    owner_filter = OwnerHistoryFilter.from_mapping({"last_live_within": "never"}, 10)

    clause, params = self.query._conditions(owner_filter)

    self.assertIn("s.last_checked_at IS NULL", clause)
    self.assertIn("s.last_live_status IS NULL", clause)
    self.assertEqual([LIVE_STATUS_LIVING], params)

  def test_no_filters_produce_no_where_clause(self):
    clause, params = self.query._conditions(OwnerHistoryFilter.from_mapping({}, 10))

    self.assertEqual("", clause)
    self.assertEqual([], params)


class OwnerHistorySearchTest(unittest.TestCase):
  def test_search_returns_the_total_and_the_requested_page(self):
    database = FakeDatabase([{"total": 42}, [{"owner_user_id": "1"}]])
    query = OwnerHistoryQuery(database)

    page = query.search(OwnerHistoryFilter.from_mapping({"page": "3"}, 10))

    self.assertEqual(42, page.total)
    self.assertEqual(3, page.page)
    self.assertEqual(10, page.page_size)
    self.assertEqual(({"owner_user_id": "1"},), page.items)

  def test_search_offsets_by_page_and_orders_deterministically(self):
    database = FakeDatabase([{"total": 0}, []])
    query = OwnerHistoryQuery(database)

    query.search(
      OwnerHistoryFilter.from_mapping(
        {"page": "4", "sort": "actived_count", "order": "asc"}, 10
      )
    )

    page_sql, page_params = database.cursor.executed[-1]
    self.assertIn("ORDER BY s.actived_count ASC, s.owner_user_id ASC", page_sql)
    self.assertEqual(10, page_params[-2])
    self.assertEqual(30, page_params[-1])

  def test_platform_parameter_leads_the_bound_values(self):
    database = FakeDatabase([{"total": 0}, []])
    query = OwnerHistoryQuery(database)

    query.search(OwnerHistoryFilter.from_mapping({"platform": "douyin", "q": "a"}, 10))

    _count_sql, count_params = database.cursor.executed[0]
    self.assertEqual("douyin", count_params[0])
    self.assertEqual("%a%", count_params[1])


class OwnerHistorySessionsTest(unittest.TestCase):
  def test_sessions_join_room_base_on_the_same_typed_room_id(self):
    database = FakeDatabase([[{"room_id": "7"}]])
    query = OwnerHistoryQuery(database)

    rows = query.sessions("owner-1", "douyin", 5)

    sql, params = database.cursor.executed[0]
    self.assertIn("rb.id = lr.room_id", sql)
    self.assertNotIn("CAST", sql.upper())
    self.assertEqual(("owner-1", "douyin", 5), params)
    self.assertEqual(({"room_id": "7"},), rows)

  def test_sessions_reject_a_missing_owner_or_an_empty_limit(self):
    query = OwnerHistoryQuery(FakeDatabase([]))

    with self.assertRaises(ValueError):
      query.sessions("", "douyin", 5)
    with self.assertRaises(ValueError):
      query.sessions("owner-1", "douyin", 0)


class OwnerHistoryLookupTest(unittest.TestCase):
  def test_live_share_urls_are_keyed_by_owner_and_skip_empty_input(self):
    database = FakeDatabase([[{"owner_user_id": "1", "live_share_url": "u"}]])
    query = OwnerHistoryQuery(database)

    self.assertEqual(dict(), query.live_share_urls([]))
    resolved = query.live_share_urls(["1", "2"])

    self.assertEqual("u", resolved["1"]["live_share_url"])
    self.assertNotIn("2", resolved)


if __name__ == "__main__":
  unittest.main()
