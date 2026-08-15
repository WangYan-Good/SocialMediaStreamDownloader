import { computed, ref, watch } from 'vue'

import { ApiError } from '@/api/client'
import { resolveResource as defaultResolveResource } from '@/api/resolve'
import { createTask as defaultCreateTask, getTask as defaultGetTask } from '@/api/tasks'
import type { ResolvedResource } from '@/types/resolution'
import { TERMINAL_TASK_STATES } from '@/types/task'
import type { CreateTaskRequest, CreatedTask, Task } from '@/types/task'

/**
 * Where the flow is, as one value.
 *
 * A set of independent booleans - `isResolving`, `hasResult`, `creating` - can
 * describe combinations that cannot happen, and the one that bit hardest during
 * design was "phase says resolved, resolution is null". One phase instead of
 * several flags removes most of them.
 *
 * Not all of them: `phase` and `resolved` are still separate refs, so that
 * particular pair remains constructible in the type system and is held together
 * by this file rather than by the compiler. Making it genuinely unrepresentable
 * would mean one discriminated-union state object - worth doing when a second
 * screen needs the same shape, not for one workflow.
 */
export type NewDownloadPhase =
  | 'editing'
  | 'resolving'
  | 'resolved'
  | 'creating'
  | 'tracking'
  | 'terminal'

/**
 * How often the current task is read while it is still going.
 *
 * Named rather than inlined so the tests that assert timing and the code that
 * schedules it cannot drift apart - and so changing it is one edit, not a
 * search for every place a `2000` happened to mean this.
 */
export const TASK_POLL_INTERVAL_MS = 2000

export interface NewDownloadApi {
  resolveResource: (input: string) => Promise<ResolvedResource>
  createTask: (request: CreateTaskRequest) => Promise<CreatedTask>
  getTask: (taskId: string) => Promise<Task>
}

function messageOf(caught: unknown, fallback: string): string {
  //
  // Only the message. An ApiError also carries a status and a kind, which are
  // useful for branching but not for reading, and the underlying Response is
  // never allowed near the UI at all.
  //
  if (caught instanceof ApiError) {
    return caught.message || fallback
  }
  return fallback
}

/**
 * Turn one server-side resolution into the task it can currently become.
 *
 * A switch over `resource_type` rather than a lookup table plus a cast: the
 * three arms have genuinely different shapes - only the owner one carries
 * options - and a table would need a type assertion to paper over that, which
 * is exactly where the compatibility matrix would silently drift from the
 * backend's.
 *
 * Nothing describing the resource is sent. The receipt is the whole claim: the
 * server reads the aweme id, the sec_user_id and the urls back from its own
 * store, so a browser that wanted a different post could not ask for one.
 */
export function buildCreateTaskRequest(resolved: ResolvedResource): CreateTaskRequest {
  switch (resolved.resource_type) {
    case 'post':
      return {
        resolve_id: resolved.resolve_id,
        task_type: 'post_download',
      }

    case 'live':
      return {
        resolve_id: resolved.resolve_id,
        task_type: 'live_record',
      }

    case 'owner':
      return {
        resolve_id: resolved.resolve_id,
        task_type: 'owner_batch_download',
        //
        // Stated in words because the backend requires it, and the backend
        // requires it because an owner link on its own does not mean "download
        // the entire back catalogue" - it is the most expensive thing this api
        // can start.
        //
        options: { mode: 'all' },
      }

    default:
      //
      // A fourth resource type added to the wire contract without a decision
      // about what it should do here fails to compile, rather than reaching a
      // user as a button that does nothing.
      //
      return assertNever(resolved)
  }
}

function assertNever(value: never): never {
  throw new Error(`unhandled resource type: ${JSON.stringify(value)}`)
}

/**
 * The New Download workflow: paste, resolve, confirm, create, watch.
 *
 * A composable rather than a store on purpose. This is the state of one visit
 * to one screen - it has no meaning anywhere else in the application, and
 * nothing else needs to read it. A global task store arrives with the task
 * centre, which is the first screen that genuinely needs to know about work it
 * did not start itself.
 *
 * The api arrives as an argument so a test can drive the flow without a
 * network and without stubbing globals.
 */
