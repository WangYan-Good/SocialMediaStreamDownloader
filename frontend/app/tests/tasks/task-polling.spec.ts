import { createPinia, setActivePinia } from 'pinia'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import { ApiError } from '../../src/api/client'
import { listTasks } from '../../src/api/tasks'
import { TASK_CENTER_POLL_INTERVAL_MS, useTaskStore } from '../../src/stores/tasks'
import type { Task } from '../../src/types/task'

vi.mock('../../src/api/tasks', () => ({
  listTasks: vi.fn(),
}))

const mockedList = vi.mocked(listTasks)

function task(overrides: Partial<Task> = {}): Task {
  return {
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
    ...overrides,
  }
}

function page(items: Task[], total = items.length) {
  return { items, total }
}

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
  for (let index = 0; index < 5; index += 1) {
    await Promise.resolve()
  }
}

beforeEach(() => {
  setActivePinia(createPinia())
  mockedList.mockReset()
  mockedList.mockResolvedValue(page([]))
  vi.useFakeTimers()
})

afterEach(() => {
  vi.useRealTimers()
})

describe('the polling interval', () => {
  it('is a named constant in a sensible range', () => {
    expect(typeof TASK_CENTER_POLL_INTERVAL_MS).toBe('number')
    expect(TASK_CENTER_POLL_INTERVAL_MS).toBeGreaterThanOrEqual(3000)
    expect(TASK_CENTER_POLL_INTERVAL_MS).toBeLessThanOrEqual(5000)
  })
})

describe('starting and stopping', () => {
  it('reads immediately and then keeps reading', async () => {
    const store = useTaskStore()

    await store.startAutoRefresh()
    expect(mockedList).toHaveBeenCalledTimes(1)
    expect(store.pollingActive).toBe(true)

    await vi.advanceTimersByTimeAsync(TASK_CENTER_POLL_INTERVAL_MS)
    expect(mockedList).toHaveBeenCalledTimes(2)

    await vi.advanceTimersByTimeAsync(TASK_CENTER_POLL_INTERVAL_MS)
    expect(mockedList).toHaveBeenCalledTimes(3)
  })

  it('stops when told to', async () => {
    const store = useTaskStore()
    await store.startAutoRefresh()
    const before = mockedList.mock.calls.length

    store.stopAutoRefresh()

    await vi.advanceTimersByTimeAsync(TASK_CENTER_POLL_INTERVAL_MS * 5)
    expect(mockedList).toHaveBeenCalledTimes(before)
    expect(store.pollingActive).toBe(false)
  })

  it('runs exactly one loop however many times it is started', async () => {
    //
    // Two loops would double the request rate and interleave their answers.
    // Mounting the screen twice, or a remount racing an unmount, must not be
    // able to produce that.
    //
    const store = useTaskStore()

    await store.startAutoRefresh()
    await store.startAutoRefresh()
    await store.startAutoRefresh()

    const afterStarts = mockedList.mock.calls.length
    await vi.advanceTimersByTimeAsync(TASK_CENTER_POLL_INTERVAL_MS)

    expect(mockedList.mock.calls.length).toBe(afterStarts + 1)
  })

  it('runs one loop across a stop and a restart', async () => {
    const store = useTaskStore()
    await store.startAutoRefresh()
    store.stopAutoRefresh()
    await store.startAutoRefresh()

    const afterRestart = mockedList.mock.calls.length
    await vi.advanceTimersByTimeAsync(TASK_CENTER_POLL_INTERVAL_MS)

    expect(mockedList.mock.calls.length).toBe(afterRestart + 1)
  })
})

