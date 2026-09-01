##<<Base>>
from dataclasses import dataclass

##<<Third-part>>
from backend.src.platform.resource_resolution import (
  RESOURCE_TYPE_LIVE,
  RESOURCE_TYPE_OWNER,
  RESOURCE_TYPE_POST,
)
from backend.src.task.model import (
  TASK_TYPE_LIVE_RECORD,
  TASK_TYPE_OWNER_BATCH_DOWNLOAD,
  TASK_TYPE_POST_DOWNLOAD,
  TASK_TYPES,
)


##
## >>============================= failures =============================>>
##

class TaskCreateError(Exception):
  """One of the known ways creating a task from a receipt can fail.

  Every failure carries the ``kind`` logs record and the ``status_code`` the api
  answers with, so neither is re-derived from the message text at the edge.
  """

  kind = "task_create_failed"
  status_code = 400


class UnknownTaskType(TaskCreateError):
  """A word that is not one of the task vocabulary's own identifiers."""

  kind = "unknown_task_type"


class ResolutionNotFound(TaskCreateError):
  """The receipt is unknown or has aged out.

  Answered 404 and never repaired.  Re-resolving the url here would mean the
  server deciding what the user meant, minutes after they asked - which is the
  one thing the receipt exists to prevent.
  """

  kind = "resolution_not_found"
  status_code = 404


class UnsupportedTaskForResource(TaskCreateError):
  """A task type this stage cannot start for that kind of resource."""

  kind = "unsupported_task_for_resource"


class InvalidTaskOptions(TaskCreateError):
  """The options do not describe work this stage knows how to start.

  Unknown keys are refused rather than ignored: "accepted but had no effect" is
  the worst answer an api can give, because the caller goes on believing a
  promise nothing here made.
  """

  kind = "invalid_task_options"


class TaskCreationUnavailable(TaskCreateError):
  """Nothing is wired to run this kind of work in this application.

  A deployment fault rather than a bad request, so it answers 503: no
  correction the caller could make to the request would start the work.
  """

  kind = "task_creation_unavailable"
  status_code = 503


CAPACITY_MESSAGE = "服务当前繁忙，请稍后重试"


class TaskCreationCapacityExceeded(TaskCreateError):
  """This process cannot safely admit another task right now."""

  kind = "task_capacity"
  status_code = 503


##
## >>============================= result =============================>>
##

@dataclass(frozen=True)
class TaskCreationResult:
  """What one accepted creation produced.

  Deliberately three fields.  A future, a listener, a legacy job id or a whole
  task snapshot would each be something a client could start depending on, and
  the only thing it needs is the id to watch.
  """

  task_id: str
  task_type: str
  resolve_id: str


##
## The one matrix this stage allows.  ``live_probe`` is absent on purpose: the
## existing probe is a batch over owners already saved in history, not a question
## about a url someone just resolved, and accepting it here would mint a second
## probe workflow to keep in step with the first.
##
_ALLOWED_TASK_TYPE = {
  RESOURCE_TYPE_POST: TASK_TYPE_POST_DOWNLOAD,
  RESOURCE_TYPE_LIVE: TASK_TYPE_LIVE_RECORD,
  RESOURCE_TYPE_OWNER: TASK_TYPE_OWNER_BATCH_DOWNLOAD,
}

##
## The whole back catalogue, and the only owner mode this stage runs.
##
OWNER_MODE_ALL = "all"

##
## ``selected`` is named so its refusal can say why rather than "unknown mode":
## it needs the post payloads the owner page holds in its own cache, and an owner
## receipt carries only a ``sec_user_id``.
##
OWNER_MODE_SELECTED = "selected"


class TaskCreationService:
  """Turns a receipt plus a task type into real background work.

  The trust boundary of the whole feature lives here.  Nothing a client sends
  describes the resource: the resolution is read back from this application's own
  resolve store, and every value handed to a runner comes from that snapshot.

  Platform-neutral by construction - it reads ``resource_type`` and ``identity``
  and never asks which platform they came from - and web-neutral: the runners
  arrive already built, so no wiring detail of Flask reaches this class.
  """

