##<<Base>>
from threading import Lock

##<<Extension>>
from flask import Blueprint, jsonify, request

##<<Third-part>>
from backend.src.database.orm.models.person import ACCOUNT_ROLES
from backend.src.database.table.person_identity import (
  DouyinPersonIdentityTable,
  UnknownRole,
)
from backend.src.library.configlib import load_config
from backend.src.library.loglib import get_logger
from backend.src.platform.douyin.douyin_owner_identity import (
  DouyinOwnerIdentityReader,
)
from backend.src.service.person_assignment import (
  PersonAssignmentError,
  PersonAssignmentService,
)



def _error(message: str, code: int):
  return jsonify({"status": "error", "message": message, "code": code}), code


def _ok(data: dict):
  return jsonify({"status": "success", "code": 200, "data": data}), 200


def _refusal(error: PersonAssignmentError):
  """Answer one expected refusal with the status and kind it carries.

  ``kind`` reaches the browser here, unlike the resolve and task endpoints where
  it only reaches the log.  It has to: both conflicts answer 409, and the page's
  next move is ``allow_move`` for one and ``replace_main`` for the other.  A
  client that could not tell them apart could offer neither.

  ``details`` is whatever the user needs in order to make that choice - who
  holds the account, what the current main is called - and nothing else.
  """
  body = {
    "status": "error",
    "message": str(error),
    "code": error.status_code,
    "kind": error.kind,
  }
  body.update(error.details())
  return jsonify(body), error.status_code


class PersonRuntime:
  """Holds the person table, built once and shared.

  ``table_factory`` exists so the tests can supply a stand-in without a
  database; production leaves it alone and gets the real table.
  """

  def __init__(self, config: dict = None, table_factory=None) -> None:
    self._config = config
    self._table_factory = table_factory
    self._table = None
    self._owner_runtime = None
    self._identity_reader = None
    self._lock = Lock()

  def settings(self) -> dict:
    return load_config() if self._config is None else self._config

  def owner_runtime(self):
    """The owner-browse runtime, reused for its link resolution.

    Imported lazily and shared rather than copied: following a share link needs
    the browser-shaped headers and the short-link handling that path already
    got right, and a second copy of that would drift from it.
    """
    if self._owner_runtime is None:
      with self._lock:
        if self._owner_runtime is None:
          from backend.src.web.owner_routes import OwnerRuntime

          ##
          ## Its first parameter is a config *loader*, not a config.  Handing it
          ## the mapping puts a dict where a callable is expected, and handing it
          ## ``None`` - which is what production has - makes it call ``None()``
          ## the moment anything reads a setting.
          ##
          self._owner_runtime = (
            OwnerRuntime()
            if self._config is None
            else OwnerRuntime(config_loader=lambda: self._config)
          )
    return self._owner_runtime

  def resolve_owner(self, url: str):
    """Turn pasted share text into a ``sec_user_id``."""
    return self.owner_runtime().resolve_owner(url)

  def resolve_owner_identity(self, url: str):
    """Identify the owner behind any share link, or return ``None``.

    A share link names an owner whichever kind it is - their profile, one of
    their posts, or their live room - so all three are accepted.  The link is
    followed once, here, and the resolved url is then read by the same reader
    the assignment endpoint uses; that endpoint arrives with the url already
    followed, which is the only difference between the two paths.

    The answer is always keyed on ``owner_user_id``.  The link itself is never
    an identity: douyin issues different short links for the same post, so
    matching on one would treat the same thing as two.
    """
    resolved = self.owner_runtime().follow_share_link(url)
    if not resolved:
      return None
    return self.identity_reader().from_resolved_url(resolved)

  def identity_reader(self) -> DouyinOwnerIdentityReader:
    """The one reader that turns a named resource into an owner.

    Built from this runtime's own collaborators so the profile lookup goes
    through the owner api this runtime already holds, rather than a second one
    with its own headers and its own cookie.
    """
    if self._identity_reader is None:
      with self._lock:
        if self._identity_reader is None:
          self._identity_reader = DouyinOwnerIdentityReader(
            owner_detail=self.owner_detail,
            post_resolution=self._post_resolution,
            live_probe=self._live_probe,
          )
    return self._identity_reader

  def _post_resolution(self, url: str, aweme_id: str = None):
    """Resolve one post.  Its payload already carries the author's id, sec id
    and nickname, so this answers the whole question - no second request for
    the profile."""
    from backend.src.platform.douyin.douyin_aweme_downloader import (
      get_aweme_downloader,
    )

    return get_aweme_downloader().resolver.resolve(url, aweme_id=aweme_id)

  def _live_probe(self, url: str):
    """Probe one live room, open or not.  The probe reports the room's owner
    either way, so a marked owner does not have to be streaming at the moment
    you mark them."""
    from backend.src.platform.douyin.douyin_live_downloader import (
      get_live_downloader,
    )

    return get_live_downloader().prober.probe(url)

  def assignment_service(self, require_receipts: bool = True):
    """The assignment service for the request being handled.

    Built per request rather than once, because the store it redeems receipts
    against belongs to the *application* - and this blueprint is registered
    before that store is installed.  Reading it from ``current_app`` is what
    keeps the lazy wsgi app and a test's app from redeeming each other's
    receipts.  Building one costs nothing: it holds a factory, not a connection.

    ``require_receipts`` is what the older endpoints pass.  They name an account
    the server already knows, or one they resolved themselves, so a missing
    resolve store is no reason to refuse them - answering 503 there would break
    a page that never used receipts in the first place.  They still get the same
    service, and the same guarded transaction underneath it.
    """
    from backend.src.web.resolve_routes import resolve_service

    store = resolve_service()
    if store is None and require_receipts:
      return None
    return PersonAssignmentService(
      resolve_service=store,
      table_factory=self.table,
      identity_reader=self.identity_reader(),
    )

  def owner_detail(self, sec_user_id: str):
    """Fetch the owner's profile, which is where ``uid`` comes from."""
    from backend.src.platform.douyin.douyin_owner_detail import (
      fetch_owner_detail,
    )

    return fetch_owner_detail(self.owner_runtime().api(), sec_user_id)

  def table(self):
    if self._table is None:
      with self._lock:
        if self._table is None:
          if self._table_factory is not None:
            self._table = self._table_factory()
          else:
            database = self.settings()["database"]
            self._table = DouyinPersonIdentityTable(
              host=database["host"],
              user=database["username"],
              passwd=database["password"],
              database=database["name"],
            )
    return self._table


