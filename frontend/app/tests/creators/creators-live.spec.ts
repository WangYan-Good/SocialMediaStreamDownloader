import { createPinia, setActivePinia } from 'pinia'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import { ApiError } from '../../src/api/client'
import {
  getLiveProbe,
  listHistoryOwners,
  listOwnerSessions,
  submitLiveProbe,
} from '../../src/api/history'
import { PROBE_POLL_INTERVAL_MS, useCreatorsStore } from '../../src/stores/creators'
import type { LiveProbeBatch, LiveProbeItem, LiveSession } from '../../src/types/history'

vi.mock('../../src/api/history', () => ({
  listHistoryOwners: vi.fn(async () => ({ total: 0, page: 1, page_size: 20, items: [] })),
  listOwnerSessions: vi.fn(),
  submitLiveProbe: vi.fn(),
  getLiveProbe: vi.fn(),
}))

vi.mock('../../src/api/owners', () => ({
  readOwner: vi.fn(),
  readOwnerPosts: vi.fn(),
  startOwnerSelectedDownload: vi.fn(),
  startOwnerAllDownload: vi.fn(),
}))

const mockedSessions = vi.mocked(listOwnerSessions)
const mockedSubmit = vi.mocked(submitLiveProbe)
const mockedRead = vi.mocked(getLiveProbe)

function session(overrides: Partial<LiveSession> = {}): LiveSession {
  return {
    observed_at: '2026-08-15T09:30:15.250',
    room_id: '7123',
    title: '直播中',
    room_status: 4,
    start_time: '2026-08-15T08:00:00.000',
    finish_time: '2026-08-15T09:30:00.000',
    status_code: 0,
    ...overrides,
  }
}

function probeItem(overrides: Partial<LiveProbeItem> = {}): LiveProbeItem {
  return {
    owner_user_id: '1',
    state: 'pending',
    nickname: '主播',
    live_share_url: 'https://v.douyin.com/abc/',
    ...overrides,
  }
}

function batch(overrides: Partial<LiveProbeBatch> = {}): LiveProbeBatch {
  return { batch_id: 'B', done: false, items: [probeItem()], ...overrides }
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
  mockedSessions.mockReset()
  mockedSubmit.mockReset()
  mockedRead.mockReset()
  mockedSessions.mockResolvedValue({ items: [] })
  vi.useFakeTimers()
})

afterEach(() => {
  vi.useRealTimers()
})

describe('live sessions', () => {
  it('are not read until they are asked for', () => {
    useCreatorsStore()

    expect(mockedSessions).not.toHaveBeenCalled()
  })

  it('read one account, with a limit', async () => {
    const store = useCreatorsStore()

    await store.loadSessions('58859666123')

    expect(mockedSessions).toHaveBeenCalledTimes(1)
    const [ownerUserId, options] = mockedSessions.mock.calls[0]
    expect(ownerUserId).toBe('58859666123')
    expect(options?.limit).toBe(20)
  })

  it('keep what the server sent', async () => {
    mockedSessions.mockResolvedValue({
      items: [session({ room_id: 'A' }), session({ room_id: 'B' })],
    })
    const store = useCreatorsStore()

    await store.loadSessions('1')

    expect(store.sessions.map((one) => one.room_id)).toEqual(['A', 'B'])
    expect(store.sessionsOwnerUserId).toBe('1')
  })

  it('cannot be polluted by the previous account answering late', async () => {
    //
    // Open A, change your mind, open B. A's answer is about a panel nobody is
    // looking at any more.
    //
    const slow = deferred<{ items: LiveSession[] }>()
    const fast = deferred<{ items: LiveSession[] }>()
    mockedSessions.mockReturnValueOnce(slow.promise).mockReturnValueOnce(fast.promise)
    const store = useCreatorsStore()

    const first = store.loadSessions('A')
    const second = store.loadSessions('B')

    fast.settle({ items: [session({ room_id: 'FROM-B' })] })
    await second
    await drain()

    slow.settle({ items: [session({ room_id: 'FROM-A' })] })
    await first
    await drain()

    expect(store.sessionsOwnerUserId).toBe('B')
    expect(store.sessions.map((one) => one.room_id)).toEqual(['FROM-B'])
  })

  it('keep the last ones when a read fails', async () => {
    mockedSessions.mockResolvedValueOnce({ items: [session({ room_id: 'A' })] })
    const store = useCreatorsStore()
    await store.loadSessions('1')

    mockedSessions.mockRejectedValue(
      new ApiError({ kind: 'network', status: null, code: null, message: 'offline' }),
    )
    await store.loadSessions('1')

    expect(store.sessions.map((one) => one.room_id)).toEqual(['A'])
    expect(store.sessionsError).toContain('offline')
  })
})

