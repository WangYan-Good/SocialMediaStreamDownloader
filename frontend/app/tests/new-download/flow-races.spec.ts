import { describe, expect, it, vi } from 'vitest'

import { ApiError } from '../../src/api/client'
import {
  TASK_POLL_INTERVAL_MS,
  useNewDownloadFlow,
} from '../../src/composables/useNewDownloadFlow'
import type { ResolvedResource } from '../../src/types/resolution'
import type { Task } from '../../src/types/task'
import { ownerResolution, postResolution } from './build-request.spec'

//
// Races the synchronous input watcher cannot cover on its own.
//
// The watcher answers "the text changed, so the resolution on screen is no
// longer about it". It says nothing about a request that was already in flight
// when the text changed - that answer arrives later, addressed to a question
// nobody is asking any more, and without a guard it would be written straight
// into the screen.
//

function deferred<T>() {
  let settle: (value: T) => void = () => {}
  let fail: (reason: unknown) => void = () => {}
  const promise = new Promise<T>((resolve, reject) => {
    settle = resolve
    fail = reject
  })
  return { promise, settle, fail }
}

async function drain() {
  for (let index = 0; index < 4; index += 1) {
    await Promise.resolve()
  }
}

const INPUT_A = 'https://v.douyin.com/AAAA/'
const INPUT_B = 'https://v.douyin.com/BBBB/'

/** The same resolution shape, tagged so a test can tell the two apart. */
function taggedAs(source: ResolvedResource, receipt: string, url: string): ResolvedResource {
  return { ...source, resolve_id: receipt, source_url: url }
}

describe('a resolve answer that arrives after the question changed', () => {
  it('is discarded rather than written over the new input', async () => {
    //
    // Paste A, press resolve, then edit to B before the answer comes back. The
    // answer is about A. Showing it would put A's identity on screen beside B's
    // text - and the confirm button underneath would create a task for A.
    //
    const pending = deferred<ResolvedResource>()
    const flow = useNewDownloadFlow({
      resolveResource: vi.fn(() => pending.promise),
    })
    flow.input.value = INPUT_A

    const inFlight = flow.resolve()
    flow.input.value = INPUT_B

    pending.settle(taggedAs(postResolution, 'receipt-A', INPUT_A))
    await inFlight
    await drain()

    expect(flow.resolved.value).toBeNull()
    expect(flow.phase.value).toBe('editing')
    expect(flow.canCreate.value).toBe(false)
  })

  it('cannot be confirmed into a task', async () => {
    const pending = deferred<ResolvedResource>()
    const createTask = vi.fn()
    const flow = useNewDownloadFlow({
      resolveResource: vi.fn(() => pending.promise),
      createTask,
    })
    flow.input.value = INPUT_A

    const inFlight = flow.resolve()
    flow.input.value = INPUT_B
    pending.settle(taggedAs(postResolution, 'receipt-A', INPUT_A))
    await inFlight
    await drain()

    await flow.create()

    expect(createTask).not.toHaveBeenCalled()
  })

  it('does not resurrect an owner confirmation either', async () => {
    const pending = deferred<ResolvedResource>()
    const flow = useNewDownloadFlow({
      resolveResource: vi.fn(() => pending.promise),
    })
    flow.input.value = INPUT_A

    const inFlight = flow.resolve()
    flow.input.value = INPUT_B
    pending.settle(taggedAs(ownerResolution, 'receipt-A', INPUT_A))
    await inFlight
    await drain()

    expect(flow.needsOwnerConfirmation.value).toBe(false)
    expect(flow.ownerConfirmed.value).toBe(false)
  })

  it('leaves no error behind from the abandoned request', async () => {
    const pending = deferred<ResolvedResource>()
    const flow = useNewDownloadFlow({
      resolveResource: vi.fn(() => pending.promise),
    })
    flow.input.value = INPUT_A

    const inFlight = flow.resolve()
    flow.input.value = INPUT_B
    pending.fail(new Error('the abandoned request also failed'))
    await inFlight
    await drain()

    //
    // The user is no longer asking about A, so A's failure is not their problem
    // either. Reporting it would attach an error to text it has nothing to do
    // with.
    //
    expect(flow.resolveError.value).toBeNull()
  })
})

