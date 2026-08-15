import { createPinia, setActivePinia } from 'pinia'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import { ApiError } from '../../src/api/client'
import { listHistoryOwners } from '../../src/api/history'
import { useCreatorsStore } from '../../src/stores/creators'
import type { HistoryOwner, HistoryOwnerPage } from '../../src/types/history'

vi.mock('../../src/api/history', () => ({
  listHistoryOwners: vi.fn(),
  listOwnerSessions: vi.fn(),
  submitLiveProbe: vi.fn(),
  getLiveProbe: vi.fn(),
}))

const mockedList = vi.mocked(listHistoryOwners)

export function owner(overrides: Partial<HistoryOwner> = {}): HistoryOwner {
  return {
    owner_user_id: '58859666123',
    sec_user_id: 'MS4wLjABAAAAGZkW5n1EHZD_TFyQ-QiaISBPemtKFxVVdhLSeoXhh-U',
    nickname: '主播',
    live_share_url: 'https://v.douyin.com/abc/',
    directory_name: '主播',
    user_status: '正常',
    actived_count: 12,
    score: 80,
    favorite: true,
    last_live_status: 4,
    last_checked_at: '2026-08-15T09:30:15.250',
    last_room_id: '7123',
    ...overrides,
  }
}

export function page(items: HistoryOwner[], overrides: Partial<HistoryOwnerPage> = {}) {
  return {
    total: items.length,
    page: 1,
    page_size: 20,
    items,
    ...overrides,
  }
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

/** The filters the most recent call was made with. */
function lastFilters() {
  const call = mockedList.mock.calls.at(-1)
  if (!call) {
    throw new Error('listHistoryOwners was never called')
  }
  return call[0] ?? {}
}

beforeEach(() => {
  setActivePinia(createPinia())
  mockedList.mockReset()
  mockedList.mockResolvedValue(page([]))
})

describe('initial state', () => {
  it('has read nothing until it is asked to', () => {
    const store = useCreatorsStore()

    expect(store.owners).toEqual([])
    expect(store.ownerTotal).toBe(0)
    expect(store.page).toBe(1)
    expect(store.selectedOwnerUserId).toBeNull()
    expect(store.ownersError).toBeNull()
    expect(store.hasLoadedOwners).toBe(false)
    expect(mockedList).not.toHaveBeenCalled()
  })

  it('starts unfiltered', () => {
    const store = useCreatorsStore()

    expect(store.filters.q).toBeUndefined()
    expect(store.filters.favorite).toBeUndefined()
    expect(store.filters.sort).toBe('last_checked_at')
    expect(store.filters.order).toBe('desc')
  })
})

describe('reading the directory', () => {
  it('asks with the current page and sort', async () => {
    const store = useCreatorsStore()

    await store.loadOwners()

    expect(lastFilters().page).toBe(1)
    expect(lastFilters().sort).toBe('last_checked_at')
    expect(lastFilters().order).toBe('desc')
  })

  it('keeps the page the server answered with', async () => {
    mockedList.mockResolvedValue(page([owner()], { total: 73, page: 2, page_size: 20 }))
    const store = useCreatorsStore()

    await store.loadOwners()

    expect(store.ownerTotal).toBe(73)
    expect(store.page).toBe(2)
    expect(store.pageSize).toBe(20)
    expect(store.pageCount).toBe(4)
  })

  it('keeps the order the server sent', async () => {
    const server = [
      owner({ owner_user_id: 'C' }),
      owner({ owner_user_id: 'A' }),
      owner({ owner_user_id: 'B' }),
    ]
    mockedList.mockResolvedValue(page(server))
    const store = useCreatorsStore()

    await store.loadOwners()

    expect(store.owners.map((one) => one.owner_user_id)).toEqual(['C', 'A', 'B'])
  })

  it('records that a read has succeeded', async () => {
    const store = useCreatorsStore()

    await store.loadOwners()

    expect(store.hasLoadedOwners).toBe(true)
  })
})

describe('filters', () => {
  it('sends every filter the backend understands', async () => {
    const store = useCreatorsStore()

    await store.setFilters({
      q: '主播',
      favorite: true,
      score_min: 10,
      score_max: 90,
      last_live_within: '24h',
      user_status: '正常',
      sort: 'score',
      order: 'asc',
    })

    const filters = lastFilters()
    expect(filters.q).toBe('主播')
    expect(filters.favorite).toBe(true)
    expect(filters.score_min).toBe(10)
    expect(filters.score_max).toBe(90)
    expect(filters.last_live_within).toBe('24h')
    expect(filters.user_status).toBe('正常')
    expect(filters.sort).toBe('score')
    expect(filters.order).toBe('asc')
  })

  it('returns to the first page when the filters change', async () => {
    //
    // Page 3 of one filter has nothing to do with page 3 of another, and
    // landing on an empty page would look like "no results" for a filter that
    // has plenty.
    //
    mockedList.mockResolvedValue(page([owner()], { page: 3, total: 60 }))
    const store = useCreatorsStore()
    await store.goToPage(3)

    await store.setFilters({ q: '新的' })

    expect(lastFilters().page).toBe(1)
  })

  it('clears a filter rather than sending an empty value', async () => {
    const store = useCreatorsStore()
    await store.setFilters({ q: '主播' })

    await store.setFilters({ q: undefined })

    expect(lastFilters().q).toBeUndefined()
  })

  it('never filters the list again in the browser', async () => {
    //
    // The server applied the filters and its total is bound to them; filtering
    // again here would give the count and the rows two different meanings.
    //
    mockedList.mockResolvedValue(
      page([owner({ owner_user_id: 'A', favorite: true }), owner({ owner_user_id: 'B', favorite: false })]),
    )
    const store = useCreatorsStore()

    await store.setFilters({ favorite: true })

    expect(store.owners).toHaveLength(2)
  })
})

describe('pagination', () => {
  it('asks for the page it was sent to', async () => {
    const store = useCreatorsStore()

    await store.goToPage(4)

    expect(lastFilters().page).toBe(4)
  })

  it('refuses to go below the first page', async () => {
    const store = useCreatorsStore()

    await store.goToPage(0)

    expect(lastFilters().page).toBe(1)
  })

  it('knows whether there is a page either side', async () => {
    mockedList.mockResolvedValue(page([owner()], { total: 73, page: 2, page_size: 20 }))
    const store = useCreatorsStore()

    await store.loadOwners()

    expect(store.hasPreviousPage).toBe(true)
    expect(store.hasNextPage).toBe(true)
  })

  it('knows when it is at either end', async () => {
    mockedList.mockResolvedValue(page([owner()], { total: 10, page: 1, page_size: 20 }))
    const store = useCreatorsStore()

    await store.loadOwners()

    expect(store.hasPreviousPage).toBe(false)
    expect(store.hasNextPage).toBe(false)
    expect(store.pageCount).toBe(1)
  })
})

describe('a stale answer for filters nobody is using any more', () => {
  it('cannot overwrite the list the current filters produced', async () => {
    //
    // The same race the task centre has: a slow request for the previous filter
    // landing after a fast one for the new filter would put the old rows back
    // under the new filter's label.
    //
    const slow = deferred<HistoryOwnerPage>()
    const fast = deferred<HistoryOwnerPage>()
    mockedList.mockReturnValueOnce(slow.promise).mockReturnValueOnce(fast.promise)
    const store = useCreatorsStore()

    const first = store.setFilters({ q: 'A' })
    const second = store.setFilters({ q: 'B' })

    fast.settle(page([owner({ owner_user_id: 'FROM-B' })], { total: 1 }))
    await second
    await drain()

    slow.settle(page([owner({ owner_user_id: 'FROM-A' })], { total: 99 }))
    await first
    await drain()

    expect(store.filters.q).toBe('B')
    expect(store.owners.map((one) => one.owner_user_id)).toEqual(['FROM-B'])
    expect(store.ownerTotal).toBe(1)
  })

  it('cannot report an error against filters that moved on', async () => {
    const slow = deferred<HistoryOwnerPage>()
    const fast = deferred<HistoryOwnerPage>()
    mockedList.mockReturnValueOnce(slow.promise).mockReturnValueOnce(fast.promise)
    const store = useCreatorsStore()

    const first = store.setFilters({ q: 'A' })
    const second = store.setFilters({ q: 'B' })

    fast.settle(page([]))
    await second
    await drain()
    slow.fail(new ApiError({ kind: 'network', status: null, code: null, message: 'gone' }))
    await first
    await drain()

    expect(store.ownersError).toBeNull()
  })

  it('cannot move the pagination either', async () => {
    const slow = deferred<HistoryOwnerPage>()
    const fast = deferred<HistoryOwnerPage>()
    mockedList.mockReturnValueOnce(slow.promise).mockReturnValueOnce(fast.promise)
    const store = useCreatorsStore()

    const first = store.goToPage(2)
    const second = store.goToPage(5)

    fast.settle(page([], { page: 5, total: 200 }))
    await second
    await drain()
    slow.settle(page([], { page: 2, total: 40 }))
    await first
    await drain()

    expect(store.page).toBe(5)
    expect(store.ownerTotal).toBe(200)
  })

  it('aborts the request it is abandoning', async () => {
    const pending = deferred<HistoryOwnerPage>()
    mockedList.mockReturnValueOnce(pending.promise).mockResolvedValue(page([]))
    const store = useCreatorsStore()

    void store.setFilters({ q: 'A' })
    await drain()
    const [, firstSignal] = mockedList.mock.calls[0]

    await store.setFilters({ q: 'B' })

    expect(firstSignal?.aborted).toBe(true)
  })
})

describe('when the directory cannot be read', () => {
  const offline = new ApiError({
    kind: 'network',
    status: null,
    code: null,
    message: 'Failed to fetch',
  })

  it('keeps what it last saw', async () => {
    //
    // A failed read is not evidence that there are no accounts.
    //
    mockedList.mockResolvedValueOnce(page([owner({ owner_user_id: 'A' })], { total: 1 }))
    const store = useCreatorsStore()
    await store.loadOwners()

    mockedList.mockRejectedValue(offline)
    await store.loadOwners()

    expect(store.owners.map((one) => one.owner_user_id)).toEqual(['A'])
    expect(store.ownerTotal).toBe(1)
    expect(store.ownersError).toContain('Failed to fetch')
  })

  it('does not claim the directory is empty on a first failure', async () => {
    mockedList.mockRejectedValue(offline)
    const store = useCreatorsStore()

    await store.loadOwners()

    expect(store.hasLoadedOwners).toBe(false)
    expect(store.owners).toEqual([])
    expect(store.ownersError).toBeTruthy()
  })
})

describe('selecting an account', () => {
  const listed = [owner({ owner_user_id: 'A' }), owner({ owner_user_id: 'B' })]

  beforeEach(() => {
    mockedList.mockResolvedValue(page(listed))
  })

  it('reads the selected account out of the list rather than copying it', async () => {
    const store = useCreatorsStore()
    await store.loadOwners()

    store.selectOwner('B')

    expect(store.selectedOwner?.owner_user_id).toBe('B')
  })

  it('follows the list as it is re-read', async () => {
    const store = useCreatorsStore()
    await store.loadOwners()
    store.selectOwner('B')

    mockedList.mockResolvedValue(
      page([owner({ owner_user_id: 'A' }), owner({ owner_user_id: 'B', score: 5 })]),
    )
    await store.loadOwners()

    expect(store.selectedOwner?.score).toBe(5)
  })

  it('forgets a selection the page no longer contains', async () => {
    const store = useCreatorsStore()
    await store.loadOwners()
    store.selectOwner('B')

    mockedList.mockResolvedValue(page([owner({ owner_user_id: 'A' })]))
    await store.loadOwners()

    expect(store.selectedOwnerUserId).toBeNull()
    expect(store.selectedOwner).toBeNull()
  })
})
