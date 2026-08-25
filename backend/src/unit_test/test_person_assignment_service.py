import unittest

from backend.src.database.table.person_identity import (
  AccountAttachedElsewhere,
  LastMainRemoval,
  MainAlreadyAssigned,
  PersonMissing,
  UnknownRole,
)
from backend.src.database.schema_guard import DatabaseWriteBlocked
from backend.src.platform.douyin.douyin_owner_identity import (
  DouyinOwnerIdentityReader,
)
from backend.src.platform.resource_resolution import (
  RESOURCE_TYPE_LIVE,
  RESOURCE_TYPE_OWNER,
  RESOURCE_TYPE_POST,
  ResourceResolution,
)
from backend.src.service.resource_resolve import (
  ResolveStore,
  ResourceResolveService,
)
from backend.src.service.person_assignment import (
  AccountAlreadyAttached,
  AssignmentUnavailable,
  InvalidAssignment,
  LastMainRemovalConflict,
  MainAccountConflict,
  OwnerIdentityUnavailable,
  PersonAssignmentError,
  PersonAssignmentResult,
  PersonAssignmentService,
  PersonLookupUnavailable,
  PersonNotFound,
  ResolutionNotFound,
)


##
## The ids from the real share links used during design verification.
##
SEC_UID = "MS4wLjABAAAAGZkW5n1EHZD_TFyQ-QiaISBPemtKFxVVdhLSeoXhh-U"
AWEME_ID = "7657271784144009946"

SHORT_LINK = "https://v.douyin.com/M-kmspLye0o/"
POST_URL = "https://www.douyin.com/video/" + AWEME_ID
OWNER_URL = "https://www.douyin.com/user/" + SEC_UID
LIVE_URL = "https://live.douyin.com/123456"

RESOLVE_ID = "receipt-1"
TEST_APP_USER_ID = 9001


def owner_resolution():
  return ResourceResolution(
    platform="douyin",
    resource_type=RESOURCE_TYPE_OWNER,
    source_url=SHORT_LINK,
    resolved_url=OWNER_URL,
    identity={"sec_user_id": SEC_UID},
  )


def post_resolution():
  return ResourceResolution(
    platform="douyin",
    resource_type=RESOURCE_TYPE_POST,
    source_url=SHORT_LINK,
    resolved_url=POST_URL,
    identity={"aweme_id": AWEME_ID},
  )


def live_resolution():
  return ResourceResolution(
    platform="douyin",
    resource_type=RESOURCE_TYPE_LIVE,
    source_url=SHORT_LINK,
    resolved_url=LIVE_URL,
    identity={},
  )


IDENTITY = {
  "owner_user_id": "acc-9",
  "sec_user_id": SEC_UID,
  "nickname": "主播甲",
}


##
## >>============================= stand-ins =============================>>
##
##
## A sentinel, because ``None`` and an empty mapping are both real answers the
## tests below need to be able to give.
##
_DEFAULT = object()


class StubResolveService:
  """The server's own memory of what it resolved.

  Answers ``None`` for anything it did not issue, which is the whole point of
  the receipt.
  """

  def __init__(self, resolutions=_DEFAULT):
    ##
    ## Distinguished from an empty mapping on purpose: "a store holding
    ## nothing" is precisely the case these tests are about, and ``or`` would
    ## quietly turn it back into the default.
    ##
    self._resolutions = dict(
      {RESOLVE_ID: owner_resolution()} if resolutions is _DEFAULT
      else resolutions
    )
    self.asked = []

  def get_for_user(self, resolve_id, app_user_id):
    self.asked.append(resolve_id)
    return self._resolutions.get(resolve_id)


class _PersonAssignmentServiceForTest(PersonAssignmentService):
  """Keeps unit cases terse while production callers must name the owner."""

  def assign(self, request, *, app_user_id=TEST_APP_USER_ID):
    return super().assign(request, app_user_id=app_user_id)

  def inspect(self, request, *, app_user_id=TEST_APP_USER_ID):
    return super().inspect(request, app_user_id=app_user_id)


class StubIdentityReader:
  def __init__(self, identity=_DEFAULT, failure=None, on_call=None):
    ##
    ## ``None`` is an answer here - it means the link named nobody - so it
    ## cannot double as "no argument given".
    ##
    self._identity = IDENTITY if identity is _DEFAULT else identity
    self._failure = failure
    self._on_call = on_call
    self.resolutions = []

  def from_resolution(self, resolution):
    if self._on_call is not None:
      self._on_call()
    self.resolutions.append(resolution)
    if self._failure is not None:
      raise self._failure
    return None if self._identity is None else dict(self._identity)


class StubTable:
  def __init__(self, directory_name=None, failure=None, on_call=None,
               result=None, assignment=_DEFAULT, lookup_failure=None,
               refresh_failure=None):
    self.directory_name = directory_name
    self.failure = failure
    self._on_call = on_call
    self._result = result
    ##
    ## ``None`` is the answer for an account this program never saw, so it
    ## cannot double as "no argument given".
    ##
    self._assignment = None if assignment is _DEFAULT else assignment
    self._lookup_failure = lookup_failure
    self._refresh_failure = refresh_failure
    self.assignments = []
    self.directory_lookups = []
    self.assignment_lookups = []
    self.identity_refreshes = []
    self.created_people = []
    self.attachments = []

  def get_account_assignment(self, owner_user_id, platform="douyin"):
    if self._on_call is not None:
      self._on_call()
    self.assignment_lookups.append(owner_user_id)
    if self._lookup_failure is not None:
      raise self._lookup_failure
    return None if self._assignment is None else dict(self._assignment)

  def upsert_account_identity(self, owner_user_id, sec_user_id=None,
                              nickname=None):
    self.identity_refreshes.append((owner_user_id, sec_user_id, nickname))
    if self._refresh_failure is not None:
      raise self._refresh_failure

  ##
  ## Present only so a test can prove they were never reached.  An inspection
  ## that created a person or attached an account would be a read endpoint
  ## writing the very relationship the user has not confirmed yet.
  ##
  def create_person(self, display_name, note=None):
    self.created_people.append((display_name, note))
    return 99

  def attach_account(self, platform, owner_user_id, person_id, role):
    self.attachments.append((platform, owner_user_id, person_id, role))

  def update_person(self, person_id, **fields):
    raise AssertionError("an inspection must never rename anybody")

  def account_directory_name(self, owner_user_id, platform="douyin"):
    ##
    ## Counts as touching the database, exactly like the assignment does.  The
    ## ordering test below is about when this service stops talking to a
    ## platform and starts talking to a connection, and a read is still a
    ## connection.
    ##
    if self._on_call is not None:
      self._on_call()
    self.directory_lookups.append(owner_user_id)
    return self.directory_name

  def assign_account(self, **kwargs):
    if self._on_call is not None:
      self._on_call()
    self.assignments.append(kwargs)
    if self.failure is not None:
      raise self.failure
    if self._result is not None:
      return dict(self._result)
    return {
      "person_id": kwargs.get("person_id") or 11,
      "created_person": kwargs.get("person_id") is None,
      "owner_user_id": kwargs["owner_user_id"],
      "role": kwargs["role"],
      "display_name": kwargs.get("display_name") or "现有的人",
    }


def build_service(resolve_service=None, table=None, reader=None):
  table = table if table is not None else StubTable()
  service = _PersonAssignmentServiceForTest(
    resolve_service=(
      resolve_service if resolve_service is not None else StubResolveService()
    ),
    table_factory=lambda: table,
    identity_reader=reader if reader is not None else StubIdentityReader(),
  )
  return service, table


def new_request(**overrides):
  request = {
    "resolve_id": RESOLVE_ID,
    "target": {"kind": "new", "display_name": "张三"},
    "role": "alt",
  }
  request.update(overrides)
  return request


def existing_request(**overrides):
  request = {
    "resolve_id": RESOLVE_ID,
    "target": {"kind": "existing", "person_id": 12},
    "role": "main",
  }
  request.update(overrides)
  return request


