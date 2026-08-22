## <<Third-Part>>
from backend.src.database.orm.models.person import (
  ACCOUNT_ROLES,
  MAIN_UNIQUE_NAME,
  ROLE_MAIN,
)
from backend.src.database.social_media_stream_database import (
  SocialMediaStreamDataBase,
)
from backend.src.library.loglib import get_logger


PLATFORM = "douyin"


##
## Only alt and matrix.  Demoting the old main *to* main is the two-main state
## written out in full, so the value is refused rather than being allowed to
## mean "leave it alone".
##
_DEMOTABLE_ROLES = tuple(role for role in ACCOUNT_ROLES if role != ROLE_MAIN)

##
## The statements the assignment transaction runs, named so its steps read as
## steps.  Every one of them binds its values; only the two lock reads differ
## from the statements the single-purpose methods above already use, and they
## differ only by FOR UPDATE.
##
_LOCK_PERSON_SQL = '''SELECT person_id, display_name
             FROM person
             WHERE person_id = %s
             FOR UPDATE;
          '''

##
## Which person an account currently belongs to, read *without* a lock.
##
## Deliberately unlocked, and deliberately first.  The account row is what says
## which person a request touches, but the person has to be locked before the
## account is - otherwise two requests take the same pair of locks in opposite
## orders and deadlock.  So the person is discovered here, locked next, and the
## account is then locked and re-checked against what this read said.  The
## unlocked read is safe precisely because nothing is decided on it: it only
## chooses which rows to lock, and the re-check catches it if it chose wrongly.
##
_FIND_ATTACHMENT_SQL = '''SELECT person_id, role
             FROM person_account
             WHERE platform = %s AND owner_user_id = %s;
          '''

_LOCK_ATTACHMENT_SQL = '''SELECT person_id, role
             FROM person_account
             WHERE platform = %s AND owner_user_id = %s
             FOR UPDATE;
          '''

_LOCK_MAIN_SQL = '''SELECT owner_user_id, platform
             FROM person_account
             WHERE person_id = %s AND role = 'main'
             FOR UPDATE;
          '''

##
## Read only to describe a refusal, so no lock: the answer is shown to a user
## and nothing is written on the strength of it.
##
##
## How many accounts this person holds, and how many of them are mains.
##
## No FOR UPDATE of its own: the person row is already locked, and every write
## path that could change these numbers takes that lock first, so the counts
## cannot move underneath this transaction.  ``role = %s`` binds rather than
## naming 'main' inline so the statement stays one question about a parameter
## instead of two statements that happen to differ by a literal.
##
_COUNT_PERSON_ACCOUNTS_SQL = '''SELECT COUNT(*) AS account_count,
                    SUM(CASE WHEN role = %s THEN 1 ELSE 0 END) AS main_count
             FROM person_account
             WHERE person_id = %s;
          '''

_DETACH_ACCOUNT_SQL = '''DELETE FROM person_account
             WHERE platform = %s AND owner_user_id = %s;
          '''

_NAME_PERSON_SQL = '''SELECT display_name FROM person WHERE person_id = %s;'''

_NAME_ACCOUNT_SQL = '''SELECT nickname FROM share_url WHERE owner_user_id = %s;'''

_UPSERT_IDENTITY_SQL = '''INSERT INTO share_url
               (owner_user_id, sec_user_id, nickname)
             VALUES (%s, %s, %s)
             ON DUPLICATE KEY UPDATE
               sec_user_id = COALESCE(VALUES(sec_user_id), sec_user_id),
               nickname    = COALESCE(VALUES(nickname), nickname);
          '''

_INSERT_PERSON_SQL = '''INSERT INTO person (display_name, note)
             VALUES (%s, %s);
          '''

_DEMOTE_MAIN_SQL = '''UPDATE person_account SET role = %s
             WHERE platform = %s AND owner_user_id = %s;
          '''

_ATTACH_ACCOUNT_SQL = '''INSERT INTO person_account
               (platform, owner_user_id, person_id, role)
             VALUES (%s, %s, %s, %s)
             ON DUPLICATE KEY UPDATE
               person_id = VALUES(person_id),
               role      = VALUES(role);
          '''

##
## Shared by ``align_accounts_to_main`` and by the assignment transaction, which
## has to run the very same statement inside its own connection.  A second copy
## would be a second answer to "where do this person's sub-accounts file", and
## the two would drift the first time either was corrected.
##
## Note ``sub.role <> 'main'``: the main account's own row is never written.
## That exclusion is what makes losing the last main unrecoverable for the
## *others* and harmless for a person who holds only the main - which is the
## whole basis of _guarded_main_departure below.
##
_ALIGN_TO_MAIN_SQL = '''UPDATE share_url AS s
             JOIN person_account AS sub
               ON sub.owner_user_id = s.owner_user_id AND sub.platform = %s
             JOIN person_account AS main_account
               ON main_account.person_id = sub.person_id
              AND main_account.role = 'main'
             JOIN share_url AS m
               ON m.owner_user_id = main_account.owner_user_id
             SET s.directory_name = m.directory_name
             WHERE sub.person_id = %s
               AND sub.role <> 'main'
               AND m.directory_name IS NOT NULL
               AND TRIM(m.directory_name) <> '';
          '''


##
## MySQL's duplicate-key error number.
##
## The number and the index's own name are what this classifies on - both are
## stable and one of them is ours.  The driver's message is English prose
## written by MySQL; deciding a business outcome by matching on it would break
## silently the day it is reworded.
##
_MYSQL_DUPLICATE_KEY = 1062


def _is_duplicate_main(error) -> bool:
  """Whether ``error`` is the unique index refusing a second main account.

  The transaction below already refuses one, so this fires only for a write that
  reached the database another way - or for a check that failed to hold.  Either
  way the user is better served by the sentence that describes their situation
  than by a generic failure.
  """
  arguments = getattr(error, "args", ()) or ()
  if not arguments or arguments[0] != _MYSQL_DUPLICATE_KEY:
    return False
  ##
  ## The primary key raises 1062 as well, so the index has to be named.  Reading
  ## every duplicate as "this person already has a main" would explain the wrong
  ## thing to somebody who attached the same account twice.
  ##
  return MAIN_UNIQUE_NAME in "".join(str(one) for one in arguments)


