import { createPinia, setActivePinia } from 'pinia'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import { ApiError } from '../../src/api/client'
import { listHistoryOwners } from '../../src/api/history'
import { listLibraryLives, listLibraryPosts } from '../../src/api/library'
import { getSystemStatus } from '../../src/api/system'
import { listTasks } from '../../src/api/tasks'
import { useOverviewStore } from '../../src/stores/overview'
import { historyOwner, libraryLive, libraryPost, systemStatus, task } from './fixtures'

vi.mock('../../src/api/system', () => ({ getSystemStatus: vi.fn() }))
vi.mock('../../src/api/tasks', () => ({ listTasks: vi.fn(), getTask: vi.fn(), createTask: vi.fn() }))
vi.mock('../../src/api/history', () => ({
  listHistoryOwners: vi.fn(),
  listOwnerSessions: vi.fn(),
  submitLiveProbe: vi.fn(),
  getLiveProbe: vi.fn(),
}))
vi.mock('../../src/api/library', () => ({
  listLibraryPosts: vi.fn(),
  listLibraryLives: vi.fn(),
}))

const mockedSystem = vi.mocked(getSystemStatus)
const mockedTasks = vi.mocked(listTasks)
const mockedOwners = vi.mocked(listHistoryOwners)
const mockedPosts = vi.mocked(listLibraryPosts)
const mockedLives = vi.mocked(listLibraryLives)

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
  for (let index = 0; index < 8; index += 1) {
    await Promise.resolve()
  }
}

const offline = new ApiError({
  kind: 'network',
  status: null,
  code: null,
  message: 'offline',
})

const unavailable = new ApiError({
  kind: 'backend',
  status: 503,
  code: 503,
  message: '媒体库需要启用数据库',
})

beforeEach(() => {
  setActivePinia(createPinia())
  vi.clearAllMocks()
  mockedSystem.mockResolvedValue(systemStatus())
  mockedTasks.mockResolvedValue({ items: [task()], total: 37 })
  mockedOwners.mockResolvedValue({
    total: 128,
    page: 1,
    page_size: 1,
    items: [historyOwner()],
  })
  mockedPosts.mockResolvedValue({
    total: 4210,
    page: 1,
    page_size: 1,
    items: [libraryPost()],
  })
  mockedLives.mockResolvedValue({
    total: 96,
    page: 1,
    page_size: 1,
    items: [libraryLive()],
  })
})

afterEach(() => {
  vi.useRealTimers()
})

describe('what the overview reads', () => {
  it('reads nothing until it is asked to', () => {
    useOverviewStore()

    expect(mockedSystem).not.toHaveBeenCalled()
    expect(mockedTasks).not.toHaveBeenCalled()
    expect(mockedOwners).not.toHaveBeenCalled()
  })

  it('asks each existing read model for exactly what it needs', async () => {
    //
    // Five reads against five read models that already exist. There is no
    // overview endpoint behind this: a dashboard that needed its own aggregate
    // would be a second implementation of five queries that already answer.
    //
    const store = useOverviewStore()

    await store.load()

    expect(mockedSystem).toHaveBeenCalledTimes(1)
    expect(mockedTasks).toHaveBeenCalledWith({ limit: 5 }, expect.anything())
    expect(mockedOwners).toHaveBeenCalledWith(
      { page: 1, page_size: 1, sort: 'last_checked_at', order: 'desc' },
      expect.anything(),
    )
    expect(mockedPosts).toHaveBeenCalledWith(
      { page: 1, page_size: 1, sort: 'downloaded_at', order: 'desc' },
      expect.anything(),
    )
    expect(mockedLives).toHaveBeenCalledWith(
      { page: 1, page_size: 1, sort: 'observed_at', order: 'desc' },
      expect.anything(),
    )
  })

  it('keeps the totals the server counted rather than what it returned', async () => {
    //
    // Every one of these pages asked for a single row. The number beside it is
    // the server's count of everything matching, and using the page length
    // instead would report 1, 1, 1.
    //
    const store = useOverviewStore()

    await store.load()

    expect(store.taskTotal).toBe(37)
    expect(store.creatorTotal).toBe(128)
    expect(store.libraryPostTotal).toBe(4210)
    expect(store.libraryLiveTotal).toBe(96)
    expect(store.recentTasks).toHaveLength(1)
  })

  it('keeps the order the task api produced', async () => {
    mockedTasks.mockResolvedValue({
      items: [
        task({ task_id: 'c' }),
        task({ task_id: 'a' }),
        task({ task_id: 'b' }),
      ],
      total: 3,
    })
    const store = useOverviewStore()

    await store.load()

    expect(store.recentTasks.map((one) => one.task_id)).toEqual(['c', 'a', 'b'])
  })

  it('takes the newest post and live from the single row it asked for', async () => {
    const store = useOverviewStore()

    await store.load()

    expect(store.latestPost?.aweme_id).toBe('7300000000000000001')
    expect(store.latestLive?.room_id).toBe('7123')
  })

  it('has no newest content when there is none recorded', async () => {
    mockedPosts.mockResolvedValue({ total: 0, page: 1, page_size: 1, items: [] })
    mockedLives.mockResolvedValue({ total: 0, page: 1, page_size: 1, items: [] })
    const store = useOverviewStore()

    await store.load()

    expect(store.latestPost).toBeNull()
    expect(store.latestLive).toBeNull()
    expect(store.libraryPostTotal).toBe(0)
  })
})

