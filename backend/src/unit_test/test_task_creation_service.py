import unittest

from backend.src.platform.resource_resolution import (
  RESOURCE_TYPE_LIVE,
  RESOURCE_TYPE_OWNER,
  RESOURCE_TYPE_POST,
  ResourceResolution,
)
from backend.src.service.task_creation import (
  InvalidTaskOptions,
  ResolutionNotFound,
  TaskCreateError,
  TaskCreationResult,
  TaskCreationService,
  TaskCreationUnavailable,
  UnknownTaskType,
  UnsupportedTaskForResource,
)
from backend.src.task.model import (
  TASK_TYPE_LIVE_PROBE,
  TASK_TYPE_LIVE_RECORD,
  TASK_TYPE_OWNER_BATCH_DOWNLOAD,
  TASK_TYPE_POST_DOWNLOAD,
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


def owner_resolution():
  return ResourceResolution(
    platform="douyin",
    resource_type=RESOURCE_TYPE_OWNER,
    source_url=SHORT_LINK,
    resolved_url=OWNER_URL,
    identity={"sec_user_id": SEC_UID},
  )


RESOLUTIONS = {
  RESOURCE_TYPE_POST: post_resolution,
  RESOURCE_TYPE_LIVE: live_resolution,
  RESOURCE_TYPE_OWNER: owner_resolution,
}

##
## The one matrix P6 allows.  Stated here as data so the rejection tests can be
## the complement of it rather than a hand-written list that could drift.
##
ALLOWED = {
  RESOURCE_TYPE_POST: TASK_TYPE_POST_DOWNLOAD,
  RESOURCE_TYPE_LIVE: TASK_TYPE_LIVE_RECORD,
  RESOURCE_TYPE_OWNER: TASK_TYPE_OWNER_BATCH_DOWNLOAD,
}

EVERY_TASK_TYPE = (
  TASK_TYPE_POST_DOWNLOAD,
  TASK_TYPE_LIVE_RECORD,
  TASK_TYPE_OWNER_BATCH_DOWNLOAD,
  TASK_TYPE_LIVE_PROBE,
)


class RecordingResolveService:
  """Stands in for the app's ResourceResolveService, recording every lookup."""

  def __init__(self, receipts=None):
    self.receipts = dict(receipts or {})
    self.gets = []

  def get(self, resolve_id):
    self.gets.append(resolve_id)
    return self.receipts.get(resolve_id)


class RecordingRunner:
  """A tracked runner: records how it was called, answers with a task id."""

  def __init__(self, task_id="task-1", error=None):
    self.task_id = task_id
    self.error = error
    self.calls = []

  def _record(self, kwargs):
    self.calls.append(dict(kwargs))
    if self.error is not None:
      raise self.error
    ##
    ## A fresh id per call, so a test can tell two creations apart.
    ##
    return "{}-{}".format(self.task_id, len(self.calls))

  def submit_tracked(self, **kwargs):
    return self._record(kwargs)

  def start_all_tracked(self, **kwargs):
    return self._record(kwargs)


def build_service(receipts=None, post=None, live=None, owner=None):
  resolve_service = RecordingResolveService(receipts)
  post = post if post is not None else RecordingRunner("task-post")
  live = live if live is not None else RecordingRunner("task-live")
  owner = owner if owner is not None else RecordingRunner("task-owner")
  service = TaskCreationService(
    resolve_service=resolve_service,
    direct_post_service=post,
    live_record_service=live,
    owner_service_factory=lambda: owner,
  )
  return service, resolve_service, post, live, owner


def options_for(task_type):
  """The one option set each task type accepts, so matrix tests are about the matrix."""
  if task_type == TASK_TYPE_OWNER_BATCH_DOWNLOAD:
    return {"mode": "all"}
  return {}


class TaskTypeVocabularyTest(unittest.TestCase):
  """``task_type`` is the existing wire vocabulary, not a new one."""

  def test_a_word_that_is_not_a_task_type_is_refused(self):
    """P6 reuses ``post_download``; ``download`` is a second vocabulary."""
    service, resolve_service, post, _, _ = build_service(
      {"R": post_resolution()}
    )

    for word in ("download", "record", "download_owner", "", "post-download"):
      with self.subTest(word=word):
        with self.assertRaises(UnknownTaskType) as caught:
          service.create("R", word, {})
        self.assertEqual(caught.exception.status_code, 400)

    self.assertEqual(post.calls, [])

  def test_the_vocabulary_is_checked_before_the_receipt_is_read(self):
    """A garbage task type must not be reported as an expired receipt.

    Telling the user to resolve again would send them round a loop that cannot
    fix what is actually wrong with the request.
    """
    service, resolve_service, _, _, _ = build_service({})

    with self.assertRaises(UnknownTaskType):
      service.create("expired-receipt", "download", {})

    self.assertEqual(resolve_service.gets, [])

  def test_a_task_type_that_is_not_a_string_is_refused(self):
    service, _, _, _, _ = build_service({"R": post_resolution()})

    for value in (None, 42, ["post_download"]):
      with self.subTest(value=value):
        with self.assertRaises(UnknownTaskType):
          service.create("R", value, {})


class ReceiptTest(unittest.TestCase):
  """Only the receipt is trusted, and it is read from the server's own store."""

  def test_an_unknown_receipt_is_not_found(self):
    service, _, post, live, owner = build_service({})

    with self.assertRaises(ResolutionNotFound) as caught:
      service.create("nope", TASK_TYPE_POST_DOWNLOAD, {})

    self.assertEqual(caught.exception.status_code, 404)
    self.assertEqual(caught.exception.kind, "resolution_not_found")

  def test_an_expired_receipt_starts_no_work(self):
    """A receipt that aged out must not be re-resolved or guessed at."""
    service, _, post, live, owner = build_service({})

    for task_type in (TASK_TYPE_POST_DOWNLOAD, TASK_TYPE_LIVE_RECORD,
                      TASK_TYPE_OWNER_BATCH_DOWNLOAD):
      with self.subTest(task_type=task_type):
        with self.assertRaises(ResolutionNotFound):
          service.create("gone", task_type, options_for(task_type))

    self.assertEqual(post.calls, [])
    self.assertEqual(live.calls, [])
    self.assertEqual(owner.calls, [])

  def test_the_receipt_is_read_exactly_once(self):
    """The whole creation runs off one detached snapshot.

    Reading twice would let a receipt expiring mid-request fail a creation that
    had already been accepted on a valid resolution.
    """
    service, resolve_service, _, _, _ = build_service({"R": post_resolution()})

    service.create("R", TASK_TYPE_POST_DOWNLOAD, {})

    self.assertEqual(resolve_service.gets, ["R"])

  def test_the_receipt_is_not_consumed(self):
    """P5's store is non-destructive and P6 must keep it that way."""
    service, resolve_service, _, _, _ = build_service({"R": post_resolution()})

    service.create("R", TASK_TYPE_POST_DOWNLOAD, {})

    self.assertIsNotNone(resolve_service.receipts.get("R"))


class CompatibilityMatrixTest(unittest.TestCase):
  def test_application_user_is_forwarded_to_every_tracked_runner(self):
    for resource_type, task_type in ALLOWED.items():
      with self.subTest(resource_type=resource_type):
        service, _, post, live, owner = build_service(
          {"R": RESOLUTIONS[resource_type]()}
        )

        service.create("R", task_type, options_for(task_type), app_user_id=31)

        calls = post.calls + live.calls + owner.calls
        self.assertEqual(len(calls), 1)
        self.assertEqual(calls[0]["app_user_id"], 31)

  """Exactly three resource/task pairs are work this stage knows how to start."""

  def test_each_allowed_pair_reaches_its_runner(self):
    expected_runner = {
      RESOURCE_TYPE_POST: "post",
      RESOURCE_TYPE_LIVE: "live",
      RESOURCE_TYPE_OWNER: "owner",
    }
    for resource_type, task_type in ALLOWED.items():
      with self.subTest(resource_type=resource_type):
        service, _, post, live, owner = build_service(
          {"R": RESOLUTIONS[resource_type]()}
        )
        runners = {"post": post, "live": live, "owner": owner}

        result = service.create("R", task_type, options_for(task_type))

        chosen = runners.pop(expected_runner[resource_type])
        self.assertEqual(len(chosen.calls), 1)
        for name, untouched in runners.items():
          self.assertEqual(untouched.calls, [], "{} must not run".format(name))
        self.assertEqual(result.task_type, task_type)

    ##
    ## Three pairs, and the rejection test below is the complement of this map,
    ## so widening one without the other cannot pass unnoticed.
    ##
    self.assertEqual(len(ALLOWED), 3)

  def test_every_other_pair_is_refused_and_starts_nothing(self):
    for resource_type in RESOLUTIONS:
      for task_type in EVERY_TASK_TYPE:
        if ALLOWED[resource_type] == task_type:
          continue
        with self.subTest(resource_type=resource_type, task_type=task_type):
          service, _, post, live, owner = build_service(
            {"R": RESOLUTIONS[resource_type]()}
          )

          with self.assertRaises(UnsupportedTaskForResource) as caught:
            service.create("R", task_type, options_for(task_type))

          self.assertEqual(caught.exception.status_code, 400)
          self.assertEqual(post.calls, [])
          self.assertEqual(live.calls, [])
          self.assertEqual(owner.calls, [])

  def test_live_probe_cannot_be_created_from_a_receipt(self):
    """Probing is a history-page batch over saved owners, not a resolved url.

    Accepting it here would mint a second live-probe workflow that has to be
    kept in step with the first for no gain.
    """
    for resource_type in RESOLUTIONS:
      with self.subTest(resource_type=resource_type):
        service, _, _, _, _ = build_service({"R": RESOLUTIONS[resource_type]()})

        with self.assertRaises(UnsupportedTaskForResource):
          service.create("R", TASK_TYPE_LIVE_PROBE, {})

  def test_every_refusal_is_one_family_the_route_can_map(self):
    self.assertTrue(issubclass(ResolutionNotFound, TaskCreateError))
    self.assertTrue(issubclass(UnknownTaskType, TaskCreateError))
    self.assertTrue(issubclass(UnsupportedTaskForResource, TaskCreateError))


class TaskCreationResultTest(unittest.TestCase):
  """The minimal receipt of a created task."""

  def test_it_carries_the_task_its_type_and_the_receipt_it_came_from(self):
    service, _, post, _, _ = build_service({"R": post_resolution()})

    result = service.create("R", TASK_TYPE_POST_DOWNLOAD, {})

    self.assertIsInstance(result, TaskCreationResult)
    self.assertEqual(result.task_id, "task-post-1")
    self.assertEqual(result.task_type, TASK_TYPE_POST_DOWNLOAD)
    self.assertEqual(result.resolve_id, "R")

  def test_it_cannot_be_reassigned(self):
    result = TaskCreationResult(
      task_id="T", task_type=TASK_TYPE_POST_DOWNLOAD, resolve_id="R"
    )

    with self.assertRaises(Exception):
      result.task_id = "other"


class PostAndLiveOptionsTest(unittest.TestCase):
  """Neither has a task-level option yet, so neither may be given one."""

  def test_no_options_at_all_is_accepted(self):
    for resource_type in (RESOURCE_TYPE_POST, RESOURCE_TYPE_LIVE):
      for options in (None, {}):
        with self.subTest(resource_type=resource_type, options=options):
          service, _, _, _, _ = build_service({"R": RESOLUTIONS[resource_type]()})

          result = service.create("R", ALLOWED[resource_type], options)

          self.assertTrue(result.task_id)

  def test_an_unknown_option_is_refused_rather_than_ignored(self):
    """"Accepted but had no effect" is the worst answer an api can give.

    A client asking for 1080p and silently getting whatever the config says
    would believe a promise nothing here made.
    """
    for resource_type in (RESOURCE_TYPE_POST, RESOURCE_TYPE_LIVE):
      for options in ({"quality": "1080p"}, {"mode": "all"}, {"unknown": 1}):
        with self.subTest(resource_type=resource_type, options=options):
          service, _, post, live, _ = build_service(
            {"R": RESOLUTIONS[resource_type]()}
          )

          with self.assertRaises(InvalidTaskOptions) as caught:
            service.create("R", ALLOWED[resource_type], options)

          self.assertEqual(caught.exception.status_code, 400)
          self.assertEqual(post.calls, [])
          self.assertEqual(live.calls, [])

  def test_options_that_are_not_an_object_are_refused(self):
    service, _, _, _, _ = build_service({"R": post_resolution()})

    for options in ([], "all", 7):
      with self.subTest(options=options):
        with self.assertRaises(InvalidTaskOptions):
          service.create("R", TASK_TYPE_POST_DOWNLOAD, options)


class OwnerOptionsTest(unittest.TestCase):
  """Downloading an entire back catalogue has to be asked for in words."""

  def test_mode_all_is_accepted(self):
    service, _, _, _, owner = build_service({"R": owner_resolution()})

    result = service.create(
      "R", TASK_TYPE_OWNER_BATCH_DOWNLOAD, {"mode": "all"}
    )

    self.assertTrue(result.task_id)
    self.assertEqual(len(owner.calls), 1)

  def test_a_missing_mode_is_refused(self):
    """An owner link does not mean "download everything" on its own.

    It is the most expensive thing this api can start - hundreds of posts, a
    long walk, real quota - so it is never the default reading of a url.
    """
    service, _, _, _, owner = build_service({"R": owner_resolution()})

    for options in (None, {}):
      with self.subTest(options=options):
        with self.assertRaises(InvalidTaskOptions):
          service.create("R", TASK_TYPE_OWNER_BATCH_DOWNLOAD, options)

    self.assertEqual(owner.calls, [])

  def test_selected_mode_is_refused_for_now(self):
    """Selected needs post payloads, and an owner receipt has only a sec_user_id.

    The existing owner page keeps those payloads in its own cache and its own
    endpoint still serves that flow; inventing a second route to it here would
    mean guessing which posts the user meant.
    """
    service, _, _, _, owner = build_service({"R": owner_resolution()})

    with self.assertRaises(InvalidTaskOptions):
      service.create(
        "R",
        TASK_TYPE_OWNER_BATCH_DOWNLOAD,
        {"mode": "selected", "aweme_ids": [AWEME_ID]},
      )

    self.assertEqual(owner.calls, [])

  def test_an_unknown_mode_is_refused(self):
    service, _, _, _, _ = build_service({"R": owner_resolution()})

    for mode in ("ALL", "All", "everything", "", None, 1):
      with self.subTest(mode=mode):
        with self.assertRaises(InvalidTaskOptions):
          service.create("R", TASK_TYPE_OWNER_BATCH_DOWNLOAD, {"mode": mode})

  def test_an_extra_option_beside_a_valid_mode_is_refused(self):
    service, _, _, _, owner = build_service({"R": owner_resolution()})

    with self.assertRaises(InvalidTaskOptions):
      service.create(
        "R",
        TASK_TYPE_OWNER_BATCH_DOWNLOAD,
        {"mode": "all", "aweme_ids": [AWEME_ID]},
      )

    self.assertEqual(owner.calls, [])


class TrustedExecutionInputTest(unittest.TestCase):
  """What the runner is handed comes from the snapshot, never from a client."""

  def test_a_post_runs_against_the_resolved_url_and_the_trusted_id(self):
    service, _, post, _, _ = build_service({"R": post_resolution()})

    service.create("R", TASK_TYPE_POST_DOWNLOAD, {})

    self.assertEqual(
      post.calls[0],
      {
        "aweme_id": AWEME_ID,
        "resolved_url": POST_URL,
        "source_url": SHORT_LINK,
        "resolve_id": "R",
      },
    )

  def test_a_post_is_never_executed_against_the_short_link(self):
    """P5 already followed it, once and safely.  Doing it again would repeat
    both the decision and the request that made it."""
    service, _, post, _, _ = build_service({"R": post_resolution()})

    service.create("R", TASK_TYPE_POST_DOWNLOAD, {})

    self.assertNotEqual(post.calls[0]["resolved_url"], SHORT_LINK)

  def test_a_recording_runs_against_the_resolved_url(self):
    service, _, _, live, _ = build_service({"R": live_resolution()})

    service.create("R", TASK_TYPE_LIVE_RECORD, {})

    self.assertEqual(
      live.calls[0],
      {"resolved_url": LIVE_URL, "source_url": SHORT_LINK, "resolve_id": "R"},
    )

  def test_an_owner_walk_runs_against_the_trusted_sec_user_id(self):
    service, _, _, _, owner = build_service({"R": owner_resolution()})

    service.create("R", TASK_TYPE_OWNER_BATCH_DOWNLOAD, {"mode": "all"})

    self.assertEqual(
      owner.calls[0],
      {
        "sec_user_id": SEC_UID,
        "resolved_url": OWNER_URL,
        "source_url": SHORT_LINK,
        "resolve_id": "R",
      },
    )

  def test_there_is_no_way_to_pass_an_identity_in(self):
    """The signature is the guarantee: no identity argument exists to forge."""
    service, _, post, _, _ = build_service({"R": post_resolution()})

    with self.assertRaises(TypeError):
      service.create("R", TASK_TYPE_POST_DOWNLOAD, {}, aweme_id="999")

    self.assertEqual(post.calls, [])


class RepeatedCreationTest(unittest.TestCase):
  """One receipt may be acted on more than once, and each time is its own task."""

  def test_the_same_receipt_creates_two_independent_tasks(self):
    """A retried click, or a deliberate second recording.  Whether that is
    wise is the user's call; silently returning the first task would hide
    that a second was never started."""
    service, resolve_service, post, _, _ = build_service({"R": post_resolution()})

    first = service.create("R", TASK_TYPE_POST_DOWNLOAD, {})
    second = service.create("R", TASK_TYPE_POST_DOWNLOAD, {})

    self.assertNotEqual(first.task_id, second.task_id)
    self.assertEqual(len(post.calls), 2)
    self.assertEqual(resolve_service.gets, ["R", "R"])
    self.assertIsNotNone(resolve_service.receipts.get("R"))

  def test_no_deduplication_is_attempted(self):
    service, _, post, _, _ = build_service({"R": post_resolution()})

    ids = {service.create("R", TASK_TYPE_POST_DOWNLOAD, {}).task_id
           for _ in range(3)}

    self.assertEqual(len(ids), 3)
    self.assertEqual(len(post.calls), 3)


class RunnerAvailabilityTest(unittest.TestCase):
  """A creation path that was never wired is a deployment fault, not a 400."""

  def build_without(self, resource_type, **missing):
    resolve_service = RecordingResolveService({"R": RESOLUTIONS[resource_type]()})
    defaults = {
      "direct_post_service": RecordingRunner("task-post"),
      "live_record_service": RecordingRunner("task-live"),
      "owner_service_factory": lambda: RecordingRunner("task-owner"),
    }
    defaults.update(missing)
    return TaskCreationService(resolve_service=resolve_service, **defaults)

  def test_a_missing_post_runner_is_unavailable(self):
    service = self.build_without(RESOURCE_TYPE_POST, direct_post_service=None)

    with self.assertRaises(TaskCreationUnavailable) as caught:
      service.create("R", TASK_TYPE_POST_DOWNLOAD, {})

    self.assertEqual(caught.exception.status_code, 503)
    self.assertEqual(caught.exception.kind, "task_creation_unavailable")

  def test_a_missing_live_runner_is_unavailable(self):
    service = self.build_without(RESOURCE_TYPE_LIVE, live_record_service=None)

    with self.assertRaises(TaskCreationUnavailable):
      service.create("R", TASK_TYPE_LIVE_RECORD, {})

  def test_a_missing_owner_factory_is_unavailable(self):
    service = self.build_without(
      RESOURCE_TYPE_OWNER, owner_service_factory=None
    )

    with self.assertRaises(TaskCreationUnavailable):
      service.create("R", TASK_TYPE_OWNER_BATCH_DOWNLOAD, {"mode": "all"})

  def test_an_owner_factory_that_yields_nothing_is_unavailable(self):
    service = self.build_without(
      RESOURCE_TYPE_OWNER, owner_service_factory=lambda: None
    )

    with self.assertRaises(TaskCreationUnavailable):
      service.create("R", TASK_TYPE_OWNER_BATCH_DOWNLOAD, {"mode": "all"})

  def test_unavailability_outranks_a_bad_option(self):
    """Both are true at once, and only one of them the caller can act on.

    With nothing wired to run the work, no correction to the request would make
    it start; saying "bad option" would send the user to fix their end of a
    fault that is entirely this deployment's.
    """
    service = self.build_without(RESOURCE_TYPE_POST, direct_post_service=None)

    with self.assertRaises(TaskCreationUnavailable):
      service.create("R", TASK_TYPE_POST_DOWNLOAD, {"quality": "1080p"})

  def test_every_refusal_stays_in_one_family(self):
    self.assertTrue(issubclass(InvalidTaskOptions, TaskCreateError))
    self.assertTrue(issubclass(TaskCreationUnavailable, TaskCreateError))


if __name__ == "__main__":
  unittest.main()
