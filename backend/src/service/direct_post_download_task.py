##<<Base>>
from threading import Lock

##<<Third-part>>
from backend.src.library.baselib import get_dict_attr
from backend.src.library.loglib import get_logger
from backend.src.platform.douyin.douyin_aweme_downloader import (
  get_aweme_downloader,
  get_aweme_executor,
)
from backend.src.task.model import TASK_TYPE_POST_DOWNLOAD


##
## Which platform the work ran against, and how the user asked for it.  Both live
## in task metadata rather than in the task type: a second platform reuses
## ``post_download``, and a post reached through the task centre later will reuse
## it too with a different ``source``.
##
PLATFORM_DOUYIN = "douyin"
SOURCE_DIRECT = "direct"

##
## What each ending says to the user.  Stated once because the mapping below and
## the tests that pin it need the same words.
##
ALREADY_DOWNLOADED_MESSAGE = "已经下载，无需重复下载"
NOTHING_SAVED_MESSAGE = "没有文件被保存"
UNAVAILABLE_MESSAGE = "作品无法下载"
CRASHED_MESSAGE = "下载失败"
NO_RESULT_MESSAGE = "下载没有返回结果"
NOT_SCHEDULED_MESSAGE = "下载没有进入队列"


class DirectPostDownloadTaskService:
  """Runs one pasted post link as one unified task.

  This is the first business that has no legacy record of its own to keep in
  step: owner batches have ``JobStore`` and probes have ``ProbeBatchStore``, but
  a direct post has only ever been an anonymous future on a thread pool.  So this
  is a runner rather than a mirror - the task *is* the record - and there is no
  legacy id to associate with a task id.

  Two things it deliberately does not do:

  * **It does not download.**  ``DouyinAwemeDownloader`` keeps every part of
    that - resolving, media selection, disk deduplication, the per-post lock,
    persistence - and knows nothing about tasks, Flask or HTTP.
  * **It does not own a pool.**  Work goes to the existing post executor, so the
    concurrency limit that protects the platform quota still counts every post.

  And one rule it shares with the P1/P2 mirrors: **telemetry, never workflow.**
  Reporting failures are logged and swallowed; a post that would have downloaded
  before still downloads.
  """

