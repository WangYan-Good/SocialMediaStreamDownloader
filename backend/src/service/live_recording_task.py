##<<Third-part>>
from backend.src.library.baselib import get_dict_attr
from backend.src.library.loglib import get_logger
from backend.src.platform.douyin.douyin_listener import ListenerItem
from backend.src.platform.douyin.douyin_live_downloader import get_live_downloader
from backend.src.platform.douyin.hls_recorder import HlsCancelled
from backend.src.service.task_creation import TaskCreationUnavailable
from backend.src.task.model import TASK_TYPE_LIVE_RECORD


##
## Which platform, and how the user asked.  Both live in metadata rather than in
## the task type, so a second platform reuses ``live_record``.
##
PLATFORM_DOUYIN = "douyin"

##
## Pasted into the legacy endpoint and classified by the handler.
##
SOURCE_DIRECT = "direct"

##
## Asked for through ``POST /api/tasks`` against a server-side resolution.  The
## two differ in what they promise: one reports on work that runs regardless,
## the other is a task the caller was told exists.
##
SOURCE_TASK_API = "task_api"

##
## What a strict creation says when it could not produce a task.
##
NOT_CREATED_MESSAGE = "任务创建失败，请稍后重试"

##
## ``room.status == 2`` is broadcasting; anything else answered is not.
##
ROOM_STATUS_LIVING = 2
LIVE_STATUS_LIVING = "living"
LIVE_STATUS_OFFLINE = "offline"

##
## What each ending says to the user.
##
RECORDING_FAILED_MESSAGE = "直播录制失败"
CANCELLED_MESSAGE = "直播录制已停止"
NOT_STARTED_MESSAGE = "直播录制没有进入执行线程"


class LiveRecordingTaskService:
  """Runs one confirmed live link as one unified task.

  Like the direct post runner, this is a runner rather than a mirror: a
  recording has never had a record of its own, so the task *is* the record and
  there is no legacy id to associate with.

  What it deliberately does not do:

  * **It does not record.**  ``DouyinLiveDownloader`` keeps probing, stream
    selection, the FLV/HLS decision, retries, naming and persistence, and knows
    nothing about tasks, Flask or HTTP.
  * **It does not own a thread pool.**  Recordings still run on the same
    ``ListenerItem`` thread model, so the concurrency behaviour is unchanged.

  And the rule shared with every migration so far: **telemetry, never
  workflow.**  A recording that would have run before still runs, whatever the
  task layer does.
  """