describe('one section failing', () => {
  it('does not take the rest of the page down with it', async () => {
    //
    // The realistic degraded case: the database is unreachable, so everything
    // that reads it fails while the system status and the in-process task
    // record answer perfectly well. A page that reported one failure for all
    // five would hide the half that still works - and the system card is
    // exactly where somebody would look to find out why.
    //
    mockedOwners.mockRejectedValue(unavailable)
    mockedPosts.mockRejectedValue(unavailable)
    mockedLives.mockRejectedValue(unavailable)
    const store = useOverviewStore()

    await store.load()

    expect(store.systemStatus).not.toBeNull()
    expect(store.recentTasks).toHaveLength(1)
    expect(store.taskTotal).toBe(37)
    expect(store.creatorsError).not.toBeNull()
    expect(store.postsError).not.toBeNull()
    expect(store.livesError).not.toBeNull()
    expect(store.systemError).toBeNull()
    expect(store.tasksError).toBeNull()
  })

  it('never reports a failed read as a count of zero', async () => {
    //
    // "Could not read" and "there are none" are different facts, and a zero
    // would state the second while meaning the first.
    //
    mockedPosts.mockRejectedValue(unavailable)
    const store = useOverviewStore()

    await store.load()

    expect(store.libraryPostTotal).toBeNull()
    expect(store.postsError).not.toBeNull()
  })

  it('lets the system card fail on its own too', async () => {
    mockedSystem.mockRejectedValue(offline)
    const store = useOverviewStore()

    await store.load()

    expect(store.systemStatus).toBeNull()
    expect(store.systemError).not.toBeNull()
    expect(store.taskTotal).toBe(37)
  })
})

describe('refreshing', () => {
  it('keeps each section that had already succeeded', async () => {
    const store = useOverviewStore()
    await store.load()

    mockedPosts.mockRejectedValue(unavailable)
    await store.load()

    expect(store.libraryPostTotal).toBe(4210)
    expect(store.latestPost?.aweme_id).toBe('7300000000000000001')
    expect(store.postsError).not.toBeNull()
    //
    // The section that did succeed is untouched by its neighbour's failure.
    //
    expect(store.libraryLiveTotal).toBe(96)
  })

  it('clears a section error once it succeeds again', async () => {
    mockedPosts.mockRejectedValue(unavailable)
    const store = useOverviewStore()
    await store.load()
    expect(store.postsError).not.toBeNull()

    mockedPosts.mockResolvedValue({ total: 7, page: 1, page_size: 1, items: [] })
    await store.load()

    expect(store.postsError).toBeNull()
    expect(store.libraryPostTotal).toBe(7)
  })

  it('never runs two batches at once', async () => {
    const pending = deferred<Awaited<ReturnType<typeof getSystemStatus>>>()
    mockedSystem.mockReturnValue(pending.promise)
    const store = useOverviewStore()

    void store.load()
    void store.load()
    void store.load()
    await drain()

    expect(mockedSystem).toHaveBeenCalledTimes(1)
    expect(mockedTasks).toHaveBeenCalledTimes(1)

    pending.settle(systemStatus())
    await drain()
  })
})

describe('a batch that was superseded', () => {
  it('cannot write its answers over a newer one', async () => {
    const stale = deferred<Awaited<ReturnType<typeof listTasks>>>()
    mockedTasks.mockReturnValueOnce(stale.promise)
    const store = useOverviewStore()
    void store.load()
    await drain()

    store.abandon()
    mockedTasks.mockResolvedValue({ items: [task({ task_id: 'new' })], total: 2 })
    await store.load()

    stale.settle({ items: [task({ task_id: 'old' })], total: 999 })
    await drain()

    expect(store.taskTotal).toBe(2)
    expect(store.recentTasks.map((one) => one.task_id)).toEqual(['new'])
  })

  it('writes nothing at all once the page is gone', async () => {
    const stale = deferred<Awaited<ReturnType<typeof listTasks>>>()
    mockedTasks.mockReturnValue(stale.promise)
    const store = useOverviewStore()
    void store.load()
    await drain()

    store.abandon()
    stale.settle({ items: [task({ task_id: 'late' })], total: 5 })
    await drain()

    expect(store.taskTotal).toBeNull()
    expect(store.recentTasks).toEqual([])
    expect(store.loading).toBe(false)
  })

  it('records no error from a batch nobody is waiting for', async () => {
    const stale = deferred<Awaited<ReturnType<typeof listTasks>>>()
    mockedTasks.mockReturnValue(stale.promise)
    const store = useOverviewStore()
    void store.load()
    await drain()

    store.abandon()
    stale.fail(offline)
    await drain()

    expect(store.tasksError).toBeNull()
  })
})

describe('the overview over time', () => {
  it('never starts a timer', async () => {
    //
    // The task centre already watches work in progress and the creators screen
    // owns live probing. This is a snapshot of what those already know.
    //
    vi.useFakeTimers()
    const store = useOverviewStore()
    await store.load()

    await vi.advanceTimersByTimeAsync(10_000)
    await vi.advanceTimersByTimeAsync(60_000)
    await vi.advanceTimersByTimeAsync(600_000)

    expect(mockedSystem).toHaveBeenCalledTimes(1)
    expect(mockedTasks).toHaveBeenCalledTimes(1)
  })
})