##
## >>============================= the identity reader =============================>>
##
class OwnerIdentityFromResolutionTest(unittest.TestCase):
  """A share link names an owner whichever kind it is.

  Profile, post or live room - all three are accepted, because the user pasted
  whatever they had to hand and being told "that is a post, paste the profile
  instead" is work the server can do itself.
  """

  def build_reader(self, owner=None, post=None, probe=None, request_function=None):
    def refuse(*args, **kwargs):
      raise AssertionError("no request may be made here")

    return DouyinOwnerIdentityReader(
      owner_detail=owner if owner is not None else refuse,
      post_resolution=post if post is not None else refuse,
      live_probe=probe if probe is not None else refuse,
    )

  class Owner:
    def __init__(self, uid="acc-9", sec_user_id=SEC_UID, nickname="主播甲"):
      self.uid = uid
      self.sec_user_id = sec_user_id
      self.nickname = nickname

  class PostDetail:
    def __init__(self, owner_user_id="acc-9", sec_user_id=SEC_UID,
                 nickname="主播甲"):
      self.owner_user_id = owner_user_id
      self.sec_user_id = sec_user_id
      self.nickname = nickname

  class PostResolution:
    def __init__(self, ok=True, detail=None):
      self.ok = ok
      self.detail = detail

  class Probe:
    def __init__(self, owner_user_id="acc-9", sec_user_id=SEC_UID,
                 nickname="主播甲"):
      self.owner_user_id = owner_user_id
      self.sec_user_id = sec_user_id
      self.nickname = nickname

  def test_a_profile_receipt_reads_the_owner_from_the_profile(self):
    seen = []
    reader = self.build_reader(
      owner=lambda sec_user_id: seen.append(sec_user_id) or self.Owner()
    )

    identity = reader.from_resolution(owner_resolution())

    self.assertEqual(seen, [SEC_UID])
    self.assertEqual(identity["owner_user_id"], "acc-9")
    self.assertEqual(identity["nickname"], "主播甲")

  def test_a_post_receipt_reads_the_owner_out_of_the_post(self):
    """The post payload already carries the author's id, sec id and nickname,
    so resolving the post answers the whole question."""
    seen = []
    reader = self.build_reader(
      post=lambda url, aweme_id: (
        seen.append((url, aweme_id))
        or self.PostResolution(detail=self.PostDetail())
      )
    )

    identity = reader.from_resolution(post_resolution())

    self.assertEqual(seen, [(POST_URL, AWEME_ID)])
    self.assertEqual(identity["owner_user_id"], "acc-9")

  def test_a_live_receipt_reads_the_owner_out_of_the_room(self):
    """Open or not.  The probe reports the room's owner either way, so a
    marked owner does not have to be streaming at the moment you mark them."""
    seen = []
    reader = self.build_reader(
      probe=lambda url: seen.append(url) or self.Probe()
    )

    identity = reader.from_resolution(live_resolution())

    self.assertEqual(seen, [LIVE_URL])
    self.assertEqual(identity["owner_user_id"], "acc-9")

  def test_the_resolved_url_is_used_and_the_pasted_one_is_not(self):
    """The short link has already been followed once, safely, by ``/api/resolve``.

    Handing it over again would repeat that decision - and repeat the request
    that made it - in a place that has none of the checks which made it safe.
    """
    seen = []
    reader = self.build_reader(
      post=lambda url, aweme_id: (
        seen.append(url) or self.PostResolution(detail=self.PostDetail())
      )
    )

    reader.from_resolution(post_resolution())

    self.assertEqual(seen, [POST_URL])
    self.assertNotIn(SHORT_LINK, seen)

  def test_no_request_is_made_to_follow_anything(self):
    """The reader is built with no way to make a request of its own.

    Every collaborator it has answers a question about an already-named
    resource; there is nothing here that could follow a redirect.
    """
    reader = self.build_reader(
      post=lambda url, aweme_id: self.PostResolution(detail=self.PostDetail())
    )

    identity = reader.from_resolution(post_resolution())

    self.assertEqual(identity["owner_user_id"], "acc-9")

  def test_a_post_that_cannot_be_resolved_yields_nothing(self):
    reader = self.build_reader(
      post=lambda url, aweme_id: self.PostResolution(ok=False)
    )

    self.assertIsNone(reader.from_resolution(post_resolution()))

  def test_a_room_with_no_owner_yields_nothing(self):
    reader = self.build_reader(probe=lambda url: self.Probe(owner_user_id=""))

    self.assertIsNone(reader.from_resolution(live_resolution()))

  def test_a_profile_with_no_uid_yields_a_blank_owner_id(self):
    """Reported rather than repaired: the service decides what a blank id
    means, and it is the same decision for all three kinds."""
    reader = self.build_reader(owner=lambda sec_user_id: self.Owner(uid=""))

    identity = reader.from_resolution(owner_resolution())

    self.assertEqual(identity["owner_user_id"], "")

  def test_an_already_followed_url_can_be_read_directly(self):
    """The by-link route resolves its own url and then needs the same three
    readers.  One implementation, reached two ways - not two."""
    reader = self.build_reader(owner=lambda sec_user_id: self.Owner())

    identity = reader.from_resolved_url(OWNER_URL)

    self.assertEqual(identity["owner_user_id"], "acc-9")

  def test_an_unrecognisable_url_yields_nothing(self):
    reader = self.build_reader()

    self.assertIsNone(reader.from_resolved_url("https://www.douyin.com/"))


##
## >>============================= the request contract =============================>>
##
class RequestShapeTest(unittest.TestCase):
  """Unknown fields are refused rather than ignored.

  "Accepted but had no effect" is the worst answer an api can give, because the
  caller goes on believing a promise nothing here made.  The fields a client is
  most likely to send are the ones it wants trusted - an owner id, a nickname -
  and those are exactly what this endpoint declines to take its word for.
  """

  def test_the_body_must_be_an_object(self):
    service, table = build_service()

    for body in (None, [], "resolve_id", 3):
      with self.assertRaises(InvalidAssignment):
        service.assign(body)
    self.assertEqual(table.assignments, [])

  def test_an_unknown_top_level_field_is_refused(self):
    service, table = build_service()

    with self.assertRaises(InvalidAssignment):
      service.assign(new_request(owner_user_id="acc-9"))

    self.assertEqual(table.assignments, [])

  def test_a_client_supplied_identity_is_never_accepted(self):
    """The receipt is the only thing that says which account this is.

    A request that could name the account itself would let a browser attach an
    owner this server never resolved - which is the guarantee the receipt
    exists to provide.
    """
    service, table = build_service()

    for field in ("owner_user_id", "sec_user_id", "nickname", "resolved_url"):
      with self.assertRaises(InvalidAssignment):
        service.assign(new_request(**{field: "anything"}))
    self.assertEqual(table.assignments, [])

  def test_the_resolve_id_is_required(self):
    service, _ = build_service()

    for value in (None, "", "   ", 7, True):
      with self.assertRaises(InvalidAssignment):
        service.assign(new_request(resolve_id=value))

  def test_the_target_must_be_an_object(self):
    service, _ = build_service()

    for target in (None, "new", ["new"], 3):
      with self.assertRaises(InvalidAssignment):
        service.assign(new_request(target=target))

  def test_the_target_kind_must_be_one_of_two(self):
    service, _ = build_service()

    for kind in ("New", "person", "", None, 3):
      with self.assertRaises(InvalidAssignment):
        service.assign(new_request(target={"kind": kind}))

  def test_the_role_must_be_a_known_one(self):
    service, table = build_service()

    for role in ("boss", "MAIN", "", None, 1, True):
      with self.assertRaises(InvalidAssignment):
        service.assign(new_request(role=role))
    self.assertEqual(table.assignments, [])

  def test_every_known_role_is_accepted(self):
    for role in ("main", "alt", "matrix"):
      service, table = build_service()

      service.assign(new_request(role=role))

      self.assertEqual(table.assignments[0]["role"], role)

  def test_allow_move_must_be_a_boolean(self):
    service, _ = build_service()

    for value in ("true", 1, 0, "", None):
      with self.assertRaises(InvalidAssignment):
        service.assign(new_request(allow_move=value))

  def test_a_refused_request_never_reads_the_receipt(self):
    """A field error is wrong whatever the receipt says, and answering "your
    resolution expired" would send the user round a loop that cannot fix it."""
    resolve_service = StubResolveService()
    service, _ = build_service(resolve_service=resolve_service)

    with self.assertRaises(InvalidAssignment):
      service.assign(new_request(role="boss"))

    self.assertEqual(resolve_service.asked, [])