describe('the probe interval', () => {
  it('is a named constant', () => {
    expect(typeof PROBE_POLL_INTERVAL_MS).toBe('number')
    expect(PROBE_POLL_INTERVAL_MS).toBeGreaterThanOrEqual(1000)
    expect(PROBE_POLL_INTERVAL_MS).toBeLessThanOrEqual(5000)
  })
})

describe('submitting a probe', () => {
  it('sends exactly the ids it was given', async () => {
    mockedSubmit.mockResolvedValue(batch({ done: true, items: [] }))
    const store = useCreatorsStore()

    await store.probeOwners(['1', '2'])

    expect(mockedSubmit).toHaveBeenCalledWith(['1', '2'])
  })

  it('refuses an empty request', async () => {
    //
    // The legacy page treated "nothing ticked" as "check the whole page". A
    // probe is one real platform request per account, so an accidental empty
    // click must not become a page-wide sweep.
    //
    const store = useCreatorsStore()

    await store.probeOwners([])

    expect(mockedSubmit).not.toHaveBeenCalled()
  })

  it('keeps the items by account', async () => {
    mockedSubmit.mockResolvedValue(
      batch({
        done: true,
        items: [
          probeItem({ owner_user_id: '1', state: 'living' }),
          probeItem({ owner_user_id: '2', state: 'offline' }),
        ],
      }),
    )
    const store = useCreatorsStore()

    await store.probeOwners(['1', '2'])

    expect(store.probeItemFor('1')?.state).toBe('living')
    expect(store.probeItemFor('2')?.state).toBe('offline')
  })

  it('keeps the task id the batch was mirrored to', async () => {
    mockedSubmit.mockResolvedValue(batch({ done: true, items: [], task_id: 'T-1' }))
    const store = useCreatorsStore()

    await store.probeOwners(['1'])

    expect(store.probeTaskId).toBe('T-1')
  })
})

describe('a batch that is already finished', () => {
  it('is not polled at all', async () => {
    //
    // Everything answered from the recent-status cache. There is nothing left
    // to wait for, and a poll would only ask the server to repeat itself.
    //
    mockedSubmit.mockResolvedValue(
      batch({ done: true, items: [probeItem({ state: 'offline', cached: true })] }),
    )
    const store = useCreatorsStore()

    await store.probeOwners(['1'])

    expect(store.probePolling).toBe(false)
    await vi.advanceTimersByTimeAsync(PROBE_POLL_INTERVAL_MS * 5)
    expect(mockedRead).not.toHaveBeenCalled()
  })
})

describe('a batch that is still running', () => {
  it('is read again until it is done', async () => {
    mockedSubmit.mockResolvedValue(batch({ done: false }))
    mockedRead.mockResolvedValue(batch({ done: false }))
    const store = useCreatorsStore()

    await store.probeOwners(['1'])
    expect(store.probePolling).toBe(true)

    await vi.advanceTimersByTimeAsync(PROBE_POLL_INTERVAL_MS)
    expect(mockedRead).toHaveBeenCalledTimes(1)

    await vi.advanceTimersByTimeAsync(PROBE_POLL_INTERVAL_MS)
    expect(mockedRead).toHaveBeenCalledTimes(2)
  })

  it('stops the moment the batch reports done', async () => {
    mockedSubmit.mockResolvedValue(batch({ done: false }))
    mockedRead.mockResolvedValue(
      batch({ done: true, items: [probeItem({ state: 'living' })] }),
    )
    const store = useCreatorsStore()
    await store.probeOwners(['1'])

    await vi.advanceTimersByTimeAsync(PROBE_POLL_INTERVAL_MS)

    expect(store.probePolling).toBe(false)
    const calls = mockedRead.mock.calls.length
    await vi.advanceTimersByTimeAsync(PROBE_POLL_INTERVAL_MS * 5)
    expect(mockedRead).toHaveBeenCalledTimes(calls)
  })

  it('never has two reads in flight at once', async () => {
    const pending = deferred<LiveProbeBatch>()
    mockedSubmit.mockResolvedValue(batch({ done: false }))
    mockedRead.mockReturnValue(pending.promise)
    const store = useCreatorsStore()
    await store.probeOwners(['1'])

    await vi.advanceTimersByTimeAsync(PROBE_POLL_INTERVAL_MS)
    expect(mockedRead).toHaveBeenCalledTimes(1)

    await vi.advanceTimersByTimeAsync(PROBE_POLL_INTERVAL_MS * 4)
    expect(mockedRead).toHaveBeenCalledTimes(1)

    pending.settle(batch({ done: false }))
    await drain()
    await vi.advanceTimersByTimeAsync(PROBE_POLL_INTERVAL_MS)
    expect(mockedRead).toHaveBeenCalledTimes(2)
  })

  it('updates the items as they arrive', async () => {
    mockedSubmit.mockResolvedValue(
      batch({ done: false, items: [probeItem({ owner_user_id: '1', state: 'running' })] }),
    )
    mockedRead.mockResolvedValue(
      batch({ done: true, items: [probeItem({ owner_user_id: '1', state: 'living' })] }),
    )
    const store = useCreatorsStore()
    await store.probeOwners(['1'])
    expect(store.probeItemFor('1')?.state).toBe('running')

    await vi.advanceTimersByTimeAsync(PROBE_POLL_INTERVAL_MS)

    expect(store.probeItemFor('1')?.state).toBe('living')
  })
})

