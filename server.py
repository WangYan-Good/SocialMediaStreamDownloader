##>> Test
import os
import sys
sys.path.append(os.getcwd())
##<< Test

## <<Base>>
import os
import signal
import threading

## <<Extension>>
from flask import Flask

## <<Third-Part>>
from backend.src.library.loglib    import get_logger
from backend.src.library.configlib import load_config
from backend.src.base.log import LoggerManager
from backend.src.database.schema_guard import initialize_schema_guard
from backend.src.platform.douyin.douyin_aweme_downloader import shutdown_aweme_downloads
from backend.src.platform.douyin.douyin_live_downloader import cancel_live_downloads
from backend.src.service.direct_post_download_task import DirectPostDownloadTaskService
from backend.src.service.live_recording_task import LiveRecordingTaskService
from backend.src.service.recording_recovery import RecordingRecoveryReconciler
from backend.src.service.recording_recovery_journal import RecordingRecoveryJournal
from backend.src.service.recording_resource import RecordingResourceService
from backend.src.service.task_creation import TaskCreationService
from backend.src.web.history_routes import build_history_blueprint
from backend.src.web.library_routes import build_library_blueprint
from backend.src.web.owner_routes import (
  OWNER_RUNTIME_KEY,
  OwnerRuntime,
  build_owner_blueprint,
)
from backend.src.web.person_routes import build_person_blueprint
from backend.src.web.resolve_routes import (
  build_resolve_blueprint,
  install_resolve_service,
)
from backend.src.web.spa_routes import build_spa_blueprint
from backend.src.web.system_routes import (
  build_system_blueprint,
  install_system_config,
)
from backend.src.web.auth_routes import build_auth_blueprint, build_auth_runtime
from backend.src.web.task_routes import (
  build_task_blueprint,
  install_task_creation_service,
  install_task_service,
)

##
## The reconciler class, reachable under a second name.
##
## A test that wants to *observe* what the application wired patches
## ``RecordingRecoveryReconciler`` and still needs to build the real thing.
## Without this the factory it installs would be the only class in scope and
## the patch would recurse.
##
RECONCILER_CLASS = RecordingRecoveryReconciler

##
## Where an application keeps the collaborators it built.
##
## On the application rather than in a module global, for the reason everything
## else here is: two applications in one interpreter - the lazy wsgi app and a
## test's - must not share recovery state any more than they share a task store.
##
RUNTIME_KEY = "smsd_application_runtime"


def application_runtime(configured_app) -> dict:
  """The collaborators ``configured_app`` was built with."""
  return configured_app.extensions[RUNTIME_KEY]


def _server_options(config: dict) -> dict:
  server = config.get("server")
  if not isinstance(server, dict):
    raise ValueError("$.server must be a mapping")
  host = server.get("host")
  port = server.get("port")
  debug_mode = server.get("debug_mode")
  if not isinstance(host, str) or not host.strip():
    raise ValueError("$.server.host must be a non-empty string")
  if type(port) is not int or not 1 <= port <= 65535:
    raise ValueError("$.server.port must be an integer from 1 to 65535")
  if type(debug_mode) is not bool:
    raise ValueError("$.server.debug_mode must be a boolean")
  return {"host": host, "port": port, "debug": debug_mode}