def _serialize_work(work: dict) -> dict:
  """Dates become strings; everything else passes through."""
  downloaded_at = work.get("downloaded_at")
  return {
    "aweme_id": work.get("aweme_id"),
    "desc": work.get("desc"),
    "save_dir": work.get("save_dir"),
    "downloaded_at": (
      downloaded_at.isoformat() if hasattr(downloaded_at, "isoformat")
      else downloaded_at
    ),
    "owner_display_name": work.get("owner_display_name"),
  }


def build_person_blueprint(runtime: PersonRuntime = None) -> Blueprint:
  runtime = runtime if runtime is not None else PersonRuntime()
  blueprint = Blueprint("person", __name__, url_prefix="/api")

  def _payload():
    """Return the JSON body, or ``None`` when there is not a usable one."""
    if not request.is_json:
      return None
    try:
      body = request.get_json(silent=True)
    except Exception:
      return None
    return body if isinstance(body, dict) else None

  def _int_field(body: dict, name: str):
    value = body.get(name)
    if isinstance(value, bool) or not isinstance(value, int):
      try:
        value = int(str(value).strip())
      except (TypeError, ValueError):
        return None
    return value

  @blueprint.route("/person", methods=["GET"])
  def list_people():
    try:
      persons = runtime.table().list_persons()
    except Exception as e:
      get_logger().error("list persons failed: {}".format(e))
      return _error("读取人物列表失败", 502)
    return _ok({"persons": persons})

  @blueprint.route("/person", methods=["POST"])
  def create_person():
    body = _payload()
    if body is None:
      return _error("请求必须是 JSON 格式", 400)
    display_name = (body.get("display_name") or "").strip()
    if not display_name:
      return _error("缺少必需字段: display_name", 400)

    note = (body.get("note") or "").strip() or None
    try:
      ##
      ## No folder is asked for.  It is the main account's, so it arrives with
      ## the first account marked as main rather than being invented here.
      ##
      person_id = runtime.table().create_person(display_name, note=note)
    except Exception as e:
      get_logger().error("create person failed: {}".format(e))
      return _error("创建人物失败", 502)
    return _ok({"person_id": person_id})

  @blueprint.route("/person/<int:person_id>", methods=["PATCH"])
  def update_person(person_id: int):
    body = _payload()
    if body is None:
      return _error("请求必须是 JSON 格式", 400)

    ##
    ## Only what was sent is forwarded.  A field the page did not include keeps
    ## its stored value rather than being blanked.
    ##
    fields = {}
    for name in ("display_name", "note"):
      if name in body:
        value = body.get(name)
        fields[name] = value.strip() if isinstance(value, str) else value
    if not fields:
      return _error("没有要修改的字段", 400)

    try:
      runtime.table().update_person(person_id, **fields)
    except Exception as e:
      get_logger().error("update person {} failed: {}".format(person_id, e))
      return _error("修改人物失败", 502)
    return _ok({"person_id": person_id})

  @blueprint.route("/person/<int:person_id>", methods=["DELETE"])
  def delete_person(person_id: int):
    try:
      runtime.table().delete_person(person_id)
    except Exception as e:
      get_logger().error("delete person {} failed: {}".format(person_id, e))
      return _error("删除人物失败", 502)
    return _ok({"person_id": person_id})

  @blueprint.route("/person/<int:person_id>/detail", methods=["GET"])
  def person_detail(person_id: int):
    """Everything about one person: accounts, counts, and both sides of the
    collaboration relation.

    Both directions are returned because the relation is directed and a person
    can be on either end - somebody who shoots and also streams appears in both
    lists, and only showing one would hide half of what is recorded.
    """
    try:
      table = runtime.table()
      data = {
        "accounts": table.list_person_accounts(person_id),
        "summary": table.person_summary(person_id),
        "subjects": table.list_subjects_of(person_id),
        "photographers": table.list_photographers_of(person_id),
      }
    except Exception as e:
      get_logger().error("person detail {} failed: {}".format(person_id, e))
      return _error("读取人物详情失败", 502)
    return _ok(data)

  @blueprint.route("/person/<int:person_id>/works", methods=["GET"])
  def works_by_photographer(person_id: int):
    try:
      works = runtime.table().list_works_by_photographer(person_id)
    except Exception as e:
      get_logger().error("works by {} failed: {}".format(person_id, e))
      return _error("读取作品失败", 502)
    return _ok({"works": [_serialize_work(work) for work in works]})

  @blueprint.route("/person/accounts", methods=["GET"])
  def search_accounts():
    keyword = (request.args.get("keyword") or "").strip()
    if not keyword:
      return _error("缺少必需参数: keyword", 400)
    try:
      accounts = runtime.table().search_accounts(keyword)
    except Exception as e:
      get_logger().error("search accounts failed: {}".format(e))
      return _error("搜索账号失败", 502)
    return _ok({"accounts": accounts})

  @blueprint.route("/person/account", methods=["POST"])
  def attach_account():
    body = _payload()
    if body is None:
      return _error("请求必须是 JSON 格式", 400)
    owner_user_id = (body.get("owner_user_id") or "").strip()
    if not owner_user_id:
      return _error("缺少必需字段: owner_user_id", 400)
    person_id = _int_field(body, "person_id")
    if person_id is None:
      return _error("缺少必需字段: person_id", 400)

    try:
      ##
      ## Through the guarded transaction, not ``attach_account`` followed by
      ## ``align_accounts_to_main``.  Those were two commits with a gap between
      ## them and no check in either, so this endpoint could put a second main
      ## on a person - or take their only one away - while the newer one refused
      ## to.  A rule a browser can walk around is not a rule.
      ##
      result = runtime.assignment_service(require_receipts=False)\
        .assign_known_account(
          owner_user_id=owner_user_id,
          person_id=person_id,
          role=body.get("role"),
        )
    except PersonAssignmentError as e:
      get_logger().info("attach account refused: {}".format(e.kind))
      return _refusal(e)
    except UnknownRole as e:
      return _error(str(e), 400)
    except Exception as e:
      get_logger().error("attach account failed: {}".format(e))
      return _error("挂载账号失败", 502)
    ##
    ## The success shape is unchanged - the page that calls this reads these two
    ## fields, and hardening a route is no reason to move them.
    ##
    return _ok({
      "owner_user_id": result.owner_user_id, "person_id": result.person_id
    })

  @blueprint.route("/person/account/by-link", methods=["POST"])
  def attach_account_by_link():
    """Attach an account named by a share link, downloaded or not.

    This is the only way to mark an owner who has never been downloaded and has
    never streamed: ``share_url`` gets a row from the live path or from a post
    download, so an owner with neither is invisible to the search - while the
    folder is decided at the start of the very first download.  Without this the
    first batch would always land under the nickname.
    """
    body = _payload()
    if body is None:
      return _error("请求必须是 JSON 格式", 400)
    url = (body.get("url") or "").strip()
    if not url:
      return _error("缺少必需字段: url", 400)
    person_id = _int_field(body, "person_id")
    if person_id is None:
      return _error("缺少必需字段: person_id", 400)
    role = body.get("role")
    if role not in ACCOUNT_ROLES:
      ##
      ## Checked before the network request: a bad role would waste it.
      ##
      return _error(
        "role 必须是 {} 之一".format("/".join(ACCOUNT_ROLES)), 400
      )

    try:
      identity = runtime.resolve_owner_identity(url)
    except Exception as e:
      get_logger().error("resolve owner link failed: {}".format(e))
      return _error("无法解析该链接，请稍后重试", 502)
    if identity is None:
      return _error("这条链接指向不了任何主播，请检查后重试", 400)

    owner_user_id = (identity.get("owner_user_id") or "").strip()
    if not owner_user_id:
      ##
      ## person_account is keyed on the account id.  A blank one would create a
      ## row nothing can ever match, and the download path looks the owner up by
      ## exactly this id.
      ##
      return _error("该主播没有可用的账号 id，无法挂载", 502)

    nickname = identity.get("nickname")
    try:
      ##
      ## The link has been followed above, outside the transaction, and what it
      ## said is carried in.  Recording the identity and the attachment as two
      ## separate commits - which is what this route used to do - left an
      ## identity row able to survive an attach that failed, and checked nothing
      ## about mains on the way through.
      ##
      result = runtime.assignment_service(require_receipts=False)\
        .assign_resolved_account(
          identity=identity,
          person_id=person_id,
          role=role,
        )
    except PersonAssignmentError as e:
      get_logger().info("attach by link refused: {}".format(e.kind))
      return _refusal(e)
    except UnknownRole as e:
      return _error(str(e), 400)
    except Exception as e:
      get_logger().error("attach by link failed: {}".format(e))
      return _error("挂载账号失败", 502)

    ##
    ## Unchanged for the page that calls it, nickname included.
    ##
    return _ok({
      "owner_user_id": result.owner_user_id,
      "person_id": result.person_id,
      "nickname": nickname,
    })

  @blueprint.route("/person/assignment", methods=["POST"])
  def assign_account():
    """Paste a link, and end up with one person holding one more account.

    The whole operation, in one request: create the person or merge into an
    existing one, record who the account is, attach it in the role that was
    asked for, and point the folders at the main account - all in one
    transaction, so there is no state in which half of it happened.

    This route does http and nothing else.  What the link names, what the person
    should be called, whether the account may be taken from somebody else and
    whether the person already has a main are all decided by the service, where
    they can be tested without a request context - and where they are decided
    once rather than once here and once again in a browser.
    """
    service = runtime.assignment_service()
    if service is None:
      ##
      ## The resolve store is what receipts are redeemed against, so without it
      ## every request would answer "expired" - which reads as the user's fault
      ## and is not.
      ##
      return _error("解析服务未初始化", 503)

    body = _payload()
    if body is None:
      return _error("请求必须是 JSON 格式", 400)

    try:
      ##
      ## Handed over whole.  Validating it here as well as in the service is how
      ## the two come to disagree, and the disagreement would be a hole.
      ##
      result = service.assign(body)
    except PersonAssignmentError as e:
      ##
      ## The category, never the request.  A refusal has to be diagnosable from
      ## the log without the log holding what a client sent - a resolve id names
      ## a link somebody pasted, and a share link can carry a signature.
      ##
      get_logger().info("person assignment refused: {}".format(e.kind))
      return _refusal(e)
    except Exception as e:
      ##
      ## Logged in full here, answered generically there: the message of an
      ## unexpected failure carries paths and internals that belong in the log
      ## and not in a browser.
      ##
      get_logger().error(
        "person assignment failed: {}: {}".format(type(e).__name__, e)
      )
      return _error("服务器内部错误，请稍后重试", 500)

    get_logger().info(
      "assigned an account as {} to person {}".format(
        result.role, result.person_id
      )
    )
    return _ok({
      "person_id": result.person_id,
      "owner_user_id": result.owner_user_id,
      "role": result.role,
      "created_person": result.created_person,
      "display_name": result.display_name,
    })

  @blueprint.route("/person/inspect", methods=["POST"])
  def inspect_assignment():
    """Say what a pasted link turns out to be, and whether we already have it.

    The step that was missing between resolving a link and filing it.  Without
    it the only thing that ever noticed a duplicate was the assignment
    transaction, so a user pasting an account they added last month filled in a
    form, named a person and pressed confirm before being told it had been there
    all along - and the obvious reading of that screen was "I must create this
    person again".

    Answered 200 with the state, never 409.  "You already have this" is the
    answer the caller asked for, not a refusal: nothing is being written, and a
    conflict status would make the page treat a successful check as a failure.

    Same receipt, same service, same identity reader as the assignment that
    follows it - which is what stops the two disagreeing about who a link names.
    What this reports is a hint for the interface and nothing more; the
    assignment discovers ownership again under its own locks and refuses on what
    it finds there.
    """
    service = runtime.assignment_service()
    if service is None:
      ##
      ## Same reason as the assignment route: without the store every receipt
      ## would read as expired, which looks like the user's fault and is not.
      ##
      return _error("解析服务未初始化", 503)

    body = _payload()
    if body is None:
      return _error("请求必须是 JSON 格式", 400)

    try:
      ##
      ## Handed over whole, unedited.  The field list is the trust boundary
      ## here - an account named by a client must be *refused*, not quietly
      ## dropped, because dropping it answers as though the request had said
      ## something else.
      ##
      found = service.inspect(body)
    except PersonAssignmentError as e:
      ##
      ## The category, never the request.  A resolve id names a link somebody
      ## pasted, and a share link can carry a signature.
      ##
      get_logger().info("person inspect refused: {}".format(e.kind))
      return _refusal(e)
    except Exception as e:
      get_logger().error(
        "person inspect failed: {}: {}".format(type(e).__name__, e)
      )
      return _error("服务器内部错误，请稍后重试", 500)

    return _ok({
      ##
      ## The account as the platform describes it right now, so the user
      ## recognises what they just pasted.  No folder and no url: a directory is
      ## the download paths' business, and a resolved url can carry a signature.
      ##
      "owner": {
        "owner_user_id": found.owner_user_id,
        "sec_user_id": found.sec_user_id,
        "nickname": found.nickname,
      },
      ##
      ## Two fields rather than one, because "this program has heard of this
      ## account" and "somebody has filed it" are different facts and the page
      ## shows different things for them.  An account downloaded months ago and
      ## never marked is the commonest case of all, and it is not a duplicate.
      ##
      "known_account": found.known_account,
      "assignment": None if found.person_id is None else {
        "person_id": found.person_id,
        ##
        ## The person's name, which is a name somebody typed.  It is not
        ## updated to follow a nickname, so a renamed account legitimately
        ## reads "账号：程小程 / 人物：程儿".
        ##
        "display_name": found.display_name,
        "role": found.role,
      },
    })

  @blueprint.route("/person/account", methods=["DELETE"])
  def detach_account():
    owner_user_id = (request.args.get("owner_user_id") or "").strip()
    if not owner_user_id:
      return _error("缺少必需参数: owner_user_id", 400)
    try:
      ##
      ## Unmarking is not the harmless inverse of marking.  The folders of every
      ## account aligned to a main are not restored when that main stops being
      ## one, so this is the shortest road to the same damage a demotion would
      ## do - and it answers to the same rule.
      ##
      runtime.assignment_service(require_receipts=False).detach_account(
        owner_user_id
      )
    except PersonAssignmentError as e:
      get_logger().info("detach account refused: {}".format(e.kind))
      return _refusal(e)
    except Exception as e:
      get_logger().error("detach account failed: {}".format(e))
      return _error("解除挂载失败", 502)
    return _ok({"owner_user_id": owner_user_id})

  @blueprint.route("/person/collaboration", methods=["POST"])
  def add_collaboration():
    body = _payload()
    if body is None:
      return _error("请求必须是 JSON 格式", 400)
    photographer_id = _int_field(body, "photographer_id")
    subject_id = _int_field(body, "subject_id")
    if photographer_id is None or subject_id is None:
      return _error("缺少必需字段: photographer_id / subject_id", 400)

    note = (body.get("note") or "").strip() or None
    try:
      runtime.table().add_collaboration(photographer_id, subject_id, note)
    except ValueError as e:
      return _error(str(e), 400)
    except Exception as e:
      get_logger().error("add collaboration failed: {}".format(e))
      return _error("记录合作关系失败", 502)
    return _ok({"photographer_id": photographer_id, "subject_id": subject_id})

  @blueprint.route("/person/collaboration", methods=["DELETE"])
  def remove_collaboration():
    photographer_id = request.args.get("photographer_id")
    subject_id = request.args.get("subject_id")
    try:
      photographer_id = int(str(photographer_id).strip())
      subject_id = int(str(subject_id).strip())
    except (TypeError, ValueError):
      return _error("photographer_id / subject_id 必须是整数", 400)

    try:
      runtime.table().remove_collaboration(photographer_id, subject_id)
    except Exception as e:
      get_logger().error("remove collaboration failed: {}".format(e))
      return _error("删除合作关系失败", 502)
    return _ok({"photographer_id": photographer_id, "subject_id": subject_id})

  return blueprint