class UnknownRole(ValueError):
  """Raised when an account is attached with a role nobody defined.

  Its own type so a caller can turn it into a field-level message rather than a
  generic failure: the user picked something from a list, and the list is short.
  """


class AssignmentConflict(Exception):
  """An assignment refused because of what the database already says.

  Not a failure: nothing malfunctioned and the request was well formed.  It
  describes a state the user has to decide about, so each subclass carries the
  facts the page needs to offer that decision - and nothing else, because this
  reaches a browser.

  One base class so a caller that only cares that the assignment was refused
  catches one thing, while the two below stay distinguishable: the answer to
  one is ``allow_move`` and the answer to the other is ``replace_main``, and a
  page that could not tell them apart could offer neither.
  """


class AccountAttachedElsewhere(AssignmentConflict):
  """The account already belongs to a different person.

  ``person_account`` is keyed on the account, so attaching it here really does
  take it away from whoever holds it - and every download of theirs changes
  folder the moment it happens.  That is a decision, so it is asked for rather
  than assumed.
  """

  def __init__(self, person_id, display_name=None) -> None:
    super().__init__(
      "account already belongs to person {}".format(person_id)
    )
    self.person_id = person_id
    self.display_name = display_name


class MainAlreadyAssigned(AssignmentConflict):
  """The person already has a main account, and it is not this one.

  Zero or one, never two.  Nothing in the schema forbids the second - the
  column is a plain string and the page that used to be the only guard is a
  browser, which cannot be one - so the invariant lives in the transaction that
  writes it.
  """

  def __init__(self, owner_user_id, nickname=None) -> None:
    super().__init__(
      "person already has main account {}".format(owner_user_id)
    )
    self.owner_user_id = owner_user_id
    self.nickname = nickname


class LastMainRemoval(AssignmentConflict):
  """The person's only main account was about to stop being their main.

  Refused because the damage is not reversible.  ``align_accounts_to_main``
  copies the main's folder onto the person's *other* accounts, and the download
  path writes ``directory_name = COALESCE(directory_name, VALUES(...))`` - the
  stored value wins - so the folder those accounts used to file under is no
  longer written down anywhere.  Take the main away and they fall back to "their
  own" recorded folder, which is now the ex-main's, with no person left to
  explain it.

  Deliberately *not* "a person must always have a main".  A person who never had
  one never had a folder copied off one, and creating a person from their spare
  account is the ordinary way this feature is used.  The rule is only that an
  established folder relationship may not be dismantled from underneath the
  accounts that were aligned to it - so it applies exactly when the person still
  holds other accounts.

  ``replace_main`` remains the way through: it demotes and promotes in one
  transaction, so there is no moment in between.
  """

  def __init__(
    self,
    person_id,
    display_name=None,
    owner_user_id=None,
    nickname=None,
  ) -> None:
    super().__init__(
      "person {} would be left without a main account".format(person_id)
    )
    self.person_id = person_id
    self.display_name = display_name
    self.owner_user_id = owner_user_id
    self.nickname = nickname


class AssignmentRaced(AssignmentConflict):
  """The account moved between being looked up and being locked.

  The narrow window the discovery read leaves open.  Whoever won it holds locks
  this transaction does not, so carrying on would mean deciding the last-main
  question against a person nobody here has locked - which is the whole thing
  the ordering exists to prevent.

  Refused rather than retried in place: taking the other person's lock now would
  mean holding two out of order, which is the deadlock this design avoids.  The
  caller retries the request instead, and the second attempt discovers the new
  owner and locks it properly.
  """

  def __init__(self, owner_user_id) -> None:
    super().__init__(
      "account {} changed hands while being assigned".format(owner_user_id)
    )
    self.owner_user_id = owner_user_id


class NotAttached(AssignmentConflict):
  """The account is not marked as belonging to anybody.

  Reported rather than answered as a success: "removed nothing" and "removed the
  thing you meant" look identical to a page that is only told it worked, and the
  difference matters when the id was mistyped.
  """

  def __init__(self, owner_user_id) -> None:
    super().__init__("account {} is not attached".format(owner_user_id))
    self.owner_user_id = owner_user_id


class PersonMissing(AssignmentConflict):
  """The person named by the request does not exist.

  Checked rather than left to the foreign key: a constraint violation answers
  500 and tells the page nothing it can act on, and the id it was given may
  simply be stale.
  """

  def __init__(self, person_id) -> None:
    super().__init__("person {} does not exist".format(person_id))
    self.person_id = person_id


class DouyinPersonIdentityTable(SocialMediaStreamDataBase):
  """Reads and writes the three tables that record who an account belongs to.

  A person is created on demand.  An account nobody marked has no row here, and
  every path that consults this table has to behave exactly as it did before -
  that is what keeps the feature at zero effect until it is actually used.
  """