##
## >>============================= private method =============================>>
##
  def __init__(
    self,
    resolve_service,
    direct_post_service=None,
    live_record_service=None,
    owner_service_factory=None,
  ) -> None:
    self._resolve_service = resolve_service
    self._direct_post_service = direct_post_service
    self._live_record_service = live_record_service
    ##
    ## A factory rather than an instance: the owner service is built lazily by
    ## the runtime that owns the job store and the payload cache, and calling it
    ## here is what keeps P6 on that one runtime instead of a second copy.
    ##
    self._owner_service_factory = owner_service_factory

  @property
  def resolve_service(self):
    """The store this service redeems receipts against.

    Exposed for the same reason as ``owner_service_factory``: whether this is
    the application's own resolve service is the difference between every
    receipt working and every receipt reading as expired, and a wiring mistake
    that severe should be assertable rather than only discoverable at runtime.
    """
    return self._resolve_service

  @property
  def owner_service_factory(self):
    """The factory this service will build owner work from.

    Exposed so wiring can be checked rather than assumed: whether the task api
    and the owner page share one runtime is the difference between one job
    store and two, and that is worth being able to assert.
    """
    return self._owner_service_factory

  @staticmethod
  def _validated_task_type(task_type: str) -> str:
    ##
    ## Checked before the receipt is read.  A word that is not a task type is
    ## wrong whatever the receipt says, and answering "your receipt expired"
    ## would send the user round a loop that cannot fix their request.
    ##
    if not isinstance(task_type, str) or task_type not in TASK_TYPES:
      raise UnknownTaskType("不支持的任务类型: {!r}".format(task_type))
    return task_type

  def _resolution(self, resolve_id: str, app_user_id: int):
    ##
    ## Read once, here.  Everything downstream works off this one detached
    ## snapshot, so a receipt expiring mid-request cannot fail a creation that
    ## was already accepted on a valid resolution.
    ##
    resolution = self._resolve_service.get_for_user(resolve_id, app_user_id)
    if resolution is None:
      raise ResolutionNotFound("解析结果不存在或已过期，请重新解析")
    return resolution

  def _runner_for(self, task_type: str):
    """The thing that will run ``task_type`` here, or say nothing can.

    Resolved before the options are read.  Both can be wrong at once, and only
    one of them is something the caller could fix.
    """
    if task_type == TASK_TYPE_POST_DOWNLOAD:
      runner = self._direct_post_service
    elif task_type == TASK_TYPE_LIVE_RECORD:
      runner = self._live_record_service
    else:
      factory = self._owner_service_factory
      ##
      ## A factory that answers ``None`` counts as not wired.  The owner service
      ## is built lazily from a runtime, and a runtime that could not build one
      ## must not be mistaken for "there is nothing to do".
      ##
      runner = None if factory is None else factory()
    if runner is None:
      raise TaskCreationUnavailable("当前服务无法创建该类型的任务")
    return runner

  @staticmethod
  def _validated_options(task_type: str, options) -> dict:
    if options is None:
      options = {}
    if not isinstance(options, dict):
      raise InvalidTaskOptions("options 必须是对象")

    if task_type != TASK_TYPE_OWNER_BATCH_DOWNLOAD:
      ##
      ## Neither a post download nor a recording takes a task-level option yet.
      ## Refusing the unknown ones now is what keeps the contract free to grow:
      ## a key quietly ignored today is a key someone depends on tomorrow.
      ##
      unknown = sorted(options)
      if unknown:
        raise InvalidTaskOptions(
          "不支持的任务参数: {}".format(", ".join(unknown))
        )
      return {}

    unknown = sorted(set(options) - {"mode"})
    if unknown:
      raise InvalidTaskOptions("不支持的任务参数: {}".format(", ".join(unknown)))
    mode = options.get("mode")
    if mode == OWNER_MODE_SELECTED:
      raise InvalidTaskOptions(
        "暂不支持按作品选择下载，请使用主播页面的下载功能"
      )
    if mode != OWNER_MODE_ALL:
      ##
      ## Required, not defaulted.  An owner link on its own does not mean
      ## "download everything": it is the most expensive thing this api can
      ## start, so it has to be asked for in words.
      ##
      raise InvalidTaskOptions('主播批量下载需要 options.mode = "all"')
    return {"mode": OWNER_MODE_ALL}

  def _create_post_download(self, runner, resolution, resolve_id: str, options: dict,
                            app_user_id=None):
    return runner.submit_tracked(
      ##
      ## Every value from the server's own snapshot.  The execution url is the
      ## *resolved* one: the short link has already been followed once, safely,
      ## and handing it over again would repeat that decision - and repeat the
      ## request that made it.
      ##
      aweme_id=resolution.identity.get("aweme_id"),
      resolved_url=resolution.resolved_url,
      source_url=resolution.source_url,
      resolve_id=resolve_id,
      **({"app_user_id": app_user_id} if app_user_id is not None else {}),
    )

  def _create_live_record(self, runner, resolution, resolve_id: str, options: dict,
                          app_user_id=None):
    return runner.submit_tracked(
      resolved_url=resolution.resolved_url,
      source_url=resolution.source_url,
      resolve_id=resolve_id,
      **({"app_user_id": app_user_id} if app_user_id is not None else {}),
    )

  def _create_owner_batch_download(self, runner, resolution, resolve_id: str,
                                   options: dict, app_user_id=None):
    return runner.start_all_tracked(
      sec_user_id=resolution.identity.get("sec_user_id"),
      resolved_url=resolution.resolved_url,
      source_url=resolution.source_url,
      resolve_id=resolve_id,
      **({"app_user_id": app_user_id} if app_user_id is not None else {}),
    )

##
## >>============================= sub class method =============================>>
##
  def create(self, resolve_id: str, task_type: str, options: dict = None,
             *, app_user_id: int):
    """Start the work ``task_type`` names for the resource ``resolve_id`` named.

    Raises a ``TaskCreateError`` for every expected refusal, each carrying the
    status the api answers with.
    """
    task_type = self._validated_task_type(task_type)
    if type(app_user_id) is not int or app_user_id < 1:
      raise ValueError("app_user_id must be a positive integer")
    resolution = self._resolution(resolve_id, app_user_id)

    allowed = _ALLOWED_TASK_TYPE.get(resolution.resource_type)
    if allowed is None or allowed != task_type:
      raise UnsupportedTaskForResource(
        "{} 类型的资源不支持 {} 任务".format(resolution.resource_type, task_type)
      )

    runner = self._runner_for(task_type)
    validated = self._validated_options(task_type, options)

    creators = {
      TASK_TYPE_POST_DOWNLOAD: self._create_post_download,
      TASK_TYPE_LIVE_RECORD: self._create_live_record,
      TASK_TYPE_OWNER_BATCH_DOWNLOAD: self._create_owner_batch_download,
    }
    task_id = creators[task_type](
      runner,
      resolution,
      resolve_id,
      validated,
      app_user_id,
    )
    return TaskCreationResult(
      task_id=task_id, task_type=task_type, resolve_id=resolve_id
    )