##
## >>============================= private method =============================>>
##
  def __init__(
    self,
    task_service=None,
    downloader_factory=get_live_downloader,
    listener_factory=ListenerItem,
  ) -> None:
    ##
    ## ``None`` is a supported wiring: a dispatch with no task service behind it
    ## records exactly as it did before this stage, reporting nothing.
    ##
    self._task_service = task_service
    self._downloader_factory = downloader_factory
    self._listener_factory = listener_factory

  @property
  def enabled(self) -> bool:
    return self._task_service is not None

  def _safe(self, action: str, task_id, call):
    """Run one task-layer call, turning any failure into a logged no-op."""
    try:
      return call()
    except Exception as e:
      get_logger().error(
        "live recording task: {} failed for task {}: {}".format(action, task_id, e)
      )
      return None

  def _open(self, token: dict):
    """Create the task for a room the handler has already confirmed is live.

    Returns the task id, or ``None`` when nothing is mirroring or the task layer
    refused - after which the recording proceeds unobserved.
    """
    if not self.enabled:
      return None

    task = self._safe(
      "create",
      None,
      lambda: self._task_service.create_task(
        TASK_TYPE_LIVE_RECORD,
        ##
        ## Named without asking the platform anything.  Who is streaming is
        ## discovered by the probe the recording itself runs, and lands in the
        ## result metadata; spending a request here to make a prettier title
        ## would be paying the platform for decoration.
        ##
        title="录制抖音直播",
        metadata={
          "platform": PLATFORM_DOUYIN,
          "source": SOURCE_DIRECT,
          "source_url": get_dict_attr(token, "$.url"),
          "resolved_url": get_dict_attr(token, "$.resolved_url"),
        },
        ##
        ## No total.  A recording runs until the broadcast ends, so there is
        ## nothing to divide by, and ``None`` is the honest answer rather than a
        ## fabricated "1" that would render as a bar stuck at zero for hours.
        ##
        total=None,
      ),
    )
    if task is None:
      return None
    return task["task_id"]

  def _result_metadata(self, result) -> dict:
    """A summary of the attempt, never the stream it read.

    A live stream url is signed - it carries ``sign`` and ``token`` parameters
    that grant access to the broadcast - so nothing derived from it appears
    here.  The fields are named one by one rather than copied wholesale for
    exactly that reason.
    """
    if result is None:
      return {}
    live_status = None
    if result.room_status is not None:
      live_status = (
        LIVE_STATUS_LIVING
        if result.room_status == ROOM_STATUS_LIVING
        else LIVE_STATUS_OFFLINE
      )
    return {
      "ok": bool(result.ok),
      "recorded": bool(result.recorded),
      "live_status": live_status,
      "room_status": result.room_status,
      "room_id": result.room_id,
      "owner_user_id": result.owner_user_id,
      "nickname": result.nickname,
      "protocol": result.protocol,
      "output_path": result.output_path,
      "test_mode": bool(result.test_mode),
      "reason": result.reason,
    }

  def _finish(self, task_id, outcome: str, message, result_metadata: dict) -> None:
    """Write the record, then end the task - in that order.

    A finished task refuses further metadata, so the account of what happened
    has to land before the task is closed.
    """
    if task_id is None:
      return

    if result_metadata:
      self._safe(
        "record result",
        task_id,
        lambda: self._task_service.update_metadata(
          task_id, {"result": result_metadata}
        ),
      )

    finishers = {
      "success": self._task_service.finish_success,
      "failed": self._task_service.finish_failed,
      "cancelled": self._task_service.cancel_task,
    }
    self._safe(
      "finish {}".format(outcome),
      task_id,
      lambda: finishers[outcome](task_id, message=message),
    )

  def _run(self, task_id, token: dict):
    """The recording thread: start the task, record, then report the ending."""
    if task_id is not None:
      self._safe("start", task_id, lambda: self._task_service.start_task(task_id))

    try:
      result = self._downloader_factory().run_with_result(token)
    except HlsCancelled as e:
      ##
      ## Deliberately stopped, most often by the server shutting down.  Recorded
      ## as cancelled because that is what happened - it is not a fault, and
      ## calling it a failure would put a red mark against an orderly shutdown.
      ##
      ## This is the *only* cancellation this stage can describe.  There is no
      ## user-facing way to ask for it, and the FLV path has no equivalent, so
      ## nothing here should be read as "recordings can be cancelled".
      ##
      get_logger().info(
        "live recording cancelled for {}: {}".format(
          get_dict_attr(token, "$.url"), e
        )
      )
      self._finish(task_id, "cancelled", CANCELLED_MESSAGE, {})
      raise
    except Exception as e:
      ##
      ## The full trace goes to the log; the task keeps one short sentence,
      ## because task metadata is read by a browser.
      ##
      get_logger().exception(
        "live recording crashed for {}: {}".format(get_dict_attr(token, "$.url"), e)
      )
      self._finish(task_id, "failed", RECORDING_FAILED_MESSAGE, {})
      ##
      ## Re-raised so the recording thread behaves exactly as it did before this
      ## stage existed.  Reporting must not quietly turn a crash into a normal
      ## return.
      ##
      raise

    outcome = "success" if result is not None and result.ok else "failed"
    message = None
    if outcome == "failed":
      message = (result.reason if result is not None else None) or RECORDING_FAILED_MESSAGE
    self._finish(task_id, outcome, message, self._result_metadata(result))
    return result

  def _open_tracked(self, source_url, resolved_url, resolve_id) -> str:
    """Create the task for a request that was promised one, or refuse.

    The opposite of ``_open``: nothing is swallowed.  A caller told a recording
    started must be able to watch it, so if no task exists the only honest
    answer is that the request was not accepted.
    """
    if not self.enabled:
      raise TaskCreationUnavailable(NOT_CREATED_MESSAGE)

    try:
      task = self._task_service.create_task(
        TASK_TYPE_LIVE_RECORD,
        ##
        ## Named without asking the platform anything, exactly as the legacy
        ## path does.  Who is streaming, and whether they are on air at all, is
        ## discovered by the probe the recording itself runs.
        ##
        title="录制抖音直播",
        metadata={
          "platform": PLATFORM_DOUYIN,
          "source": SOURCE_TASK_API,
          "resolve_id": resolve_id,
          "source_url": source_url,
          "resolved_url": resolved_url,
        },
        total=None,
      )
    except Exception as e:
      get_logger().error(
        "live recording task: strict create failed: {}".format(e)
      )
      raise TaskCreationUnavailable(NOT_CREATED_MESSAGE)

    if task is None:
      raise TaskCreationUnavailable(NOT_CREATED_MESSAGE)
    return task["task_id"]

