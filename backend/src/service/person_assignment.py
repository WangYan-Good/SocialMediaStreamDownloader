##<<Base>>
from dataclasses import dataclass

##<<Third-part>>
from backend.src.database.orm.models.person import (
  ACCOUNT_ROLES,
  ROLE_MAIN,
)

##
## The one platform these tables record.  Named here rather than taken from a
## caller so the guarded detach cannot be pointed at a different one by mistake.
##
PLATFORM = "douyin"
from backend.src.database.schema_guard import DatabaseWriteBlocked
from backend.src.library.loglib import get_logger
from backend.src.database.table.person_identity import (
  AccountAttachedElsewhere,
  AssignmentRaced,
  LastMainRemoval,
  MainAlreadyAssigned,
  NotAttached,
  PersonMissing,
  UnknownRole,
)


##
## >>============================= failures =============================>>
##

class PersonAssignmentError(Exception):
  """One of the known ways an assignment can be refused.

  Every refusal carries the ``kind`` logs record and the ``status_code`` the api
  answers with, so neither is re-derived from the message text at the edge -
  which is how "already has a main" and "no such person" end up sharing a status
  nobody chose.

  ``details`` is what the page needs in order to offer the user their next move,
  and nothing else.  A refusal reaches a browser, so it says who holds an
  account and what the current main is called; it does not say what the platform
  answered, what the sql was, or anything about rows the user did not ask about.
  """

  kind = "person_assignment_failed"
  status_code = 400

  def details(self) -> dict:
    return {}


class InvalidAssignment(PersonAssignmentError):
  """The request does not describe an assignment this service can make.

  Unknown fields land here rather than being ignored: "accepted but had no
  effect" is the worst answer an api can give, because the caller goes on
  believing a promise nothing here made.
  """

  kind = "invalid_assignment"


class ResolutionNotFound(PersonAssignmentError):
  """The receipt is unknown or has aged out.

  Answered 404 and never repaired.  Re-resolving the link here would mean the
  server deciding what the user meant, minutes after they asked - which is the
  one thing the receipt exists to prevent.  They resolve again instead.
  """

  kind = "resolution_not_found"
  status_code = 404


class OwnerIdentityUnavailable(PersonAssignmentError):
  """The link named no account this program can file anything under.

  ``person_account`` is keyed on ``owner_user_id``, and the download paths look
  the owner up by exactly that id, so a blank one would create a row nothing can
  ever match.  No person is created.
  """

  kind = "owner_identity_unavailable"


class PersonNotFound(PersonAssignmentError):
  """The person named by the request does not exist.

  Reported rather than created: an id that is merely stale must not silently
  mint a second person holding the same accounts.
  """

  kind = "person_not_found"
  status_code = 404


class AccountAlreadyAttached(PersonAssignmentError):
  """The account belongs to somebody else, and the move was not asked for.

  409 because nothing is wrong with the request - it describes a state the user
  has to decide about.  The answer to this one is ``allow_move``.
  """

  kind = "account_already_attached"
  status_code = 409

  def __init__(self, message, person_id=None, display_name=None) -> None:
    super().__init__(message)
    self._person_id = person_id
    self._display_name = display_name

  def details(self) -> dict:
    return {
      "current_person": {
        "person_id": self._person_id,
        "display_name": self._display_name,
      }
    }


class MainAccountConflict(PersonAssignmentError):
  """The person already has a main account, and this is not it.

  The answer to this one is ``replace_main``, which is why it has to stay
  distinguishable from the refusal above rather than both being "409".
  """

  kind = "main_account_conflict"
  status_code = 409

  def __init__(self, message, owner_user_id=None, nickname=None) -> None:
    super().__init__(message)
    self._owner_user_id = owner_user_id
    self._nickname = nickname

  def details(self) -> dict:
    return {
      "current_main": {
        "owner_user_id": self._owner_user_id,
        "nickname": self._nickname,
      }
    }


