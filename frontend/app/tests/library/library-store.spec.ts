import { createPinia, setActivePinia } from 'pinia'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import { ApiError } from '../../src/api/client'
import {
  listLibraryLives,
  listLibraryPosts,
  listLibraryRecordings,
} from '../../src/api/library'
import { getPersonWorks, listPeople } from '../../src/api/people'
import { useAuthStore } from '../../src/stores/auth'
import { useLibraryStore } from '../../src/stores/library'
import type {
  LibraryLive,
  LibraryPost,
  LibraryRecording,
} from '../../src/types/library'

vi.mock('../../src/api/library', () => ({
  listLibraryPosts: vi.fn(),
  listLibraryLives: vi.fn(),
  listLibraryRecordings: vi.fn(),
}))
vi.mock('../../src/api/people', () => ({
  listPeople: vi.fn(),
  getPersonWorks: vi.fn(),
}))

const mockedPosts = vi.mocked(listLibraryPosts)
const mockedLives = vi.mocked(listLibraryLives)
const mockedRecordings = vi.mocked(listLibraryRecordings)
const mockedPeople = vi.mocked(listPeople)
const mockedWorks = vi.mocked(getPersonWorks)

function post(overrides: Partial<LibraryPost> = {}): LibraryPost {
  return {
    platform: 'douyin',
    aweme_id: '1',
    owner_user_id: '5885',
    sec_user_id: 'MS4w',
    nickname: '主播',
    directory_name: '主播',
    person_id: null,
    person_display_name: null,
    aweme_type: 'video',
    desc: '一条作品',
    create_time: null,
    downloaded_at: '2026-08-15T09:30:15.250',
    media_count: 1,
    saved_count: 1,
    save_dir: '/data/主播',
    source: 'api',
    ...overrides,
  }
}

function live(overrides: Partial<LibraryLive> = {}): LibraryLive {
  return {
    observed_at: '2026-08-15T09:30:15.250',
    platform: 'douyin',
    room_id: '7123',
    owner_user_id: '5885',
    nickname: '主播',
    directory_name: '主播',
    person_id: null,
    person_display_name: null,
    title: '晚间直播',
    room_status: 4,
    start_time: null,
    finish_time: null,
    status_code: 0,
    ...overrides,
  }
}

function postPage(items: LibraryPost[], total = items.length, page = 1) {
  return { total, page, page_size: 25, items }
}

function livePage(items: LibraryLive[], total = items.length, page = 1) {
  return { total, page, page_size: 25, items }
}

function recording(overrides: Partial<LibraryRecording> = {}): LibraryRecording {
  return {
    recording_id: 'rec-1',
    platform: 'douyin',
    room_id: '7123',
    nickname: '主播',
    title: '晚间直播',
    started_at: null,
    finished_at: null,
    created_at: '2026-08-15T09:30:15.250',
    ...overrides,
  }
}

function recordingPage(items: LibraryRecording[], total = items.length, page = 1) {
  return { total, page, page_size: 25, items }
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
  for (let index = 0; index < 6; index += 1) {
    await Promise.resolve()
  }
}

const offline = new ApiError({
  kind: 'network',
  status: null,
  code: null,
  message: 'offline',
})

beforeEach(() => {
  setActivePinia(createPinia())
  vi.clearAllMocks()
  mockedPosts.mockResolvedValue(postPage([]))
  mockedLives.mockResolvedValue(livePage([]))
  mockedRecordings.mockResolvedValue(recordingPage([]))
  mockedPeople.mockResolvedValue([])
  mockedWorks.mockResolvedValue([])
})

describe('arriving at the library', () => {
  it('has read nothing until it is asked to', () => {
    useLibraryStore()

    expect(mockedPosts).not.toHaveBeenCalled()
    expect(mockedLives).not.toHaveBeenCalled()
    expect(mockedWorks).not.toHaveBeenCalled()
  })

  it('reads live records only when that tab is opened', async () => {
    const store = useLibraryStore()

    await store.loadPosts()

    expect(mockedPosts).toHaveBeenCalledTimes(1)
    expect(mockedLives).not.toHaveBeenCalled()
  })

  it('never reads a photographer association on its own', async () => {
    const store = useLibraryStore()

    await store.loadPosts()
    await store.loadPeopleOptions()

    expect(mockedWorks).not.toHaveBeenCalled()
  })
})

