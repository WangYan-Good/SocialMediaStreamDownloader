import { createPinia, setActivePinia } from 'pinia'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import { ApiError } from '../../src/api/client'
import { readOwnerPosts } from '../../src/api/owners'
import { useCreatorsStore } from '../../src/stores/creators'
import type { OwnerPost, OwnerPostPage, OwnerRead } from '../../src/types/owner'

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

const mockedPosts = vi.mocked(readOwnerPosts)

const SEC_UID = 'MS4wLjABAAAAGZkW5n1EHZD_TFyQ-QiaISBPemtKFxVVdhLSeoXhh-U'

function post(awemeId: string, overrides: Partial<OwnerPost> = {}): OwnerPost {
  return {
    aweme_id: awemeId,
    desc: `作品 ${awemeId}`,
    create_time: 1712484087,
    cover_url: 'https://p3.douyinpic.com/cover.jpeg',
    duration: 15000,
    aweme_type: 'video',
    digg_count: 10,
    comment_count: 2,
    downloaded: false,
    saved_count: null,
    media_count: null,
    ...overrides,
  }
}

function postPage(ids: string[], next = 0, more = false): OwnerPostPage {
  return { posts: ids.map((id) => post(id)), next_cursor: next, has_more: more }
}

function ownerRead(overrides: Partial<OwnerRead> = {}): OwnerRead {
  return {
    sec_user_id: SEC_UID,
    owner: null,
    owner_message: null,
    credential: { expires_in_days: 30 },
    posts: [post('1'), post('2')],
    next_cursor: 1712484087000,
    has_more: true,
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

beforeEach(() => {
  setActivePinia(createPinia())
  mockedPosts.mockReset()
  mockedPosts.mockResolvedValue(postPage([]))
})

describe('opening posts from a history account', () => {
  it('reads the first page by cursor zero', async () => {
    const store = useCreatorsStore()

    await store.openPostsForOwner(SEC_UID)

    expect(mockedPosts).toHaveBeenCalledTimes(1)
    const [secUserId, cursor] = mockedPosts.mock.calls[0]
    expect(secUserId).toBe(SEC_UID)
    expect(cursor).toBe(0)
  })

  it('adopts the page it was answered with', async () => {
    mockedPosts.mockResolvedValue(postPage(['1', '2', '3'], 999, true))
    const store = useCreatorsStore()

    await store.openPostsForOwner(SEC_UID)

    expect(store.posts.map((one) => one.aweme_id)).toEqual(['1', '2', '3'])
    expect(store.nextCursor).toBe(999)
    expect(store.hasMorePosts).toBe(true)
    expect(store.postsSecUserId).toBe(SEC_UID)
  })
})

describe('opening posts from a profile that was just read', () => {
  it('never asks for the first page again', async () => {
    //
    // `/api/owner` already paid for that page - a real platform request with a
    // real cookie. Asking again would spend a second one, and the two answers
    // could differ, so the same screen would show a different first page
    // depending on which arrived last.
    //
    const store = useCreatorsStore()

    store.adoptPostsFromOwnerRead(ownerRead())

    expect(mockedPosts).not.toHaveBeenCalled()
  })

  it('takes the posts, the cursor and the flag from that read', async () => {
    const store = useCreatorsStore()

    store.adoptPostsFromOwnerRead(
      ownerRead({ posts: [post('a'), post('b')], next_cursor: 4242, has_more: true }),
    )

    expect(store.posts.map((one) => one.aweme_id)).toEqual(['a', 'b'])
    expect(store.nextCursor).toBe(4242)
    expect(store.hasMorePosts).toBe(true)
  })

  it('takes the paging identity from the owner read, not from anywhere earlier', async () => {
    //
    // Once the owner api has answered, its `sec_user_id` is the contract for
    // every later page. A receipt from the resolve step is about the link the
    // user pasted, and is not the thing /owner/posts is keyed on.
    //
    const store = useCreatorsStore()

    store.adoptPostsFromOwnerRead(ownerRead({ sec_user_id: 'MS4w-FROM-OWNER-API' }))
    await store.loadMorePosts()

    expect(mockedPosts.mock.calls[0][0]).toBe('MS4w-FROM-OWNER-API')
  })
})

describe('loading more', () => {
  it('uses the cursor the last page answered with', async () => {
    const store = useCreatorsStore()
    store.adoptPostsFromOwnerRead(ownerRead({ next_cursor: 555, has_more: true }))

    mockedPosts.mockResolvedValue(postPage(['3'], 777, false))
    await store.loadMorePosts()

    expect(mockedPosts.mock.calls[0][1]).toBe(555)
    expect(store.nextCursor).toBe(777)
    expect(store.hasMorePosts).toBe(false)
  })

  it('works the same whichever entry produced the first page', async () => {
    const store = useCreatorsStore()
    mockedPosts.mockResolvedValueOnce(postPage(['1'], 111, true))
    await store.openPostsForOwner(SEC_UID)

    mockedPosts.mockResolvedValueOnce(postPage(['2'], 222, false))
    await store.loadMorePosts()

    expect(mockedPosts.mock.calls[1]).toEqual([SEC_UID, 111, expect.anything()])
    expect(store.posts.map((one) => one.aweme_id)).toEqual(['1', '2'])
  })

  it('refuses when there is no more to load', async () => {
    const store = useCreatorsStore()
    store.adoptPostsFromOwnerRead(ownerRead({ has_more: false }))

    await store.loadMorePosts()

    expect(mockedPosts).not.toHaveBeenCalled()
  })

  it('appends rather than replacing', async () => {
    const store = useCreatorsStore()
    store.adoptPostsFromOwnerRead(ownerRead({ posts: [post('1')], has_more: true }))

    mockedPosts.mockResolvedValue(postPage(['2', '3'], 0, false))
    await store.loadMorePosts()

    expect(store.posts.map((one) => one.aweme_id)).toEqual(['1', '2', '3'])
  })
})

describe('pages that overlap', () => {
  it('keeps one row per post, in the order first seen', async () => {
    //
    // Platform paging repeats rows across page boundaries often enough that a
    // list without this shows the same post twice.
    //
    const store = useCreatorsStore()
    store.adoptPostsFromOwnerRead(
      ownerRead({ posts: [post('1'), post('2'), post('3')], has_more: true }),
    )

    mockedPosts.mockResolvedValue(postPage(['3', '4', '5'], 0, false))
    await store.loadMorePosts()

    expect(store.posts.map((one) => one.aweme_id)).toEqual(['1', '2', '3', '4', '5'])
    expect(store.loadedPostCount).toBe(5)
  })

  it('still takes the cursor from the server rather than inferring one', async () => {
    //
    // Deduplication is a display decision. Paging is the platform's, and
    // guessing a cursor from what was kept would eventually skip a page.
    //
    const store = useCreatorsStore()
    store.adoptPostsFromOwnerRead(ownerRead({ posts: [post('1')], has_more: true }))

    mockedPosts.mockResolvedValue(postPage(['1', '2'], 8888, true))
    await store.loadMorePosts()

    expect(store.nextCursor).toBe(8888)
    expect(store.hasMorePosts).toBe(true)
  })
})

describe('switching to another creator', () => {
  it('clears everything the previous one left behind', async () => {
    const store = useCreatorsStore()
    store.adoptPostsFromOwnerRead(ownerRead({ posts: [post('1'), post('2')] }))
    store.togglePostSelection('1')
    expect(store.selectedAwemeIds).toEqual(['1'])

    mockedPosts.mockResolvedValue(postPage(['9'], 0, false))
    await store.openPostsForOwner('MS4w-OTHER')

    expect(store.posts.map((one) => one.aweme_id)).toEqual(['9'])
    expect(store.selectedAwemeIds).toEqual([])
    expect(store.postsError).toBeNull()
  })

  it('clears a profile adoption when a history account is opened', async () => {
    const store = useCreatorsStore()
    store.adoptPostsFromOwnerRead(ownerRead({ posts: [post('from-profile')] }))
    store.togglePostSelection('from-profile')

    mockedPosts.mockResolvedValue(postPage(['from-history'], 0, false))
    await store.openPostsForOwner(SEC_UID)

    expect(store.posts.map((one) => one.aweme_id)).toEqual(['from-history'])
    expect(store.selectedAwemeIds).toEqual([])
  })

  it('cannot be polluted by the previous creator answering late', async () => {
    const slow = deferred<OwnerPostPage>()
    const fast = deferred<OwnerPostPage>()
    mockedPosts.mockReturnValueOnce(slow.promise).mockReturnValueOnce(fast.promise)
    const store = useCreatorsStore()

    const first = store.openPostsForOwner('CREATOR-A')
    const second = store.openPostsForOwner('CREATOR-B')

    fast.settle(postPage(['B-1'], 0, false))
    await second
    await drain()

    slow.settle(postPage(['A-1'], 999, true))
    await first
    await drain()

    expect(store.postsSecUserId).toBe('CREATOR-B')
    expect(store.posts.map((one) => one.aweme_id)).toEqual(['B-1'])
    expect(store.nextCursor).toBe(0)
    expect(store.hasMorePosts).toBe(false)
  })

  it('cannot report the previous creator error either', async () => {
    const slow = deferred<OwnerPostPage>()
    const fast = deferred<OwnerPostPage>()
    mockedPosts.mockReturnValueOnce(slow.promise).mockReturnValueOnce(fast.promise)
    const store = useCreatorsStore()

    const first = store.openPostsForOwner('CREATOR-A')
    const second = store.openPostsForOwner('CREATOR-B')

    fast.settle(postPage([], 0, false))
    await second
    await drain()
    slow.fail(new ApiError({ kind: 'network', status: null, code: null, message: 'x' }))
    await first
    await drain()

    expect(store.postsError).toBeNull()
  })

  it('aborts the request it is abandoning', async () => {
    const pending = deferred<OwnerPostPage>()
    mockedPosts.mockReturnValueOnce(pending.promise).mockResolvedValue(postPage([]))
    const store = useCreatorsStore()

    void store.openPostsForOwner('CREATOR-A')
    await drain()
    const firstSignal = mockedPosts.mock.calls[0][2]

    await store.openPostsForOwner('CREATOR-B')

    expect(firstSignal?.aborted).toBe(true)
  })
})

describe('selecting posts', () => {
  it('collects exactly the ids that were ticked', async () => {
    const store = useCreatorsStore()
    store.adoptPostsFromOwnerRead(
      ownerRead({ posts: [post('1'), post('2'), post('3')] }),
    )

    store.togglePostSelection('1')
    store.togglePostSelection('3')

    expect(store.selectedAwemeIds).toEqual(['1', '3'])
  })

  it('unticks again', async () => {
    const store = useCreatorsStore()
    store.adoptPostsFromOwnerRead(ownerRead({ posts: [post('1')] }))

    store.togglePostSelection('1')
    store.togglePostSelection('1')

    expect(store.selectedAwemeIds).toEqual([])
  })

  it('can take everything currently loaded', async () => {
    const store = useCreatorsStore()
    store.adoptPostsFromOwnerRead(ownerRead({ posts: [post('1'), post('2')] }))

    store.selectAllLoadedPosts()

    expect(store.selectedAwemeIds).toEqual(['1', '2'])
  })

  it('can clear the selection', async () => {
    const store = useCreatorsStore()
    store.adoptPostsFromOwnerRead(ownerRead({ posts: [post('1')] }))
    store.selectAllLoadedPosts()

    store.clearPostSelection()

    expect(store.selectedAwemeIds).toEqual([])
  })
})

describe('when a page of posts cannot be read', () => {
  it('keeps what was already loaded', async () => {
    const store = useCreatorsStore()
    store.adoptPostsFromOwnerRead(ownerRead({ posts: [post('1')], has_more: true }))

    mockedPosts.mockRejectedValue(
      new ApiError({ kind: 'network', status: null, code: null, message: 'offline' }),
    )
    await store.loadMorePosts()

    expect(store.posts.map((one) => one.aweme_id)).toEqual(['1'])
    expect(store.postsError).toContain('offline')
    expect(store.hasMorePosts).toBe(true)
  })
})