describe('polling never stops just because the work did', () => {
  it('keeps reading when every task has already finished', async () => {
    //
    // The difference between this screen and New Download's single-task poll.
    //
    // A task centre that stopped once everything was terminal would never
    // notice the next task - and the next task routinely arrives from
    // somewhere else entirely: New Download in this tab, the legacy interface,
    // another browser, a live probe started from history.
    //
    mockedList.mockResolvedValue(
      page([
        task({ task_id: 'A', state: 'success' }),
        task({ task_id: 'B', state: 'failed' }),
        task({ task_id: 'C', state: 'cancelled' }),
      ]),
    )
    const store = useTaskStore()

    await store.startAutoRefresh()
    expect(mockedList).toHaveBeenCalledTimes(1)

    await vi.advanceTimersByTimeAsync(TASK_CENTER_POLL_INTERVAL_MS)
    expect(mockedList).toHaveBeenCalledTimes(2)

    await vi.advanceTimersByTimeAsync(TASK_CENTER_POLL_INTERVAL_MS)
    expect(mockedList).toHaveBeenCalledTimes(3)
  })

  it('keeps reading when the list is empty', async () => {
    const store = useTaskStore()

    await store.startAutoRefresh()
    await vi.advanceTimersByTimeAsync(TASK_CENTER_POLL_INTERVAL_MS * 3)

    expect(mockedList.mock.calls.length).toBeGreaterThan(3)
  })

  it('discovers a task created while it was watching nothing', async () => {
    const store = useTaskStore()
    await store.startAutoRefresh()
    expect(store.tasks).toHaveLength(0)

    mockedList.mockResolvedValue(page([task({ task_id: 'new' })]))
    await vi.advanceTimersByTimeAsync(TASK_CENTER_POLL_INTERVAL_MS)

    expect(store.tasks.map((one) => one.task_id)).toEqual(['new'])
  })
})

describe('never two reads at once', () => {
  it('waits for a slow read instead of stacking another on top', async () => {
    const pending = deferred<{ items: Task[]; total: number }>()
    mockedList.mockReturnValue(pending.promise)
    const store = useTaskStore()

    void store.startAutoRefresh()
    await drain()
    expect(mockedList).toHaveBeenCalledTimes(1)

    await vi.advanceTimersByTimeAsync(TASK_CENTER_POLL_INTERVAL_MS * 4)
    expect(mockedList).toHaveBeenCalledTimes(1)

    pending.settle(page([]))
    await drain()

    await vi.advanceTimersByTimeAsync(TASK_CENTER_POLL_INTERVAL_MS)
    expect(mockedList).toHaveBeenCalledTimes(2)
  })
})

describe('a stale answer for a filter nobody is using any more', () => {
  it('cannot overwrite the list the current filter produced', async () => {
    //
    // The race this guard exists for:
    //
    //   state=running  → request A, slow
    //   user picks failed → request B, fast
    //   B lands: the failed list appears
    //   A lands: without a guard, the running list replaces it - under a filter
    //   that says "failed"
    //
    const slowRunning = deferred<{ items: Task[]; total: number }>()
    const fastFailed = deferred<{ items: Task[]; total: number }>()
    mockedList
      .mockReturnValueOnce(slowRunning.promise)
      .mockReturnValueOnce(fastFailed.promise)
    const store = useTaskStore()

    const filteringRunning = store.setStateFilter('running')
    const filteringFailed = store.setStateFilter('failed')

    fastFailed.settle(page([task({ task_id: 'FAILED-1', state: 'failed' })]))
    await filteringFailed
    await drain()

    slowRunning.settle(page([task({ task_id: 'RUNNING-1', state: 'running' })]))
    await filteringRunning
    await drain()

    expect(store.stateFilter).toBe('failed')
    expect(store.tasks.map((one) => one.task_id)).toEqual(['FAILED-1'])
  })

  it('cannot overwrite the total either', async () => {
    const slow = deferred<{ items: Task[]; total: number }>()
    const fast = deferred<{ items: Task[]; total: number }>()
    mockedList.mockReturnValueOnce(slow.promise).mockReturnValueOnce(fast.promise)
    const store = useTaskStore()

    const first = store.setStateFilter('running')
    const second = store.setStateFilter('failed')

    fast.settle(page([task({ task_id: 'F' })], 3))
    await second
    await drain()
    slow.settle(page([task({ task_id: 'R' })], 99))
    await first
    await drain()

    expect(store.total).toBe(3)
  })

  it('cannot report an error against a filter that moved on', async () => {
    const slow = deferred<{ items: Task[]; total: number }>()
    const fast = deferred<{ items: Task[]; total: number }>()
    mockedList.mockReturnValueOnce(slow.promise).mockReturnValueOnce(fast.promise)
    const store = useTaskStore()

    const first = store.setStateFilter('running')
    const second = store.setStateFilter('failed')

    fast.settle(page([]))
    await second
    await drain()
    slow.fail(new ApiError({ kind: 'network', status: null, code: null, message: 'gone' }))
    await first
    await drain()

    expect(store.refreshError).toBeNull()
  })

  it('aborts the request it is abandoning', async () => {
    const pending = deferred<{ items: Task[]; total: number }>()
    mockedList.mockReturnValueOnce(pending.promise).mockResolvedValue(page([]))
    const store = useTaskStore()

    void store.setStateFilter('running')
    await drain()
    const [, firstSignal] = mockedList.mock.calls[0]

    await store.setStateFilter('failed')

    expect(firstSignal?.aborted).toBe(true)
  })
})