def _new_flask_app(
  lazy_config=False,
  schema_guard_factory=initialize_schema_guard,
  initial_schema_guard=None,
  initial_config=None,
):
  configured_app = Flask(
    __name__,
    static_folder=None,
    template_folder=None,
  )
  runtime = {
    "initialized": not lazy_config and initial_config is not None,
    "config": initial_config,
    ##
    ## One reconciliation attempt per application, and this is the flag that
    ## makes it one. Application-local rather than a module global: two
    ## applications in one interpreter each get their own startup, and a global
    ## would let the first one silently cancel the second's.
    ##
    "recovery_attempted": False,
  }
  configured_app.extensions[RUNTIME_KEY] = runtime
  if initial_schema_guard is not None:
    configured_app.extensions["smsd_schema_guard"] = initial_schema_guard
  initialization_lock = threading.Lock()
  reconciliation_lock = threading.Lock()

  def initialize_runtime():
    if runtime["initialized"]:
      return
    with initialization_lock:
      if runtime["initialized"]:
        return
      source = load_config()
      options = _server_options(source)
      LoggerManager(source["log"])
      schema_guard = schema_guard_factory(source)
      configured_app.debug = options["debug"]
      configured_app.extensions["smsd_schema_guard"] = schema_guard
      ##
      ## Reduced to the publishable fields here, at the moment this application
      ## first learns its configuration.  What it stores is already safe, so the
      ## status route has no full configuration to disclose even by mistake.
      ##
      install_system_config(configured_app, source)
      runtime["config"] = source
      runtime["initialized"] = True

    ##
    ## Strictly after the flag is set, and outside the initialisation lock.
    ##
    ## The reconciler reads this application's configuration through
    ## ``recording_config`` below, which calls back into here when the runtime
    ## is not yet initialised. Running it any earlier would re-enter this
    ## function while it holds the lock.
    ##
    ## After the schema guard for the same reason: a replay writes, and
    ## ``require_database_write_ready`` is the thing that decides whether a
    ## write may be attempted at all. Reconciling before the guard exists would
    ## be reconciling around it.
    ##
    reconcile_pending_recoveries()

  def recording_config():
    """Return the exact application snapshot its schema guard validated."""
    if not runtime["initialized"]:
      initialize_runtime()
    source = runtime.get("config")
    if source is None:
      raise RuntimeError("application configuration is unavailable")
    return source

  ##
  ## The crash handoff Phase 11B made durable, finally consumed.
  ##
  ## A note published before an insert survives the process that wrote it. Until
  ## now nothing ever read one back, so the gap this whole line of work exists
  ## to close - media on disk, no row, nobody can see the recording - was
  ## recorded rather than repaired. This is where the repair happens.
  ##
  ## Best-effort, synchronous, and exactly once per application. Synchronous
  ## because a recovered recording should be visible to the first request, not
  ## some time after it; bounded, so a backlog cannot hold a startup open; and
  ## once, because a scan on every request would put the journal directory on
  ## the hot path forever. Notes this run could not act on wait for the next
  ## process start - there is no periodic retry in this phase.
  ##
  ## The flag is set *before* the attempt, not after. "Once" means one attempt,
  ## not one success: a database that is down would otherwise be rescanned by
  ## every request that followed.
  ##
  ## Nothing here may reach the caller. This runs inside application startup and
  ## inside a request hook, and an exception escaping would take the SPA and
  ## every unrelated API with it. ``Exception`` and not ``BaseException``, so a
  ## shutdown signal still stops the process.
  ##
  def reconcile_pending_recoveries():
    if runtime["recovery_attempted"]:
      return
    with reconciliation_lock:
      if runtime["recovery_attempted"]:
        return
      runtime["recovery_attempted"] = True
      try:
        runtime["recording_reconciler"].reconcile_once()
      except Exception as e:
        get_logger().error(
          "recording recovery reconciliation failed during startup "
          "({}: {})".format(type(e).__name__, e)
        )

  @configured_app.before_request
  def ensure_runtime_initialized():
    initialize_runtime()

  ##
  ## the unified background task record.  Installed on the app rather than kept
  ## as a module global so every request of this process reads the one store,
  ## and two apps in one interpreter - the lazy wsgi app and a test's app - do
  ## not report each other's tasks.
  ##
  ## Installed before the blueprints that report into it, so the dependency
  ## travels down into the services rather than being reached up for.
  ##
  task_service = install_task_service(configured_app)

  ##
  ## The runner that turns a pasted post link into a task of this application.
  ##
  ## These are modern TaskCreationService dependencies.  They remain
  ## application-scoped so every task they create is visible through this
  ## application's task centre.
  ##
  runtime["direct_post_service"] = DirectPostDownloadTaskService(
    task_service=task_service
  )
  ##
  ## Recording persistence has two application-scoped collaborators, and the
  ## live service is handed both explicitly rather than being allowed to reach
  ## for either.
  ##
  ## They share one ``recording_config`` because they read the same fact from
  ## it - ``$.download.save_path``. A journal that resolved storage from a
  ## different snapshot than the resource service could write its notes beside
  ## media the rest of the application does not believe in.
  ##
  ## Both are constructed once per application, not per recording: two apps in
  ## one interpreter get their own, and nothing here is a module global.
  ##
  ## Injected, never defaulted. ``LiveRecordingTaskService`` treats a missing
  ## journal as a persistence failure on purpose - catalogue-without-handoff is
  ## not a state this system supports - so a silent fallback here would turn a
  ## wiring mistake into a quiet loss of crash recovery.
  ##
  runtime["recording_service"] = RecordingResourceService(
    config_loader=recording_config
  )
  runtime["recording_recovery_journal"] = RecordingRecoveryJournal(
    config_loader=recording_config
  )
  runtime["live_record_service"] = LiveRecordingTaskService(
    task_service=task_service,
    recording_service=runtime["recording_service"],
    recovery_journal=runtime["recording_recovery_journal"],
  )
  ##
  ## The other end of the same handoff.
  ##
  ## ``LiveRecordingTaskService`` writes notes for recordings this process is
  ## making; this replays the notes a *dead* process left behind. Different
  ## lifetimes, so they are different objects - but they must be looking at the
  ## same journal directory and writing through the same repository, or one
  ## would be acknowledging notes the other never wrote.
  ##
  ## So all three collaborators are the instances built just above, passed by
  ## identity. Constructing a second journal or a second resource service here
  ## is the mistake #157 shipped in mirror image, and the wiring tests pin it
  ## with ``assertIs`` rather than by comparing fields.
  ##
  runtime["recording_reconciler"] = RecordingRecoveryReconciler(
    journal=runtime["recording_recovery_journal"],
    recording_service=runtime["recording_service"],
    config_loader=recording_config,
  )
  ##
  ## The one-shot itself, on the runtime rather than only in this closure.
  ##
  ## Both startup paths reach it from inside this function, and each of them
  ## happens to run once already - so the latch would be belt-and-braces that
  ## nothing could ever exercise, which is another way of saying nothing could
  ## ever prove it works. Installing it makes the guarantee this application
  ## offers - *at most one reconciliation attempt, whoever asks* - a thing that
  ## can be called twice and tested.
  ##
  runtime["reconcile_recoveries_once"] = reconcile_pending_recoveries

  ##
  ## download history browsing and live status probing
  ##
  configured_app.register_blueprint(
    build_history_blueprint(task_service=task_service)
  )

  ##
  ## owner profile browsing and post batch download
  ##
  ## Built here rather than inside the blueprint so the unified task api can be
  ## given the *same* runtime.  It owns the job store, the payload cache and the
  ## post locks; a second one would let the same post be walked by one and
  ## downloaded by the other, each unaware of the other's locks.
  ##
  owner_runtime = OwnerRuntime(task_service=task_service)
  configured_app.extensions[OWNER_RUNTIME_KEY] = owner_runtime
  configured_app.register_blueprint(build_owner_blueprint(runtime=owner_runtime))

  ##
  ## marking which accounts belong to the same person, and who works with whom
  ##
  configured_app.register_blueprint(build_person_blueprint())

  ##
  ## browsing what has already been downloaded
  ##
  ## Read only, and lazy in the same way history is: registering it opens no
  ## connection, so a server whose database is down still starts and still
  ## serves everything that does not need one.  It builds no platform client
  ## either - the library reports records, and reporting them never involves
  ## asking a platform anything.
  ##
  configured_app.register_blueprint(build_library_blueprint())

  ##
  ## read-only runtime status and a safe summary of the loaded configuration
  ##
  ## The summary itself is installed separately, by whichever path knows this
  ## application's configuration - see install_system_config below.  The route
  ## reads it from the application, never from a process global, so the lazy
  ## wsgi app and a test's app each describe their own settings.
  ##
  configured_app.register_blueprint(build_system_blueprint())

  ##
  ## the read side of the task centre
  ##
  configured_app.register_blueprint(build_task_blueprint())

  ##
  ## Who is making this request.
  ##
  ## Registered unconditionally, including when the database is switched off:
  ## the runtime is built lazily and answers "unavailable" when asked, so a
  ## deployment with no database still starts and still serves everything that
  ## never needed one - it simply has nobody signed in.
  ##
  ## Identity-aware business routes consume the server-selected request user
  ## and role. Authorization is enforced at each route; this global hook only
  ## resolves the session once and never chooses a business scope itself.
  ##
  configured_app.register_blueprint(
    build_auth_blueprint(runtime=build_auth_runtime(load_config))
  )

  ##
  ## Answering what a pasted link is, before anything is done about it.
  ##
  ## Installed on the application rather than kept as a module global for the
  ## same reason the task service is: a receipt is this server's own word that
  ## it resolved a resource, so two applications in one interpreter must not be
  ## able to redeem each other's.  Whatever creates tasks from a receipt reads
  ## this same instance rather than trusting the browser to hand the identity
  ## back.
  ##
  resolve_service = install_resolve_service(configured_app)
  configured_app.register_blueprint(build_resolve_blueprint())

  ##
  ## Turning a resolution into real work.
  ##
  ## Every collaborator is one already built above, never a fresh copy.  A
  ## creation service holding its own resolve store would answer "expired" to
  ## every receipt this application ever issued, and one holding its own task
  ## service would create tasks that ``GET /api/tasks`` could not see.
  ##
  ## The owner side arrives as a factory rather than an instance because the
  ## runtime builds its service lazily - a server that never downloads an owner
  ## never constructs a platform client.
  ##
  install_task_creation_service(
    configured_app,
    TaskCreationService(
      resolve_service=resolve_service,
      direct_post_service=runtime["direct_post_service"],
      live_record_service=runtime["live_record_service"],
      owner_service_factory=owner_runtime.service,
    ),
  )

  ##
  ## The Vue interface owns GET root.  Registered last so concrete API routes
  ## retain their own rules; its catch-all refuses active API and retired
  ## Legacy/static tombstone namespaces before reading the build directory.
  ##
  configured_app.register_blueprint(build_spa_blueprint())

  ##
  ## An eagerly configured application knows everything it needs before it is
  ## returned, so its one reconciliation happens here rather than waiting for a
  ## first request that may never come.
  ##
  ## The lazy wsgi application takes the other branch: nothing is known at
  ## construction - it is built at import, before any configuration exists - so
  ## its reconciliation is the last step of ``initialize_runtime``.
  ##
  if runtime["initialized"]:
    reconcile_pending_recoveries()

  return configured_app


