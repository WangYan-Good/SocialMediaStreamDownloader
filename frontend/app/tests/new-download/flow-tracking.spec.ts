import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import { ApiError } from '../../src/api/client'
import {
  TASK_POLL_INTERVAL_MS,
  useNewDownloadFlow,
} from '../../src/composables/useNewDownloadFlow'
import type { CreatedTask, Task, TaskState } from '../../src/types/task'
import { postResolution } from './build-request.spec'

function deferred<T>() {
  let settle: (value: T) => void = () => {}
  let fail: (reason: unknown) => void = () => {}
  const promise = new Promise<T>((resolve, reject) => {
    settle = resolve
    fail = reject
  })
  return { promise, settle, fail }
}

function taskIn(state: TaskState, overrides: Partial<Task> = {}): Task {
  return {
    task_id: 'task-1',
    task_type: 'post_download',
    state,
    title: '下载作品',
    message: null,
    created_at: '2026-08-15T09:30:15.250',
    started_at: state === 'pending' ? null : '2026-08-15T09:30:16.250',
    finished_at: null,
    progress: { current: 0, total: 1 },
    metadata: {},
    items: [],
    ...overrides,
  }
}

const CREATED: CreatedTask = {
  task_id: 'task-1',
  task_type: 'post_download',
  resolve_id: 'receipt-1',
}

function buildFlow(getTask: () => Promise<Task>) {
  return useNewDownloadFlow({
    resolveResource: vi.fn(async () => postResolution),
    createTask: vi.fn(async () => CREATED),
    getTask: vi.fn(getTask),
  })
}

async function trackingFlow(getTask: () => Promise<Task>) {
  const flow = buildFlow(getTask)
  flow.input.value = 'https://v.douyin.com/abc/'
  await flow.resolve()
  await flow.create()
  //
  // create() starts the first read without waiting for it, so let whatever it
  // queued settle before a test looks at the state it produced.
  //
  await settle()
  return flow
}

/** Let queued microtasks run without advancing the fake clock. */
async function settle() {
  await Promise.resolve()
  await Promise.resolve()
  await Promise.resolve()
}

beforeEach(() => {
  vi.useFakeTimers()
})

afterEach(() => {
  vi.useRealTimers()
})

describe('polling interval', () => {
  it('is a named constant rather than a number sprinkled about', () => {
    expect(typeof TASK_POLL_INTERVAL_MS).toBe('number')
    expect(TASK_POLL_INTERVAL_MS).toBeGreaterThanOrEqual(1000)
    expect(TASK_POLL_INTERVAL_MS).toBeLessThanOrEqual(2000)
  })
})

describe('tracking a task through to the end', () => {
  it('reads the task once as soon as it is created', async () => {
    const getTask = vi.fn(async () => taskIn('pending'))
    const flow = await trackingFlow(getTask)

    expect(getTask).toHaveBeenCalledTimes(1)
    expect(getTask).toHaveBeenCalledWith('task-1', expect.any(AbortSignal))
    expect(flow.currentTask.value?.state).toBe('pending')
  })

  it('keeps reading while the task is still going', async () => {
    const getTask = vi.fn(async () => taskIn('running'))
    await trackingFlow(getTask)

    expect(getTask).toHaveBeenCalledTimes(1)

    await vi.advanceTimersByTimeAsync(TASK_POLL_INTERVAL_MS)
    expect(getTask).toHaveBeenCalledTimes(2)

    await vi.advanceTimersByTimeAsync(TASK_POLL_INTERVAL_MS)
    expect(getTask).toHaveBeenCalledTimes(3)
  })

  it('walks pending to running to success and then stops', async () => {
    const states: TaskState[] = ['pending', 'running', 'success']
    let index = 0
    const getTask = vi.fn(async () => taskIn(states[Math.min(index++, states.length - 1)]))
    const flow = await trackingFlow(getTask)

    await vi.advanceTimersByTimeAsync(TASK_POLL_INTERVAL_MS)
    expect(flow.currentTask.value?.state).toBe('running')

    await vi.advanceTimersByTimeAsync(TASK_POLL_INTERVAL_MS)
    expect(flow.currentTask.value?.state).toBe('success')
    expect(flow.phase.value).toBe('terminal')

    const settledCalls = getTask.mock.calls.length
    await vi.advanceTimersByTimeAsync(TASK_POLL_INTERVAL_MS * 5)
    expect(getTask).toHaveBeenCalledTimes(settledCalls)
  })
})

