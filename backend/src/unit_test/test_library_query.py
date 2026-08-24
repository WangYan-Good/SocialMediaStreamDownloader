import unittest

from backend.src.database.query.library import (
  LibraryFilterError,
  LibraryLiveFilter,
  LibraryPostFilter,
)


##
## The library is a read model over records the downloader already wrote.  Its
## filters are the whole trust boundary: everything a caller supplies becomes a
## bound parameter, and the only strings that ever reach the SQL text are the
## ones these classes mapped from a fixed whitelist.
##


class LibraryPostFilterTest(unittest.TestCase):
  def test_defaults_to_the_newest_downloads_first(self):
    post_filter = LibraryPostFilter.from_mapping({})

    self.assertEqual("downloaded_at", post_filter.sort)
    self.assertEqual("desc", post_filter.order)
    self.assertEqual(1, post_filter.page)
    self.assertEqual(25, post_filter.page_size)

  def test_page_size_is_clamped_rather_than_rejected(self):
    ##
    ## Clamped the way history clamps, so a caller asking for everything gets a
    ## large page instead of an error they cannot act on.
    ##
    post_filter = LibraryPostFilter.from_mapping({"page_size": "5000"})

    self.assertEqual(100, post_filter.page_size)

  def test_page_size_below_one_is_refused(self):
    with self.assertRaises(LibraryFilterError):
      LibraryPostFilter.from_mapping({"page_size": "0"})

  def test_page_below_one_is_refused(self):
    with self.assertRaises(LibraryFilterError):
      LibraryPostFilter.from_mapping({"page": "0"})

  def test_page_that_is_not_a_number_is_refused(self):
    with self.assertRaises(LibraryFilterError):
      LibraryPostFilter.from_mapping({"page": "second"})

  def test_sort_outside_the_whitelist_is_refused(self):
    ##
    ## The mutation this stops: passing the request string through to ORDER BY.
    ##
    with self.assertRaises(LibraryFilterError):
      LibraryPostFilter.from_mapping({"sort": "downloaded_at; DROP TABLE aweme_record"})

  def test_every_whitelisted_sort_is_accepted(self):
    for sort in ("downloaded_at", "create_time", "nickname", "aweme_id"):
      self.assertEqual(sort, LibraryPostFilter.from_mapping({"sort": sort}).sort)

  def test_order_outside_asc_desc_is_refused(self):
    with self.assertRaises(LibraryFilterError):
      LibraryPostFilter.from_mapping({"order": "sideways"})

  def test_aweme_type_is_limited_to_what_the_downloader_writes(self):
    self.assertEqual("video", LibraryPostFilter.from_mapping({"aweme_type": "video"}).aweme_type)
    self.assertEqual("image", LibraryPostFilter.from_mapping({"aweme_type": "image"}).aweme_type)
    with self.assertRaises(LibraryFilterError):
      LibraryPostFilter.from_mapping({"aweme_type": "livestream"})

  def test_completion_is_limited_to_complete_or_partial(self):
    self.assertEqual(
      "partial", LibraryPostFilter.from_mapping({"completion": "partial"}).completion
    )
    with self.assertRaises(LibraryFilterError):
      LibraryPostFilter.from_mapping({"completion": "missing"})

  def test_source_is_limited_to_the_two_routes_that_exist(self):
    self.assertEqual("api", LibraryPostFilter.from_mapping({"source": "api"}).source)
    self.assertEqual("html", LibraryPostFilter.from_mapping({"source": "html"}).source)
    with self.assertRaises(LibraryFilterError):
      LibraryPostFilter.from_mapping({"source": "guess"})

  def test_person_id_must_be_an_integer(self):
    self.assertEqual(12, LibraryPostFilter.from_mapping({"person_id": "12"}).person_id)
    with self.assertRaises(LibraryFilterError):
      LibraryPostFilter.from_mapping({"person_id": "somebody"})

  def test_only_the_platform_this_server_downloads_is_accepted(self):
    ##
    ## One platform is implemented.  Accepting another would answer with an
    ## empty page and read as "nothing downloaded" rather than "not supported".
    ##
    self.assertEqual("douyin", LibraryPostFilter.from_mapping({}).platform)
    with self.assertRaises(LibraryFilterError):
      LibraryPostFilter.from_mapping({"platform": "kuaishou"})

  def test_blank_text_filters_are_dropped_rather_than_matched_on(self):
    post_filter = LibraryPostFilter.from_mapping({"q": "   ", "owner_user_id": ""})

    self.assertIsNone(post_filter.keyword)
    self.assertIsNone(post_filter.owner_user_id)