class LastMainRemovalConflict(PersonAssignmentError):
  """A person's only main account was about to stop being their main.

  409 for the same reason the two above are: the request is well formed and
  describes a state the user has to decide about.  Its answer is different from
  either of theirs, though - ``replace_main`` fixes the *target* person and
  ``allow_move`` fixes a busy account, while this one needs the person being
  left behind to be given a main of their own first.  So it carries who that
  person is and which account was theirs, and answers with its own ``kind``.
  """

  kind = "last_main_removal_conflict"
  status_code = 409

  def __init__(
    self,
    message,
    person_id=None,
    display_name=None,
    owner_user_id=None,
    nickname=None,
  ) -> None:
    super().__init__(message)
    self._person_id = person_id
    self._display_name = display_name
    self._owner_user_id = owner_user_id
    self._nickname = nickname

  def details(self) -> dict:
    return {
      ##
      ## Named "source" because the commonest way to hit this is moving an
      ## account to somebody else: the person harmed is the one being moved
      ## *from*, which is not the person the request names.
      ##
      "source_person": {
        "person_id": self._person_id,
        "display_name": self._display_name,
      },
      "current_main": {
        "owner_user_id": self._owner_user_id,
        "nickname": self._nickname,
      },
    }


class AssignmentConflictRetryable(PersonAssignmentError):
  """The account changed hands while this request was being processed.

  409, and the honest answer is "try again": the request was fine, it simply
  described a world that stopped being true between two statements.  Retrying
  discovers the new owner and locks it properly, which is why this is not
  something the user has to decide about - only something they have to repeat.
  """

  kind = "assignment_raced"
  status_code = 409


class AccountNotKnown(PersonAssignmentError):
  """The account is one this program has never seen.

  404, and refused before anything is written.  The endpoints that take an
  ``owner_user_id`` from a client would otherwise create a ``share_url`` row for
  whatever id arrived, which is a fact about the world this server has no
  evidence for.
  """

  kind = "account_not_known"
  status_code = 404


class AccountNotAttached(PersonAssignmentError):
  """The account being unmarked is not marked as belonging to anybody.

  404 rather than a quiet success: "removed nothing" and "removed the thing you
  meant" look identical to a page that is only told it worked.
  """

  kind = "account_not_attached"
  status_code = 404


class PersonLookupUnavailable(PersonAssignmentError):
  """Who holds this account could not be read at all.

  503, and deliberately its own refusal rather than an answer.  "This account is
  unknown" is what the page turns into an invitation to create a person, so an
  outage reported that way would produce a duplicate person for every account
  pasted during it - and duplicates of exactly the kind nothing downstream can
  tell apart afterwards.

  The distinction the whole endpoint rests on: not knowing is not the same as
  there being nothing to know.
  """

  kind = "person_lookup_unavailable"
  status_code = 503


class AssignmentUnavailable(PersonAssignmentError):
  """Nothing here can be written at the moment - the schema guard says so.

  A deployment fault rather than a bad request, so it answers 503: no correction
  the caller could make to the request would let it through.
  """

  kind = "assignment_unavailable"
  status_code = 503


##
## >>============================= result =============================>>
##

@dataclass(frozen=True)
class PersonAssignmentResult:
  """What one accepted assignment produced.

  Deliberately five fields, all of them the caller's own request read back.  A
  sec id, a room, a post payload or a whole person snapshot would each be
  something a client could start depending on, and none of them is an answer to
  "did this go where I asked".
  """

  person_id: int
  owner_user_id: str
  role: str
  created_person: bool
  display_name: str


@dataclass(frozen=True)
class PersonIdentityInspection:
  """What one link turns out to be, and whether this server already has it.

  Three fields answer the question the page asks, and they are deliberately
  three rather than one: ``known_account`` says whether this program has ever
  heard of the account, and ``person_id`` says whether anybody has filed it.
  Collapsing them would lose the commonest case of all - an account downloaded
  months ago that nobody has yet put under a person.

  The identity is what the platform says right now, so the user recognises the
  account they just pasted.  ``display_name`` is what the *person* is called,
  which is a name somebody typed and is not updated to follow a nickname.

  Nothing here describes a folder, a url or a row id beyond the person's own.
  A directory is the download paths' business and a resolved url can carry a
  signature; neither is needed to say "you have already added this".
  """

  owner_user_id: str
  sec_user_id: str
  nickname: str
  known_account: bool
  person_id: int
  display_name: str
  role: str