##
## >>============================= people =============================>>
##
  def create_person(self, display_name: str, note: str = None) -> int:
    """Create a person and return the new id.

    No folder is asked for: it comes from whichever account is later marked as
    the main one.
    """
    if not isinstance(display_name, str) or not display_name.strip():
      raise ValueError("display_name is required")

    sql = '''INSERT INTO person (display_name, note)
             VALUES (%s, %s);
          '''
    self.require_write_ready()
    try:
      with self.get_connection() as connector:
        with connector.cursor() as cursor:
          cursor.execute(
            sql,
            (display_name.strip(), note),
          )
          new_id = cursor.lastrowid
          connector.commit()
    except Exception as e:
      get_logger().error("create person {} failed: {}".format(display_name, e))
      raise e
    return new_id

  def update_person(
    self,
    person_id: int,
    display_name: str = None,
    note: str = None,
  ) -> None:
    """Update only the fields that were named.

    Renaming a folder must not blank a note that nobody mentioned, so unnamed
    fields are left out of the statement rather than written as ``None``.
    """
    if display_name is None and note is None:
      return

    ##
    ## One fixed statement with COALESCE rather than a SET clause assembled from
    ## the fields that were named.  Same effect - an unmentioned field keeps its
    ## stored value - without building SQL text at runtime, which is the line
    ## test_sql_construction_invariant draws: only identifiers may ever be
    ## interpolated, everything else binds.  share_url's upsert reads the same
    ## way, so the two stay recognisable as one idiom.
    ##
    sql = '''UPDATE person
             SET display_name = COALESCE(%s, display_name),
                 note         = COALESCE(%s, note)
             WHERE person_id = %s;
          '''
    self.require_write_ready()
    try:
      with self.get_connection() as connector:
        with connector.cursor() as cursor:
          cursor.execute(
            sql,
            (display_name, note, person_id),
          )
          connector.commit()
    except Exception as e:
      get_logger().error("update person {} failed: {}".format(person_id, e))
      raise e

  def delete_person(self, person_id: int) -> None:
    """Delete a person.

    Their account attachments and collaborations go with them through the
    foreign keys' cascade, so this deliberately issues one statement rather than
    clearing the children by hand - two places to keep in step is one too many.
    """
    sql = "DELETE FROM person WHERE person_id = %s;"
    self.require_write_ready()
    try:
      with self.get_connection() as connector:
        with connector.cursor() as cursor:
          cursor.execute(sql, (person_id,))
          connector.commit()
    except Exception as e:
      get_logger().error("delete person {} failed: {}".format(person_id, e))
      raise e

  def list_persons(self) -> list:
    """Every person, with how many accounts each holds.

    A LEFT JOIN so somebody created a moment ago, before any account was
    attached, still appears - that is the ordinary order of the operation.
    """
    ##
    ## directory_name is reported, not stored: it is the main account's, shown so
    ## the page can say where this person's files go without inventing a field.
    ##
    sql = '''SELECT p.person_id, p.display_name, p.note,
                    COUNT(pa.owner_user_id) AS account_count,
                    MAX(m.directory_name) AS directory_name
             FROM person AS p
             LEFT JOIN person_account AS pa ON pa.person_id = p.person_id
             LEFT JOIN person_account AS main_account
               ON main_account.person_id = p.person_id
              AND main_account.role = 'main'
             LEFT JOIN share_url AS m
               ON m.owner_user_id = main_account.owner_user_id
             GROUP BY p.person_id, p.display_name, p.note
             ORDER BY p.display_name;
          '''
    try:
      with self.get_connection() as connector:
        with connector.cursor() as cursor:
          cursor.execute(sql)
          rows = cursor.fetchall() or []
    except Exception as e:
      get_logger().error("list persons failed: {}".format(e))
      raise e

    return [
      {
        "person_id": row.get("person_id"),
        "display_name": row.get("display_name"),
        "directory_name": row.get("directory_name"),
        "note": row.get("note"),
        "account_count": row.get("account_count"),
      }
      for row in rows
    ]

  def search_accounts(self, keyword: str, limit: int = 30) -> list:
    """Find accounts by nickname or id, reporting who each already belongs to.

    A search rather than a list: there are more than eighteen hundred accounts,
    which no picker can show.  Each result carries its current person so that
    attaching one somewhere else is a visible move rather than a silent one.
    """
    if not isinstance(keyword, str) or not keyword.strip():
      return []

    pattern = "%{}%".format(keyword.strip())
    sql = '''SELECT s.owner_user_id, s.nickname, s.directory_name,
                    pa.person_id, pa.role
             FROM share_url AS s
             LEFT JOIN person_account AS pa
               ON pa.owner_user_id = s.owner_user_id AND pa.platform = %s
             WHERE s.nickname LIKE %s OR s.owner_user_id LIKE %s
             ORDER BY s.nickname
             LIMIT %s;
          '''
    try:
      with self.get_connection() as connector:
        with connector.cursor() as cursor:
          cursor.execute(sql, (PLATFORM, pattern, pattern, int(limit)))
          rows = cursor.fetchall() or []
    except Exception as e:
      get_logger().error("search accounts for {} failed: {}".format(keyword, e))
      raise e

    return [
      {
        "owner_user_id": row.get("owner_user_id"),
        "nickname": row.get("nickname"),
        "directory_name": row.get("directory_name"),
        "person_id": row.get("person_id"),
        "role": row.get("role"),
      }
      for row in rows
    ]