class NewTargetShapeTest(unittest.TestCase):
  def test_only_three_fields_are_allowed(self):
    service, _ = build_service()

    with self.assertRaises(InvalidAssignment):
      service.assign(new_request(target={"kind": "new", "person_id": 3}))

  def test_the_display_name_may_be_omitted(self):
    service, table = build_service()

    service.assign(new_request(target={"kind": "new"}))

    self.assertEqual(len(table.assignments), 1)

  def test_a_blank_display_name_is_a_field_error_rather_than_an_omission(self):
    """"The user did not say" and "the user said something meaningless" are
    different, and only the first one may be filled in for them."""
    service, table = build_service()

    for name in ("", "   ", "\t\n"):
      with self.assertRaises(InvalidAssignment):
        service.assign(
          new_request(target={"kind": "new", "display_name": name})
        )
    self.assertEqual(table.assignments, [])

  def test_a_display_name_that_is_not_text_is_refused(self):
    service, _ = build_service()

    for name in (7, True, [], {}):
      with self.assertRaises(InvalidAssignment):
        service.assign(
          new_request(target={"kind": "new", "display_name": name})
        )

  def test_the_display_name_is_trimmed(self):
    service, table = build_service()

    service.assign(
      new_request(target={"kind": "new", "display_name": "  张三  "})
    )

    self.assertEqual(table.assignments[0]["display_name"], "张三")

  def test_a_blank_note_becomes_nothing(self):
    service, table = build_service()

    service.assign(
      new_request(target={"kind": "new", "display_name": "张三", "note": "  "})
    )

    self.assertIsNone(table.assignments[0]["note"])

  def test_a_note_that_is_not_text_is_refused(self):
    service, _ = build_service()

    with self.assertRaises(InvalidAssignment):
      service.assign(
        new_request(target={"kind": "new", "display_name": "张三", "note": 7})
      )


class ExistingTargetShapeTest(unittest.TestCase):
  def test_only_two_fields_are_allowed(self):
    """Renaming a person is ``PATCH /api/person/<id>``, which is its own
    deliberate operation.  Accepting a name here would make a rename happen as
    a side effect of attaching an account."""
    service, table = build_service()

    with self.assertRaises(InvalidAssignment):
      service.assign(
        existing_request(
          target={"kind": "existing", "person_id": 12, "display_name": "李四"}
        )
      )
    self.assertEqual(table.assignments, [])

  def test_a_note_is_refused_too(self):
    service, _ = build_service()

    with self.assertRaises(InvalidAssignment):
      service.assign(
        existing_request(
          target={"kind": "existing", "person_id": 12, "note": "备注"}
        )
      )

  def test_the_person_id_is_required(self):
    service, _ = build_service()

    with self.assertRaises(InvalidAssignment):
      service.assign(existing_request(target={"kind": "existing"}))

  def test_the_person_id_must_be_a_real_integer(self):
    service, _ = build_service()

    for person_id in ("12", 1.5, None, [], "abc"):
      with self.assertRaises(InvalidAssignment):
        service.assign(
          existing_request(
            target={"kind": "existing", "person_id": person_id}
          )
        )

  def test_a_boolean_is_not_a_person_id(self):
    """``True`` is an ``int`` in python, and ``person_id = True`` would go to
    the database as 1 - somebody else's person."""
    service, _ = build_service()

    for person_id in (True, False):
      with self.assertRaises(InvalidAssignment):
        service.assign(
          existing_request(
            target={"kind": "existing", "person_id": person_id}
          )
        )

  def test_the_person_id_must_be_positive(self):
    service, _ = build_service()

    for person_id in (0, -1):
      with self.assertRaises(InvalidAssignment):
        service.assign(
          existing_request(
            target={"kind": "existing", "person_id": person_id}
          )
        )


class ReplaceMainShapeTest(unittest.TestCase):
  def test_it_must_name_where_the_old_main_goes(self):
    service, _ = build_service()

    for value in (True, {}, {"demote_to": None}, "alt", []):
      with self.assertRaises(InvalidAssignment):
        service.assign(existing_request(replace_main=value))

  def test_the_old_main_cannot_be_demoted_to_main(self):
    """Which is the two-main state written out in full."""
    service, _ = build_service()

    with self.assertRaises(InvalidAssignment):
      service.assign(existing_request(replace_main={"demote_to": "main"}))

  def test_only_alt_and_matrix_are_accepted(self):
    for demote_to in ("alt", "matrix"):
      service, table = build_service()

      service.assign(existing_request(replace_main={"demote_to": demote_to}))

      self.assertEqual(table.assignments[0]["demote_main_to"], demote_to)

  def test_an_unknown_field_inside_it_is_refused(self):
    service, _ = build_service()

    with self.assertRaises(InvalidAssignment):
      service.assign(
        existing_request(replace_main={"demote_to": "alt", "force": True})
      )

  def test_false_means_absent(self):
    service, table = build_service()

    service.assign(existing_request(replace_main=False))

    self.assertIsNone(table.assignments[0]["demote_main_to"])

  def test_a_new_person_cannot_replace_a_main_it_does_not_have(self):
    """A brand new person holds nothing, so there is no main to replace.  The
    caller knows that when it writes the request, so asking for it means the
    request does not say what its author thought it said."""
    service, table = build_service()

    with self.assertRaises(InvalidAssignment):
      service.assign(new_request(replace_main={"demote_to": "alt"}))

    self.assertEqual(table.assignments, [])

  def test_it_is_meaningless_unless_the_new_role_is_main(self):
    service, _ = build_service()

    with self.assertRaises(InvalidAssignment):
      service.assign(
        existing_request(role="alt", replace_main={"demote_to": "matrix"})
      )


##
## >>============================= the receipt is the authority =============================>>
##
class ReceiptAuthorityTest(unittest.TestCase):
  def test_the_resolution_is_read_from_this_servers_own_store(self):
    resolve_service = StubResolveService()
    service, _ = build_service(resolve_service=resolve_service)

    service.assign(new_request())

    self.assertEqual(resolve_service.asked, [RESOLVE_ID])

  def test_an_unknown_receipt_is_not_repaired(self):
    """Re-resolving the url here would mean the server deciding what the user
    meant, minutes after they asked - which is the one thing the receipt exists
    to prevent.  The user resolves again instead."""
    service, table = build_service(
      resolve_service=StubResolveService(resolutions={})
    )

    with self.assertRaises(ResolutionNotFound):
      service.assign(new_request())

    self.assertEqual(table.assignments, [])

  def test_an_expired_receipt_writes_nothing_at_all(self):
    reader = StubIdentityReader()
    service, table = build_service(
      resolve_service=StubResolveService(resolutions={}), reader=reader
    )

    with self.assertRaises(ResolutionNotFound):
      service.assign(new_request())

    self.assertEqual(table.assignments, [])
    self.assertEqual(table.directory_lookups, [])
    ##
    ## Not even the platform is asked.  A receipt that is gone names nothing,
    ## so there is nothing to look up.
    ##
    self.assertEqual(reader.resolutions, [])

  def test_the_snapshot_is_what_the_identity_is_read_from(self):
    reader = StubIdentityReader()
    service, _ = build_service(reader=reader)

    service.assign(new_request())

    self.assertEqual(len(reader.resolutions), 1)
    self.assertEqual(reader.resolutions[0].resolved_url, OWNER_URL)

  def test_a_receipt_for_a_post_is_accepted(self):
    service, table = build_service(
      resolve_service=StubResolveService({RESOLVE_ID: post_resolution()})
    )

    result = service.assign(new_request())

    self.assertEqual(result.owner_user_id, "acc-9")
    self.assertEqual(len(table.assignments), 1)

  def test_a_receipt_for_a_live_room_is_accepted(self):
    service, table = build_service(
      resolve_service=StubResolveService({RESOLVE_ID: live_resolution()})
    )

    result = service.assign(new_request())

    self.assertEqual(result.owner_user_id, "acc-9")