describe('a probe read that fails', () => {
  const offline = new ApiError({
    kind: 'network',
    status: null,
    code: null,
    message: 'Failed to fetch',
  })

  async function probingThenOffline() {
    mockedSubmit.mockResolvedValue(
      batch({ done: false, items: [probeItem({ owner_user_id: '1', state: 'running' })] }),
    )
    mockedRead.mockRejectedValue(offline)
    const store = useCreatorsStore()
    await store.probeOwners(['1'])
    await vi.advanceTimersByTimeAsync(PROBE_POLL_INTERVAL_MS)
    await drain()
    return store
  }

  it('is not read as "not broadcasting"', async () => {
    //
    // The distinction that matters most here. A failed read says the browser
    // could not find out; turning that into `offline` would tell the user
    // nobody is streaming on no evidence at all - and hide a recording they
    // could have started.
    //
    const store = await probingThenOffline()

    expect(store.probeItemFor('1')?.state).toBe('running')
    expect(store.probeError).toBeTruthy()
  })

  it('pauses rather than retrying on a timer', async () => {
    const store = await probingThenOffline()
    const afterFailure = mockedRead.mock.calls.length

    await vi.advanceTimersByTimeAsync(PROBE_POLL_INTERVAL_MS * 5)

    expect(mockedRead).toHaveBeenCalledTimes(afterFailure)
    expect(store.probePolling).toBe(false)
  })

  it('reads the same batch again when retried', async () => {
    const store = await probingThenOffline()
    mockedRead.mockResolvedValue(batch({ done: true }))
    const before = mockedRead.mock.calls.length

    await store.retryProbe()

    expect(mockedRead.mock.calls.length).toBe(before + 1)
    expect(mockedRead.mock.calls.at(-1)?.[0]).toBe('B')
    expect(store.probeError).toBeNull()
  })
})

describe('leaving the screen', () => {
  it('stops the probe loop', async () => {
    mockedSubmit.mockResolvedValue(batch({ done: false }))
    mockedRead.mockResolvedValue(batch({ done: false }))
    const store = useCreatorsStore()
    await store.probeOwners(['1'])

    store.stopProbePolling()
    const before = mockedRead.mock.calls.length

    await vi.advanceTimersByTimeAsync(PROBE_POLL_INTERVAL_MS * 5)

    expect(mockedRead).toHaveBeenCalledTimes(before)
    expect(store.probePolling).toBe(false)
  })

  it('schedules nothing when a read lands after it was stopped', async () => {
    const pending = deferred<LiveProbeBatch>()
    mockedSubmit.mockResolvedValue(batch({ done: false }))
    mockedRead.mockReturnValue(pending.promise)
    const store = useCreatorsStore()
    await store.probeOwners(['1'])
    await vi.advanceTimersByTimeAsync(PROBE_POLL_INTERVAL_MS)
    expect(mockedRead).toHaveBeenCalledTimes(1)

    store.stopProbePolling()
    pending.settle(batch({ done: false, items: [probeItem({ state: 'living' })] }))
    await drain()

    await vi.advanceTimersByTimeAsync(PROBE_POLL_INTERVAL_MS * 5)

    expect(mockedRead).toHaveBeenCalledTimes(1)
  })

  it('writes nothing from a read that lands after it was stopped', async () => {
    const pending = deferred<LiveProbeBatch>()
    mockedSubmit.mockResolvedValue(
      batch({ done: false, items: [probeItem({ owner_user_id: '1', state: 'running' })] }),
    )
    mockedRead.mockReturnValue(pending.promise)
    const store = useCreatorsStore()
    await store.probeOwners(['1'])
    await vi.advanceTimersByTimeAsync(PROBE_POLL_INTERVAL_MS)

    store.stopProbePolling()
    pending.settle(
      batch({ done: true, items: [probeItem({ owner_user_id: '1', state: 'living' })] }),
    )
    await drain()

    expect(store.probeItemFor('1')?.state).toBe('running')
  })
})