##
## >>============================= the request =============================>>
##

##
## The whole of what an assignment request may say.  ``owner_user_id``,
## ``sec_user_id``, ``nickname`` and ``resolved_url`` are conspicuously absent:
## those describe the account, which is exactly the thing this endpoint declines
## to take a browser's word for.  Accepting one would let a client attach an
## owner this server never resolved.
##
_REQUEST_FIELDS = ("resolve_id", "target", "role", "allow_move", "replace_main")

TARGET_KIND_NEW = "new"
TARGET_KIND_EXISTING = "existing"
TARGET_KINDS = (TARGET_KIND_NEW, TARGET_KIND_EXISTING)

##
## A new person may be named and annotated.  An existing one may not: renaming
## is ``PATCH /api/person/<id>``, its own deliberate operation, and accepting a
## name here would make a rename happen as a side effect of attaching an
## account - which is not what the user asked for and not what they would see.
##
_NEW_TARGET_FIELDS = ("kind", "display_name", "note")
_EXISTING_TARGET_FIELDS = ("kind", "person_id")

_REPLACE_MAIN_FIELDS = ("demote_to",)
_DEMOTABLE_ROLES = tuple(role for role in ACCOUNT_ROLES if role != ROLE_MAIN)

##
## Older ``share_url`` rows carry the literal text "None" where a value was
## never set.  A person called None is nobody, so it counts as absent - the same
## reading aweme_record already applies to the same column.
##
_UNUSABLE_DIRECTORY_NAMES = ("", "None")


def _unknown(fields, allowed) -> list:
  return sorted(set(fields) - set(allowed))


def _text(value, field: str) -> str:
  """A required, non-blank string.

  ``bool`` is refused before anything else because it is not text at all, and
  ``str(True)`` would quietly become the word "True".
  """
  if isinstance(value, bool) or not isinstance(value, str) or not value.strip():
    raise InvalidAssignment("{} 必须是非空字符串".format(field))
  return value.strip()


def _optional_text(target: dict, field: str):
  """A string that may be left out entirely, but not left blank.

  "The user did not say" and "the user said something meaningless" are
  different, and only the first may be filled in on their behalf.  A blank name
  is therefore a field error rather than an omission - answering it as an
  omission would put a name the user never chose on somebody, silently.
  """
  if field not in target:
    return None
  value = target.get(field)
  if isinstance(value, bool) or not isinstance(value, str):
    raise InvalidAssignment("{} 必须是字符串".format(field))
  return value.strip()


def _person_id(target: dict) -> int:
  ##
  ## ``True`` is an ``int`` in python, and ``person_id = True`` would reach the
  ## database as 1 - somebody else's person, attached to silently.
  ##
  value = target.get("person_id")
  if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
    raise InvalidAssignment("target.person_id 必须是正整数")
  return value


def _validated_target(target) -> dict:
  """Read the target down to ``(person_id, display_name, note)``.

  ``person_id`` is ``None`` for a new person, which is also how the table below
  reads "create one".
  """
  if not isinstance(target, dict):
    raise InvalidAssignment("target 必须是对象")

  kind = target.get("kind")
  if kind not in TARGET_KINDS:
    raise InvalidAssignment(
      "target.kind 必须是 {} 之一".format("/".join(TARGET_KINDS))
    )

  if kind == TARGET_KIND_EXISTING:
    unknown = _unknown(target, _EXISTING_TARGET_FIELDS)
    if unknown:
      raise InvalidAssignment(
        "已有人物不支持的字段: {}".format(", ".join(unknown))
      )
    return {"person_id": _person_id(target), "display_name": None, "note": None}

  unknown = _unknown(target, _NEW_TARGET_FIELDS)
  if unknown:
    raise InvalidAssignment("新建人物不支持的字段: {}".format(", ".join(unknown)))

  display_name = _optional_text(target, "display_name")
  if "display_name" in target and not display_name:
    raise InvalidAssignment("display_name 不能是空白；可以整个省略")
  note = _optional_text(target, "note")
  return {
    "person_id": None,
    "display_name": display_name,
    ##
    ## A note that is only whitespace is stored as nothing rather than as
    ## spaces: the column means "there is a note", and a blank one does not.
    ##
    "note": note or None,
  }