class OwnerIdentityUnavailableTest(unittest.TestCase):
  def test_a_link_that_names_no_owner_creates_no_person(self):
    service, table = build_service(reader=StubIdentityReader(identity=None))

    with self.assertRaises(OwnerIdentityUnavailable):
      service.assign(new_request())

    self.assertEqual(table.assignments, [])

  def test_a_blank_owner_id_creates_no_person(self):
    """``person_account`` is keyed on the account id.  A blank one would create
    a row nothing can ever match, and the download path looks the owner up by
    exactly this id."""
    service, table = build_service(
      reader=StubIdentityReader(identity={"owner_user_id": "  "})
    )

    with self.assertRaises(OwnerIdentityUnavailable):
      service.assign(new_request())

    self.assertEqual(table.assignments, [])

  def test_a_platform_failure_is_reported_rather_than_crashing(self):
    service, table = build_service(
      reader=StubIdentityReader(failure=RuntimeError("gone"))
    )

    with self.assertRaises(PersonAssignmentError):
      service.assign(new_request())

    self.assertEqual(table.assignments, [])

  def test_the_owner_id_is_trimmed_before_it_is_used(self):
    service, table = build_service(
      reader=StubIdentityReader(
        identity={"owner_user_id": " acc-9 ", "nickname": "主播甲"}
      )
    )

    service.assign(new_request())

    self.assertEqual(table.assignments[0]["owner_user_id"], "acc-9")


##
## >>============================= naming the person =============================>>
##
class DisplayNameFallbackTest(unittest.TestCase):
  """A name is optional, so the server has to have one ready.

  What it picks is a *person* name, shown to a user, so nothing here is passed
  through the folder sanitiser - that would rewrite somebody's name for a
  reason that has nothing to do with them.  The one value read from a folder is
  read because it is already the safe text somebody's files live under.
  """

  def assign_with(self, directory_name=None, nickname="主播甲",
                  display_name=None, owner_user_id="acc-9"):
    table = StubTable(directory_name=directory_name)
    identity = {"owner_user_id": owner_user_id, "nickname": nickname}
    service, _ = build_service(table=table, reader=StubIdentityReader(identity))
    target = {"kind": "new"}
    if display_name is not None:
      target["display_name"] = display_name
    service.assign(new_request(target=target))
    return table.assignments[0]["display_name"]

  def test_a_name_the_user_typed_wins(self):
    self.assertEqual(
      self.assign_with(directory_name="目录名", display_name="张三"), "张三"
    )

  def test_a_typed_name_is_never_overwritten_by_the_fallback(self):
    """Whichever fallback would have applied.  A user who names somebody and
    then finds the server renamed them has no reason to trust it again."""
    self.assertEqual(
      self.assign_with(
        directory_name="目录名", nickname="主播甲", display_name="张三"
      ),
      "张三",
    )

  def test_without_one_the_existing_folder_is_used(self):
    """It is what this account's files already live under, so it is the name
    the user will recognise."""
    self.assertEqual(self.assign_with(directory_name="目录名"), "目录名")

  def test_an_empty_folder_is_treated_as_absent(self):
    self.assertEqual(self.assign_with(directory_name=""), "主播甲")

  def test_the_literal_text_none_is_treated_as_absent(self):
    """Older rows carry the string "None" where a value was never set, and a
    person called None is nobody."""
    self.assertEqual(self.assign_with(directory_name="None"), "主播甲")

  def test_a_blank_folder_is_treated_as_absent(self):
    self.assertEqual(self.assign_with(directory_name="   "), "主播甲")

  def test_without_a_folder_the_nickname_is_used(self):
    self.assertEqual(self.assign_with(directory_name=None), "主播甲")

  def test_with_neither_the_account_id_is_used(self):
    """Never blank.  ``display_name`` is what the person list is ordered and
    searched by, and a row with no name is a row nobody can find again."""
    self.assertEqual(
      self.assign_with(directory_name=None, nickname=None), "acc-9"
    )

  def test_a_blank_nickname_is_treated_as_absent(self):
    self.assertEqual(
      self.assign_with(directory_name=None, nickname="   "), "acc-9"
    )

  def test_the_folder_is_looked_up_for_the_resolved_account(self):
    table = StubTable(directory_name="目录名")
    service, _ = build_service(table=table)

    service.assign(new_request(target={"kind": "new"}))

    self.assertEqual(table.directory_lookups, ["acc-9"])

  def test_an_existing_person_is_never_renamed(self):
    """Their name is theirs.  Attaching an account says nothing about it."""
    table = StubTable(directory_name="目录名")
    service, _ = build_service(table=table)

    service.assign(existing_request())

    self.assertIsNone(table.assignments[0]["display_name"])
    self.assertEqual(table.directory_lookups, [])


##
## >>============================= what came back =============================>>
##
class ResultTest(unittest.TestCase):
  def test_the_result_names_what_happened(self):
    service, _ = build_service()

    result = service.assign(new_request())

    self.assertIsInstance(result, PersonAssignmentResult)
    self.assertEqual(result.person_id, 11)
    self.assertEqual(result.owner_user_id, "acc-9")
    self.assertEqual(result.role, "alt")
    self.assertTrue(result.created_person)
    self.assertEqual(result.display_name, "张三")

  def test_an_existing_person_reports_its_own_name(self):
    service, _ = build_service()

    result = service.assign(existing_request())

    self.assertEqual(result.person_id, 12)
    self.assertFalse(result.created_person)
    self.assertEqual(result.display_name, "现有的人")

  def test_nothing_from_the_platform_reaches_the_result(self):
    """A sec id, a room, a post payload - none of it is the browser's
    business, and every field here is one somebody could start depending on."""
    service, _ = build_service()

    result = service.assign(new_request())

    self.assertEqual(
      sorted(vars(result)),
      ["created_person", "display_name", "owner_user_id", "person_id", "role"],
    )