describe('a second probe replaces the first', () => {
  it('abandons the previous batch rather than polling both', async () => {
    mockedSubmit
      .mockResolvedValueOnce(batch({ batch_id: 'FIRST', done: false }))
      .mockResolvedValueOnce(batch({ batch_id: 'SECOND', done: false }))
    mockedRead.mockResolvedValue(batch({ batch_id: 'SECOND', done: false }))
    const store = useCreatorsStore()

    await store.probeOwners(['1'])
    await store.probeOwners(['2'])

    await vi.advanceTimersByTimeAsync(PROBE_POLL_INTERVAL_MS)

    expect(store.probeBatchId).toBe('SECOND')
    for (const call of mockedRead.mock.calls) {
      expect(call[0]).toBe('SECOND')
    }
  })
})

describe('the directory after a probe finishes', () => {
  //
  // A probe writes last_live_status and last_checked_at on the server. Without
  // a re-read the row beside the result keeps showing what it said before the
  // check, which is not a lie - one says "上次", the other "本次检查" - but it
  // does leave two numbers on screen that disagree for no visible reason.
  //
  // Once, and only for the page already on screen. Not a poller.
  //
  const owners = vi.mocked(listHistoryOwners)

  beforeEach(() => {
    owners.mockClear()
    owners.mockResolvedValue({ total: 0, page: 1, page_size: 20, items: [] })
  })

  it('is re-read once when a batch finishes by polling', async () => {
    mockedSubmit.mockResolvedValue(batch({ done: false }))
    mockedRead.mockResolvedValue(batch({ done: true }))
    const store = useCreatorsStore()
    await store.probeOwners(['1'])
    expect(owners).not.toHaveBeenCalled()

    await vi.advanceTimersByTimeAsync(PROBE_POLL_INTERVAL_MS)
    await drain()

    expect(owners).toHaveBeenCalledTimes(1)
  })

  it('is re-read once when the batch was answered from the cache', async () => {
    mockedSubmit.mockResolvedValue(batch({ done: true }))
    const store = useCreatorsStore()

    await store.probeOwners(['1'])
    await drain()

    expect(owners).toHaveBeenCalledTimes(1)
  })

  it('asks for the page and filters already on screen', async () => {
    //
    // Not page one. Sending the user back to the top of the directory because a
    // probe finished would lose their place for no reason they asked for.
    //
    owners.mockResolvedValue({ total: 100, page: 3, page_size: 20, items: [] })
    const store = useCreatorsStore()
    await store.setFilters({ favorite: true })
    await store.goToPage(3)
    owners.mockClear()

    mockedSubmit.mockResolvedValue(batch({ done: true }))
    await store.probeOwners(['1'])
    await drain()

    expect(owners).toHaveBeenCalledTimes(1)
    expect(owners.mock.calls[0][0]).toMatchObject({ page: 3, favorite: true })
  })

  it('does not keep re-reading afterwards', async () => {
    mockedSubmit.mockResolvedValue(batch({ done: true }))
    const store = useCreatorsStore()
    await store.probeOwners(['1'])
    await drain()

    await vi.advanceTimersByTimeAsync(PROBE_POLL_INTERVAL_MS * 10)
    await drain()

    expect(owners).toHaveBeenCalledTimes(1)
  })

  it('never turns a successful probe into a failed one', async () => {
    //
    // The probe answered. That the directory could not be re-read afterwards is
    // a separate failure and belongs to the directory, not to the check the
    // user actually asked for.
    //
    owners.mockRejectedValue(
      new ApiError({ kind: 'network', status: null, code: null, message: 'offline' }),
    )
    mockedSubmit.mockResolvedValue(
      batch({ done: true, items: [probeItem({ owner_user_id: '1', state: 'living' })] }),
    )
    const store = useCreatorsStore()

    await store.probeOwners(['1'])
    await drain()

    expect(store.probeError).toBeNull()
    expect(store.probeItemFor('1')?.state).toBe('living')
    expect(store.ownersError).not.toBeNull()
  })

  it('cannot land on filters the user has since moved to', async () => {
    //
    // The refresh is an ordinary directory read and goes through the same
    // generation guard: one that started under the old filters must not write
    // its answer under the new ones.
    //
    const stale = deferred<{ total: number; page: number; page_size: number; items: [] }>()
    owners.mockReturnValueOnce(stale.promise)
    mockedSubmit.mockResolvedValue(batch({ done: true }))
    const store = useCreatorsStore()
    //
    // Deliberately not awaited: the refresh is part of this call, so awaiting it
    // here would wait on the very answer the test is holding back.
    //
    const probing = store.probeOwners(['1'])
    await drain()

    owners.mockResolvedValue({ total: 7, page: 1, page_size: 20, items: [] })
    await store.setFilters({ q: '新的' })

    stale.settle({ total: 999, page: 9, page_size: 20, items: [] })
    await probing
    await drain()

    expect(store.ownerTotal).toBe(7)
    expect(store.page).toBe(1)
  })
})