describe('two resolve answers arriving out of order', () => {
  it('keeps the one that was asked for last', async () => {
    //
    // A is submitted, the text changes to B, B is submitted, and then the
    // answers race. Whichever lands last, the screen has to end up showing B -
    // ordering answers by arrival time is exactly how a slow first request
    // overwrites a fast second one.
    //
    const first = deferred<ResolvedResource>()
    const second = deferred<ResolvedResource>()
    const resolveResource = vi
      .fn<(input: string) => Promise<ResolvedResource>>()
      .mockReturnValueOnce(first.promise)
      .mockReturnValueOnce(second.promise)
    const flow = useNewDownloadFlow({ resolveResource })

    flow.input.value = INPUT_A
    const resolvingA = flow.resolve()

    flow.input.value = INPUT_B
    const resolvingB = flow.resolve()

    //
    // B answers first, then A - the order that breaks a naive implementation.
    //
    second.settle(taggedAs(postResolution, 'receipt-B', INPUT_B))
    await resolvingB
    await drain()

    first.settle(taggedAs(postResolution, 'receipt-A', INPUT_A))
    await resolvingA
    await drain()

    expect(resolveResource).toHaveBeenCalledTimes(2)
    expect(flow.resolved.value?.resolve_id).toBe('receipt-B')
    expect(flow.resolved.value?.source_url).toBe(INPUT_B)
    expect(flow.phase.value).toBe('resolved')
  })

  it('creates the task for the link that is actually on screen', async () => {
    const first = deferred<ResolvedResource>()
    const second = deferred<ResolvedResource>()
    const createTask = vi.fn(async () => ({
      task_id: 'task-1',
      task_type: 'post_download' as const,
      resolve_id: 'receipt-B',
    }))
    const flow = useNewDownloadFlow({
      resolveResource: vi
        .fn<(input: string) => Promise<ResolvedResource>>()
        .mockReturnValueOnce(first.promise)
        .mockReturnValueOnce(second.promise),
      createTask,
      getTask: vi.fn(async () => {
        throw new Error('not reached in this test')
      }),
    })

    flow.input.value = INPUT_A
    const resolvingA = flow.resolve()
    flow.input.value = INPUT_B
    const resolvingB = flow.resolve()

    second.settle(taggedAs(postResolution, 'receipt-B', INPUT_B))
    await resolvingB
    await drain()
    first.settle(taggedAs(postResolution, 'receipt-A', INPUT_A))
    await resolvingA
    await drain()

    await flow.create()

    expect(createTask).toHaveBeenCalledWith({
      resolve_id: 'receipt-B',
      task_type: 'post_download',
    })
  })

  it('lets the second question be asked while the first is still open', async () => {
    //
    // Editing the box during a resolve abandons that resolve rather than
    // locking the button until it answers: the user has moved on, and making
    // them wait for an answer they no longer want is the wrong trade.
    //
    const first = deferred<ResolvedResource>()
    const flow = useNewDownloadFlow({
      resolveResource: vi.fn(() => first.promise),
    })

    flow.input.value = INPUT_A
    void flow.resolve()
    expect(flow.canResolve.value).toBe(false)

    flow.input.value = INPUT_B

    expect(flow.canResolve.value).toBe(true)
  })
})