describe('every terminal state stops the polling', () => {
  it.each<TaskState>(['success', 'partial', 'failed', 'cancelled'])(
    'stops on %s',
    async (state) => {
      const getTask = vi.fn(async () => taskIn(state))
      const flow = await trackingFlow(getTask)

      expect(flow.phase.value).toBe('terminal')
      expect(getTask).toHaveBeenCalledTimes(1)

      await vi.advanceTimersByTimeAsync(TASK_POLL_INTERVAL_MS * 5)

      expect(getTask).toHaveBeenCalledTimes(1)
    },
  )

  it.each<TaskState>(['pending', 'running'])('keeps going on %s', async (state) => {
    const getTask = vi.fn(async () => taskIn(state))
    const flow = await trackingFlow(getTask)

    expect(flow.phase.value).toBe('tracking')

    await vi.advanceTimersByTimeAsync(TASK_POLL_INTERVAL_MS * 3)

    expect(getTask.mock.calls.length).toBeGreaterThan(1)
  })
})

describe('never two reads at once', () => {
  it('waits for a slow read instead of stacking another on top', async () => {
    //
    // With setInterval this is the bug: a read that takes longer than the
    // interval gets a second one launched on top of it, then a third, and the
    // answers start arriving out of order. A recursive timeout scheduled after
    // each answer cannot do that.
    //
    const first = deferred<Task>()
    const getTask = vi.fn(() => first.promise)
    await trackingFlow(getTask)

    expect(getTask).toHaveBeenCalledTimes(1)

    await vi.advanceTimersByTimeAsync(TASK_POLL_INTERVAL_MS * 4)

    expect(getTask).toHaveBeenCalledTimes(1)

    first.settle(taskIn('running'))
    await settle()

    await vi.advanceTimersByTimeAsync(TASK_POLL_INTERVAL_MS)
    expect(getTask).toHaveBeenCalledTimes(2)
  })
})

describe('a read that fails is not a task that failed', () => {
  //
  // The distinction this whole block exists for. A failed GET means the browser
  // cannot see the task; it says nothing about whether the download is going
  // fine. Marking the task failed would be the client inventing an outcome.
  //
  async function flowWithFailingRead(error: ApiError, firstState: TaskState = 'running') {
    let call = 0
    const getTask = vi.fn(async () => {
      call += 1
      if (call === 1) {
        return taskIn(firstState)
      }
      throw error
    })
    const flow = await trackingFlow(getTask)
    await vi.advanceTimersByTimeAsync(TASK_POLL_INTERVAL_MS)
    return { flow, getTask }
  }

  it('leaves the last known state alone', async () => {
    const offline = new ApiError({
      kind: 'network',
      status: null,
      code: null,
      message: 'Failed to fetch',
    })

    const { flow } = await flowWithFailingRead(offline)

    expect(flow.currentTask.value?.state).toBe('running')
    expect(flow.phase.value).toBe('tracking')
  })

  it('pauses rather than hammering a backend that is not answering', async () => {
    const offline = new ApiError({
      kind: 'network',
      status: null,
      code: null,
      message: 'Failed to fetch',
    })

    const { flow, getTask } = await flowWithFailingRead(offline)
    const afterFailure = getTask.mock.calls.length

    await vi.advanceTimersByTimeAsync(TASK_POLL_INTERVAL_MS * 5)

    expect(getTask).toHaveBeenCalledTimes(afterFailure)
    expect(flow.trackError.value).toBeTruthy()
  })

  it('says the status is unavailable, not that the download failed', async () => {
    const offline = new ApiError({
      kind: 'network',
      status: null,
      code: null,
      message: 'Failed to fetch',
    })

    const { flow } = await flowWithFailingRead(offline)

    expect(flow.trackError.value).toContain('状态')
    expect(flow.trackError.value).not.toContain('下载失败')
  })

  it('resumes on a deliberate retry, against the same task', async () => {
    const offline = new ApiError({
      kind: 'network',
      status: null,
      code: null,
      message: 'Failed to fetch',
    })
    const { flow, getTask } = await flowWithFailingRead(offline)
    const beforeRetry = getTask.mock.calls.length

    await flow.retryTracking()

    expect(getTask.mock.calls.length).toBe(beforeRetry + 1)
    expect(getTask).toHaveBeenLastCalledWith('task-1', expect.any(AbortSignal))
  })
})