describe('when the list cannot be read', () => {
  const offline = new ApiError({
    kind: 'network',
    status: null,
    code: null,
    message: 'Failed to fetch',
  })

  async function loadedThenOffline() {
    mockedList.mockResolvedValueOnce(page([task({ task_id: 'A', state: 'running' })]))
    const store = useTaskStore()
    await store.startAutoRefresh()

    mockedList.mockRejectedValue(offline)
    await vi.advanceTimersByTimeAsync(TASK_CENTER_POLL_INTERVAL_MS)
    await drain()
    return store
  }

  it('keeps the tasks it last saw', async () => {
    //
    // A failed read is not evidence that there are no tasks. Emptying the list
    // would turn a network blip into "everything disappeared".
    //
    const store = await loadedThenOffline()

    expect(store.tasks.map((one) => one.task_id)).toEqual(['A'])
    expect(store.total).toBe(1)
  })

  it('changes no task state', async () => {
    const store = await loadedThenOffline()

    expect(store.tasks[0].state).toBe('running')
  })

  it('says the list could not be refreshed', async () => {
    const store = await loadedThenOffline()

    expect(store.refreshError).toContain('无法刷新任务列表')
    expect(store.refreshError).toContain('Failed to fetch')
  })

  it('pauses rather than hammering a backend that is not answering', async () => {
    const store = await loadedThenOffline()
    const afterFailure = mockedList.mock.calls.length

    await vi.advanceTimersByTimeAsync(TASK_CENTER_POLL_INTERVAL_MS * 5)

    expect(mockedList).toHaveBeenCalledTimes(afterFailure)
    expect(store.pollingActive).toBe(false)
  })

  it('resumes on a deliberate retry', async () => {
    const store = await loadedThenOffline()
    mockedList.mockResolvedValue(page([task({ task_id: 'A', state: 'success' })]))

    await store.retry()

    expect(store.refreshError).toBeNull()
    expect(store.tasks[0].state).toBe('success')
    expect(store.pollingActive).toBe(true)

    const afterRetry = mockedList.mock.calls.length
    await vi.advanceTimersByTimeAsync(TASK_CENTER_POLL_INTERVAL_MS)
    expect(mockedList.mock.calls.length).toBe(afterRetry + 1)
  })

  it('runs one loop after retrying, not two', async () => {
    const store = await loadedThenOffline()
    mockedList.mockResolvedValue(page([]))

    await store.retry()
    const afterRetry = mockedList.mock.calls.length

    await vi.advanceTimersByTimeAsync(TASK_CENTER_POLL_INTERVAL_MS)

    expect(mockedList.mock.calls.length).toBe(afterRetry + 1)
  })
})

describe('the very first read fails', () => {
  it('is an error, not an empty task centre', async () => {
    //
    // "Nothing was read" and "there is nothing" are different facts, and only
    // the first one is known here.
    //
    mockedList.mockRejectedValue(
      new ApiError({ kind: 'network', status: null, code: null, message: 'offline' }),
    )
    const store = useTaskStore()

    await store.startAutoRefresh()

    expect(store.refreshError).toBeTruthy()
    expect(store.hasLoaded).toBe(false)
    expect(store.tasks).toEqual([])
  })
})

describe('a manual refresh', () => {
  it('reads at once without starting a second loop', async () => {
    const store = useTaskStore()
    await store.startAutoRefresh()

    await store.refresh()
    const afterManual = mockedList.mock.calls.length

    await vi.advanceTimersByTimeAsync(TASK_CENTER_POLL_INTERVAL_MS)

    expect(mockedList.mock.calls.length).toBe(afterManual + 1)
  })
})

describe('a change of filters while polling', () => {
  it('does not leave the old schedule running beside the new one', async () => {
    const store = useTaskStore()
    await store.startAutoRefresh()

    await store.setStateFilter('running')
    const afterFilter = mockedList.mock.calls.length

    await vi.advanceTimersByTimeAsync(TASK_CENTER_POLL_INTERVAL_MS)

    expect(mockedList.mock.calls.length).toBe(afterFilter + 1)
  })
})