##
## >>============================= refusals from the database =============================>>
##
class ConflictReportingTest(unittest.TestCase):
  def test_an_account_held_by_somebody_else_is_a_conflict(self):
    service, _ = build_service(
      table=StubTable(failure=AccountAttachedElsewhere(7, "原来的人"))
    )

    with self.assertRaises(AccountAlreadyAttached) as caught:
      service.assign(existing_request())

    self.assertEqual(caught.exception.status_code, 409)
    self.assertEqual(
      caught.exception.details(),
      {"current_person": {"person_id": 7, "display_name": "原来的人"}},
    )

  def test_a_second_main_is_a_conflict(self):
    service, _ = build_service(
      table=StubTable(failure=MainAlreadyAssigned("acc-1", "主号"))
    )

    with self.assertRaises(MainAccountConflict) as caught:
      service.assign(existing_request())

    self.assertEqual(caught.exception.status_code, 409)
    self.assertEqual(
      caught.exception.details(),
      {"current_main": {"owner_user_id": "acc-1", "nickname": "主号"}},
    )

  def test_stranding_a_persons_aligned_accounts_is_a_conflict(self):
    """The refusal has to say *which* person is being left without a main, and
    which account was theirs - the page's next move is to give that person a new
    main first, and it cannot offer that without both."""
    service, _ = build_service(
      table=StubTable(
        failure=LastMainRemoval(
          7, display_name="原来的人", owner_user_id="acc-1", nickname="主号"
        )
      )
    )

    with self.assertRaises(LastMainRemovalConflict) as caught:
      service.assign(existing_request())

    self.assertEqual(caught.exception.status_code, 409)
    self.assertEqual(caught.exception.kind, "last_main_removal_conflict")
    self.assertEqual(
      caught.exception.details(),
      {
        "source_person": {"person_id": 7, "display_name": "原来的人"},
        "current_main": {"owner_user_id": "acc-1", "nickname": "主号"},
      },
    )

  def test_it_is_told_apart_from_gaining_a_second_main(self):
    """Both are 409 and both are about the main account, and the answers are
    opposite: one needs ``replace_main``, the other needs the source person to
    be given a main of its own first."""
    self.assertNotEqual(
      LastMainRemovalConflict.kind, MainAccountConflict.kind
    )
    self.assertNotEqual(
      LastMainRemovalConflict.kind, AccountAlreadyAttached.kind
    )

  def test_an_unknown_person_is_reported_as_missing(self):
    service, _ = build_service(table=StubTable(failure=PersonMissing(999)))

    with self.assertRaises(PersonNotFound) as caught:
      service.assign(existing_request())

    self.assertEqual(caught.exception.status_code, 404)

  def test_a_move_is_permitted_when_it_is_asked_for(self):
    service, table = build_service()

    service.assign(existing_request(allow_move=True))

    self.assertTrue(table.assignments[0]["allow_move"])

  def test_a_move_is_refused_by_default(self):
    service, table = build_service()

    service.assign(existing_request())

    self.assertFalse(table.assignments[0]["allow_move"])

  def test_a_blocked_schema_is_reported_as_unavailable(self):
    """No correction the caller could make to the request would let it
    through, so it is not a bad request."""
    service, _ = build_service(
      table=StubTable(failure=DatabaseWriteBlocked("schema state is behind"))
    )

    with self.assertRaises(AssignmentUnavailable) as caught:
      service.assign(new_request())

    self.assertEqual(caught.exception.status_code, 503)

  def test_a_role_the_table_does_not_know_is_a_field_error(self):
    service, _ = build_service(table=StubTable(failure=UnknownRole("bad role")))

    with self.assertRaises(InvalidAssignment):
      service.assign(new_request())

  def test_every_expected_refusal_carries_its_own_status_and_kind(self):
    """Never re-derived from the message text at the edge."""
    for error in (
      ResolutionNotFound("x"),
      InvalidAssignment("x"),
      OwnerIdentityUnavailable("x"),
      PersonNotFound("x"),
      AccountAlreadyAttached("x", person_id=7, display_name="原来的人"),
      MainAccountConflict("x", owner_user_id="acc-1", nickname="主号"),
      LastMainRemovalConflict(
        "x", person_id=7, display_name="原来的人",
        owner_user_id="acc-1", nickname="主号",
      ),
      AssignmentUnavailable("x"),
    ):
      self.assertIsInstance(error, PersonAssignmentError)
      self.assertIsInstance(error.kind, str)
      self.assertTrue(error.kind)
      self.assertIn(error.status_code, (400, 404, 409, 503))

  def test_the_kinds_are_all_different(self):
    kinds = [
      ResolutionNotFound.kind,
      InvalidAssignment.kind,
      OwnerIdentityUnavailable.kind,
      PersonNotFound.kind,
      AccountAlreadyAttached.kind,
      MainAccountConflict.kind,
      LastMainRemovalConflict.kind,
      AssignmentUnavailable.kind,
    ]
    self.assertEqual(len(set(kinds)), len(kinds))


##
## >>============================= where the network stops =============================>>
##
class NetworkAndTransactionBoundaryTest(unittest.TestCase):
  """The platform is asked *before* the transaction opens, never inside it.

  A request made between ``BEGIN`` and ``COMMIT`` holds every row lock the
  transaction has taken for as long as douyin takes to answer - which is
  seconds when it answers and the full timeout when it does not.  Every other
  assignment for those rows waits behind it.
  """

  def test_the_identity_is_read_before_the_database_is_touched(self):
    order = []
    reader = StubIdentityReader(on_call=lambda: order.append("platform"))
    table = StubTable(on_call=lambda: order.append("database"))
    service, _ = build_service(table=table, reader=reader)

    service.assign(new_request())

    self.assertEqual(order, ["platform", "database"])

  def test_the_platform_is_not_consulted_once_the_assignment_has_started(self):
    reader = StubIdentityReader()
    calls = []

    def refuse():
      if calls:
        raise AssertionError("the platform was asked inside the transaction")

    table = StubTable(on_call=lambda: calls.append(1))
    service, _ = build_service(table=table, reader=reader)
    reader._on_call = refuse

    service.assign(new_request())

    self.assertEqual(len(reader.resolutions), 1)

  def test_the_assignment_reaches_the_database_as_one_call(self):
    """Not create-then-attach.  Two calls have a middle, and a person created
    in that middle survives the failure of the attach that was meant to follow
    it."""
    service, table = build_service()

    service.assign(new_request())

    self.assertEqual(len(table.assignments), 1)

  def test_everything_the_assignment_needs_is_handed_over_at_once(self):
    service, table = build_service()

    service.assign(
      new_request(
        target={"kind": "new", "display_name": "张三", "note": "备注"}
      )
    )

    assignment = table.assignments[0]
    self.assertEqual(assignment["owner_user_id"], "acc-9")
    self.assertEqual(assignment["role"], "alt")
    self.assertEqual(assignment["display_name"], "张三")
    self.assertEqual(assignment["note"], "备注")
    self.assertEqual(assignment["nickname"], "主播甲")
    self.assertEqual(assignment["sec_user_id"], SEC_UID)
    self.assertIsNone(assignment["person_id"])


##
## >>============================= the network bomb =============================>>
##
class NoRealNetworkTest(unittest.TestCase):
  """The suite's own guarantee that it is not talking to douyin.

  Asserted rather than assumed, because the failure mode is silent: a test that
  stops stubbing its seam and falls through to the real downloader still passes,
  and nothing in the output says a request was made.  That happened once during
  this feature's development.  If ``conftest`` ever stops arming the block, this
  is what says so - and it lives beside the assignment tests because those are
  the ones with a platform call one refactor away.
  """

  ##
  ## An address literal, never a hostname.
  ##
  ## A name has to be resolved before anything is connected, so on a machine
  ## whose resolver does not answer for it the request dies in DNS having
  ## proved nothing about this gate - which is exactly what happened on CI,
  ## where the first version of these tests passed locally and failed there.
  ## 192.0.2.0/24 is the documentation range: reserved, never routed, and
  ## resolvable without asking anybody.
  ##
  UNROUTABLE = ("192.0.2.1", 80)

  ##
  ## Short, and present on every call that could reach a socket.
  ##
  ## With the block armed nothing waits - the connection is refused before it is
  ## attempted - so this only matters when the block is *not* armed, which is
  ## precisely the case these tests exist to catch.  Without it a broken gate
  ## makes the suite hang on an unroutable address until the operating system
  ## gives up, and a hung CI job says far less than a failed one.
  ##
  TIMEOUT = 0.25

  @staticmethod
  def _refused_by_the_gate(error) -> bool:
    """Whether ``error`` was caused by the block, however it was wrapped.

    Walks the chain rather than matching the message: the text belongs to
    whichever library was in the way, and asserting on it is how a test ends up
    passing for a reason that has nothing to do with what it checks.
    """
    from backend.src.unit_test.no_network import RealNetworkAccessDenied

    seen = set()
    while error is not None and id(error) not in seen:
      if isinstance(error, RealNetworkAccessDenied):
        return True
      seen.add(id(error))
      error = error.__cause__ or error.__context__
    return False

  def test_opening_a_socket_is_refused(self):
    import socket

    from backend.src.unit_test.no_network import RealNetworkAccessDenied

    with self.assertRaises(RealNetworkAccessDenied):
      socket.create_connection(self.UNROUTABLE, timeout=self.TIMEOUT)

  def test_connecting_a_socket_directly_is_refused(self):
    """The other half of the block.

    ``create_connection`` is a module-level helper; a client that builds its own
    socket goes through the method instead, and urllib3 is one of those.
    """
    import socket

    from backend.src.unit_test.no_network import RealNetworkAccessDenied

    opened = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    opened.settimeout(self.TIMEOUT)
    with self.assertRaises(RealNetworkAccessDenied):
      opened.connect(self.UNROUTABLE)

  def test_an_http_client_cannot_get_out_either(self):
    """Through the library the platform code actually uses, not just the
    primitive underneath it."""
    import requests

    with self.assertRaises(Exception) as caught:
      requests.get("http://192.0.2.1/", timeout=self.TIMEOUT)

    self.assertTrue(
      self._refused_by_the_gate(caught.exception),
      "the request failed, but not because the gate stopped it: {!r}".format(
        caught.exception
      ),
    )

  def test_reading_an_identity_needs_no_network_of_its_own(self):
    """The reader's collaborators are all injected, so nothing it does could
    reach a socket even if the block were lifted."""
    reader = DouyinOwnerIdentityReader(
      owner_detail=lambda sec_user_id: None,
      post_resolution=lambda url, aweme_id: None,
      live_probe=lambda url: None,
    )

    self.assertIsNone(reader.from_resolution(owner_resolution()))