##
## >>============================= accounts =============================>>
##
  def upsert_account_identity(
    self,
    owner_user_id: str,
    sec_user_id: str = None,
    nickname: str = None,
  ) -> None:
    """Record who an account is, without claiming anything else about it.

    Marking an owner who has never been downloaded would otherwise leave the
    person page showing a bare ``owner_user_id``: ``share_url`` has no row for
    them yet, because only a download creates one.  Marking is a deliberate
    statement of interest - unlike merely browsing - so an identity row for
    somebody just marked is earned.

    Identity columns only.  ``directory_name`` belongs to the person and the
    download paths, the two share urls each belong to their own path, and
    ``actived_count`` belongs to the live path; a row created here leaves every
    one of them to whoever owns it.  ``directory_name`` in particular stays
    empty on purpose - the first download fills it through its own COALESCE, and
    the person's folder wins over it regardless.
    """
    if not isinstance(owner_user_id, str) or not owner_user_id.strip():
      raise ValueError("owner_user_id is required")

    sql = '''INSERT INTO share_url (owner_user_id, sec_user_id, nickname)
             VALUES (%s, %s, %s)
             ON DUPLICATE KEY UPDATE
               sec_user_id = COALESCE(VALUES(sec_user_id), sec_user_id),
               nickname    = COALESCE(VALUES(nickname), nickname);
          '''
    self.require_write_ready()
    try:
      with self.get_connection() as connector:
        with connector.cursor() as cursor:
          cursor.execute(sql, (owner_user_id.strip(), sec_user_id, nickname))
          connector.commit()
    except Exception as e:
      get_logger().error(
        "record identity for {} failed: {}".format(owner_user_id, e)
      )
      raise e

  def attach_account(
    self,
    platform: str,
    owner_user_id: str,
    person_id: int,
    role: str,
  ) -> None:
    """Record that an account belongs to a person, in the given role.

    Upserts on the account rather than inserting.  An account belongs to at most
    one person, and re-attaching is the ordinary way to correct a mistake, so a
    second attach has to move the account rather than leave it under two people.
    """
    if role not in ACCOUNT_ROLES:
      raise UnknownRole(
        "role must be one of {}, got {!r}".format(ACCOUNT_ROLES, role)
      )

    sql = '''INSERT INTO person_account
               (platform, owner_user_id, person_id, role)
             VALUES (%s, %s, %s, %s)
             ON DUPLICATE KEY UPDATE
               person_id = VALUES(person_id),
               role      = VALUES(role);
          '''
    self.require_write_ready()
    try:
      with self.get_connection() as connector:
        with connector.cursor() as cursor:
          cursor.execute(sql, (platform, owner_user_id, person_id, role))
          connector.commit()
    except Exception as e:
      get_logger().error(
        "attach account {} to person {} failed: {}".format(
          owner_user_id,
          person_id,
          e,
        )
      )
      raise e

  def account_exists(self, owner_user_id: str) -> bool:
    """Whether this program has ever heard of this account.

    ``share_url`` is the register of accounts this server knows: a download, a
    live probe or a marking puts a row there.  The endpoints that take an
    ``owner_user_id`` straight from a client check it here first, so a made-up
    id is refused rather than quietly minting a row for an account that does not
    exist - which is what the identity upsert inside an assignment would
    otherwise do.
    """
    if not isinstance(owner_user_id, str) or not owner_user_id.strip():
      return False

    sql = '''SELECT 1 AS present
             FROM share_url
             WHERE owner_user_id = %s
             LIMIT 1;
          '''
    try:
      with self.get_connection() as connector:
        with connector.cursor() as cursor:
          cursor.execute(sql, (owner_user_id.strip(),))
          row = cursor.fetchone()
    except Exception as e:
      get_logger().error(
        "look up account {} failed: {}".format(owner_user_id, e)
      )
      raise e
    return bool(row)

  def account_directory_name(self, owner_user_id: str):
    """The folder this one account is recorded under, exactly as stored.

    Reported raw - blanks and the literal text ``"None"`` that older rows carry
    are left in - because what counts as an unusable value is a question about
    what the caller wants the value *for*, and the only caller wants it as a
    fallback name for a person.  Deciding that here would put half the policy
    in the wrong place.
    """
    sql = '''SELECT directory_name
             FROM share_url
             WHERE owner_user_id = %s;
          '''
    try:
      with self.get_connection() as connector:
        with connector.cursor() as cursor:
          cursor.execute(sql, (owner_user_id,))
          row = cursor.fetchone()
    except Exception as e:
      get_logger().error(
        "look up folder for {} failed: {}".format(owner_user_id, e)
      )
      raise e
    return None if not row else row.get("directory_name")