describe('a status read that lands after the screen is gone', () => {
  //
  // Clearing the timer is not enough on its own. At the moment the user
  // navigates away there may be no timer at all - only a request already in
  // flight - and when it answers, the code resumes after its `await` and would
  // happily schedule the next poll into a component nobody is looking at.
  //

  async function trackingWithPendingRead() {
    const pending = deferred<Task>()
    const signals: AbortSignal[] = []
    const getTask = vi.fn((_taskId: string, signal?: AbortSignal) => {
      if (signal) {
        signals.push(signal)
      }
      return pending.promise
    })
    const flow = useNewDownloadFlow({
      resolveResource: vi.fn(async () => postResolution),
      createTask: vi.fn(async () => ({
        task_id: 'task-1',
        task_type: 'post_download' as const,
        resolve_id: 'receipt-1',
      })),
      getTask,
    })
    flow.input.value = INPUT_A
    await flow.resolve()
    await flow.create()
    await drain()
    return { flow, getTask, pending, signals }
  }

  async function failedThenRetryPending() {
    const retry = deferred<Task>()
    const signals: AbortSignal[] = []
    let reads = 0
    const getTask = vi.fn((_taskId: string, signal?: AbortSignal) => {
      reads += 1
      if (signal) {
        signals.push(signal)
      }
      if (reads === 1) {
        return Promise.reject(new ApiError({
          kind: 'network',
          status: null,
          code: null,
          message: 'initial status failure',
        }))
      }
      return retry.promise
    })
    const flow = useNewDownloadFlow({
      resolveResource: vi.fn(async () => postResolution),
      createTask: vi.fn(async () => ({
        task_id: 'task-1',
        task_type: 'post_download' as const,
        resolve_id: 'receipt-1',
      })),
      getTask,
    })
    flow.input.value = INPUT_A
    await flow.resolve()
    await flow.create()
    await drain()
    expect(flow.trackError.value).toContain('状态')

    void flow.retryTracking()
    await drain()
    expect(getTask).toHaveBeenCalledTimes(2)
    return { flow, getTask, retry, signals }
  }

  it('schedules nothing after the flow was stopped', async () => {
    vi.useFakeTimers()
    try {
      const { flow, getTask, pending } = await trackingWithPendingRead()
      expect(getTask).toHaveBeenCalledTimes(1)

      //
      // The component unmounts while the read is still open.
      //
      flow.stop()

      pending.settle({
        task_id: 'task-1',
        task_type: 'post_download',
        state: 'running',
        title: null,
        message: null,
        created_at: '2026-08-15T09:30:15.250',
        started_at: '2026-08-15T09:30:16.250',
        finished_at: null,
        progress: { current: 0, total: 1 },
        metadata: {},
        items: [],
      })
      await drain()

      await vi.advanceTimersByTimeAsync(TASK_POLL_INTERVAL_MS * 5)

      expect(getTask).toHaveBeenCalledTimes(1)
    } finally {
      vi.useRealTimers()
    }
  })

  it('does not write the late answer into state either', async () => {
    vi.useFakeTimers()
    try {
      const { flow, pending } = await trackingWithPendingRead()
      flow.stop()

      pending.settle({
        task_id: 'task-1',
        task_type: 'post_download',
        state: 'success',
        title: null,
        message: null,
        created_at: '2026-08-15T09:30:15.250',
        started_at: null,
        finished_at: '2026-08-15T09:31:00.000',
        progress: { current: 1, total: 1 },
        metadata: {},
        items: [],
      })
      await drain()

      expect(flow.currentTask.value).toBeNull()
      expect(flow.phase.value).toBe('tracking')
    } finally {
      vi.useRealTimers()
    }
  })

  it('is also silent when the late answer is a failure', async () => {
    vi.useFakeTimers()
    try {
      const pending = deferred<Task>()
      const getTask = vi.fn(() => pending.promise)
      const flow = useNewDownloadFlow({
        resolveResource: vi.fn(async () => postResolution),
        createTask: vi.fn(async () => ({
          task_id: 'task-1',
          task_type: 'post_download' as const,
          resolve_id: 'receipt-1',
        })),
        getTask,
      })
      flow.input.value = INPUT_A
      await flow.resolve()
      await flow.create()
      await drain()

      flow.stop()
      pending.fail(new ApiError({
        kind: 'network',
        status: null,
        code: null,
        message: 'Failed to fetch',
      }))
      await drain()

      expect(flow.trackError.value).toBeNull()
      await vi.advanceTimersByTimeAsync(TASK_POLL_INTERVAL_MS * 5)
      expect(getTask).toHaveBeenCalledTimes(1)
    } finally {
      vi.useRealTimers()
    }
  })

  it('cannot write a successful answer after start over reopens the flow', async () => {
    vi.useFakeTimers()
    try {
      const { flow, getTask, pending } = await trackingWithPendingRead()

      flow.startOver()
      pending.settle({
        task_id: 'task-1',
        task_type: 'post_download',
        state: 'success',
        title: 'old task',
        message: null,
        created_at: '2026-08-15T09:30:15.250',
        started_at: null,
        finished_at: '2026-08-15T09:31:00.000',
        progress: { current: 1, total: 1 },
        metadata: {},
        items: [],
      })
      await drain()

      expect(flow.phase.value).toBe('editing')
      expect(flow.createdTask.value).toBeNull()
      expect(flow.currentTask.value).toBeNull()
      expect(flow.trackError.value).toBeNull()
      expect(flow.taskRecordMissing.value).toBe(false)

      await vi.advanceTimersByTimeAsync(TASK_POLL_INTERVAL_MS * 5)
      expect(getTask).toHaveBeenCalledTimes(1)
    } finally {
      vi.useRealTimers()
    }
  })

  it('cannot resurrect a missing-record result after start over', async () => {
    const { flow, pending } = await trackingWithPendingRead()

    flow.startOver()
    pending.fail(new ApiError({
      kind: 'backend',
      status: 404,
      code: 404,
      message: 'old task is gone',
    }))
    await drain()

    expect(flow.phase.value).toBe('editing')
    expect(flow.createdTask.value).toBeNull()
    expect(flow.currentTask.value).toBeNull()
    expect(flow.trackError.value).toBeNull()
    expect(flow.taskRecordMissing.value).toBe(false)
    expect(flow.canStartOver.value).toBe(false)
  })

  it('cannot attach an old network failure after start over', async () => {
    const { flow, pending } = await trackingWithPendingRead()

    flow.startOver()
    pending.fail(new ApiError({
      kind: 'network',
      status: null,
      code: null,
      message: 'Failed to fetch',
    }))
    await drain()

    expect(flow.phase.value).toBe('editing')
    expect(flow.createdTask.value).toBeNull()
    expect(flow.currentTask.value).toBeNull()
    expect(flow.trackError.value).toBeNull()
    expect(flow.taskRecordMissing.value).toBe(false)
  })

  it.each([
    [
      '404',
      new ApiError({
        kind: 'backend',
        status: 404,
        code: 404,
        message: 'old task is gone',
      }),
    ],
    [
      'network failure',
      new ApiError({
        kind: 'network',
        status: null,
        code: null,
        message: 'old task failed',
      }),
    ],
  ])(
    'uses generation to reject stale %s even if abort is ineffective',
    async (_label, error) => {
      const NativeAbortController = globalThis.AbortController
      class IneffectiveAbortController {
        readonly signal = new NativeAbortController().signal

        abort(): void {
          // Fault injection: correctness must not depend on cancellation being
          // delivered by the runtime or adapter.
        }
      }
      vi.stubGlobal('AbortController', IneffectiveAbortController)
      try {
        const { flow, pending, signals } = await trackingWithPendingRead()

        flow.startOver()
        expect(signals[0].aborted).toBe(false)
        pending.fail(error)
        await drain()

        expect(flow.phase.value).toBe('editing')
        expect(flow.currentTask.value).toBeNull()
        expect(flow.trackError.value).toBeNull()
        expect(flow.taskRecordMissing.value).toBe(false)
      } finally {
        vi.unstubAllGlobals()
      }
    },
  )

  it('aborts the active status read when starting over', async () => {
    const { flow, pending, signals } = await trackingWithPendingRead()

    expect(signals).toHaveLength(1)
    expect(signals[0].aborted).toBe(false)

    flow.startOver()

    expect(signals[0].aborted).toBe(true)

    // Abort is an optimisation, not the correctness proof: an adapter may
    // ignore it, so let the old promise answer and prove generation still wins.
    pending.settle({
      task_id: 'task-1',
      task_type: 'post_download',
      state: 'success',
      title: 'old task',
      message: null,
      created_at: '2026-08-15T09:30:15.250',
      started_at: null,
      finished_at: '2026-08-15T09:31:00.000',
      progress: { current: 1, total: 1 },
      metadata: {},
      items: [],
    })
    await drain()

    expect(flow.phase.value).toBe('editing')
    expect(flow.currentTask.value).toBeNull()
    expect(flow.trackError.value).toBeNull()
  })

  it('does not let an old finally forget the newer active controller', async () => {
    const first = deferred<Task>()
    const second = deferred<Task>()
    const signals: AbortSignal[] = []
    const getTask = vi
      .fn((_taskId: string, signal?: AbortSignal) => {
        if (signal) {
          signals.push(signal)
        }
        return signals.length === 1 ? first.promise : second.promise
      })
    const flow = useNewDownloadFlow({
      resolveResource: vi.fn(async () => postResolution),
      createTask: vi.fn(async () => ({
        task_id: 'task-1',
        task_type: 'post_download' as const,
        resolve_id: 'receipt-1',
      })),
      getTask,
    })
    flow.input.value = INPUT_A
    await flow.resolve()
    await flow.create()
    await drain()

    expect(signals).toHaveLength(1)
    void flow.retryTracking()
    await drain()
    expect(signals).toHaveLength(2)
    expect(signals[0].aborted).toBe(true)
    expect(signals[1].aborted).toBe(false)

    first.settle({
      task_id: 'task-1',
      task_type: 'post_download',
      state: 'running',
      title: 'superseded read',
      message: null,
      created_at: '2026-08-15T09:30:15.250',
      started_at: '2026-08-15T09:30:16.250',
      finished_at: null,
      progress: { current: 0, total: 1 },
      metadata: {},
      items: [],
    })
    await drain()

    expect(flow.currentTask.value).toBeNull()
    expect(flow.trackError.value).toBeNull()
    expect(flow.taskRecordMissing.value).toBe(false)

    flow.stop()
    expect(signals[1].aborted).toBe(true)

    second.settle({
      task_id: 'task-1',
      task_type: 'post_download',
      state: 'running',
      title: null,
      message: null,
      created_at: '2026-08-15T09:30:15.250',
      started_at: '2026-08-15T09:30:16.250',
      finished_at: null,
      progress: { current: 0, total: 1 },
      metadata: {},
      items: [],
    })
    await drain()
  })

  it.each([
    [
      '404',
      new ApiError({
        kind: 'backend',
        status: 404,
        code: 404,
        message: 'superseded record is gone',
      }),
    ],
    [
      'network failure',
      new ApiError({
        kind: 'network',
        status: null,
        code: null,
        message: 'superseded read failed',
      }),
    ],
  ])('ignores a superseded same-task %s after retry starts', async (_label, error) => {
    const first = deferred<Task>()
    const second = deferred<Task>()
    const getTask = vi
      .fn()
      .mockReturnValueOnce(first.promise)
      .mockReturnValueOnce(second.promise)
    const flow = useNewDownloadFlow({
      resolveResource: vi.fn(async () => postResolution),
      createTask: vi.fn(async () => ({
        task_id: 'task-1',
        task_type: 'post_download' as const,
        resolve_id: 'receipt-1',
      })),
      getTask,
    })
    flow.input.value = INPUT_A
    await flow.resolve()
    await flow.create()
    await drain()

    void flow.retryTracking()
    await drain()
    first.fail(error)
    await drain()

    expect(flow.currentTask.value).toBeNull()
    expect(flow.trackError.value).toBeNull()
    expect(flow.taskRecordMissing.value).toBe(false)

    flow.stop()
    second.settle({
      task_id: 'task-1',
      task_type: 'post_download',
      state: 'running',
      title: null,
      message: null,
      created_at: '2026-08-15T09:30:15.250',
      started_at: '2026-08-15T09:30:16.250',
      finished_at: null,
      progress: { current: 0, total: 1 },
      metadata: {},
      items: [],
    })
    await drain()
  })

  it('rejects an answer whose frozen task identity no longer matches', async () => {
    const { flow, pending } = await trackingWithPendingRead()

    flow.createdTask.value = {
      task_id: 'task-B',
      task_type: 'post_download',
      resolve_id: 'receipt-B',
    }
    pending.settle({
      task_id: 'task-1',
      task_type: 'post_download',
      state: 'success',
      title: 'wrong identity',
      message: null,
      created_at: '2026-08-15T09:30:15.250',
      started_at: null,
      finished_at: '2026-08-15T09:31:00.000',
      progress: { current: 1, total: 1 },
      metadata: {},
      items: [],
    })
    await drain()

    expect(flow.currentTask.value).toBeNull()
    expect(flow.phase.value).toBe('tracking')
    expect(flow.trackError.value).toBeNull()
  })

  it('keeps an old timer stale even if cancelling the timer is ineffective', async () => {
    vi.useFakeTimers()
    const ineffectiveClear = vi
      .spyOn(globalThis, 'clearTimeout')
      .mockImplementation(() => undefined)
    try {
      const resolutionA = taggedAs(postResolution, 'receipt-A', INPUT_A)
      const resolutionB = taggedAs(postResolution, 'receipt-B', INPUT_B)
      const resolveResource = vi
        .fn<() => Promise<ResolvedResource>>()
        .mockResolvedValueOnce(resolutionA)
        .mockResolvedValueOnce(resolutionB)
      const createTask = vi
        .fn()
        .mockResolvedValueOnce({
          task_id: 'same-task-id',
          task_type: 'post_download' as const,
          resolve_id: 'receipt-A',
        })
        .mockResolvedValueOnce({
          task_id: 'same-task-id',
          task_type: 'post_download' as const,
          resolve_id: 'receipt-B',
        })
      const getTask = vi
        .fn()
        .mockResolvedValueOnce({
          task_id: 'same-task-id',
          task_type: 'post_download' as const,
          state: 'running' as const,
          title: 'old task',
          message: null,
          created_at: '2026-08-15T09:30:15.250',
          started_at: '2026-08-15T09:30:16.250',
          finished_at: null,
          progress: { current: 0, total: 1 },
          metadata: {},
          items: [],
        })
        .mockResolvedValue({
          task_id: 'same-task-id',
          task_type: 'post_download' as const,
          state: 'success' as const,
          title: 'new task',
          message: null,
          created_at: '2026-08-15T10:00:00.000',
          started_at: '2026-08-15T10:00:01.000',
          finished_at: '2026-08-15T10:01:00.000',
          progress: { current: 1, total: 1 },
          metadata: {},
          items: [],
        })
      const flow = useNewDownloadFlow({ resolveResource, createTask, getTask })

      flow.input.value = INPUT_A
      await flow.resolve()
      await flow.create()
      await drain()
      expect(getTask).toHaveBeenCalledTimes(1)

      flow.startOver()
      flow.input.value = INPUT_B
      await flow.resolve()
      await flow.create()
      await drain()
      expect(getTask).toHaveBeenCalledTimes(2)

      await vi.advanceTimersByTimeAsync(TASK_POLL_INTERVAL_MS * 2)

      expect(getTask).toHaveBeenCalledTimes(2)
      expect(flow.currentTask.value?.title).toBe('new task')
      expect(flow.phase.value).toBe('terminal')
    } finally {
      ineffectiveClear.mockRestore()
      vi.useRealTimers()
    }
  })

  it('ignores a retry success that arrives after start over', async () => {
    const { flow, retry, signals } = await failedThenRetryPending()
    expect(signals).toHaveLength(2)
    expect(signals[1].aborted).toBe(false)

    flow.startOver()
    expect(signals[1].aborted).toBe(true)
    retry.settle({
      task_id: 'task-1',
      task_type: 'post_download',
      state: 'success',
      title: 'old retry',
      message: null,
      created_at: '2026-08-15T09:30:15.250',
      started_at: null,
      finished_at: '2026-08-15T09:31:00.000',
      progress: { current: 1, total: 1 },
      metadata: {},
      items: [],
    })
    await drain()

    expect(flow.phase.value).toBe('editing')
    expect(flow.createdTask.value).toBeNull()
    expect(flow.currentTask.value).toBeNull()
    expect(flow.trackError.value).toBeNull()
    expect(flow.taskRecordMissing.value).toBe(false)
  })

  it.each([
    [
      'network failure',
      new ApiError({
        kind: 'network',
        status: null,
        code: null,
        message: 'old retry failed',
      }),
    ],
    [
      '404',
      new ApiError({
        kind: 'backend',
        status: 404,
        code: 404,
        message: 'old retry record is gone',
      }),
    ],
  ])('ignores a retry %s that arrives after start over', async (_label, error) => {
    const { flow, retry, signals } = await failedThenRetryPending()

    flow.startOver()
    expect(signals[1].aborted).toBe(true)
    retry.fail(error)
    await drain()

    expect(flow.phase.value).toBe('editing')
    expect(flow.createdTask.value).toBeNull()
    expect(flow.currentTask.value).toBeNull()
    expect(flow.trackError.value).toBeNull()
    expect(flow.taskRecordMissing.value).toBe(false)
  })
})