def _validated_demote_to(replace_main, role: str, person_id) -> str:
  """Where the old main goes, or ``None`` when no replacement was asked for."""
  if replace_main is None or replace_main is False:
    ##
    ## ``false`` is spelled out as "absent" rather than refused: it is what a
    ## client sends when it builds the field unconditionally, and it says
    ## exactly what leaving it out says.
    ##
    return None

  if role != ROLE_MAIN:
    raise InvalidAssignment("replace_main 只在 role 为 main 时有意义")
  if person_id is None:
    ##
    ## A person being created holds nothing, so there is no main to replace.
    ## The caller knows that when it writes the request, so asking for it means
    ## the request does not say what its author thought it said.
    ##
    raise InvalidAssignment("新建人物没有可替换的大号")
  if not isinstance(replace_main, dict):
    raise InvalidAssignment("replace_main 必须是对象")

  unknown = _unknown(replace_main, _REPLACE_MAIN_FIELDS)
  if unknown:
    raise InvalidAssignment(
      "replace_main 不支持的字段: {}".format(", ".join(unknown))
    )

  demote_to = replace_main.get("demote_to")
  if demote_to not in _DEMOTABLE_ROLES:
    ##
    ## ``main`` most of all: demoting the old main *to* main is the two-main
    ## state written out in full.
    ##
    raise InvalidAssignment(
      "replace_main.demote_to 必须是 {} 之一".format("/".join(_DEMOTABLE_ROLES))
    )
  return demote_to


def _validated_request(request) -> dict:
  """Read one request body down to the values the assignment needs.

  Every refusal here is a field error, decided before the receipt is looked up:
  a bad role is wrong whatever the receipt says, and answering "your resolution
  expired" would send the user round a loop that cannot fix their request.
  """
  if not isinstance(request, dict):
    raise InvalidAssignment("请求体必须是对象")

  unknown = _unknown(request, _REQUEST_FIELDS)
  if unknown:
    ##
    ## Named in the message.  The fields a client is most likely to send here
    ## are the ones it wants trusted - an owner id, a nickname - and "unknown
    ## field" alone would read as pedantry rather than as the refusal it is.
    ##
    raise InvalidAssignment("不支持的字段: {}".format(", ".join(unknown)))

  resolve_id = _text(request.get("resolve_id"), "resolve_id")

  role = request.get("role")
  if role not in ACCOUNT_ROLES:
    raise InvalidAssignment(
      "role 必须是 {} 之一".format("/".join(ACCOUNT_ROLES))
    )

  allow_move = request.get("allow_move", False)
  if not isinstance(allow_move, bool):
    ##
    ## Not "truthy".  This flag is what stands between a mis-paste and somebody
    ## else's account changing hands, so it has to be said in the one way that
    ## cannot be an accident.
    ##
    raise InvalidAssignment("allow_move 必须是布尔值")

  target = _validated_target(request.get("target"))
  return {
    "resolve_id": resolve_id,
    "role": role,
    "allow_move": allow_move,
    "demote_main_to": _validated_demote_to(
      request.get("replace_main"), role, target["person_id"]
    ),
    "person_id": target["person_id"],
    "display_name": target["display_name"],
    "note": target["note"],
  }