##
## >>============================= assignment =============================>>
##
  def assign_account(
    self,
    owner_user_id: str,
    role: str,
    platform: str = PLATFORM,
    person_id: int = None,
    display_name: str = None,
    note: str = None,
    sec_user_id: str = None,
    nickname: str = None,
    allow_move: bool = False,
    demote_main_to: str = None,
  ) -> dict:
    """Create or find a person, attach one account to them, in one transaction.

    Done as separate calls - ``create_person``, ``upsert_account_identity``,
    ``attach_account``, ``align_accounts_to_main``, each committing its own work
    - this operation has four middles.  A person exists holding nothing and the
    attach that was meant to follow has already failed; an account is attached
    but the folders still point somewhere else; a main is demoted and its
    replacement never arrives, so the person has no main at all.  Nobody ever
    goes back to clean those up, so the invariant has to be that they cannot
    happen: one connection, one transaction, one commit.

    Two things are decided here rather than above, because both are read-then-
    write and only a lock makes that safe:

    * whether the account already belongs to somebody else, and
    * whether the person already has a main account.

    ``person_account`` has no unique constraint that would forbid a second main
    - ``role`` is a plain string, chosen so that which account is the main one
    stays a judgement call - so the rows are locked while the decision is made.
    A person is locked before their accounts are, always in that order, so two
    of these running at once cannot deadlock against each other.

    Nothing here talks to a platform.  Every identity value arrives already
    resolved, because a request made between BEGIN and COMMIT would hold every
    lock this transaction has taken for as long as douyin takes to answer.
    """
    if role not in ACCOUNT_ROLES:
      ##
      ## Before the guard and before the connection: a bad role is wrong
      ## whatever the database is doing, and finding that out after taking locks
      ## would be a transaction opened for nothing.
      ##
      raise UnknownRole(
        "role must be one of {}, got {!r}".format(ACCOUNT_ROLES, role)
      )
    if demote_main_to is not None and demote_main_to not in _DEMOTABLE_ROLES:
      ##
      ## ``main`` in particular.  Demoting the old main *to* main is the
      ## two-main state written out in full.
      ##
      raise UnknownRole(
        "demote_main_to must be one of {}, got {!r}".format(
          _DEMOTABLE_ROLES, demote_main_to
        )
      )
    if not isinstance(owner_user_id, str) or not owner_user_id.strip():
      raise ValueError("owner_user_id is required")
    if person_id is None and (
      not isinstance(display_name, str) or not display_name.strip()
    ):
      raise ValueError("display_name is required to create a person")

    owner_user_id = owner_user_id.strip()
    self.require_write_ready()

    with self.get_connection() as connector:
      connector.begin()
      try:
        result = self._assign_within_transaction(
          connector,
          owner_user_id=owner_user_id,
          role=role,
          platform=platform,
          person_id=person_id,
          display_name=display_name,
          note=note,
          sec_user_id=sec_user_id,
          nickname=nickname,
          allow_move=allow_move,
          demote_main_to=demote_main_to,
        )
        connector.commit()
      except Exception as e:
        ##
        ## Issued here rather than left to whoever hands out the connection.
        ## The transaction is opened in this method, so it is closed in it too:
        ## a caller that one day reaches for the connection differently must not
        ## silently lose the only thing keeping these rows consistent.
        ##
        connector.rollback()
        if _is_duplicate_main(e):
          ##
          ## The schema said no.  Raised as the conflict this method raises
          ## itself, so every caller above already knows what to do with it -
          ## without the two answers to one situation reading differently
          ## depending on which layer noticed.
          ##
          ## Which account currently holds the main is not reported: the
          ## transaction is gone and there is nothing left to read it from.
          ## Absent rather than guessed - the page then shows the plain refusal
          ## and offers no "replace the main" action, which is correct, because
          ## there is nothing here to replace against.
          ##
          get_logger().warning(
            "database refused a second main for person {}".format(person_id)
          )
          raise MainAlreadyAssigned(None, None) from e
        if not isinstance(e, AssignmentConflict):
          get_logger().error(
            "assign {} to person {} failed: {}".format(
              owner_user_id, person_id, e
            )
          )
        raise
    return result

  def detach_account_guarded(
    self,
    platform: str,
    owner_user_id: str,
  ) -> dict:
    """Unmark an account, unless doing so strands the ones aligned to it.

    The guarded twin of ``detach_account``.  That one is a bare DELETE and stays
    that way for callers that already know what they are removing; this is the
    one an http request reaches, because a person page has an "unmark" button
    beside every account and it reaches the same rows by a shorter road than the
    assignment endpoint does.

    Same transaction shape and the same rule as an assignment: the account is
    read first - it is the row that says which person this is - then the person
    is locked, then the decision is made and written.
    """
    if not isinstance(owner_user_id, str) or not owner_user_id.strip():
      raise ValueError("owner_user_id is required")

    owner_user_id = owner_user_id.strip()
    self.require_write_ready()

    with self.get_connection() as connector:
      connector.begin()
      try:
        result = self._detach_within_transaction(
          connector, platform, owner_user_id
        )
        connector.commit()
      except Exception as e:
        connector.rollback()
        if not isinstance(e, AssignmentConflict):
          get_logger().error(
            "detach account {} failed: {}".format(owner_user_id, e)
          )
        raise
    return result

  def _detach_within_transaction(
    self,
    connector,
    platform: str,
    owner_user_id: str,
  ) -> dict:
    with connector.cursor() as cursor:
      ##
      ## 1. Which person this account belongs to - read without a lock.
      ##
      ## The account row is what names the person, and the person must be locked
      ## first.  Locking the account here to find out, as this used to, gave
      ## detach the order account -> person while every assignment takes
      ## person -> account: two requests on the same pair of rows would each
      ## hold what the other was waiting for.
      ##
      cursor.execute(_FIND_ATTACHMENT_SQL, (platform, owner_user_id))
      observed = cursor.fetchone()
      if not observed:
        raise NotAttached(owner_user_id)
      person_id = observed.get("person_id")

      ##
      ## 2. The person, before anything is decided or written, so the counts the
      ## guard reads cannot move underneath this transaction.
      ##
      cursor.execute(_LOCK_PERSON_SQL, (person_id,))
      cursor.fetchone()

      ##
      ## 3. The account, locked - and confirmed still to belong to the person
      ## just locked.  Between the two reads it could have been moved, and the
      ## person holding it now is one this transaction has not locked.
      ##
      cursor.execute(_LOCK_ATTACHMENT_SQL, (platform, owner_user_id))
      current = cursor.fetchone()
      if not current:
        raise NotAttached(owner_user_id)
      if current.get("person_id") != person_id:
        raise AssignmentRaced(owner_user_id)

      self._guarded_main_departure(
        cursor, person_id, owner_user_id, current.get("role")
      )

      cursor.execute(_DETACH_ACCOUNT_SQL, (platform, owner_user_id))

    return {
      "owner_user_id": owner_user_id,
      "person_id": person_id,
      "role": current.get("role"),
    }

  def _guarded_main_departure(
    self,
    cursor,
    person_id,
    owner_user_id: str,
    current_role,
  ) -> None:
    """Refuse to take a person's last main away from the accounts aligned to it.

    Called wherever an account stops being somebody's main - demoted in place,
    moved to another person, or unmarked altogether - so the three cannot answer
    the question differently.

    Two conditions, both read inside the transaction while the person row is
    held: this account is the person's *only* main, and the person still holds
    other accounts.  The second is what keeps the rule honest.  Align writes
    only rows with ``role <> 'main'``, so a person holding nothing but this
    account has never had a folder copied anywhere - not even onto this one -
    and letting it go leaves its own recorded folder exactly as it was.
    """
    if current_role != ROLE_MAIN or person_id is None:
      return

    cursor.execute(_COUNT_PERSON_ACCOUNTS_SQL, (ROLE_MAIN, person_id))
    counts = cursor.fetchone() or {}
    account_count = int(counts.get("account_count") or 0)
    ##
    ## Rows written before this rule existed can hold two mains.  Demoting one
    ## of them still leaves a main behind, so the relationship the rule protects
    ## survives - and refusing would make that pre-existing mess impossible to
    ## tidy up.
    ##
    main_count = int(counts.get("main_count") or 0)
    if main_count > 1 or account_count <= 1:
      return

    cursor.execute(_NAME_PERSON_SQL, (person_id,))
    person = cursor.fetchone()
    cursor.execute(_NAME_ACCOUNT_SQL, (owner_user_id,))
    named = cursor.fetchone()
    raise LastMainRemoval(
      person_id,
      display_name=None if not person else person.get("display_name"),
      owner_user_id=owner_user_id,
      nickname=None if not named else named.get("nickname"),
    )

  def _assign_within_transaction(
    self,
    connector,
    owner_user_id: str,
    role: str,
    platform: str,
    person_id,
    display_name,
    note,
    sec_user_id,
    nickname,
    allow_move: bool,
    demote_main_to,
  ) -> dict:
    """The body of the transaction.  Every statement runs on ``connector``."""
    with connector.cursor() as cursor:
      target_display_name = display_name.strip() if display_name else None

      ##
      ## 1. Which people this touches, discovered without a lock.
      ##
      ## A move touches two: the person named by the request, and whoever holds
      ## the account today.  Both have to be locked, and the second one is only
      ## knowable by reading the account - which is exactly the row that must be
      ## locked *after* the people.  So it is read unlocked here, purely to
      ## choose what to lock, and re-checked in step 3.
      ##
      cursor.execute(_FIND_ATTACHMENT_SQL, (platform, owner_user_id))
      observed = cursor.fetchone()
      observed_person_id = None if not observed else observed.get("person_id")

      ##
      ## 2. The people, locked lowest id first.
      ##
      ## For a person that already exists this is also the serialisation point
      ## for their single main slot: two requests each promoting a different
      ## account of one person find no main row to lock, so without this both
      ## would see "no main" and both would write one.  A person created below
      ## needs no such lock - nobody else can see them yet - and holds the row
      ## from the insert onwards.
      ##
      ## Ascending id rather than "target then source".  Two moves swapping a
      ## pair of accounts between two people would otherwise take the same two
      ## locks in opposite orders, which is a deadlock that only shows up under
      ## real traffic.
      ##
      involved = set()
      if person_id is not None:
        involved.add(person_id)
      if observed_person_id is not None:
        involved.add(observed_person_id)

      locked = {}
      for each in sorted(involved):
        cursor.execute(_LOCK_PERSON_SQL, (each,))
        row = cursor.fetchone()
        if row:
          locked[each] = row

      if person_id is not None:
        if person_id not in locked:
          raise PersonMissing(person_id)
        target_display_name = locked[person_id].get("display_name")

      ##
      ## 3. The account, locked - and confirmed to be where the unlocked read
      ## said it was.  If it changed hands in between, the person now holding it
      ## is one this transaction has not locked, and the last-main question
      ## below would be decided against rows nobody is holding still.
      ##
      cursor.execute(_LOCK_ATTACHMENT_SQL, (platform, owner_user_id))
      current = cursor.fetchone()
      settled_person_id = None if not current else current.get("person_id")
      if settled_person_id != observed_person_id:
        raise AssignmentRaced(owner_user_id)

      ##
      ## 4. Whether this is a move, and whether the move was asked for.
      ##
      held_by = None if not current else current.get("person_id")
      current_role = None if not current else current.get("role")
      moving = held_by is not None and held_by != person_id
      if moving and not allow_move:
        cursor.execute(_NAME_PERSON_SQL, (held_by,))
        holder = cursor.fetchone()
        raise AccountAttachedElsewhere(
          held_by, None if not holder else holder.get("display_name")
        )
      if moving:
        ##
        ## ``allow_move`` answers "may this account leave its person".  It does
        ## not answer "may that person be left with no main", which is a
        ## question about the person being left behind - and one nobody asked.
        ##
        self._guarded_main_departure(
          cursor, held_by, owner_user_id, current_role
        )

      ##
      ## 5. Whether the relationship being asked for is already the one on
      ## record.  A browser retrying a request it never saw the answer to must
      ## not turn into a second, different state, so nothing below moves the
      ## account, changes its role, or creates anybody.
      ##
      ## Note what this does *not* cover: who the account *is*.  That is a
      ## different fact in a different table, and it arrived from a resolution
      ## made seconds ago - very possibly newer than what ``share_url`` holds.
      ## See step 6.
      ##
      relationship_unchanged = (
        not moving and current is not None and current.get("role") == role
      )

      ##
      ## 6. The person's current main, locked, and what to do about it - in both
      ## directions.  Gaining a second main and losing the only one are the same
      ## invariant seen from either end.
      ##
      if not relationship_unchanged and not moving and role != ROLE_MAIN:
        ##
        ## The same account, same person, new role.  If it was the main, this is
        ## the invariant's other direction: not "two mains" but "none", and the
        ## accounts aligned to it are just as stranded either way.
        ##
        self._guarded_main_departure(
          cursor, person_id, owner_user_id, current_role
        )

      demoted = None
      if (
        not relationship_unchanged
        and role == ROLE_MAIN
        and person_id is not None
      ):
        cursor.execute(_LOCK_MAIN_SQL, (person_id,))
        main = cursor.fetchone()
        held_main = None if not main else main.get("owner_user_id")
        if held_main is not None and held_main != owner_user_id:
          if demote_main_to is None:
            cursor.execute(_NAME_ACCOUNT_SQL, (held_main,))
            named = cursor.fetchone()
            raise MainAlreadyAssigned(
              held_main, None if not named else named.get("nickname")
            )
          demoted = held_main

      ##
      ## 7. Identity - refreshed on every accepted assignment, including one
      ## that changes no relationship at all.  It is also what lets the page
      ## name an account that has never been
      ## downloaded - ``share_url`` gets a row from a download or from here, and
      ## an owner with neither is invisible to the account search.
      ##
      ## ``directory_name`` is deliberately not among the columns: it belongs to
      ## the download paths and to the alignment below, and the person's folder
      ## wins over it regardless.
      ##
      cursor.execute(
        _UPSERT_IDENTITY_SQL, (owner_user_id, sec_user_id, nickname)
      )

      if relationship_unchanged:
        ##
        ## Who the account belongs to is unchanged; who the account *is* has
        ## just been refreshed.  Returning before this upsert instead - which is
        ## what "repeating an assignment writes nothing" used to mean - left a
        ## user re-pasting a link, watching it succeed, and still seeing the
        ## nickname the account had a year ago, or no sec_user_id at all for one
        ## marked by link before it was ever downloaded.
        ##
        ## The person is deliberately *not* renamed to follow the nickname.  A
        ## name somebody typed is theirs; renaming is PATCH /api/person/<id>.
        ##
        return {
          "person_id": person_id,
          "created_person": False,
          "owner_user_id": owner_user_id,
          "role": role,
          "display_name": target_display_name,
        }

      created_person = False
      if person_id is None:
        cursor.execute(_INSERT_PERSON_SQL, (target_display_name, note))
        person_id = cursor.lastrowid
        created_person = True

      if demoted is not None:
        cursor.execute(_DEMOTE_MAIN_SQL, (demote_main_to, platform, demoted))

      cursor.execute(
        _ATTACH_ACCOUNT_SQL, (platform, owner_user_id, person_id, role)
      )

      ##
      ## Inside the same transaction.  Aligning afterwards would leave a window
      ## in which the account is attached and the folders still say something
      ## else, and whoever downloaded during it would file in the wrong place.
      ##
      cursor.execute(_ALIGN_TO_MAIN_SQL, (platform, person_id))

    return {
      "person_id": person_id,
      "created_person": created_person,
      "owner_user_id": owner_user_id,
      "role": role,
      "display_name": target_display_name,
    }

  def find_person_folder(self, owner_user_id: str, platform: str = PLATFORM):
    """Return this account's person folder and the id that discriminates it.

    ``{"directory_name": ..., "main_owner_user_id": ...}`` or ``None``.

    Both come from the main account: the folder because that is where the
    person's files live, and the id because a folder shared by two different
    people has to be split, and every account of one person must land on the
    same side of that split.
    """
    sql = '''SELECT s.directory_name, s.owner_user_id
             FROM person_account AS mine
             JOIN person_account AS main_account
               ON main_account.person_id = mine.person_id
              AND main_account.role = 'main'
             JOIN share_url AS s
               ON s.owner_user_id = main_account.owner_user_id
             WHERE mine.platform = %s AND mine.owner_user_id = %s
             LIMIT 1;
          '''
    try:
      with self.get_connection() as connector:
        with connector.cursor() as cursor:
          cursor.execute(sql, (platform, owner_user_id))
          row = cursor.fetchone()
    except Exception as e:
      get_logger().error(
        "look up person folder for {} failed: {}".format(owner_user_id, e)
      )
      raise e

    if not row:
      return None
    directory = row.get("directory_name")
    if not isinstance(directory, str) or not directory.strip():
      return None
    return {
      "directory_name": directory,
      "main_owner_user_id": row.get("owner_user_id"),
    }

  def count_identities_using_directory_name(
    self,
    directory_name: str,
    platform: str = PLATFORM,
  ) -> int:
    """How many distinct identities file under this folder name.

    An identity is a person, or an account nobody marked.  Counting accounts
    instead would let one person's own accounts look like a collision: they all
    record the same folder after alignment, so a single person would count as
    two and their accounts would be split apart by the discriminator meant to
    separate strangers.
    """
    if not isinstance(directory_name, str) or not directory_name.strip():
      return 0

    sql = '''SELECT COUNT(DISTINCT
                      COALESCE(CAST(pa.person_id AS CHAR), s.owner_user_id)
                    ) AS identity_count
             FROM share_url AS s
             LEFT JOIN person_account AS pa
               ON pa.owner_user_id = s.owner_user_id AND pa.platform = %s
             WHERE s.directory_name = %s;
          '''
    try:
      with self.get_connection() as connector:
        with connector.cursor() as cursor:
          cursor.execute(sql, (platform, directory_name))
          row = cursor.fetchone()
    except Exception as e:
      get_logger().error(
        "count identities using {} failed: {}".format(directory_name, e)
      )
      raise e
    if not row:
      return 0
    return int(row.get("identity_count") or 0)

  def align_accounts_to_main(self, person_id: int) -> None:
    """Point this person's other accounts at the main account's folder.

    Their downloads already land there - the resolver reads the main account's
    folder for every account of the person - so leaving each sub-account's own
    row saying something else would give the database two answers to the same
    question, and whoever read the wrong one would be wrong.

    The main account's own row is the fact being copied, so it is excluded; and
    a main account that has no folder yet copies nothing, rather than blanking
    what the sub-accounts already had.
    """
    sql = _ALIGN_TO_MAIN_SQL
    self.require_write_ready()
    try:
      with self.get_connection() as connector:
        with connector.cursor() as cursor:
          cursor.execute(sql, (PLATFORM, person_id))
          connector.commit()
    except Exception as e:
      get_logger().error(
        "align accounts of person {} failed: {}".format(person_id, e)
      )
      raise e

  def detach_account(self, platform: str, owner_user_id: str) -> None:
    """Unmark an account.

    Its downloads fall back to the account's own recorded folder, which is what
    makes a mis-marked account recoverable.
    """
    sql = '''DELETE FROM person_account
             WHERE platform = %s AND owner_user_id = %s;
          '''
    self.require_write_ready()
    try:
      with self.get_connection() as connector:
        with connector.cursor() as cursor:
          cursor.execute(sql, (platform, owner_user_id))
          connector.commit()
    except Exception as e:
      get_logger().error(
        "detach account {} failed: {}".format(owner_user_id, e)
      )
      raise e