describe('an old task answer that lands after a new task exists', () => {
  async function pendingTaskAThenTaskB() {
    const taskA = deferred<Task>()
    const resolutionA = taggedAs(postResolution, 'receipt-A', INPUT_A)
    const resolutionB = taggedAs(postResolution, 'receipt-B', INPUT_B)
    const resolveResource = vi
      .fn<() => Promise<ResolvedResource>>()
      .mockResolvedValueOnce(resolutionA)
      .mockResolvedValueOnce(resolutionB)
    const createTask = vi
      .fn()
      .mockResolvedValueOnce({
        task_id: 'task-A',
        task_type: 'post_download' as const,
        resolve_id: 'receipt-A',
      })
      .mockResolvedValueOnce({
        task_id: 'task-B',
        task_type: 'post_download' as const,
        resolve_id: 'receipt-B',
      })
    const getTask = vi.fn((taskId: string) => {
      if (taskId === 'task-A') {
        return taskA.promise
      }
      return Promise.resolve({
        task_id: 'task-B',
        task_type: 'post_download' as const,
        state: 'success' as const,
        title: 'current task B',
        message: null,
        created_at: '2026-08-15T10:00:00.000',
        started_at: '2026-08-15T10:00:01.000',
        finished_at: '2026-08-15T10:01:00.000',
        progress: { current: 1, total: 1 },
        metadata: {},
        items: [],
      })
    })
    const flow = useNewDownloadFlow({ resolveResource, createTask, getTask })

    flow.input.value = INPUT_A
    await flow.resolve()
    await flow.create()
    await drain()
    expect(getTask).toHaveBeenCalledWith('task-A', expect.any(AbortSignal))

    flow.startOver()
    flow.input.value = INPUT_B
    await flow.resolve()
    await flow.create()
    await drain()
    expect(flow.createdTask.value?.task_id).toBe('task-B')
    expect(flow.currentTask.value?.task_id).toBe('task-B')
    expect(flow.currentTask.value?.title).toBe('current task B')
    expect(flow.phase.value).toBe('terminal')

    return { flow, getTask, taskA }
  }

  async function sameIdPendingAThenRunningB() {
    const taskA = deferred<Task>()
    const resolutionA = taggedAs(postResolution, 'receipt-A', INPUT_A)
    const resolutionB = taggedAs(postResolution, 'receipt-B', INPUT_B)
    const resolveResource = vi
      .fn<() => Promise<ResolvedResource>>()
      .mockResolvedValueOnce(resolutionA)
      .mockResolvedValueOnce(resolutionB)
    const createTask = vi
      .fn()
      .mockResolvedValueOnce({
        task_id: 'same-task-id',
        task_type: 'post_download' as const,
        resolve_id: 'receipt-A',
      })
      .mockResolvedValueOnce({
        task_id: 'same-task-id',
        task_type: 'post_download' as const,
        resolve_id: 'receipt-B',
      })
    const getTask = vi
      .fn()
      .mockReturnValueOnce(taskA.promise)
      .mockResolvedValueOnce({
        task_id: 'same-task-id',
        task_type: 'post_download' as const,
        state: 'running' as const,
        title: 'current running task B',
        message: null,
        created_at: '2026-08-15T10:00:00.000',
        started_at: '2026-08-15T10:00:01.000',
        finished_at: null,
        progress: { current: 0, total: 1 },
        metadata: {},
        items: [],
      })
      .mockResolvedValue({
        task_id: 'same-task-id',
        task_type: 'post_download' as const,
        state: 'success' as const,
        title: 'current finished task B',
        message: null,
        created_at: '2026-08-15T10:00:00.000',
        started_at: '2026-08-15T10:00:01.000',
        finished_at: '2026-08-15T10:01:00.000',
        progress: { current: 1, total: 1 },
        metadata: {},
        items: [],
      })
    const flow = useNewDownloadFlow({ resolveResource, createTask, getTask })

    flow.input.value = INPUT_A
    await flow.resolve()
    await flow.create()
    await drain()
    flow.startOver()
    flow.input.value = INPUT_B
    await flow.resolve()
    await flow.create()
    await drain()

    expect(flow.createdTask.value?.task_id).toBe('same-task-id')
    expect(flow.currentTask.value?.title).toBe('current running task B')
    expect(flow.phase.value).toBe('tracking')
    return { flow, getTask, taskA }
  }

  it('cannot overwrite task B or schedule task A again with a late success', async () => {
    vi.useFakeTimers()
    try {
      const { flow, getTask, taskA } = await pendingTaskAThenTaskB()

      taskA.settle({
        task_id: 'task-A',
        task_type: 'post_download',
        state: 'success',
        title: 'stale task A',
        message: null,
        created_at: '2026-08-15T09:30:15.250',
        started_at: '2026-08-15T09:30:16.250',
        finished_at: '2026-08-15T09:31:00.000',
        progress: { current: 1, total: 1 },
        metadata: {},
        items: [],
      })
      await drain()
      await vi.advanceTimersByTimeAsync(TASK_POLL_INTERVAL_MS * 5)

      expect(flow.createdTask.value?.task_id).toBe('task-B')
      expect(flow.currentTask.value?.task_id).toBe('task-B')
      expect(flow.currentTask.value?.title).toBe('current task B')
      expect(flow.phase.value).toBe('terminal')
      expect(flow.trackError.value).toBeNull()
      expect(getTask).toHaveBeenCalledTimes(2)
    } finally {
      vi.useRealTimers()
    }
  })

  it('cannot attach task A failure state to task B', async () => {
    const { flow, taskA } = await pendingTaskAThenTaskB()

    taskA.fail(new ApiError({
      kind: 'network',
      status: null,
      code: null,
      message: 'task A failed late',
    }))
    await drain()

    expect(flow.createdTask.value?.task_id).toBe('task-B')
    expect(flow.currentTask.value?.task_id).toBe('task-B')
    expect(flow.currentTask.value?.title).toBe('current task B')
    expect(flow.phase.value).toBe('terminal')
    expect(flow.trackError.value).toBeNull()
    expect(flow.taskRecordMissing.value).toBe(false)
  })

  it('uses generation when task A and task B have the same id', async () => {
    vi.useFakeTimers()
    try {
      const { flow, taskA } = await sameIdPendingAThenRunningB()

      taskA.settle({
        task_id: 'same-task-id',
        task_type: 'post_download',
        state: 'success',
        title: 'stale terminal task A',
        message: null,
        created_at: '2026-08-15T09:30:15.250',
        started_at: '2026-08-15T09:30:16.250',
        finished_at: '2026-08-15T09:31:00.000',
        progress: { current: 1, total: 1 },
        metadata: {},
        items: [],
      })
      await drain()

      expect(flow.currentTask.value?.title).toBe('current running task B')
      expect(flow.phase.value).toBe('tracking')
      expect(flow.trackError.value).toBeNull()
      flow.stop()
    } finally {
      vi.useRealTimers()
    }
  })

  it('does not let stale non-terminal task A schedule another poll', async () => {
    vi.useFakeTimers()
    const scheduled = vi.spyOn(globalThis, 'setTimeout')
    try {
      const { flow, getTask, taskA } = await sameIdPendingAThenRunningB()
      const timersBeforeA = scheduled.mock.calls.length

      taskA.settle({
        task_id: 'same-task-id',
        task_type: 'post_download',
        state: 'running',
        title: 'stale running task A',
        message: null,
        created_at: '2026-08-15T09:30:15.250',
        started_at: '2026-08-15T09:30:16.250',
        finished_at: null,
        progress: { current: 0, total: 1 },
        metadata: {},
        items: [],
      })
      await drain()

      expect(scheduled).toHaveBeenCalledTimes(timersBeforeA)
      expect(flow.currentTask.value?.title).toBe('current running task B')
      expect(flow.phase.value).toBe('tracking')

      await vi.advanceTimersByTimeAsync(TASK_POLL_INTERVAL_MS)
      expect(getTask).toHaveBeenCalledTimes(3)
      expect(flow.currentTask.value?.title).toBe('current finished task B')
      expect(flow.phase.value).toBe('terminal')
    } finally {
      scheduled.mockRestore()
      vi.useRealTimers()
    }
  })
})