class LibraryLiveFilterTest(unittest.TestCase):
  def test_defaults_to_the_newest_observation_first(self):
    live_filter = LibraryLiveFilter.from_mapping({})

    self.assertEqual("observed_at", live_filter.sort)
    self.assertEqual("desc", live_filter.order)
    self.assertEqual(25, live_filter.page_size)

  def test_every_whitelisted_sort_is_accepted(self):
    for sort in ("observed_at", "start_time", "finish_time", "nickname"):
      self.assertEqual(sort, LibraryLiveFilter.from_mapping({"sort": sort}).sort)

  def test_sort_outside_the_whitelist_is_refused(self):
    with self.assertRaises(LibraryFilterError):
      LibraryLiveFilter.from_mapping({"sort": "room_id"})

  def test_page_size_is_clamped(self):
    self.assertEqual(100, LibraryLiveFilter.from_mapping({"page_size": "400"}).page_size)

  def test_there_is_no_filter_for_whether_somebody_is_live_now(self):
    ##
    ## The library is a record of what was observed.  Whether a room is live at
    ## this moment is only answerable by a probe, and offering it here would
    ## invite the page to claim it.
    ##
    live_filter = LibraryLiveFilter.from_mapping({"live_now": "true"})

    self.assertFalse(hasattr(live_filter, "live_now"))


from backend.src.database.query.library import LibraryQuery


class FakeCursor:
  def __init__(self, results):
    self._results = list(results)
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


def post_row(**overrides):
  row = {
    "platform": "douyin",
    "aweme_id": "7300000000000000001",
    "owner_user_id": "58859666123",
    "sec_user_id": "MS4wLjAB",
    "nickname": "主播",
    "directory_name": "主播",
    "person_id": None,
    "person_display_name": None,
    "aweme_type": "video",
    "desc": "一条作品",
    "create_time": None,
    "downloaded_at": None,
    "media_count": 1,
    "saved_count": 1,
    "save_dir": "/data/主播",
    "source": "api",
  }
  row.update(overrides)
  return row


