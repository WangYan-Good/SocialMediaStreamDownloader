##<<Base>>
from threading import Lock

##<<Extension>>
from flask import Blueprint, jsonify, request

##<<Third-part>>
from backend.src.database.table.person_identity import (
  DouyinPersonIdentityTable,
  UnknownRole,
)
from backend.src.library.configlib import load_config
from backend.src.library.loglib import get_logger


PLATFORM = "douyin"


def _error(message: str, code: int):
  return jsonify({"status": "error", "message": message, "code": code}), code


def _ok(data: dict):
  return jsonify({"status": "success", "code": 200, "data": data}), 200


class PersonRuntime:
  """Holds the person table, built once and shared.

  ``table_factory`` exists so the tests can supply a stand-in without a
  database; production leaves it alone and gets the real table.
  """

  def __init__(self, config: dict = None, table_factory=None) -> None:
    self._config = config
    self._table_factory = table_factory
    self._table = None
    self._lock = Lock()

  def settings(self) -> dict:
    return load_config() if self._config is None else self._config

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

    directory_name = (body.get("directory_name") or "").strip() or None
    note = (body.get("note") or "").strip() or None
    try:
      person_id = runtime.table().create_person(
        display_name,
        directory_name=directory_name,
        note=note,
      )
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
    for name in ("display_name", "directory_name", "note"):
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
      runtime.table().attach_account(
        PLATFORM,
        owner_user_id,
        person_id,
        body.get("role"),
      )
    except UnknownRole as e:
      ##
      ## The role came from a list of three, so a bad one is a field problem the
      ## page can point at - not a failure of the request.
      ##
      return _error(str(e), 400)
    except Exception as e:
      get_logger().error("attach account failed: {}".format(e))
      return _error("挂载账号失败", 502)
    return _ok({"owner_user_id": owner_user_id, "person_id": person_id})

  @blueprint.route("/person/account", methods=["DELETE"])
  def detach_account():
    owner_user_id = (request.args.get("owner_user_id") or "").strip()
    if not owner_user_id:
      return _error("缺少必需参数: owner_user_id", 400)
    try:
      runtime.table().detach_account(PLATFORM, owner_user_id)
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