describe('a page of downloaded posts', () => {
  it('keeps the totals the server counted', async () => {
    mockedPosts.mockResolvedValue(postPage([post()], 163, 1))
    const store = useLibraryStore()

    await store.loadPosts()

    expect(store.postTotal).toBe(163)
    expect(store.postPage).toBe(1)
    expect(store.posts).toHaveLength(1)
  })

  it('keeps the order the server produced', async () => {
    mockedPosts.mockResolvedValue(
      postPage([post({ aweme_id: 'c' }), post({ aweme_id: 'a' }), post({ aweme_id: 'b' })]),
    )
    const store = useLibraryStore()

    await store.loadPosts()

    expect(store.posts.map((one) => one.aweme_id)).toEqual(['c', 'a', 'b'])
  })

  it('sends the filters to the server rather than narrowing here', async () => {
    const store = useLibraryStore()

    await store.setPostFilters({ q: '绿萝', completion: 'partial' })

    expect(mockedPosts).toHaveBeenLastCalledWith(
      expect.objectContaining({ q: '绿萝', completion: 'partial', page: 1 }),
      expect.anything(),
    )
  })

  it('returns to the first page when the filters change', async () => {
    const store = useLibraryStore()
    await store.goToPostPage(4)

    await store.setPostFilters({ q: '绿萝' })

    expect(mockedPosts).toHaveBeenLastCalledWith(
      expect.objectContaining({ page: 1 }),
      expect.anything(),
    )
  })

  it('does not claim the library is empty when the read failed', async () => {
    mockedPosts.mockRejectedValue(offline)
    const store = useLibraryStore()

    await store.loadPosts()

    expect(store.postError).not.toBeNull()
    expect(store.hasLoadedPosts).toBe(false)
  })

  it('keeps what it last showed when a refresh fails', async () => {
    mockedPosts.mockResolvedValue(postPage([post({ aweme_id: 'kept' })], 9))
    const store = useLibraryStore()
    await store.loadPosts()

    mockedPosts.mockRejectedValue(offline)
    await store.loadPosts()

    expect(store.posts.map((one) => one.aweme_id)).toEqual(['kept'])
    expect(store.postTotal).toBe(9)
    expect(store.postError).not.toBeNull()
  })
})

describe('a page of posts that was superseded', () => {
  it('cannot overwrite the list the current filters produced', async () => {
    const stale = deferred<ReturnType<typeof postPage>>()
    mockedPosts.mockReturnValueOnce(stale.promise)
    const store = useLibraryStore()
    void store.loadPosts()
    await drain()

    mockedPosts.mockResolvedValue(postPage([post({ aweme_id: 'new' })], 2))
    await store.setPostFilters({ q: '新的' })

    stale.settle(postPage([post({ aweme_id: 'old' })], 999))
    await drain()

    expect(store.posts.map((one) => one.aweme_id)).toEqual(['new'])
    expect(store.postTotal).toBe(2)
  })

  it('cannot report an error against filters that moved on', async () => {
    const stale = deferred<ReturnType<typeof postPage>>()
    mockedPosts.mockReturnValueOnce(stale.promise)
    const store = useLibraryStore()
    void store.loadPosts()
    await drain()

    mockedPosts.mockResolvedValue(postPage([post()], 1))
    await store.setPostFilters({ q: '新的' })

    stale.fail(offline)
    await drain()

    expect(store.postError).toBeNull()
  })

  it('cannot move the pagination either', async () => {
    const stale = deferred<ReturnType<typeof postPage>>()
    mockedPosts.mockReturnValueOnce(stale.promise)
    const store = useLibraryStore()
    void store.goToPostPage(1)
    await drain()

    mockedPosts.mockResolvedValue(postPage([post()], 50, 2))
    await store.goToPostPage(2)

    stale.settle(postPage([post()], 50, 1))
    await drain()

    expect(store.postPage).toBe(2)
  })
})

describe('a page of live records', () => {
  it('keeps the totals and the order the server produced', async () => {
    mockedLives.mockResolvedValue(
      livePage([live({ room_id: 'c' }), live({ room_id: 'a' })], 40, 1),
    )
    const store = useLibraryStore()

    await store.loadLives()

    expect(store.liveTotal).toBe(40)
    expect(store.lives.map((one) => one.room_id)).toEqual(['c', 'a'])
  })

  it('keeps what it last showed when a refresh fails', async () => {
    mockedLives.mockResolvedValue(livePage([live({ room_id: 'kept' })], 3))
    const store = useLibraryStore()
    await store.loadLives()

    mockedLives.mockRejectedValue(offline)
    await store.loadLives()

    expect(store.lives.map((one) => one.room_id)).toEqual(['kept'])
    expect(store.liveError).not.toBeNull()
  })

  it('cannot be overwritten by a superseded page', async () => {
    const stale = deferred<ReturnType<typeof livePage>>()
    mockedLives.mockReturnValueOnce(stale.promise)
    const store = useLibraryStore()
    void store.loadLives()
    await drain()

    mockedLives.mockResolvedValue(livePage([live({ room_id: 'new' })], 2))
    await store.setLiveFilters({ q: '新的' })

    stale.settle(livePage([live({ room_id: 'old' })], 999))
    await drain()

    expect(store.lives.map((one) => one.room_id)).toEqual(['new'])
    expect(store.liveTotal).toBe(2)
  })
})