class LibraryPostQueryTest(unittest.TestCase):
  def _run(self, arguments, rows=None, total=3):
    database = FakeDatabase([{"total": total}, rows if rows is not None else []])
    query = LibraryQuery(database)
    page = query.posts(LibraryPostFilter.from_mapping(arguments))
    return (page, database.cursor.executed)

  def _run_scoped(self, app_user_id, arguments, rows=None, total=2):
    database = FakeDatabase([{"total": total}, rows if rows is not None else []])
    query = LibraryQuery(database)
    page = query.posts_for_user(
      app_user_id,
      LibraryPostFilter.from_mapping(arguments),
    )
    return (page, database.cursor.executed)

  def test_scoped_posts_join_the_relation_and_bind_server_user(self):
    _, executed = self._run_scoped(17, {})

    for sql, params in executed:
      self.assertIn("JOIN app_user_aweme_record uar", sql)
      self.assertIn("uar.app_user_id = %s", sql)
      self.assertIn(17, params)

  def test_scoped_posts_keep_filters_sort_total_and_pagination(self):
    page, executed = self._run_scoped(
      17,
      {
        "q": "绿萝",
        "aweme_type": "image",
        "completion": "partial",
        "source": "html",
        "sort": "aweme_id",
        "order": "asc",
        "page": "2",
        "page_size": "10",
      },
      total=27,
    )

    sql, params = executed[1]
    self.assertEqual(page.total, 27)
    self.assertIn("a.aweme_id LIKE", sql)
    self.assertIn("a.aweme_type = %s", sql)
    self.assertIn("a.saved_count < a.media_count", sql)
    self.assertIn("a.source = %s", sql)
    self.assertIn("ORDER BY a.aweme_id ASC", sql)
    self.assertEqual([10, 10], list(params)[-2:])

  def test_global_posts_do_not_require_an_ownership_relation(self):
    _, executed = self._run({})

    self.assertNotIn("app_user_aweme_record", executed[0][0])
    self.assertNotIn("app_user_aweme_record", executed[1][0])

  def test_counts_with_a_separate_query_rather_than_the_page_length(self):
    ##
    ## The mutation this stops: total = len(items).  A 25-row page out of 163
    ## would then report 25, and the pager would show one page.
    ##
    page, executed = self._run({}, rows=[post_row(), post_row(aweme_id="2")], total=163)

    self.assertEqual(163, page.total)
    self.assertEqual(2, len(page.items))
    self.assertIn("COUNT(*)", executed[0][0])

  def test_newest_download_first_by_default(self):
    _, executed = self._run({})
    page_sql = executed[1][0]

    self.assertIn("ORDER BY a.downloaded_at DESC", page_sql)

  def test_ordering_has_a_deterministic_tie_breaker(self):
    ##
    ## Two rows downloaded in the same millisecond must not be able to swap
    ## places between one page request and the next, or a row is shown twice and
    ## another never at all.
    ##
    _, executed = self._run({})
    page_sql = executed[1][0]
    tail = page_sql.split("ORDER BY")[1]

    self.assertIn("a.platform", tail)
    self.assertIn("a.aweme_id", tail)

  def test_sort_key_reaches_sql_only_through_the_whitelist(self):
    _, executed = self._run({"sort": "nickname", "order": "asc"})
    page_sql = executed[1][0]

    self.assertIn("ORDER BY s.nickname ASC", page_sql)

  def test_keyword_searches_the_four_things_a_person_would_type(self):
    _, executed = self._run({"q": "绿萝"})
    page_sql, params = executed[1]

    self.assertIn("a.aweme_id LIKE", page_sql)
    self.assertIn("a.`desc` LIKE", page_sql)
    self.assertIn("s.nickname LIKE", page_sql)
    self.assertIn("p.display_name LIKE", page_sql)
    self.assertEqual(4, list(params).count("%绿萝%"))

  def test_keyword_wildcards_are_escaped(self):
    _, executed = self._run({"q": "100%_x"})
    _, params = executed[1]

    self.assertIn("%100\\%\\_x%", list(params))

  def test_person_filter_is_bound(self):
    _, executed = self._run({"person_id": "12"})
    page_sql, params = executed[1]

    self.assertIn("pa.person_id = %s", page_sql)
    self.assertIn(12, list(params))

  def test_owner_filter_is_bound(self):
    _, executed = self._run({"owner_user_id": "58859666123"})
    page_sql, params = executed[1]

    self.assertIn("a.owner_user_id = %s", page_sql)
    self.assertIn("58859666123", list(params))

  def test_type_filter_is_bound(self):
    _, executed = self._run({"aweme_type": "image"})
    page_sql, params = executed[1]

    self.assertIn("a.aweme_type = %s", page_sql)
    self.assertIn("image", list(params))

  def test_source_filter_is_bound(self):
    _, executed = self._run({"source": "html"})
    page_sql, params = executed[1]

    self.assertIn("a.source = %s", page_sql)
    self.assertIn("html", list(params))

  def test_partial_means_fewer_saved_than_planned(self):
    _, executed = self._run({"completion": "partial"})
    page_sql = executed[1][0]

    self.assertIn("a.saved_count < a.media_count", page_sql)

  def test_complete_means_everything_planned_was_saved(self):
    _, executed = self._run({"completion": "complete"})
    page_sql = executed[1][0]

    self.assertIn("a.saved_count >= a.media_count", page_sql)

  def test_person_is_joined_so_unmerged_accounts_still_appear(self):
    ##
    ## Most downloaded accounts belong to no person at all.  An inner join here
    ## would silently hide them, and the library would be missing most of what
    ## was downloaded.
    ##
    _, executed = self._run({})
    page_sql = executed[1][0]

    self.assertIn("LEFT JOIN person_account", page_sql)
    self.assertIn("LEFT JOIN person ", page_sql)
    self.assertIn("LEFT JOIN share_url", page_sql)

  def test_pagination_offsets_by_whole_pages(self):
    _, executed = self._run({"page": "3", "page_size": "25"})
    _, params = executed[1]

    self.assertEqual([25, 50], list(params)[-2:])

  def test_rows_are_returned_in_the_order_the_server_produced_them(self):
    rows = [post_row(aweme_id="c"), post_row(aweme_id="a"), post_row(aweme_id="b")]
    page, _ = self._run({}, rows=rows)

    self.assertEqual(["c", "a", "b"], [item["aweme_id"] for item in page.items])

  def test_the_platform_is_bound_not_formatted(self):
    _, executed = self._run({})
    _, params = executed[1]

    self.assertIn("douyin", list(params))