##
## >>============================= directory =============================>>
##
  def find_person_directory_name(
    self,
    owner_user_id: str,
    platform: str = PLATFORM,
  ):
    """Return the folder this account's person files under, or ``None``.

    The answer is the **main account's** recorded folder.  A person does not
    carry a folder of their own: if a person exists then one of their accounts
    is the main one, and its ``share_url.directory_name`` is already the fact of
    where that person's files live.  A second copy on ``person`` would only be
    somewhere for the two to disagree.

    ``None`` covers every way there is no answer - the account is not marked,
    the person has no main account, the main account has no row or no recorded
    folder - because the caller does the same thing in all of them: fall back to
    what it did before people existed.
    """
    sql = '''SELECT s.directory_name
             FROM person_account AS mine
             JOIN person_account AS main_account
               ON main_account.person_id = mine.person_id
              AND main_account.role = 'main'
             JOIN share_url AS s
               ON s.owner_user_id = main_account.owner_user_id
             WHERE mine.platform = %s AND mine.owner_user_id = %s
             LIMIT 1;
          '''
    try:
      with self.get_connection() as connector:
        with connector.cursor() as cursor:
          cursor.execute(sql, (platform, owner_user_id))
          row = cursor.fetchone()
    except Exception as e:
      get_logger().error(
        "look up person directory for {} failed: {}".format(owner_user_id, e)
      )
      raise e

    if not row:
      return None
    found = row.get("directory_name")
    if not isinstance(found, str) or not found.strip():
      return None
    return found