##
## The whole of what an inspection may say, which is one field.
##
## Shorter than the assignment's list and for a stronger reason.  An inspection
## answers "does this server already hold this account", and the page turns
## "no" into an invitation to create a person - so a client able to name the
## account would be choosing which account gets checked, and could ask about one
## while holding a receipt for another.  There is no target either: an
## inspection has nothing to write to, and a field for one would read as though
## the answer depended on it.
##
_INSPECT_REQUEST_FIELDS = ("resolve_id",)


def _validated_inspect_request(request) -> str:
  """Read one inspection request down to the receipt it names.

  Every refusal is a field error decided before the receipt is looked up: an
  unsupported field is wrong whatever the receipt says, and answering "your
  resolution expired" would send the user round a loop that cannot fix it.
  """
  if not isinstance(request, dict):
    raise InvalidAssignment("请求体必须是对象")

  unknown = _unknown(request, _INSPECT_REQUEST_FIELDS)
  if unknown:
    raise InvalidAssignment("不支持的字段: {}".format(", ".join(unknown)))

  return _text(request.get("resolve_id"), "resolve_id")


##
## >>============================= the service =============================>>
##

class PersonAssignmentService:
  """Turns a receipt plus a target into one person holding one more account.

  The trust boundary of the whole feature lives here.  Nothing a client sends
  describes the account: the resolution is read back from this application's own
  resolve store, and the owner behind it is read from the platform using that
  snapshot's own resolved url.  A request that could name the account itself
  would let a browser attach an owner this server never resolved, which is the
  guarantee the receipt exists to provide.

  Two boundaries are kept deliberately sharp.

  The platform is asked *before* the transaction opens, never inside it: a
  request made between BEGIN and COMMIT holds every row lock the transaction has
  taken for as long as douyin takes to answer - seconds when it answers, the
  full timeout when it does not - and every other assignment for those rows
  waits behind it.

  And the whole write is one call.  Creating the person, recording the identity,
  attaching the account and aligning the folders done as four calls has three
  middles, each of which leaves something nobody goes back to clean up.

  Web-neutral by construction: it reads a plain mapping and raises its own
  errors, so no wiring detail of Flask reaches it and every refusal above can be
  tested without a request context.
  """

##
## >>============================= private method =============================>>
##
  def __init__(self, resolve_service, table_factory, identity_reader) -> None:
    self._resolve_service = resolve_service
    ##
    ## A factory rather than a table: the real one opens a connection pool when
    ## it is built, and a service constructed per request must not cost that
    ## until something actually writes.
    ##
    self._table_factory = table_factory
    self._identity_reader = identity_reader

  @property
  def resolve_service(self):
    """The store this service redeems receipts against.

    Exposed so the wiring can be asserted rather than assumed: whether this is
    the application's own resolve service is the difference between every
    receipt working and every receipt reading as expired.
    """
    return self._resolve_service

  def _resolution(self, resolve_id: str):
    ##
    ## Read once, here.  Everything downstream works off this one detached
    ## snapshot, so a receipt expiring mid-request cannot fail an assignment
    ## that was already accepted on a valid resolution.
    ##
    resolution = self._resolve_service.get(resolve_id)
    if resolution is None:
      raise ResolutionNotFound("解析结果不存在或已过期，请重新解析")
    return resolution

  def _identity(self, resolution) -> dict:
    """Who the resolved resource belongs to.

    The one place this service talks to a platform, and it happens before any
    row is touched.
    """
    try:
      identity = self._identity_reader.from_resolution(resolution)
    except Exception as e:
      ##
      ## Logged in full by the edge, answered as a field problem here: a link
      ## that cannot be read names nobody, and that is a property of the link.
      ##
      raise OwnerIdentityUnavailable(
        "无法识别该链接对应的主播，请稍后重试"
      ) from e

    owner_user_id = (
      "" if not identity else (identity.get("owner_user_id") or "")
    ).strip()
    if not owner_user_id:
      raise OwnerIdentityUnavailable("这条链接指向不了任何主播，请检查后重试")
    return {
      "owner_user_id": owner_user_id,
      "sec_user_id": identity.get("sec_user_id"),
      "nickname": identity.get("nickname"),
    }

  def _display_name(self, requested, identity: dict) -> str:
    """What to call a person the user did not name.

    Never blank: ``display_name`` is what the person list is ordered and
    searched by, and a row with no name is a row nobody can find again.

    Nothing here is passed through the folder sanitiser.  This is a person's
    name, shown to a user, and rewriting it to fit a filesystem would change
    somebody's name for a reason that has nothing to do with them.  The folder
    is read only *as* a name, because it is already the safe text this account's
    files live under and therefore the name the user will recognise.
    """
    if requested:
      return requested

    recorded = self._table_factory().account_directory_name(
      identity["owner_user_id"]
    )
    if (
      isinstance(recorded, str)
      and recorded.strip() not in _UNUSABLE_DIRECTORY_NAMES
    ):
      return recorded.strip()

    nickname = (identity.get("nickname") or "").strip()
    if nickname:
      return nickname
    ##
    ## The id itself, last.  Ugly, and still better than a person nobody can
    ## tell apart from the next one.
    ##
    return identity["owner_user_id"]