describe('the box is frozen while a task is being created', () => {
  //
  // Between pressing confirm and the server answering there is a window where
  // the request is already on its way. Editing the text in that window would
  // leave the screen describing B while a task for A was being created - and
  // the watcher, seeing the change, would helpfully clear A from view, so the
  // task that did start would be invisible.
  //

  async function creatingFlow() {
    const pending = deferred<{
      task_id: string
      task_type: 'post_download'
      resolve_id: string
    }>()
    const flow = useNewDownloadFlow({
      resolveResource: vi.fn(async () => postResolution),
      createTask: vi.fn(() => pending.promise),
      getTask: vi.fn(async () => {
        throw new Error('not reached')
      }),
    })
    flow.input.value = INPUT_A
    await flow.resolve()
    void flow.create()
    await drain()
    return { flow, pending }
  }

  it('reports the input as locked once confirm is pressed', async () => {
    const { flow } = await creatingFlow()

    expect(flow.phase.value).toBe('creating')
    expect(flow.inputLocked.value).toBe(true)
  })

  it('keeps the resolution even if the text somehow changes', async () => {
    const { flow } = await creatingFlow()

    flow.input.value = INPUT_B

    //
    // The resolution stays, because a task for it is already being created.
    // Clearing it here is what would make that task unfindable.
    //
    expect(flow.resolved.value).not.toBeNull()
    expect(flow.phase.value).toBe('creating')
  })

  it('still tracks the task it actually created', async () => {
    const { flow, pending } = await creatingFlow()

    flow.input.value = INPUT_B
    pending.settle({
      task_id: 'task-1',
      task_type: 'post_download',
      resolve_id: 'receipt-1',
    })
    await drain()

    expect(flow.createdTask.value?.task_id).toBe('task-1')
    expect(flow.phase.value).toBe('tracking')
  })

  it('unlocks again if the creation failed', async () => {
    const refused = new ApiError({
      kind: 'backend',
      status: 400,
      code: 400,
      message: 'refused',
    })
    const flow = useNewDownloadFlow({
      resolveResource: vi.fn(async () => postResolution),
      createTask: vi.fn(async () => Promise.reject(refused)),
    })
    flow.input.value = INPUT_A
    await flow.resolve()
    await flow.create()

    //
    // No task exists, so nothing is frozen: the user is free to edit and try
    // something else.
    //
    expect(flow.inputLocked.value).toBe(false)
    expect(flow.phase.value).toBe('resolved')
  })
})