describe('the task record is gone', () => {
  it('says the record expired rather than that the work failed', async () => {
    //
    // A task store drops finished tasks on its own schedule. "I cannot find the
    // record" and "the download failed" are different facts, and only one of
    // them is known here.
    //
    let call = 0
    const missing = new ApiError({
      kind: 'backend',
      status: 404,
      code: 404,
      message: '任务不存在或已过期',
    })
    const getTask = vi.fn(async () => {
      call += 1
      if (call === 1) {
        return taskIn('running')
      }
      throw missing
    })
    const flow = await trackingFlow(getTask)

    await vi.advanceTimersByTimeAsync(TASK_POLL_INTERVAL_MS)

    expect(flow.taskRecordMissing.value).toBe(true)
    expect(flow.currentTask.value?.state).toBe('running')
    expect(flow.trackError.value).not.toContain('下载失败')
  })

  it('stops polling a record that is not there', async () => {
    const missing = new ApiError({
      kind: 'backend',
      status: 404,
      code: 404,
      message: '任务不存在或已过期',
    })
    const getTask = vi.fn(async () => Promise.reject(missing))
    const flow = await trackingFlow(getTask)

    expect(flow.taskRecordMissing.value).toBe(true)
    const calls = getTask.mock.calls.length

    await vi.advanceTimersByTimeAsync(TASK_POLL_INTERVAL_MS * 5)

    expect(getTask).toHaveBeenCalledTimes(calls)
  })
})

describe('progress with no total', () => {
  it('carries a null total through untouched', async () => {
    //
    // A recording has no final count. Anything derived from it here would be a
    // division by null somewhere in a template.
    //
    const getTask = vi.fn(async () =>
      taskIn('running', {
        task_type: 'live_record',
        progress: { current: 97, total: null },
      }),
    )
    const flow = await trackingFlow(getTask)

    expect(flow.currentTask.value?.progress).toEqual({ current: 97, total: null })
    expect(flow.progressPercent.value).toBeNull()
  })

  it('reports a percentage only when there is something to divide by', async () => {
    const getTask = vi.fn(async () =>
      taskIn('running', { progress: { current: 3, total: 4 } }),
    )
    const flow = await trackingFlow(getTask)

    expect(flow.progressPercent.value).toBe(75)
  })

  it('never divides by zero', async () => {
    const getTask = vi.fn(async () =>
      taskIn('running', { progress: { current: 0, total: 0 } }),
    )
    const flow = await trackingFlow(getTask)

    expect(flow.progressPercent.value).toBeNull()
  })
})

describe('stopping', () => {
  it('stops polling when the flow is torn down', async () => {
    const getTask = vi.fn(async () => taskIn('running'))
    const flow = await trackingFlow(getTask)
    const before = getTask.mock.calls.length

    flow.stop()
    await vi.advanceTimersByTimeAsync(TASK_POLL_INTERVAL_MS * 5)

    expect(getTask).toHaveBeenCalledTimes(before)
  })
})

describe('starting over', () => {
  it('is not offered while the task is still going', async () => {
    //
    // There is no task centre yet, so a task dropped from this screen has
    // nowhere to be found again.
    //
    const getTask = vi.fn(async () => taskIn('running'))
    const flow = await trackingFlow(getTask)

    expect(flow.canStartOver.value).toBe(false)
  })

  it('is offered once the task has ended', async () => {
    const getTask = vi.fn(async () => taskIn('success'))
    const flow = await trackingFlow(getTask)

    expect(flow.canStartOver.value).toBe(true)
  })

  it('clears everything back to an empty form', async () => {
    const getTask = vi.fn(async () => taskIn('success'))
    const flow = await trackingFlow(getTask)

    flow.startOver()

    expect(flow.phase.value).toBe('editing')
    expect(flow.input.value).toBe('')
    expect(flow.resolved.value).toBeNull()
    expect(flow.createdTask.value).toBeNull()
    expect(flow.currentTask.value).toBeNull()
    expect(flow.resolveError.value).toBeNull()
    expect(flow.createError.value).toBeNull()
    expect(flow.trackError.value).toBeNull()
    expect(flow.ownerConfirmed.value).toBe(false)
    expect(flow.inputLocked.value).toBe(false)
  })

  it('stops polling as it resets', async () => {
    const getTask = vi.fn(async () => taskIn('success'))
    const flow = await trackingFlow(getTask)

    flow.startOver()
    const before = getTask.mock.calls.length
    await vi.advanceTimersByTimeAsync(TASK_POLL_INTERVAL_MS * 5)

    expect(getTask).toHaveBeenCalledTimes(before)
  })
})