##
## >>============================= inspection =============================>>
##
##
## Reading a receipt back as "who is this, and do we already have them" - the
## question the page has to be able to ask *before* it offers a form.
##
## The trust boundary is exactly the assignment's: the account is named by the
## receipt this server issued, and by nothing a client sends.  What differs is
## that nothing here decides anything - the answer is a hint for the interface,
## and the assignment transaction discovers ownership again under its own locks.
##
KNOWN_UNASSIGNED = {
  "owner_user_id": "acc-9",
  "sec_user_id": SEC_UID,
  "nickname": "程儿",
  "person_id": None,
  "role": None,
  "display_name": None,
}

KNOWN_ASSIGNED = {
  "owner_user_id": "acc-9",
  "sec_user_id": SEC_UID,
  "nickname": "程儿",
  "person_id": 12,
  "role": "main",
  "display_name": "程儿",
}


def inspect_request(**overrides):
  request = {"resolve_id": RESOLVE_ID}
  request.update(overrides)
  return request


class InspectionRequestTest(unittest.TestCase):
  """What an inspection may be asked, which is one field.

  The endpoint answers "does this server already know this account", and the
  answer decides whether the user is offered a "create a new person" button.  A
  client that could name the account would be choosing which account gets
  checked - and could ask about one account while holding a receipt for
  another.
  """

  def test_a_receipt_is_all_it_takes(self):
    service, _ = build_service(
      table=StubTable(assignment=None)
    )

    found = service.inspect(inspect_request())

    self.assertEqual(found.owner_user_id, "acc-9")

  def test_the_body_must_be_an_object(self):
    service, _ = build_service()

    with self.assertRaises(InvalidAssignment):
      service.inspect(["receipt-1"])

  def test_a_missing_receipt_is_refused(self):
    service, _ = build_service()

    with self.assertRaises(InvalidAssignment):
      service.inspect({})

  def test_a_blank_receipt_is_refused(self):
    service, _ = build_service()

    with self.assertRaises(InvalidAssignment):
      service.inspect(inspect_request(resolve_id="   "))

  def test_a_client_may_not_name_the_account(self):
    """The whole point.  Accepting any of these would let a browser ask about
    an owner this server never resolved - and then be told, authoritatively,
    that it is free to create a person for it."""
    for field, value in (
      ("owner_user_id", "acc-1"),
      ("sec_user_id", SEC_UID),
      ("nickname", "程儿"),
      ("resolved_url", OWNER_URL),
    ):
      service, table = build_service(table=StubTable(assignment=None))

      with self.assertRaises(InvalidAssignment):
        service.inspect(inspect_request(**{field: value}))

      self.assertEqual(table.assignment_lookups, [])

  def test_a_client_may_not_name_a_person_or_a_role(self):
    """An inspection has no target.  A field for one would read as though the
    answer depended on it, and the first caller to send it would be wrong."""
    for field, value in (("person_id", 12), ("role", "main")):
      service, _ = build_service(table=StubTable(assignment=None))

      with self.assertRaises(InvalidAssignment):
        service.inspect(inspect_request(**{field: value}))

  def test_the_refused_field_is_named(self):
    service, _ = build_service()

    with self.assertRaises(InvalidAssignment) as caught:
      service.inspect(inspect_request(owner_user_id="acc-1"))

    self.assertIn("owner_user_id", str(caught.exception))

  def test_a_field_error_is_decided_before_the_receipt_is_looked_up(self):
    """A bad field is wrong whatever the receipt says, and answering "your
    resolution expired" would send the user round a loop that cannot fix it."""
    store = StubResolveService(resolutions={})
    service, _ = build_service(resolve_service=store)

    with self.assertRaises(InvalidAssignment):
      service.inspect(inspect_request(owner_user_id="acc-1"))

    self.assertEqual(store.asked, [])


class InspectionStateTest(unittest.TestCase):
  """Three answers, and the differences between them are the whole feature.

  "Never seen" is the only one for which creating a person is the right offer.
  "Seen, unfiled" is an account waiting to be filed - common, because a row
  appears the first time anything is downloaded.  "Filed" needs no form at all.
  """

  def test_an_account_this_server_never_saw_is_reported_as_new(self):
    service, table = build_service(table=StubTable(assignment=None))

    found = service.inspect(inspect_request())

    self.assertFalse(found.known_account)
    self.assertIsNone(found.person_id)
    self.assertIsNone(found.role)
    self.assertEqual(table.assignment_lookups, ["acc-9"])

  def test_a_known_account_nobody_filed_is_known_but_unassigned(self):
    """Two facts, not one.  Telling the user "this person already exists"
    because a download once created a ``share_url`` row would be false, and
    would leave them with no way to file the account at all."""
    service, _ = build_service(table=StubTable(assignment=KNOWN_UNASSIGNED))

    found = service.inspect(inspect_request())

    self.assertTrue(found.known_account)
    self.assertIsNone(found.person_id)
    self.assertIsNone(found.role)
    self.assertIsNone(found.display_name)

  def test_a_filed_account_reports_the_person_holding_it(self):
    service, _ = build_service(table=StubTable(assignment=KNOWN_ASSIGNED))

    found = service.inspect(inspect_request())

    self.assertTrue(found.known_account)
    self.assertEqual(found.person_id, 12)
    self.assertEqual(found.display_name, "程儿")
    self.assertEqual(found.role, "main")

  def test_the_account_is_looked_up_by_the_id_the_platform_gave(self):
    """Not by the nickname, which is neither unique nor stable, and not by
    anything a client said."""
    service, table = build_service(
      table=StubTable(assignment=None),
      reader=StubIdentityReader(
        identity={
          "owner_user_id": "acc-42",
          "sec_user_id": SEC_UID,
          "nickname": "程儿",
        }
      ),
    )

    service.inspect(inspect_request())

    self.assertEqual(table.assignment_lookups, ["acc-42"])

  def test_two_people_sharing_a_name_do_not_confuse_the_answer(self):
    """The person comes from the account's own attachment.  Reaching for a name
    match instead would hand somebody else's account to whichever "小明" the
    query happened to return first."""
    service, _ = build_service(
      table=StubTable(
        assignment={
          "owner_user_id": "acc-9",
          "sec_user_id": SEC_UID,
          "nickname": "小明",
          "person_id": 2,
          "role": "alt",
          "display_name": "小明",
        }
      )
    )

    found = service.inspect(inspect_request())

    self.assertEqual(found.person_id, 2)

  def test_a_renamed_account_shows_its_current_nickname(self):
    """The account's nickname is whatever the platform says right now - that is
    what makes it recognisable to the user who just pasted the link."""
    service, _ = build_service(
      table=StubTable(assignment=KNOWN_ASSIGNED),
      reader=StubIdentityReader(
        identity={
          "owner_user_id": "acc-9",
          "sec_user_id": SEC_UID,
          "nickname": "程小程",
        }
      ),
    )

    found = service.inspect(inspect_request())

    self.assertEqual(found.nickname, "程小程")

  def test_a_renamed_account_does_not_rename_the_person(self):
    """A name somebody typed is theirs.  Renaming is PATCH /api/person/<id>,
    its own deliberate operation - and the stub raises if this is forgotten."""
    service, table = build_service(
      table=StubTable(assignment=KNOWN_ASSIGNED),
      reader=StubIdentityReader(
        identity={
          "owner_user_id": "acc-9",
          "sec_user_id": SEC_UID,
          "nickname": "程小程",
        }
      ),
    )

    found = service.inspect(inspect_request())

    self.assertEqual(found.display_name, "程儿")

  def test_a_profile_link_is_inspected(self):
    service, table = build_service(table=StubTable(assignment=KNOWN_ASSIGNED))

    self.assertEqual(service.inspect(inspect_request()).person_id, 12)

  def test_a_post_link_is_inspected(self):
    """The user pastes whatever they had to hand, and a post names its author
    just as well as a profile does."""
    service, _ = build_service(
      resolve_service=StubResolveService({RESOLVE_ID: post_resolution()}),
      table=StubTable(assignment=KNOWN_ASSIGNED),
    )

    self.assertEqual(service.inspect(inspect_request()).person_id, 12)

  def test_a_live_link_is_inspected(self):
    service, _ = build_service(
      resolve_service=StubResolveService({RESOLVE_ID: live_resolution()}),
      table=StubTable(assignment=KNOWN_ASSIGNED),
    )

    self.assertEqual(service.inspect(inspect_request()).person_id, 12)