app = _new_flask_app(lazy_config=True)


def create_app(
  config: dict = None,
  schema_guard_factory=initialize_schema_guard,
):
  source = load_config() if config is None else config
  options = _server_options(source)
  LoggerManager(source["log"])
  schema_guard = schema_guard_factory(source)
  configured_app = _new_flask_app(
    initial_schema_guard=schema_guard,
    initial_config=source,
  )
  configured_app.debug = options["debug"]
  ##
  ## The same reduction for an application built around an explicit
  ## configuration.  Without this an application created here would report the
  ## settings of whichever one happened to be initialised last.
  ##
  install_system_config(configured_app, source)
  return configured_app


def run_server(config: dict = None):
  source = load_config() if config is None else config
  options = _server_options(source)
  configured_app = create_app(source)
  cancellation_requested = False
  previous_handlers = {}
  installed_signals = []

  def cancel_once():
    nonlocal cancellation_requested
    if cancellation_requested:
      return
    cancellation_requested = True
    try:
      cancel_live_downloads()
    except BaseException:
      try:
        get_logger().error("live download cancellation failed during shutdown")
      except BaseException:
        pass
    ##
    ## Post downloads run on their own pool, so stopping recordings does not stop
    ## them.  Queued posts are dropped; a file mid-transfer is discarded rather
    ## than left truncated on disk.
    ##
    try:
      shutdown_aweme_downloads()
    except BaseException:
      try:
        get_logger().error("post download shutdown failed during shutdown")
      except BaseException:
        pass

  def handle_shutdown(signum, _frame):
    cancel_once()
    raise SystemExit(128 + signum)

  try:
    for signum in (signal.SIGINT, signal.SIGTERM):
      previous_handlers[signum] = signal.signal(signum, handle_shutdown)
      installed_signals.append(signum)
    configured_app.run(**options)
  finally:
    try:
      cancel_once()
    finally:
      for signum in reversed(installed_signals):
        signal.signal(signum, previous_handlers[signum])

if __name__ == '__main__':
  run_server()