export function useNewDownloadFlow(api: Partial<NewDownloadApi> = {}) {
  const resolveResource = api.resolveResource ?? defaultResolveResource
  const createTask = api.createTask ?? defaultCreateTask
  const getTask = api.getTask ?? defaultGetTask

  const input = ref('')
  const phase = ref<NewDownloadPhase>('editing')
  const resolved = ref<ResolvedResource | null>(null)
  const createdTask = ref<CreatedTask | null>(null)
  const currentTask = ref<Task | null>(null)
  const ownerConfirmed = ref(false)

  const resolveError = ref<string | null>(null)
  const createError = ref<string | null>(null)
  const trackError = ref<string | null>(null)

  //
  // The record could not be found. Distinguished from any other read failure
  // because it has a different meaning: the task store reclaims finished tasks,
  // so this is "the receipt of the work is gone", not "the work failed".
  //
  const taskRecordMissing = ref(false)

  let timer: ReturnType<typeof setTimeout> | null = null
  let stopped = false

  //
  // Which question the screen is currently waiting on an answer to.
  //
  // Bumped whenever a new resolve starts and whenever the text changes under
  // one that is already in flight. An answer whose generation is stale is
  // dropped: it is about a link the user has moved on from, and writing it in
  // would put one link's identity on screen beside another link's text - with a
  // confirm button underneath that creates a task for the wrong one.
  //
  let resolveGeneration = 0

  //
  // The text the current resolution was produced from. Kept so a later edit can
  // be recognised as one - see the watcher below, which is the single most
  // important rule in this file.
  //
  const resolvedFrom = ref<string | null>(null)

  function discardResolution() {
    resolved.value = null
    resolvedFrom.value = null
    createError.value = null
    receiptExpired.value = false
    ownerConfirmed.value = false
  }

  watch(
    input,
    (next) => {
      //
      // Editing the box invalidates the receipt.
      //
      // Without this: paste A, resolve A, edit to B, press download - and a
      // task is created for A while the screen shows B. The server would be
      // right to accept it, because the receipt really was A's; the mistake is
      // entirely this screen's, and it would be invisible to the user.
      //
      // Only before a task exists. Once one has been created it belongs to the
      // resolution it was created from, whatever the box says afterwards.
      //
      if (createdTask.value !== null || phase.value === 'creating') {
        return
      }
      if (phase.value === 'resolving') {
        //
        // A resolve is in flight and the user has moved on. Abandon it - and
        // return to editing rather than holding the button hostage until an
        // answer nobody wants any more finally arrives.
        //
        resolveGeneration += 1
        phase.value = 'editing'
        return
      }
      if (resolvedFrom.value !== null && next.trim() !== resolvedFrom.value.trim()) {
        discardResolution()
        phase.value = 'editing'
      }
    },
    //
    // Synchronous on purpose. The default flush would leave one tick during
    // which the text says B and `canCreate` still says yes for A - short, but
    // long enough for the click that is already on its way down.
    //
    { flush: 'sync' },
  )

  const canResolve = computed(
    () => input.value.trim().length > 0 && phase.value !== 'resolving',
  )

  const needsOwnerConfirmation = computed(
    () => resolved.value?.resource_type === 'owner',
  )

  //
  // The receipt aged out between resolving and confirming. Distinguished from
  // any other refusal because it has its own remedy - resolve again - and
  // because the one thing that must never happen is the browser deciding to
  // carry on with the identity it still has in memory.
  //
  const receiptExpired = ref(false)

  //
  // Frozen from the moment confirm is pressed, not from the moment the server
  // answers. In between, a request is already on its way: editing the text
  // there would leave the screen describing B while a task for A was being
  // created, and the watcher would clear A from view - hiding the very task
  // that did start.
  //
  const inputLocked = computed(
    () => createdTask.value !== null || phase.value === 'creating',
  )

  //
  // Null when there is nothing to divide by. A recording runs until the
  // broadcast ends, so its total is honestly unknown - and a template that
  // divided by it anyway would render NaN%.
  //
  const progressPercent = computed<number | null>(() => {
    const progress = currentTask.value?.progress
    if (!progress || progress.total === null || progress.total <= 0) {
      return null
    }
    return Math.round((progress.current / progress.total) * 100)
  })

  //
  // Only once the task has ended. There is no task centre yet, so a task
  // dropped from this screen would have nowhere left to be found.
  //
  const canStartOver = computed(
    () => phase.value === 'terminal' || taskRecordMissing.value,
  )

  const canCreate = computed(() => {
    if (phase.value !== 'resolved' || resolved.value === null) {
      return false
    }
    //
    // An owner batch downloads an entire back catalogue. Not a permission check
    // - the backend does not care - just a guard against one misplaced click
    // starting hours of work.
    //
    return !needsOwnerConfirmation.value || ownerConfirmed.value
  })

  async function resolve(): Promise<void> {
    if (!canResolve.value) {
      return
    }
    const submitted = input.value
    const generation = ++resolveGeneration
    phase.value = 'resolving'
    resolveError.value = null
    discardResolution()

    try {
      //
      // Sent exactly as typed. Pulling the link out of a share sentence is the
      // server's job and it has the punctuation cases covered; a regex copied
      // into the browser would be a second opinion that eventually disagrees.
      //
      const answer = await resolveResource(submitted)
      //
      // Two checks rather than one. The generation catches a newer request
      // having started; comparing the text catches the case where the box
      // changed without another resolve being launched. Either way this answer
      // is about something the screen is no longer asking.
      //
      if (generation !== resolveGeneration || input.value.trim() !== submitted.trim()) {
        return
      }
      resolved.value = answer
      resolvedFrom.value = submitted
      phase.value = 'resolved'
    } catch (caught) {
      //
      // An abandoned request's failure is not the user's problem either:
      // attaching it to text it has nothing to do with would be worse than
      // silence.
      //
      if (generation !== resolveGeneration) {
        return
      }
      resolveError.value = messageOf(caught, '解析失败，请稍后重试')
      phase.value = 'editing'
    }
  }

  async function create(): Promise<void> {
    //
    // The single guard against a double submission. Not a debounce: a debounce
    // hides a second intent behind a timer, while this says plainly that there
    // is nothing to create because a creation is already under way.
    //
    if (!canCreate.value || resolved.value === null) {
      return
    }

    const request = buildCreateTaskRequest(resolved.value)
    phase.value = 'creating'
    createError.value = null
    receiptExpired.value = false

    let created: CreatedTask
    try {
      created = await createTask(request)
    } catch (caught) {
      //
      // No task was created, so there is no task to show as failed. Saying
      // otherwise would invent a record the server never made - and would send
      // the user looking for it in a task centre that has nothing to show.
      //
      if (caught instanceof ApiError && caught.status === 404) {
        receiptExpired.value = true
      }
      createError.value = messageOf(caught, '创建任务失败，请稍后重试')
      phase.value = 'resolved'
      return
    }

    createdTask.value = created
    phase.value = 'tracking'
    //
    // Deliberately not awaited. The task exists the moment the server answers,
    // and the screen should say so; blocking here would leave the button in
    // "creating" for as long as the first status read takes - or forever, if it
    // never answers - while a task was in fact already running.
    //
    void track()
  }

  /**
   * Read the current task once, then decide whether to read it again.
   *
   * A recursive timeout rather than an interval, and the next one is scheduled
   * only after an answer arrives. An interval would launch a second read on top
   * of a slow first one, then a third, and the answers would start landing out
   * of order - the newest state overwritten by an older one still in flight.
   */
  async function track(): Promise<void> {
    const created = createdTask.value
    if (created === null || stopped) {
      return
    }

    let task: Task
    try {
      task = await getTask(created.task_id)
    } catch (caught) {
      //
      // Checked here as well as on the success path. The screen may already be
      // gone - a read is often still in flight when the user navigates away -
      // and a late failure written into a torn-down flow is a message nobody
      // will see attached to a screen nobody is on.
      //
      if (stopped) {
        return
      }
      if (caught instanceof ApiError && caught.status === 404) {
        //
        // The record is gone - a finished task the store has since reclaimed.
        // That is a fact about the record, not about the download, and saying
        // "failed" here would be this client inventing an outcome.
        //
        taskRecordMissing.value = true
        trackError.value = '任务记录不存在或已过期'
        return
      }
      //
      // The browser cannot see the task. Whether the work is going fine is
      // simply not known from here, so the last state stands and polling stops
      // rather than hammering a backend that is not answering.
      //
      //
      // This screen's own wording, not the transport's. "Failed to fetch" is
      // true and useless; what the user needs to know is that the *status* is
      // unavailable and the download itself is not being claimed to have
      // failed. The underlying reason is appended, not substituted.
      //
      const reason = messageOf(caught, '')
      trackError.value = reason
        ? `暂时无法获取任务状态：${reason}`
        : '暂时无法获取任务状态'
      return
    }

    if (stopped) {
      return
    }

    currentTask.value = task
    trackError.value = null
    taskRecordMissing.value = false

    if (TERMINAL_TASK_STATES.includes(task.state)) {
      phase.value = 'terminal'
      return
    }

    timer = setTimeout(() => {
      void track()
    }, TASK_POLL_INTERVAL_MS)
  }

  function stop(): void {
    stopped = true
    if (timer !== null) {
      clearTimeout(timer)
      timer = null
    }
  }

  /** Read again after a failure the user has chosen to retry. */
  async function retryTracking(): Promise<void> {
    if (createdTask.value === null) {
      return
    }
    stopped = false
    trackError.value = null
    await track()
  }

  function startOver(): void {
    stop()
    stopped = false
    input.value = ''
    phase.value = 'editing'
    resolved.value = null
    resolvedFrom.value = null
    createdTask.value = null
    currentTask.value = null
    ownerConfirmed.value = false
    resolveError.value = null
    createError.value = null
    trackError.value = null
    receiptExpired.value = false
    taskRecordMissing.value = false
  }

  return {
    input,
    phase,
    resolved,
    createdTask,
    currentTask,
    ownerConfirmed,
    resolveError,
    createError,
    trackError,
    receiptExpired,
    taskRecordMissing,
    canResolve,
    canCreate,
    canStartOver,
    needsOwnerConfirmation,
    inputLocked,
    progressPercent,
    resolve,
    create,
    retryTracking,
    startOver,
    stop,
  }
}