class InspectionRefusalTest(unittest.TestCase):
  """An inspection can fail in exactly the ways an assignment's first half can.

  Deliberately the same errors, carrying the same statuses: the two read the
  receipt and the platform through one implementation, so a link that cannot be
  inspected cannot be assigned either, and the page is told why once.
  """

  def test_an_unknown_receipt_is_not_repaired(self):
    service, _ = build_service(
      resolve_service=StubResolveService(resolutions={})
    )

    with self.assertRaises(ResolutionNotFound):
      service.inspect(inspect_request())

  def test_an_unknown_receipt_answers_404(self):
    service, _ = build_service(
      resolve_service=StubResolveService(resolutions={})
    )

    with self.assertRaises(PersonAssignmentError) as caught:
      service.inspect(inspect_request())

    self.assertEqual(caught.exception.status_code, 404)
    self.assertEqual(caught.exception.kind, "resolution_not_found")

  def test_a_link_naming_nobody_is_refused(self):
    service, table = build_service(
      table=StubTable(assignment=None),
      reader=StubIdentityReader(identity=None),
    )

    with self.assertRaises(OwnerIdentityUnavailable):
      service.inspect(inspect_request())

    self.assertEqual(table.assignment_lookups, [])

  def test_a_platform_failure_is_refused_rather_than_guessed(self):
    """"We could not read the link" must not arrive as "this account is new" -
    the second sentence is an invitation to create a duplicate person."""
    service, _ = build_service(
      table=StubTable(assignment=None),
      reader=StubIdentityReader(failure=RuntimeError("douyin said no")),
    )

    with self.assertRaises(OwnerIdentityUnavailable) as caught:
      service.inspect(inspect_request())

    self.assertEqual(caught.exception.status_code, 400)

  def test_a_blank_account_id_is_refused(self):
    service, _ = build_service(
      table=StubTable(assignment=None),
      reader=StubIdentityReader(
        identity={"owner_user_id": "  ", "sec_user_id": None, "nickname": None}
      ),
    )

    with self.assertRaises(OwnerIdentityUnavailable):
      service.inspect(inspect_request())


class InspectionReceiptTest(unittest.TestCase):
  """The receipt survives being looked at.

  Reading is not acting.  An inspection happens on the way to an assignment -
  always, now, because the page runs one automatically - so a consuming read
  would mean every user's first click reported "your resolution expired".
  """

  def build_store(self):
    store = ResourceResolveService(store=ResolveStore())
    return store, store._store.put(
      owner_resolution(), app_user_id=TEST_APP_USER_ID
    )

  def test_the_receipt_still_works_afterwards(self):
    store, resolve_id = self.build_store()
    service, _ = build_service(
      resolve_service=store, table=StubTable(assignment=None)
    )

    service.inspect({"resolve_id": resolve_id})

    self.assertIsNotNone(store.get(resolve_id))

  def test_an_assignment_can_still_redeem_it(self):
    """The sequence the page actually performs: resolve, inspect, submit."""
    store, resolve_id = self.build_store()
    service, _ = build_service(
      resolve_service=store, table=StubTable(assignment=None)
    )

    service.inspect({"resolve_id": resolve_id})
    result = service.assign({
      "resolve_id": resolve_id,
      "target": {"kind": "new", "display_name": "程儿"},
      "role": "alt",
    })

    self.assertEqual(result.owner_user_id, "acc-9")

  def test_inspecting_twice_answers_twice(self):
    store, resolve_id = self.build_store()
    service, _ = build_service(
      resolve_service=store, table=StubTable(assignment=KNOWN_ASSIGNED)
    )

    service.inspect({"resolve_id": resolve_id})

    self.assertEqual(service.inspect({"resolve_id": resolve_id}).person_id, 12)

  def test_no_second_receipt_is_issued(self):
    """An inspection is not a resolve.  Handing back a fresh id would leave the
    page holding two receipts for one link and no rule about which to submit."""
    store, resolve_id = self.build_store()
    service, _ = build_service(
      resolve_service=store, table=StubTable(assignment=None)
    )

    service.inspect({"resolve_id": resolve_id})

    self.assertEqual(store._store.tracked(), 1)

  def test_another_user_cannot_inspect_or_assign_the_receipt(self):
    store, resolve_id = self.build_store()
    service, _ = build_service(
      resolve_service=store, table=StubTable(assignment=None)
    )

    with self.assertRaises(ResolutionNotFound):
      service.inspect({"resolve_id": resolve_id}, app_user_id=9002)
    with self.assertRaises(ResolutionNotFound):
      service.assign({
        "resolve_id": resolve_id,
        "target": {"kind": "new", "display_name": "程儿"},
        "role": "alt",
      }, app_user_id=9002)

  def test_the_receipt_is_read_rather_than_the_link_followed_again(self):
    """The identity is read from the resolution this server stored, url and
    verdict included.  Following ``source_url`` again would repeat the request
    and the decision, in a place with none of the resolver's checks - and could
    legitimately name a different resource minutes later."""
    reader = StubIdentityReader()
    service, _ = build_service(table=StubTable(assignment=None), reader=reader)

    service.inspect(inspect_request())

    self.assertEqual(len(reader.resolutions), 1)
    self.assertEqual(reader.resolutions[0].resolved_url, OWNER_URL)