##
## >>============================= aggregation =============================>>
##
  def list_person_accounts(self, person_id: int) -> list:
    """Every account this person holds, with its role and current nickname."""
    sql = '''SELECT pa.owner_user_id, s.nickname, pa.role
             FROM person_account AS pa
             LEFT JOIN share_url AS s
               ON s.owner_user_id = pa.owner_user_id
             WHERE pa.person_id = %s
             ORDER BY pa.role, s.nickname;
          '''
    try:
      with self.get_connection() as connector:
        with connector.cursor() as cursor:
          cursor.execute(sql, (person_id,))
          rows = cursor.fetchall() or []
    except Exception as e:
      get_logger().error("list accounts of {} failed: {}".format(person_id, e))
      raise e

    return [
      {
        "owner_user_id": row.get("owner_user_id"),
        "nickname": row.get("nickname"),
        "role": row.get("role"),
      }
      for row in rows
    ]

  def person_summary(self, person_id: int) -> dict:
    """How many posts and recordings this person has, across every account.

    Counted with subqueries rather than joined together: joining both record
    tables onto the accounts would multiply their rows against each other and
    report a product instead of two counts.
    """
    sql = '''SELECT
               (SELECT COUNT(*)
                FROM aweme_record AS a
                JOIN person_account AS pa
                  ON pa.owner_user_id = a.owner_user_id
                WHERE pa.person_id = %s) AS aweme_count,
               (SELECT COUNT(*)
                FROM live_record AS l
                JOIN person_account AS pa
                  ON pa.owner_user_id = l.owner_user_id
                WHERE pa.person_id = %s) AS live_count;
          '''
    try:
      with self.get_connection() as connector:
        with connector.cursor() as cursor:
          cursor.execute(sql, (person_id, person_id))
          row = cursor.fetchone()
    except Exception as e:
      get_logger().error("summarise person {} failed: {}".format(person_id, e))
      raise e

    if not row:
      return {"aweme_count": 0, "live_count": 0}
    return {
      "aweme_count": row.get("aweme_count") or 0,
      "live_count": row.get("live_count") or 0,
    }

  def list_subjects_of(self, photographer_id: int) -> list:
    """The people this photographer has worked with."""
    sql = '''SELECT p.person_id, p.display_name, c.note
             FROM person_collaboration AS c
             JOIN person AS p ON p.person_id = c.subject_id
             WHERE c.photographer_id = %s
             ORDER BY p.display_name;
          '''
    return self._collaboration_side(sql, photographer_id, "subjects")

  def list_photographers_of(self, subject_id: int) -> list:
    """The photographers who have shot this person.

    The mirror of ``list_subjects_of``: the relation is directed, so asking it
    from the other end is a different query rather than the same one reversed.
    """
    sql = '''SELECT p.person_id, p.display_name, c.note
             FROM person_collaboration AS c
             JOIN person AS p ON p.person_id = c.photographer_id
             WHERE c.subject_id = %s
             ORDER BY p.display_name;
          '''
    return self._collaboration_side(sql, subject_id, "photographers")

  def _collaboration_side(self, sql: str, person_id: int, side: str) -> list:
    try:
      with self.get_connection() as connector:
        with connector.cursor() as cursor:
          cursor.execute(sql, (person_id,))
          rows = cursor.fetchall() or []
    except Exception as e:
      get_logger().error(
        "list {} of {} failed: {}".format(side, person_id, e)
      )
      raise e

    return [
      {
        "person_id": row.get("person_id"),
        "display_name": row.get("display_name"),
        "note": row.get("note"),
      }
      for row in rows
    ]

  def list_works_by_photographer(self, photographer_id: int, limit: int = 200):
    """Posts belonging to everyone this photographer has worked with.

    Recorded between people, not against individual posts, so this returns the
    subjects' whole output rather than the specific shoots.  Marking 1547 posts
    one by one, and each new one after them, costs more than that precision is
    worth; a pair is marked once.
    """
    sql = '''SELECT a.aweme_id, a.desc, a.save_dir, a.downloaded_at,
                    p.display_name
             FROM person_collaboration AS c
             JOIN person_account AS pa ON pa.person_id = c.subject_id
             JOIN aweme_record AS a
               ON a.owner_user_id = pa.owner_user_id
             JOIN person AS p ON p.person_id = c.subject_id
             WHERE c.photographer_id = %s
             ORDER BY a.downloaded_at DESC
             LIMIT %s;
          '''
    try:
      with self.get_connection() as connector:
        with connector.cursor() as cursor:
          cursor.execute(sql, (photographer_id, int(limit)))
          rows = cursor.fetchall() or []
    except Exception as e:
      get_logger().error(
        "list works by photographer {} failed: {}".format(photographer_id, e)
      )
      raise e

    return [
      {
        "aweme_id": row.get("aweme_id"),
        "desc": row.get("desc"),
        "save_dir": row.get("save_dir"),
        "downloaded_at": row.get("downloaded_at"),
        "owner_display_name": row.get("display_name"),
      }
      for row in rows
    ]