describe('persistent recording state', () => {
  it('is loaded independently from Admin live observations', async () => {
    mockedLives.mockResolvedValue(livePage([live()]))
    mockedRecordings.mockResolvedValue(recordingPage([recording()]))
    const store = useLibraryStore()

    await store.loadRecordings()

    expect(store.recordings).toHaveLength(1)
    expect(store.lives).toHaveLength(0)
    expect(mockedRecordings).toHaveBeenCalledTimes(1)
    expect(mockedLives).not.toHaveBeenCalled()
  })
})

describe('authentication principal changes', () => {
  it('clears cached resources and rejects responses started by the previous user', async () => {
    const auth = useAuthStore()
    auth.$patch({
      status: 'authenticated',
      user: { user_id: 71, username: 'alice', role: 'user' },
    })
    mockedPosts.mockResolvedValue(postPage([post({ aweme_id: 'alice-post' })], 1))
    const store = useLibraryStore()
    await store.loadPosts()

    const stale = deferred<ReturnType<typeof recordingPage>>()
    mockedRecordings.mockReturnValueOnce(stale.promise)
    void store.loadRecordings()
    await drain()

    auth.$patch({
      status: 'authenticated',
      user: { user_id: 72, username: 'bob', role: 'user' },
    })
    stale.settle(recordingPage([recording({ recording_id: 'alice-recording' })], 1))
    await drain()

    expect(store.posts).toEqual([])
    expect(store.postTotal).toBe(0)
    expect(store.hasLoadedPosts).toBe(false)
    expect(store.recordings).toEqual([])
    expect(store.recordingTotal).toBe(0)
    expect(store.hasLoadedRecordings).toBe(false)
    expect(store.recordingLoading).toBe(false)
  })
})

describe('the person options a library filter offers', () => {
  it('does not stop the library working when they cannot be read', async () => {
    //
    // The filter is a convenience. Failing to populate it must not take the
    // index down with it.
    //
    mockedPeople.mockRejectedValue(offline)
    mockedPosts.mockResolvedValue(postPage([post()], 1))
    const store = useLibraryStore()

    await store.loadPeopleOptions()
    await store.loadPosts()

    expect(store.peopleOptionsError).not.toBeNull()
    expect(store.posts).toHaveLength(1)
    expect(store.postError).toBeNull()
  })

  it('never touches the creators workspace selection', async () => {
    //
    // Two screens, two selections. Reaching into the people store would make
    // opening a library filter change what the identity screen is showing.
    //
    const people = await import('../../src/api/people')

    expect(Object.keys(people)).not.toContain('usePeopleStore')
  })
})

describe('the works associated with a photographer', () => {
  it('reads nothing until somebody is chosen', async () => {
    const store = useLibraryStore()

    await store.loadPeopleOptions()

    expect(mockedWorks).not.toHaveBeenCalled()
  })

  it('reads the chosen photographer', async () => {
    mockedWorks.mockResolvedValue([
      {
        aweme_id: '1',
        desc: '一条',
        save_dir: '/data/某人',
        downloaded_at: null,
        owner_display_name: '被拍的人',
      },
    ])
    const store = useLibraryStore()

    await store.selectPhotographer(7)

    expect(mockedWorks).toHaveBeenCalledWith(7, expect.anything())
    expect(store.personWorks).toHaveLength(1)
  })

  it('cannot be crossed by an earlier photographer answering late', async () => {
    const stale = deferred<Awaited<ReturnType<typeof getPersonWorks>>>()
    mockedWorks.mockReturnValueOnce(stale.promise)
    const store = useLibraryStore()
    void store.selectPhotographer(1)
    await drain()

    mockedWorks.mockResolvedValue([
      {
        aweme_id: 'B',
        desc: null,
        save_dir: null,
        downloaded_at: null,
        owner_display_name: '第二位',
      },
    ])
    await store.selectPhotographer(2)

    stale.settle([
      {
        aweme_id: 'A',
        desc: null,
        save_dir: null,
        downloaded_at: null,
        owner_display_name: '第一位',
      },
    ])
    await drain()

    expect(store.personWorks.map((one) => one.aweme_id)).toEqual(['B'])
    expect(store.selectedPhotographerId).toBe(2)
  })

  it('says so when the association could not be read', async () => {
    mockedWorks.mockRejectedValue(offline)
    const store = useLibraryStore()

    await store.selectPhotographer(7)

    expect(store.personWorksError).not.toBeNull()
  })
})