class InspectionIdentityRefreshTest(unittest.TestCase):
  """A nickname may be brought up to date without anybody being re-filed.

  Before this, the only way to refresh a stored nickname was to run the
  assignment again - which meant clicking "confirm" on a screen that had just
  said the account was already added.  So the refresh happens here, and it
  touches identity columns only.
  """

  def test_a_known_account_has_its_identity_refreshed(self):
    service, table = build_service(
      table=StubTable(assignment=KNOWN_ASSIGNED),
      reader=StubIdentityReader(
        identity={
          "owner_user_id": "acc-9",
          "sec_user_id": SEC_UID,
          "nickname": "程小程",
        }
      ),
    )

    service.inspect(inspect_request())

    self.assertEqual(table.identity_refreshes, [("acc-9", SEC_UID, "程小程")])

  def test_a_known_unfiled_account_is_refreshed_too(self):
    service, table = build_service(table=StubTable(assignment=KNOWN_UNASSIGNED))

    service.inspect(inspect_request())

    self.assertEqual(len(table.identity_refreshes), 1)

  def test_an_unknown_account_is_not_written_into_existence(self):
    """The decisive one.  An upsert here would create the ``share_url`` row this
    lookup just failed to find, so the next inspection of the same link would
    report a known account - a read that changes its own answer, and one that
    files an account somebody merely pasted."""
    service, table = build_service(table=StubTable(assignment=None))

    found = service.inspect(inspect_request())

    self.assertFalse(found.known_account)
    self.assertEqual(table.identity_refreshes, [])

  def test_a_refusal_to_write_does_not_lose_the_answer(self):
    """The lookup succeeded; only the courtesy write failed.  Reporting that as
    a failed inspection would block the page for a reason that has nothing to
    do with what it asked."""
    service, table = build_service(
      table=StubTable(
        assignment=KNOWN_ASSIGNED,
        refresh_failure=DatabaseWriteBlocked("schema not ready"),
      )
    )

    found = service.inspect(inspect_request())

    self.assertEqual(found.person_id, 12)
    self.assertEqual(len(table.identity_refreshes), 1)

  def test_an_unexpected_write_failure_does_not_lose_the_answer_either(self):
    service, _ = build_service(
      table=StubTable(
        assignment=KNOWN_ASSIGNED, refresh_failure=RuntimeError("gone")
      )
    )

    self.assertEqual(service.inspect(inspect_request()).person_id, 12)


class InspectionLookupUnavailableTest(unittest.TestCase):
  """"We could not ask" must never arrive as "this account is new".

  The two sentences lead to opposite actions.  The second one tells the user to
  create a person, and if the account was in fact already filed, that is a
  duplicate person created by an outage - the exact thing this whole feature
  exists to prevent.
  """

  def test_a_database_failure_is_reported_rather_than_answered(self):
    service, _ = build_service(
      table=StubTable(lookup_failure=RuntimeError("connection refused"))
    )

    with self.assertRaises(PersonLookupUnavailable):
      service.inspect(inspect_request())

  def test_it_answers_503_because_no_request_could_fix_it(self):
    service, _ = build_service(
      table=StubTable(lookup_failure=RuntimeError("connection refused"))
    )

    with self.assertRaises(PersonAssignmentError) as caught:
      service.inspect(inspect_request())

    self.assertEqual(caught.exception.status_code, 503)
    self.assertEqual(caught.exception.kind, "person_lookup_unavailable")

  def test_it_never_degrades_into_an_unknown_account(self):
    service, _ = build_service(
      table=StubTable(lookup_failure=RuntimeError("connection refused"))
    )

    with self.assertRaises(PersonAssignmentError) as caught:
      service.inspect(inspect_request())

    self.assertNotEqual(caught.exception.kind, "account_not_known")

  def test_the_database_message_does_not_reach_the_browser(self):
    """It carries hosts, users and sql.  The log gets it; the page gets a
    sentence about what to do."""
    service, _ = build_service(
      table=StubTable(
        lookup_failure=RuntimeError("Access denied for 'smsd'@'10.0.0.4'")
      )
    )

    with self.assertRaises(PersonLookupUnavailable) as caught:
      service.inspect(inspect_request())

    self.assertNotIn("10.0.0.4", str(caught.exception))
    self.assertNotIn("Access denied", str(caught.exception))


class InspectionWritesNothingTest(unittest.TestCase):
  """An inspection is a hint for the interface, not an authorisation.

  Nothing about who holds what may change on the way to answering it, and
  nothing it says may be carried into the write: the assignment transaction
  discovers ownership again, under its own locks, and refuses on what it finds
  there.
  """

  def test_no_person_is_created(self):
    service, table = build_service(table=StubTable(assignment=None))

    service.inspect(inspect_request())

    self.assertEqual(table.created_people, [])

  def test_no_account_is_attached(self):
    service, table = build_service(table=StubTable(assignment=KNOWN_UNASSIGNED))

    service.inspect(inspect_request())

    self.assertEqual(table.attachments, [])

  def test_no_assignment_transaction_is_run(self):
    service, table = build_service(table=StubTable(assignment=KNOWN_ASSIGNED))

    service.inspect(inspect_request())

    self.assertEqual(table.assignments, [])

  def test_a_filed_account_is_not_quietly_refiled(self):
    """Not even to the person it already belongs to.  "Already added" is a
    thing to report, not a thing to do again."""
    service, table = build_service(table=StubTable(assignment=KNOWN_ASSIGNED))

    service.inspect(inspect_request())

    self.assertEqual(table.assignments, [])
    self.assertEqual(table.attachments, [])


class InspectionIsNotWriteAuthorityTest(unittest.TestCase):
  """What the inspection saw has no standing once the write begins.

  The gap between the two is a user reading a screen, which is unbounded.  So
  every rule is re-decided in the transaction, and an inspection that said
  "nobody holds this" cannot become permission to take it from somebody who
  does.
  """

  def test_an_account_filed_after_the_inspection_still_refuses_the_write(self):
    """The race the page cannot avoid: inspected as unfiled, filed by somebody
    else while the user was choosing, then submitted."""
    table = StubTable(assignment=None)
    service, _ = build_service(table=table)

    found = service.inspect(inspect_request())
    self.assertFalse(found.known_account)

    table.failure = AccountAttachedElsewhere(7, "别人")
    with self.assertRaises(AccountAlreadyAttached):
      service.assign(existing_request())

  def test_the_write_is_never_sent_with_the_move_already_agreed(self):
    """An inspection naming the current holder is information, not consent.
    Filling ``allow_move`` in on the strength of it would take an account away
    from somebody on the basis of a screen the user only read."""
    table = StubTable(assignment=KNOWN_ASSIGNED)
    service, _ = build_service(table=table)

    service.inspect(inspect_request())
    service.assign(existing_request())

    self.assertFalse(table.assignments[0]["allow_move"])

  def test_a_second_inspection_reports_the_state_of_the_moment(self):
    """Nothing is remembered between calls.

    An account can change hands while a screen sits open, so an inspection is
    true of the instant it was taken and of nothing else.  Answering the second
    question from the first answer would show the user a holder who let go of
    the account minutes ago.
    """
    table = StubTable(assignment=KNOWN_ASSIGNED)
    service, _ = build_service(table=table)
    self.assertEqual(service.inspect(inspect_request()).person_id, 12)

    moved = dict(KNOWN_ASSIGNED)
    moved.update({"person_id": 20, "display_name": "别人", "role": "alt"})
    table._assignment = moved

    found = service.inspect(inspect_request())

    self.assertEqual(found.person_id, 20)
    self.assertEqual(found.role, "alt")

  def test_every_inspection_asks_the_database_again(self):
    table = StubTable(assignment=KNOWN_ASSIGNED)
    service, _ = build_service(table=table)

    service.inspect(inspect_request())
    service.inspect(inspect_request())

    self.assertEqual(table.assignment_lookups, ["acc-9", "acc-9"])

  def test_the_person_written_to_is_the_one_the_request_names(self):
    """Never the one the inspection found.  The user may well be moving the
    account, and silently writing it back where it already was would carry out
    the opposite of what they asked."""
    table = StubTable(assignment=KNOWN_ASSIGNED)
    service, _ = build_service(table=table)

    service.inspect(inspect_request())
    service.assign(existing_request())

    self.assertEqual(table.assignments[0]["person_id"], 12)


if __name__ == "__main__":
  unittest.main()