##
## >>============================= collaboration =============================>>
##
  def add_collaboration(
    self,
    photographer_id: int,
    subject_id: int,
    note: str = None,
  ) -> None:
    """Record that a photographer works with a subject.

    Directed, so the pair is stored as given.  A person photographing themselves
    is rejected: the row would carry no information and would make "who did this
    person shoot" answer with themselves.
    """
    if photographer_id == subject_id:
      raise ValueError("a person cannot be recorded as photographing themselves")

    sql = '''INSERT INTO person_collaboration
               (photographer_id, subject_id, note)
             VALUES (%s, %s, %s)
             ON DUPLICATE KEY UPDATE
               note = COALESCE(VALUES(note), note);
          '''
    self.require_write_ready()
    try:
      with self.get_connection() as connector:
        with connector.cursor() as cursor:
          cursor.execute(sql, (photographer_id, subject_id, note))
          connector.commit()
    except Exception as e:
      get_logger().error(
        "record collaboration {} -> {} failed: {}".format(
          photographer_id,
          subject_id,
          e,
        )
      )
      raise e

  def remove_collaboration(self, photographer_id: int, subject_id: int) -> None:
    sql = '''DELETE FROM person_collaboration
             WHERE photographer_id = %s AND subject_id = %s;
          '''
    self.require_write_ready()
    try:
      with self.get_connection() as connector:
        with connector.cursor() as cursor:
          cursor.execute(sql, (photographer_id, subject_id))
          connector.commit()
    except Exception as e:
      get_logger().error(
        "remove collaboration {} -> {} failed: {}".format(
          photographer_id,
          subject_id,
          e,
        )
      )
      raise e