##
## >>============================= sub class method =============================>>
##
  def submit_tracked(
    self,
    resolved_url=None,
    source_url=None,
    resolve_id=None,
  ) -> str:
    """Record one server-resolved live room as a task the caller can watch.

    Strict where ``submit`` is best-effort: the task is created first and the
    recording thread is started **only** if that succeeded.

    The recorder starts from ``resolved_url``.  The share link was already
    followed once, by the resolver, under the host checks that make following it
    safe; handing the short link over again would repeat that whole decision.
    """
    task_id = self._open_tracked(source_url, resolved_url, resolve_id)

    token = {"url": resolved_url, "resolved_url": resolved_url}

    ##
    ## Whether the worker ever began - the same distinction the legacy path
    ## draws.  A listener that runs its target inline raises the *worker's*
    ## exception out of ``start_item``, and reporting that as "never started"
    ## would overwrite an ending the worker already recorded correctly.
    ##
    began = []

    def worker():
      began.append(True)
      return self._run(task_id, token)

    try:
      self._listener_factory(func=worker, args=()).start_item()
    except Exception as e:
      if began:
        ##
        ## The recording ran and failed, and ``_run`` has already said so.  The
        ## caller still gets the id: a task that exists and failed is exactly
        ## what it should be looking at.
        ##
        get_logger().info(
          "live recording task {} failed while running inline: {}".format(
            task_id, e
          )
        )
      else:
        get_logger().error(
          "live recording was not started for task {}: {}".format(task_id, e)
        )
        self._finish(task_id, "failed", NOT_STARTED_MESSAGE, {})
    return task_id

  def submit(self, token: dict):
    """Schedule one confirmed live room, returning the listener running it.

    The task is created first so a browser polling the task centre sees the
    recording queued rather than missing.  If the thread cannot be started the
    task is closed as failed rather than left pending: the store only ever
    reclaims tasks that have ended, so one abandoned in ``pending`` would stay
    for the life of the process.
    """
    task_id = self._open(token)

    ##
    ## Whether the worker ever began.  ``ListenerItem`` normally hands the work
    ## to a new thread, so a failure out of ``start_item`` means the thread could
    ## not be created; but a listener that runs its target inline would raise the
    ## *worker's* exception here instead, and reporting that as "never started"
    ## would overwrite an ending the worker had already recorded correctly.
    ##
    began = []

    def worker():
      began.append(True)
      return self._run(task_id, token)

    try:
      item = self._listener_factory(func=worker, args=())
      item.start_item()
      return item
    except Exception as e:
      if began:
        ##
        ## The recording itself failed, and ``_run`` has already said so.  Let it
        ## travel on exactly as it would from a real recording thread.
        ##
        raise
      get_logger().error(
        "live recording was not started for {}: {}".format(
          get_dict_attr(token, "$.url"), e
        )
      )
      self._finish(task_id, "failed", NOT_STARTED_MESSAGE, {})
      return None