describe('an answer that lands after the screen is gone', () => {
  it('schedules nothing', async () => {
    const pending = deferred<{ items: Task[]; total: number }>()
    mockedList.mockReturnValue(pending.promise)
    const store = useTaskStore()

    void store.startAutoRefresh()
    await drain()
    expect(mockedList).toHaveBeenCalledTimes(1)

    store.stopAutoRefresh()
    pending.settle(page([task({ task_id: 'late' })]))
    await drain()

    await vi.advanceTimersByTimeAsync(TASK_CENTER_POLL_INTERVAL_MS * 5)

    expect(mockedList).toHaveBeenCalledTimes(1)
  })

  it('writes nothing into the store', async () => {
    const pending = deferred<{ items: Task[]; total: number }>()
    mockedList.mockReturnValue(pending.promise)
    const store = useTaskStore()

    void store.startAutoRefresh()
    await drain()
    store.stopAutoRefresh()

    pending.settle(page([task({ task_id: 'late' })], 7))
    await drain()

    expect(store.tasks).toEqual([])
    expect(store.total).toBe(0)
  })

  it('reports no error from a late failure either', async () => {
    const pending = deferred<{ items: Task[]; total: number }>()
    mockedList.mockReturnValue(pending.promise)
    const store = useTaskStore()

    void store.startAutoRefresh()
    await drain()
    store.stopAutoRefresh()

    pending.fail(new ApiError({ kind: 'network', status: null, code: null, message: 'x' }))
    await drain()

    expect(store.refreshError).toBeNull()
  })

  it('aborts the request on the way out', async () => {
    const pending = deferred<{ items: Task[]; total: number }>()
    mockedList.mockReturnValue(pending.promise)
    const store = useTaskStore()

    void store.startAutoRefresh()
    await drain()
    const [, signal] = mockedList.mock.calls[0]

    store.stopAutoRefresh()

    expect(signal?.aborted).toBe(true)
  })
})

describe('a manual refresh is under the same concurrency rule as the loop', () => {
  it('replaces the request in flight rather than running beside it', async () => {
    //
    // The refresh button is disabled while a read is in flight, so this should
    // not be reachable through the interface - but the store is the thing that
    // has to hold the rule, because a second entry point will eventually exist.
    //
    const pending = deferred<{ items: Task[]; total: number }>()
    mockedList.mockReturnValueOnce(pending.promise).mockResolvedValue(page([]))
    const store = useTaskStore()

    void store.startAutoRefresh()
    await drain()
    const [, firstSignal] = mockedList.mock.calls[0]

    await store.refresh()

    expect(firstSignal?.aborted).toBe(true)
  })

  it('cannot let the abandoned answer overwrite the newer one', async () => {
    const slow = deferred<{ items: Task[]; total: number }>()
    const fast = deferred<{ items: Task[]; total: number }>()
    mockedList.mockReturnValueOnce(slow.promise).mockReturnValueOnce(fast.promise)
    const store = useTaskStore()

    void store.startAutoRefresh()
    await drain()

    const manual = store.refresh()
    fast.settle(page([task({ task_id: 'NEW' })], 1))
    await manual
    await drain()

    slow.settle(page([task({ task_id: 'OLD' })], 99))
    await drain()

    expect(store.tasks.map((one) => one.task_id)).toEqual(['NEW'])
    expect(store.total).toBe(1)
  })

  it('leaves exactly one schedule behind it', async () => {
    const store = useTaskStore()
    await store.startAutoRefresh()

    await store.refresh()
    await store.refresh()
    await store.refresh()

    const afterManual = mockedList.mock.calls.length
    await vi.advanceTimersByTimeAsync(TASK_CENTER_POLL_INTERVAL_MS)

    expect(mockedList.mock.calls.length).toBe(afterManual + 1)
  })

  it('reports that a read is in flight so the button can say so', async () => {
    const pending = deferred<{ items: Task[]; total: number }>()
    mockedList.mockReturnValue(pending.promise)
    const store = useTaskStore()

    void store.startAutoRefresh()
    await drain()

    expect(store.refreshing).toBe(true)

    pending.settle(page([]))
    await drain()
    expect(store.refreshing).toBe(false)
  })
})