##
## >>============================= private method =============================>>
##
  def __init__(
    self,
    task_service=None,
    downloader_factory=get_aweme_downloader,
    executor_factory=get_aweme_executor,
  ) -> None:
    ##
    ## ``None`` is a supported wiring: a dispatch with no task service behind it
    ## downloads exactly as it did before this stage, reporting nothing.
    ##
    self._task_service = task_service
    self._downloader_factory = downloader_factory
    self._executor_factory = executor_factory
    self._guard = Lock()

  @property
  def enabled(self) -> bool:
    return self._task_service is not None

  def _safe(self, action: str, task_id, call):
    """Run one task-layer call, turning any failure into a logged no-op."""
    try:
      return call()
    except Exception as e:
      ##
      ## Deliberately broad, deliberately loud.  Anything the task layer can
      ## raise is a reporting problem, and the download it describes is real work
      ## that must go on regardless.
      ##
      get_logger().error(
        "direct post task: {} failed for task {}: {}".format(action, task_id, e)
      )
      return None

  def _title(self, aweme_id) -> str:
    if aweme_id:
      return "下载作品 {}".format(aweme_id)
    return "下载抖音作品"

  def _open(self, token: dict):
    """Create the task for a post the handler has already confirmed.

    Returns the task id, or ``None`` when nothing is mirroring or the task layer
    refused - after which every later report for this post is a no-op and the
    download proceeds unobserved.
    """
    if not self.enabled:
      return None

    aweme_id = get_dict_attr(token, "$.aweme_id")
    task = self._safe(
      "create",
      None,
      lambda: self._task_service.create_task(
        TASK_TYPE_POST_DOWNLOAD,
        title=self._title(aweme_id),
        metadata={
          "platform": PLATFORM_DOUYIN,
          "source": SOURCE_DIRECT,
          "source_url": get_dict_attr(token, "$.url"),
          "resolved_url": get_dict_attr(token, "$.resolved_url"),
          "aweme_id": aweme_id,
        },
        ##
        ## One logical unit of work, declared up front.  No items: the task is
        ## the post, so there is nothing to enumerate beneath it.
        ##
        total=1,
      ),
    )
    if task is None:
      return None
    return task["task_id"]

  def _verdict(self, result):
    """Turn one ``AwemeDownloadResult`` into an ending for the task.

    Order matters here, and each branch is a decision about what the *user*
    asked for rather than about how the code returned.
    """
    if result is None:
      return "failed", NO_RESULT_MESSAGE

    if result.ok is not True:
      ##
      ## Deleted, private, follower-only, unresolvable.  An ordinary answer in
      ## control-flow terms, but the post the user asked for is not on disk.
      ##
      return "failed", result.reason or UNAVAILABLE_MESSAGE

    if result.skipped:
      ##
      ## Already on disk.  The user's goal is met, so this is a success and never
      ## a cancellation or a failure.
      ##
      return "success", ALREADY_DOWNLOADED_MESSAGE

    if result.partial:
      return "partial", "已保存 {} / {} 个媒体文件".format(
        result.saved_count, result.media_count
      )

    if result.media_count > 0 and result.saved_count == 0:
      ##
      ## The trap this mapping exists to avoid.  The downloader reports ``ok``
      ## for a post it reached but could not keep a single file of, and its
      ## ``partial`` flag is false precisely because *nothing* was saved - so the
      ## shape is indistinguishable from a clean success unless it is checked
      ## here.  The user has no files; that is a failure.
      ##
      return "failed", NOTHING_SAVED_MESSAGE

    return "success", None

  def _result_metadata(self, result) -> dict:
    if result is None:
      return {}
    ##
    ## A summary of the attempt, never the platform payload it came from.  Nulls
    ## are kept rather than dropped: "there was no reason" is itself the answer
    ## for a download that went fine.
    ##
    return {
      "ok": bool(result.ok),
      "skipped": bool(result.skipped),
      "partial": bool(result.partial),
      "saved_count": result.saved_count,
      "media_count": result.media_count,
      "save_dir": result.save_dir,
      "reason": result.reason,
    }

  def _finish(self, task_id, outcome: str, message, result_metadata: dict) -> None:
    """Write the record, then the progress, then the ending - in that order.

    A finished task refuses further metadata, so the account of what happened has
    to land before the task is closed.
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
    ##
    ## One logical unit, now dealt with - whatever the verdict.  This counts work
    ## processed, not work that succeeded.
    ##
    self._safe(
      "advance progress",
      task_id,
      lambda: self._task_service.update_progress(task_id, current=1),
    )

    finishers = {
      "success": self._task_service.finish_success,
      "partial": self._task_service.finish_partial,
      "failed": self._task_service.finish_failed,
    }
    self._safe(
      "finish {}".format(outcome),
      task_id,
      lambda: finishers[outcome](task_id, message=message),
    )

  def _run(self, task_id, token: dict):
    """The worker: start the task, download, then report what happened."""
    if task_id is not None:
      self._safe(
        "start", task_id, lambda: self._task_service.start_task(task_id)
      )

    try:
      result = self._downloader_factory().run(token)
    except Exception as e:
      ##
      ## The full trace goes to the log, where it belongs; the task keeps a short
      ## sentence, because task metadata is read by a browser and a traceback
      ## there is both noise and a disclosure risk.
      ##
      get_logger().exception(
        "direct post download crashed for {}: {}".format(
          get_dict_attr(token, "$.url"), e
        )
      )
      self._finish(task_id, "failed", CRASHED_MESSAGE, {})
      ##
      ## Re-raised so the future carries it exactly as it did when the downloader
      ## was submitted to the pool directly.  Reporting must not quietly turn a
      ## crash into a normal return.
      ##
      raise

    outcome, message = self._verdict(result)
    self._finish(task_id, outcome, message, self._result_metadata(result))
    return result

##
## >>============================= sub class method =============================>>
##
  def submit(self, token: dict):
    """Schedule one confirmed post, returning the future that runs it.

    The task is created first so that a browser polling the task centre sees the
    post queued rather than missing, and the download is submitted second.  If
    the pool refuses the work the task is closed as failed rather than left
    pending forever - a task nobody will ever move is worse than a task that
    admits it never ran.
    """
    task_id = self._open(token)

    try:
      return self._executor_factory(
        self._downloader_factory().config.concurrency
      ).submit(self._run, task_id, token)
    except Exception as e:
      get_logger().error(
        "direct post download was not scheduled for {}: {}".format(
          get_dict_attr(token, "$.url"), e
        )
      )
      self._finish(task_id, "failed", NOT_SCHEDULED_MESSAGE, {})
      return None