##
## >>============================= sub class method =============================>>
##
  def assign_known_account(
    self,
    owner_user_id: str,
    person_id: int,
    role: str,
    allow_move: bool = False,
    demote_main_to: str = None,
  ) -> PersonAssignmentResult:
    """Attach an account this server already knows to an existing person.

    The way in for the endpoints that predate receipts.  They name an account
    the user picked out of this server's own search results, so there is no
    resolution to redeem and none is invented - but the account is still checked
    against ``share_url`` rather than believed, so a made-up id cannot mint a
    row for an account that does not exist.

    Everything after that is the *same* transaction as a receipt-based
    assignment, deliberately: at-most-one-main, the last-main rule, the move
    rule, the locking and the alignment all have exactly one implementation, and
    which door the request came through does not change what is allowed.

    No identity values are passed.  A client's idea of an account's nickname is
    not evidence about that account, and the row already exists.
    """
    if role not in ACCOUNT_ROLES:
      raise InvalidAssignment(
        "role 必须是 {} 之一".format("/".join(ACCOUNT_ROLES))
      )
    if isinstance(person_id, bool) or not isinstance(person_id, int):
      raise InvalidAssignment("person_id 必须是正整数")
    if person_id <= 0:
      raise InvalidAssignment("person_id 必须是正整数")
    if not isinstance(owner_user_id, str) or not owner_user_id.strip():
      raise InvalidAssignment("owner_user_id 不能为空")

    owner_user_id = owner_user_id.strip()
    table = self._table_factory()
    if not table.account_exists(owner_user_id):
      raise AccountNotKnown("该账号不存在，请重新搜索后选择")

    return self._assigned(
      table,
      owner_user_id=owner_user_id,
      role=role,
      person_id=person_id,
      display_name=None,
      note=None,
      sec_user_id=None,
      nickname=None,
      allow_move=allow_move,
      demote_main_to=demote_main_to,
    )

  def assign_resolved_account(
    self,
    identity: dict,
    person_id: int,
    role: str,
    allow_move: bool = False,
    demote_main_to: str = None,
  ) -> PersonAssignmentResult:
    """Attach an account named by an identity this server has just resolved.

    The way in for ``/api/person/account/by-link``, which follows a link itself
    rather than redeeming a receipt.  Its identity therefore *is* server-read -
    the caller resolved it, the client did not send it - so unlike the method
    above it does carry a nickname and sec id through to the upsert, and the
    account does not have to exist beforehand.  That is the whole point of that
    endpoint: it is how an owner who has never been downloaded gets a row.

    Same transaction, same rules.
    """
    if role not in ACCOUNT_ROLES:
      raise InvalidAssignment(
        "role 必须是 {} 之一".format("/".join(ACCOUNT_ROLES))
      )
    owner_user_id = ((identity or {}).get("owner_user_id") or "").strip()
    if not owner_user_id:
      raise OwnerIdentityUnavailable("该主播没有可用的账号 id，无法挂载")

    return self._assigned(
      self._table_factory(),
      owner_user_id=owner_user_id,
      role=role,
      person_id=person_id,
      display_name=None,
      note=None,
      sec_user_id=identity.get("sec_user_id"),
      nickname=identity.get("nickname"),
      allow_move=allow_move,
      demote_main_to=demote_main_to,
    )

  def detach_account(self, owner_user_id: str) -> dict:
    """Unmark one account, subject to the last-main rule.

    Removing a marking is not the harmless inverse of adding one: the folders of
    every account that was aligned to a main are not restored when that main
    stops being one, so the guard applies here exactly as it does to a demotion.
    """
    if not isinstance(owner_user_id, str) or not owner_user_id.strip():
      raise InvalidAssignment("owner_user_id 不能为空")

    try:
      return self._table_factory().detach_account_guarded(
        PLATFORM, owner_user_id.strip()
      )
    except NotAttached as e:
      raise AccountNotAttached("该账号当前没有挂在任何人物上") from e
    except AssignmentRaced as e:
      raise AssignmentConflictRetryable(
        "该账号刚刚被其他操作改动，请重试"
      ) from e
    except LastMainRemoval as e:
      raise LastMainRemovalConflict(
        "该大号是当前人物的统一目录基准，请先为该人物指定新的大号，再解除挂载",
        person_id=e.person_id,
        display_name=e.display_name,
        owner_user_id=e.owner_user_id,
        nickname=e.nickname,
      ) from e
    except DatabaseWriteBlocked as e:
      raise AssignmentUnavailable("人物写入暂时不可用，请稍后重试") from e

  def inspect(self, request) -> PersonIdentityInspection:
    """Say who a receipt names, and whether this server already holds them.

    Read-oriented, and the answer is a hint for the interface rather than an
    authorisation.  It exists because the only thing that used to notice a
    duplicate was the assignment transaction, which meant the user filled in a
    form, named a person and pressed confirm before being told the account had
    been there all along.

    Two guarantees make it safe to act on in a browser and safe to ignore in a
    transaction.

    It shares ``_resolution`` and ``_identity`` with the assignment, so the two
    cannot come to disagree about who a link names: if an inspection says this
    is account 100, the assignment made from the same receipt attaches account
    100.

    And it decides nothing.  Nothing it reports is carried into the write - the
    assignment discovers ownership again, under its own locks, and refuses on
    what it finds there.  So an inspection that said "nobody holds this" cannot
    become permission to take it from somebody who does, however long the user
    spent reading the screen in between.

    The receipt is left intact.  The store is a TTL store rather than a
    consume-once one, deliberately, and this is now the first thing every
    assignment does - a consuming read here would report "your resolution
    expired" on every user's first click.
    """
    resolve_id = _validated_inspect_request(request)
    resolution = self._resolution(resolve_id)
    identity = self._identity(resolution)

    table = self._table_factory()
    try:
      found = table.get_account_assignment(identity["owner_user_id"])
    except Exception as e:
      ##
      ## Logged in full, answered as an outage.  Reporting it as "unknown
      ## account" would be a lie that reads as an invitation: the page offers to
      ## create a person for exactly that answer.
      ##
      get_logger().error(
        "person lookup for an inspection failed: {}: {}".format(
          type(e).__name__, e
        )
      )
      raise PersonLookupUnavailable(
        "暂时无法确认该账号的归属，请稍后重试"
      ) from e

    if found is not None:
      self._refresh_identity(table, identity)

    return PersonIdentityInspection(
      owner_user_id=identity["owner_user_id"],
      sec_user_id=identity.get("sec_user_id"),
      ##
      ## The platform's current nickname, not the stored one.  It is what the
      ## user is looking at in the app they copied the link from.
      ##
      nickname=identity.get("nickname"),
      known_account=found is not None,
      person_id=None if found is None else found.get("person_id"),
      ##
      ## The *person's* name, which is a name somebody typed.  It is left alone
      ## when the account renames itself: "账号：程小程 / 人物：程儿" is the
      ## honest reading of a streamer who changed their handle.
      ##
      display_name=None if found is None else found.get("display_name"),
      role=None if found is None else found.get("role"),
    )

  def _refresh_identity(self, table, identity: dict) -> None:
    """Bring a known account's stored nickname and sec id up to date.

    Only for an account that already has a row.  An upsert for one that does not
    would create the very row the lookup just failed to find, so the next
    inspection of the same link would report a known account - a read that
    changes its own answer, and one that files an account somebody merely
    pasted into a box.

    Identity columns only, and best effort.  The lookup is what was asked for;
    a courtesy write failing is no reason to refuse an answer that is already
    correct, so it is logged and stepped over.  Nothing here touches
    ``person_account`` - who holds an account is not a thing a read may decide.
    """
    try:
      table.upsert_account_identity(
        identity["owner_user_id"],
        sec_user_id=identity.get("sec_user_id"),
        nickname=identity.get("nickname"),
      )
    except Exception as e:
      get_logger().info(
        "identity refresh during an inspection was skipped: {}".format(
          type(e).__name__
        )
      )

  def assign(self, request) -> PersonAssignmentResult:
    """Attach the account a receipt names to a person, new or existing.

    Raises a ``PersonAssignmentError`` for every expected refusal, each carrying
    the status the api answers with.
    """
    validated = _validated_request(request)
    resolution = self._resolution(validated["resolve_id"])
    identity = self._identity(resolution)

    display_name = validated["display_name"]
    if validated["person_id"] is None:
      display_name = self._display_name(display_name, identity)

    return self._assigned(
      self._table_factory(),
      owner_user_id=identity["owner_user_id"],
      role=validated["role"],
      person_id=validated["person_id"],
      display_name=display_name,
      note=validated["note"],
      sec_user_id=identity["sec_user_id"],
      nickname=identity["nickname"],
      allow_move=validated["allow_move"],
      demote_main_to=validated["demote_main_to"],
    )

  def _assigned(self, table, **assignment) -> PersonAssignmentResult:
    """Run one assignment and turn the transaction's refusals into this
    service's own.

    Shared by all three ways in.  The rules live in the transaction; this maps
    them onto statuses once, so a refusal cannot mean 409 through one door and
    502 through another.
    """
    try:
      assigned = table.assign_account(**assignment)
    except PersonMissing as e:
      raise PersonNotFound("人物不存在，请重新选择") from e
    except AccountAttachedElsewhere as e:
      raise AccountAlreadyAttached(
        "该账号已归属其他人物，确认要转移请重试",
        person_id=e.person_id,
        display_name=e.display_name,
      ) from e
    except MainAlreadyAssigned as e:
      raise MainAccountConflict(
        "该人物已经有大号了，确认要替换请重试",
        owner_user_id=e.owner_user_id,
        nickname=e.nickname,
      ) from e
    except LastMainRemoval as e:
      raise LastMainRemovalConflict(
        "该大号是当前人物的统一目录基准，请先为原人物指定新的大号，再移动或降级它",
        person_id=e.person_id,
        display_name=e.display_name,
        owner_user_id=e.owner_user_id,
        nickname=e.nickname,
      ) from e
    except AssignmentRaced as e:
      raise AssignmentConflictRetryable(
        "该账号刚刚被其他操作改动，请重试"
      ) from e
    except UnknownRole as e:
      ##
      ## The role came from a list of three, so a bad one is a field problem the
      ## page can point at - not a failure of the request.
      ##
      raise InvalidAssignment(str(e)) from e
    except DatabaseWriteBlocked as e:
      raise AssignmentUnavailable("人物写入暂时不可用，请稍后重试") from e

    return PersonAssignmentResult(
      person_id=assigned["person_id"],
      owner_user_id=assigned["owner_user_id"],
      role=assigned["role"],
      created_person=assigned["created_person"],
      display_name=assigned["display_name"],
    )