def live_row(**overrides):
  row = {
    "observed_at": "2026-08-15 09:30:15.250",
    "platform": "douyin",
    "room_id": "7123",
    "owner_user_id": "58859666123",
    "nickname": "主播",
    "directory_name": "主播",
    "person_id": None,
    "person_display_name": None,
    "start_time": None,
    "finish_time": None,
    "status_code": 0,
  }
  row.update(overrides)
  return row


def room_row(**overrides):
  row = {
    "now": "2026-08-15 09:30:15.250",
    "id": "7123",
    "title": "晚间直播",
    "status": 4,
    "start_time": 1000,
  }
  row.update(overrides)
  return row


class LibraryLiveQueryTest(unittest.TestCase):
  def _run(self, arguments, rows=None, rooms=None, total=2):
    results = [{"total": total}, rows if rows is not None else []]
    if rooms is not None:
      results.append(rooms)
    database = FakeDatabase(results)
    query = LibraryQuery(database)
    page = query.lives(LibraryLiveFilter.from_mapping(arguments))
    return (page, database.cursor.executed)

  def test_newest_observation_first_by_default(self):
    _, executed = self._run({})

    self.assertIn("ORDER BY lr.`now` DESC", executed[1][0])

  def test_ordering_has_a_deterministic_tie_breaker(self):
    _, executed = self._run({})
    tail = executed[1][0].split("ORDER BY")[1]

    for column in ("lr.platform", "lr.owner_user_id", "lr.room_id"):
      self.assertIn(column, tail)

  def test_counts_with_a_separate_query(self):
    page, executed = self._run({}, rows=[live_row()], rooms=[], total=87)

    self.assertEqual(87, page.total)
    self.assertIn("COUNT(*)", executed[0][0])

  def test_keyword_searches_room_creator_person_and_title(self):
    _, executed = self._run({"q": "晚间"})
    page_sql, params = executed[1]

    self.assertIn("lr.room_id LIKE", page_sql)
    self.assertIn("s.nickname LIKE", page_sql)
    self.assertIn("p.display_name LIKE", page_sql)
    self.assertIn("rb.title LIKE", page_sql)
    self.assertIn("%晚间%", list(params))

  def test_person_and_owner_filters_are_bound(self):
    _, executed = self._run({"person_id": "12", "owner_user_id": "5885"})
    page_sql, params = executed[1]

    self.assertIn("pa.person_id = %s", page_sql)
    self.assertIn("lr.owner_user_id = %s", page_sql)
    self.assertIn(12, list(params))
    self.assertIn("5885", list(params))

  def test_pagination_offsets_by_whole_pages(self):
    _, executed = self._run({"page": "2", "page_size": "25"})

    self.assertEqual([25, 25], list(executed[1][1])[-2:])

  def test_one_live_record_stays_one_item_however_many_room_snapshots_exist(self):
    ##
    ## room_base is keyed on (now, id, start_time), so one live_record can match
    ## several room rows.  A plain join would multiply the record into as many
    ## library entries, which is a duplicate the pager cannot even count
    ## correctly - total comes from live_record, items would not.
    ##
    page, _ = self._run(
      {},
      rows=[live_row()],
      rooms=[
        room_row(start_time=1000, title="早些的标题"),
        room_row(start_time=2000, title="后来的标题"),
      ],
      total=1,
    )

    self.assertEqual(1, len(page.items))

  def test_the_newest_room_snapshot_wins_deterministically(self):
    page, _ = self._run(
      {},
      rows=[live_row()],
      rooms=[
        room_row(start_time=1000, title="早些的标题", status=2),
        room_row(start_time=2000, title="后来的标题", status=4),
      ],
      total=1,
    )

    self.assertEqual("后来的标题", page.items[0]["title"])
    self.assertEqual(4, page.items[0]["room_status"])

  def test_the_page_query_does_not_join_room_base_into_the_result(self):
    ##
    ## The room metadata is fetched separately precisely so the page query
    ## cannot fan out.  A LEFT JOIN room_base in the page statement would put
    ## the duplication back.
    ##
    _, executed = self._run({}, rows=[live_row()], rooms=[])
    page_sql = executed[1][0]

    self.assertNotIn("LEFT JOIN room_base", page_sql)

  def test_room_metadata_is_not_looked_up_when_the_page_is_empty(self):
    _, executed = self._run({}, rows=[])

    self.assertEqual(2, len(executed))

  def test_a_record_with_no_room_snapshot_still_appears(self):
    page, _ = self._run({}, rows=[live_row(room_id="9999")], rooms=[], total=1)

    self.assertEqual(1, len(page.items))
    self.assertIsNone(page.items[0]["title"])
    self.assertIsNone(page.items[0]["room_status"])

  def test_owner_without_a_person_still_appears(self):
    _, executed = self._run({})
    page_sql = executed[1][0]

    self.assertIn("LEFT JOIN person_account", page_sql)
    self.assertIn("LEFT JOIN person ", page_sql)
    self.assertIn("LEFT JOIN share_url", page_sql)

  def test_rows_are_returned_in_the_order_the_server_produced_them(self):
    rows = [live_row(room_id="c"), live_row(room_id="a"), live_row(room_id="b")]
    page, _ = self._run({}, rows=rows, rooms=[])

    self.assertEqual(["c", "a", "b"], [item["room_id"] for item in page.items])

  def test_a_room_row_nobody_asked_for_is_dropped(self):
    ##
    ## The lookup fetches by two IN lists and pairs them up here, so a row whose
    ## (now, id) combination was never requested can come back and must not be
    ## attached to anything.
    ##
    page, _ = self._run(
      {},
      rows=[live_row(room_id="7123", observed_at="A")],
      rooms=[
        room_row(now="B", id="7123", title="别人的快照"),
        room_row(now="A", id="7123", title="正确的快照"),
      ],
      total=1,
    )

    self.assertEqual("正确的快照", page.items[0]["title"])

  def test_the_room_lookup_binds_every_value(self):
    _, executed = self._run(
      {}, rows=[live_row(observed_at="A", room_id="7123")], rooms=[]
    )
    room_sql, params = executed[2]

    self.assertIn("rb.`now` IN (%s)", room_sql)
    self.assertIn("rb.id IN (%s)", room_sql)
    self.assertEqual(("A", "7123"), tuple(params))
