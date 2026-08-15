import { createPinia, setActivePinia } from 'pinia'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import { ApiError } from '../../src/api/client'
import { resolveResource } from '../../src/api/resolve'
import { readOwner, readOwnerPosts } from '../../src/api/owners'
import { createTask } from '../../src/api/tasks'
import { useCreatorsStore } from '../../src/stores/creators'
import type { ResolvedResource } from '../../src/types/resolution'
import type { OwnerRead } from '../../src/types/owner'

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

vi.mock('../../src/api/resolve', () => ({ resolveResource: vi.fn() }))
vi.mock('../../src/api/tasks', () => ({ createTask: vi.fn(), listTasks: vi.fn(), getTask: vi.fn() }))

const mockedResolve = vi.mocked(resolveResource)
const mockedCreateTask = vi.mocked(createTask)
const mockedReadOwner = vi.mocked(readOwner)
const mockedReadPosts = vi.mocked(readOwnerPosts)

const SEC_UID = 'MS4wLjABAAAAGZkW5n1EHZD_TFyQ-QiaISBPemtKFxVVdhLSeoXhh-U'
const SHORT_LINK = 'https://v.douyin.com/abc/'
const LIVE_URL = 'https://live.douyin.com/123456'
const OWNER_URL = `https://www.douyin.com/user/${SEC_UID}`

function liveResolution(overrides: Partial<ResolvedResource> = {}): ResolvedResource {
  return {
    resolve_id: 'receipt-live',
    platform: 'douyin',
    resource_type: 'live',
    source_url: SHORT_LINK,
    resolved_url: LIVE_URL,
    identity: {},
    expires_in_seconds: 600,
    ...overrides,
  } as ResolvedResource
}

function ownerResolution(overrides: Partial<ResolvedResource> = {}): ResolvedResource {
  return {
    resolve_id: 'receipt-owner',
    platform: 'douyin',
    resource_type: 'owner',
    source_url: SHORT_LINK,
    resolved_url: OWNER_URL,
    identity: { sec_user_id: SEC_UID },
    expires_in_seconds: 600,
    ...overrides,
  } as ResolvedResource
}

function postResolution(): ResolvedResource {
  return {
    resolve_id: 'receipt-post',
    platform: 'douyin',
    resource_type: 'post',
    source_url: SHORT_LINK,
    resolved_url: 'https://www.douyin.com/video/7657271784144009946',
    identity: { aweme_id: '7657271784144009946' },
    expires_in_seconds: 600,
  } as ResolvedResource
}

function ownerRead(overrides: Partial<OwnerRead> = {}): OwnerRead {
  return {
    sec_user_id: SEC_UID,
    owner: null,
    owner_message: null,
    credential: { expires_in_days: 30 },
    posts: [],
    next_cursor: 0,
    has_more: false,
    ...overrides,
  }
}

function deferred<T>() {
  let settle: (value: T) => void = () => {}
  const promise = new Promise<T>((resolve) => {
    settle = resolve
  })
  return { promise, settle }
}

async function drain() {
  for (let index = 0; index < 5; index += 1) {
    await Promise.resolve()
  }
}

beforeEach(() => {
  setActivePinia(createPinia())
  mockedResolve.mockReset()
  mockedCreateTask.mockReset()
  mockedReadOwner.mockReset()
  mockedReadPosts.mockReset()
  mockedReadPosts.mockResolvedValue({ posts: [], next_cursor: 0, has_more: false })
})

describe('starting a recording from a live account', () => {
  it('resolves the share link before creating anything', async () => {
    //
    // The share link is a short url the user never validated. Resolving it is
    // what applies the host allow list, the redirect limit and the loopback
    // refusal - and it is the only thing that produces a receipt the task api
    // will accept.
    //
    mockedResolve.mockResolvedValue(liveResolution())
    mockedCreateTask.mockResolvedValue({
      task_id: 'T-1',
      task_type: 'live_record',
      resolve_id: 'receipt-live',
    })
    const store = useCreatorsStore()

    await store.startRecording(SHORT_LINK)

    expect(mockedResolve).toHaveBeenCalledWith(SHORT_LINK)
    expect(mockedCreateTask).toHaveBeenCalledWith({
      resolve_id: 'receipt-live',
      task_type: 'live_record',
    })
  })

  it('never hands the share link to the task api', async () => {
    //
    // The whole point of the receipt: the browser says which resolution, not
    // which url. A url in this body would be the client deciding what gets
    // recorded.
    //
    mockedResolve.mockResolvedValue(liveResolution())
    mockedCreateTask.mockResolvedValue({
      task_id: 'T-1',
      task_type: 'live_record',
      resolve_id: 'receipt-live',
    })
    const store = useCreatorsStore()

    await store.startRecording(SHORT_LINK)

    const sent = JSON.stringify(mockedCreateTask.mock.calls[0][0])
    expect(sent).not.toContain('douyin.com')
    expect(sent).not.toContain('live_share_url')
  })

  it('keeps the task id for the handoff', async () => {
    mockedResolve.mockResolvedValue(liveResolution())
    mockedCreateTask.mockResolvedValue({
      task_id: 'T-42',
      task_type: 'live_record',
      resolve_id: 'receipt-live',
    })
    const store = useCreatorsStore()

    await store.startRecording(SHORT_LINK)

    expect(store.lastStartedTaskId).toBe('T-42')
    expect(store.actionError).toBeNull()
  })

  it('refuses when the link turns out not to be a live room', async () => {
    mockedResolve.mockResolvedValue(postResolution())
    const store = useCreatorsStore()

    await store.startRecording(SHORT_LINK)

    expect(mockedCreateTask).not.toHaveBeenCalled()
    expect(store.actionError).toContain('直播')
  })

  it('reports a resolve failure without creating anything', async () => {
    mockedResolve.mockRejectedValue(
      new ApiError({ kind: 'backend', status: 502, code: 502, message: '无法解析该短链接' }),
    )
    const store = useCreatorsStore()

    await store.startRecording(SHORT_LINK)

    expect(mockedCreateTask).not.toHaveBeenCalled()
    expect(store.actionError).toContain('无法解析该短链接')
  })

  it('reports a create failure as itself', async () => {
    mockedResolve.mockResolvedValue(liveResolution())
    mockedCreateTask.mockRejectedValue(
      new ApiError({ kind: 'backend', status: 404, code: 404, message: '解析结果已过期' }),
    )
    const store = useCreatorsStore()

    await store.startRecording(SHORT_LINK)

    expect(store.lastStartedTaskId).toBeNull()
    expect(store.actionError).toContain('解析结果已过期')
  })

  it('cannot be started twice at once', async () => {
    const pending = deferred<ResolvedResource>()
    mockedResolve.mockReturnValue(pending.promise)
    const store = useCreatorsStore()

    const first = store.startRecording(SHORT_LINK)
    await store.startRecording(SHORT_LINK)

    expect(mockedResolve).toHaveBeenCalledTimes(1)

    pending.settle(liveResolution())
    mockedCreateTask.mockResolvedValue({
      task_id: 'T-1',
      task_type: 'live_record',
      resolve_id: 'receipt-live',
    })
    await first
  })
})

describe('opening a profile from a pasted link', () => {
  it('resolves the paste before asking the owner api anything', async () => {
    //
    // `/api/owner` would follow a short link itself, outside the resolver's
    // host checks. Resolving first means the url it receives has already been
    // through them.
    //
    mockedResolve.mockResolvedValue(ownerResolution())
    mockedReadOwner.mockResolvedValue(ownerRead())
    const store = useCreatorsStore()

    await store.openProfile('4.33 复制打开抖音 ' + SHORT_LINK)

    expect(mockedResolve).toHaveBeenCalledWith('4.33 复制打开抖音 ' + SHORT_LINK)
    expect(mockedReadOwner).toHaveBeenCalledTimes(1)
    expect(mockedReadOwner.mock.calls[0][0]).toBe(OWNER_URL)
  })

  it('never sends the raw paste or the short link onward', async () => {
    mockedResolve.mockResolvedValue(ownerResolution())
    mockedReadOwner.mockResolvedValue(ownerRead())
    const store = useCreatorsStore()

    await store.openProfile(SHORT_LINK)

    const sent = mockedReadOwner.mock.calls[0][0]
    expect(sent).not.toBe(SHORT_LINK)
    expect(sent).toBe(OWNER_URL)
  })

  it('refuses anything that is not an owner', async () => {
    mockedResolve.mockResolvedValue(postResolution())
    const store = useCreatorsStore()

    await store.openProfile(SHORT_LINK)

    expect(mockedReadOwner).not.toHaveBeenCalled()
    expect(store.profileError).toContain('主播主页')
  })

  it('keeps the profile it read', async () => {
    mockedResolve.mockResolvedValue(ownerResolution())
    mockedReadOwner.mockResolvedValue(
      ownerRead({ owner: { sec_user_id: SEC_UID, uid: '1', nickname: '绿萝', unique_id: 'lv', signature: null, avatar_url: null, follower_count: 10, following_count: 2, aweme_count: 30, total_favorited: 99 } }),
    )
    const store = useCreatorsStore()

    await store.openProfile(SHORT_LINK)

    expect(store.openedProfile?.owner?.nickname).toBe('绿萝')
    expect(store.profileError).toBeNull()
  })

  it('adopts the first page of posts without asking for it again', async () => {
    mockedResolve.mockResolvedValue(ownerResolution())
    mockedReadOwner.mockResolvedValue(
      ownerRead({
        posts: [
          {
            aweme_id: '1',
            desc: '',
            create_time: 0,
            cover_url: '',
            duration: null,
            aweme_type: 'video',
            digg_count: null,
            comment_count: null,
            downloaded: false,
            saved_count: null,
            media_count: null,
          },
        ],
        next_cursor: 555,
        has_more: true,
      }),
    )
    const store = useCreatorsStore()

    await store.openProfile(SHORT_LINK)

    expect(store.posts.map((one) => one.aweme_id)).toEqual(['1'])
    expect(store.nextCursor).toBe(555)
    expect(mockedReadPosts).not.toHaveBeenCalled()
  })

  it('shows the posts even when the profile itself could not be read', async () => {
    //
    // The backend reads the profile and the post list independently on purpose:
    // an expired session hides one and not the other, and hiding both would
    // lose work the server actually did.
    //
    mockedResolve.mockResolvedValue(ownerResolution())
    mockedReadOwner.mockResolvedValue(
      ownerRead({ owner: null, owner_message: '主播详情不可用' }),
    )
    const store = useCreatorsStore()

    await store.openProfile(SHORT_LINK)

    expect(store.openedProfile?.owner).toBeNull()
    expect(store.openedProfile?.owner_message).toBe('主播详情不可用')
    expect(store.profileError).toBeNull()
  })

  it('cannot be crossed by an earlier paste answering late', async () => {
    //
    // Paste A, change it to B, press again. A's resolution is about a link the
    // box no longer holds - opening it would show one creator's profile under
    // another creator's text.
    //
    const slow = deferred<ResolvedResource>()
    const fast = deferred<ResolvedResource>()
    mockedResolve.mockReturnValueOnce(slow.promise).mockReturnValueOnce(fast.promise)
    mockedReadOwner.mockResolvedValue(ownerRead({ sec_user_id: 'FROM-B' }))
    const store = useCreatorsStore()

    const first = store.openProfile('A')
    const second = store.openProfile('B')

    fast.settle(ownerResolution({ resolved_url: 'https://www.douyin.com/user/B' }))
    await second
    await drain()

    slow.settle(ownerResolution({ resolved_url: 'https://www.douyin.com/user/A' }))
    await first
    await drain()

    expect(mockedReadOwner).toHaveBeenCalledTimes(1)
    expect(mockedReadOwner.mock.calls[0][0]).toBe('https://www.douyin.com/user/B')
  })
})

describe('starting downloads', () => {
  it('sends only the ticked ids', async () => {
    const { startOwnerSelectedDownload } = await import('../../src/api/owners')
    const mockedSelected = vi.mocked(startOwnerSelectedDownload)
    mockedSelected.mockResolvedValue({ job_id: 'J-1', task_id: 'T-1' })
    const store = useCreatorsStore()
    store.adoptPostsFromOwnerRead(
      ownerRead({
        posts: ['1', '2', '3'].map((id) => ({
          aweme_id: id,
          desc: '',
          create_time: 0,
          cover_url: '',
          duration: null,
          aweme_type: 'video' as const,
          digg_count: null,
          comment_count: null,
          downloaded: false,
          saved_count: null,
          media_count: null,
        })),
      }),
    )
    store.togglePostSelection('1')
    store.togglePostSelection('3')

    await store.downloadSelectedPosts()

    expect(mockedSelected).toHaveBeenCalledWith(['1', '3'], undefined)
  })

  it('hands back the unified task rather than the legacy job', async () => {
    //
    // The job record is the old page's compatibility surface. A new client that
    // read it would end up building a second progress view beside the task
    // centre - and polling it.
    //
    const { startOwnerSelectedDownload } = await import('../../src/api/owners')
    vi.mocked(startOwnerSelectedDownload).mockResolvedValue({
      job_id: 'J-1',
      task_id: 'T-9',
    })
    const store = useCreatorsStore()
    store.adoptPostsFromOwnerRead(
      ownerRead({
        posts: [
          {
            aweme_id: '1',
            desc: '',
            create_time: 0,
            cover_url: '',
            duration: null,
            aweme_type: 'video',
            digg_count: null,
            comment_count: null,
            downloaded: false,
            saved_count: null,
            media_count: null,
          },
        ],
      }),
    )
    store.togglePostSelection('1')

    await store.downloadSelectedPosts()

    expect(store.lastStartedTaskId).toBe('T-9')
  })

  it('says so when the unified record is missing rather than falling back', async () => {
    const { startOwnerSelectedDownload } = await import('../../src/api/owners')
    vi.mocked(startOwnerSelectedDownload).mockResolvedValue({
      job_id: 'J-1',
      task_id: null,
    })
    const store = useCreatorsStore()
    store.adoptPostsFromOwnerRead(
      ownerRead({
        posts: [
          {
            aweme_id: '1',
            desc: '',
            create_time: 0,
            cover_url: '',
            duration: null,
            aweme_type: 'video',
            digg_count: null,
            comment_count: null,
            downloaded: false,
            saved_count: null,
            media_count: null,
          },
        ],
      }),
    )
    store.togglePostSelection('1')

    await store.downloadSelectedPosts()

    expect(store.lastStartedTaskId).toBeNull()
    expect(store.actionNotice).toContain('任务记录')
  })

  it('refuses to start with nothing selected', async () => {
    const { startOwnerSelectedDownload } = await import('../../src/api/owners')
    const mockedSelected = vi.mocked(startOwnerSelectedDownload)
    mockedSelected.mockClear()
    const store = useCreatorsStore()

    await store.downloadSelectedPosts()

    expect(mockedSelected).not.toHaveBeenCalled()
  })

  it('clears the selection and asks for a re-read when the payloads expired', async () => {
    //
    // The server keeps the post payloads in its own cache; once they age out
    // the ids mean nothing to it. Retrying the same ids would fail the same
    // way, so the only useful action is to read the list again.
    //
    const { startOwnerSelectedDownload } = await import('../../src/api/owners')
    vi.mocked(startOwnerSelectedDownload).mockRejectedValue(
      new ApiError({
        kind: 'backend',
        status: 404,
        code: 404,
        message: '作品数据已过期，请重新读取该页后再下载',
      }),
    )
    const store = useCreatorsStore()
    store.adoptPostsFromOwnerRead(
      ownerRead({
        posts: [
          {
            aweme_id: '1',
            desc: '',
            create_time: 0,
            cover_url: '',
            duration: null,
            aweme_type: 'video',
            digg_count: null,
            comment_count: null,
            downloaded: false,
            saved_count: null,
            media_count: null,
          },
        ],
      }),
    )
    store.togglePostSelection('1')

    await store.downloadSelectedPosts()

    expect(store.selectedAwemeIds).toEqual([])
    expect(store.postPayloadsExpired).toBe(true)
    expect(store.actionError).toContain('重新读取')
  })

  it('asks for everything by owner id', async () => {
    const { startOwnerAllDownload } = await import('../../src/api/owners')
    const mockedAll = vi.mocked(startOwnerAllDownload)
    mockedAll.mockResolvedValue({ job_id: 'J-1', task_id: 'T-2' })
    const store = useCreatorsStore()
    store.adoptPostsFromOwnerRead(ownerRead({ sec_user_id: SEC_UID }))

    await store.downloadAllPosts()

    expect(mockedAll).toHaveBeenCalledWith(SEC_UID, undefined)
    expect(store.lastStartedTaskId).toBe('T-2')
  })

  it('never builds an all-download out of the ids it happens to have', async () => {
    //
    // "Everything" is the server walking the pages, not the browser sending the
    // few hundred ids it managed to load.
    //
    const { startOwnerAllDownload, startOwnerSelectedDownload } = await import(
      '../../src/api/owners'
    )
    vi.mocked(startOwnerAllDownload).mockResolvedValue({ job_id: 'J', task_id: 'T' })
    const mockedSelected = vi.mocked(startOwnerSelectedDownload)
    mockedSelected.mockClear()
    const store = useCreatorsStore()
    store.adoptPostsFromOwnerRead(ownerRead({ sec_user_id: SEC_UID }))

    await store.downloadAllPosts()

    expect(mockedSelected).not.toHaveBeenCalled()
  })
})

describe('one creator owns the panel at a time', () => {
  //
  // Two entry points can put a creator on screen - picking one from the
  // directory, and opening a pasted profile link - and either can be in flight
  // when the other happens. Whichever the user asked for *last* owns the panel;
  // an answer for the other one arriving afterwards is about a creator nobody
  // is looking at.
  //
  // Not just the posts array: the profile card, the sessions and the selection
  // all belong to the same "current creator", and guarding them separately is
  // how one of them ends up describing somebody else.
  //

  it('a profile read that lands after a history account was picked is ignored', async () => {
    const slow = deferred<OwnerRead>()
    mockedResolve.mockResolvedValue(ownerResolution())
    mockedReadOwner.mockReturnValue(slow.promise)
    const store = useCreatorsStore()

    const opening = store.openProfile(SHORT_LINK)
    await drain()

    //
    // The user gives up waiting and picks somebody from the directory.
    //
    store.selectOwner('FROM-HISTORY')

    slow.settle(ownerRead({ sec_user_id: 'FROM-PROFILE' }))
    await opening
    await drain()

    expect(store.openedProfile).toBeNull()
    expect(store.selectedOwnerUserId).toBe('FROM-HISTORY')
  })

  it('that late profile cannot bring its posts with it either', async () => {
    const slow = deferred<OwnerRead>()
    mockedResolve.mockResolvedValue(ownerResolution())
    mockedReadOwner.mockReturnValue(slow.promise)
    const store = useCreatorsStore()

    const opening = store.openProfile(SHORT_LINK)
    await drain()
    store.selectOwner('FROM-HISTORY')

    slow.settle(
      ownerRead({
        sec_user_id: 'FROM-PROFILE',
        posts: [
          {
            aweme_id: 'PROFILE-POST',
            desc: '',
            create_time: 0,
            cover_url: '',
            duration: null,
            aweme_type: 'video',
            digg_count: null,
            comment_count: null,
            downloaded: false,
            saved_count: null,
            media_count: null,
          },
        ],
      }),
    )
    await opening
    await drain()

    expect(store.posts).toEqual([])
    expect(store.postsSecUserId).not.toBe('FROM-PROFILE')
  })

  it('a history page of posts that lands after a profile was opened is ignored', async () => {
    const slowPosts = deferred<{ posts: never[]; next_cursor: number; has_more: boolean }>()
    mockedReadPosts.mockReturnValue(slowPosts.promise)
    mockedResolve.mockResolvedValue(ownerResolution())
    mockedReadOwner.mockResolvedValue(
      ownerRead({
        sec_user_id: 'FROM-PROFILE',
        posts: [
          {
            aweme_id: 'PROFILE-POST',
            desc: '',
            create_time: 0,
            cover_url: '',
            duration: null,
            aweme_type: 'video',
            digg_count: null,
            comment_count: null,
            downloaded: false,
            saved_count: null,
            media_count: null,
          },
        ],
      }),
    )
    const store = useCreatorsStore()

    const reading = store.openPostsForOwner('FROM-HISTORY')
    await drain()

    await store.openProfile(SHORT_LINK)
    await drain()

    slowPosts.settle({ posts: [], next_cursor: 777, has_more: true })
    await reading
    await drain()

    expect(store.postsSecUserId).toBe('FROM-PROFILE')
    expect(store.posts.map((one) => one.aweme_id)).toEqual(['PROFILE-POST'])
    expect(store.nextCursor).not.toBe(777)
  })

  it('picking a history account puts away a profile that was open', async () => {
    mockedResolve.mockResolvedValue(ownerResolution())
    mockedReadOwner.mockResolvedValue(ownerRead({ sec_user_id: 'FROM-PROFILE' }))
    const store = useCreatorsStore()
    await store.openProfile(SHORT_LINK)
    expect(store.openedProfile).not.toBeNull()

    store.selectOwner('FROM-HISTORY')

    expect(store.openedProfile).toBeNull()
  })
})

describe('a write action cannot be submitted twice', () => {
  //
  // These are not reads. A second click does not cost an extra request - it
  // starts a second recording, or a second download job, and the user has no
  // way to tell that from one.
  //

  it('holds the recording action shut across both of its steps', async () => {
    //
    // Resolve and create are one action from the user's point of view. Opening
    // the button back up in between - after the receipt, before the task - is
    // exactly the window a second click lands in.
    //
    const pendingCreate = deferred<{
      task_id: string
      task_type: 'live_record'
      resolve_id: string
    }>()
    mockedResolve.mockResolvedValue(liveResolution())
    mockedCreateTask.mockReturnValue(pendingCreate.promise)
    const store = useCreatorsStore()

    const first = store.startRecording(SHORT_LINK)
    await drain()

    expect(store.actionBusy).toBe(true)
    await store.startRecording(SHORT_LINK)
    await store.startRecording(SHORT_LINK)

    expect(mockedResolve).toHaveBeenCalledTimes(1)
    expect(mockedCreateTask).toHaveBeenCalledTimes(1)

    pendingCreate.settle({
      task_id: 'T-1',
      task_type: 'live_record',
      resolve_id: 'receipt-live',
    })
    await first
  })

  it('does not start a second download job for the same click', async () => {
    const { startOwnerSelectedDownload } = await import('../../src/api/owners')
    const mockedSelected = vi.mocked(startOwnerSelectedDownload)
    const pending = deferred<{ job_id: string; task_id: string }>()
    mockedSelected.mockReturnValue(pending.promise)
    const store = useCreatorsStore()
    store.adoptPostsFromOwnerRead(
      ownerRead({
        posts: [
          {
            aweme_id: '1',
            desc: '',
            create_time: 0,
            cover_url: '',
            duration: null,
            aweme_type: 'video',
            digg_count: null,
            comment_count: null,
            downloaded: false,
            saved_count: null,
            media_count: null,
          },
        ],
      }),
    )
    store.togglePostSelection('1')

    const first = store.downloadSelectedPosts()
    await drain()
    await store.downloadSelectedPosts()
    await store.downloadSelectedPosts()

    expect(mockedSelected).toHaveBeenCalledTimes(1)

    pending.settle({ job_id: 'J', task_id: 'T' })
    await first
  })

  it('locks the whole-catalogue download while a selected one is in flight', async () => {
    //
    // One creator, one submission at a time. Two overlapping downloads of the
    // same account is not a case worth supporting, and letting it happen by
    // accident is worse than refusing it.
    //
    const { startOwnerSelectedDownload, startOwnerAllDownload } = await import(
      '../../src/api/owners'
    )
    const mockedSelected = vi.mocked(startOwnerSelectedDownload)
    const mockedAll = vi.mocked(startOwnerAllDownload)
    const pending = deferred<{ job_id: string; task_id: string }>()
    mockedSelected.mockClear()
    mockedAll.mockClear()
    mockedSelected.mockReturnValue(pending.promise)
    mockedAll.mockResolvedValue({ job_id: 'J2', task_id: 'T2' })
    const store = useCreatorsStore()
    store.adoptPostsFromOwnerRead(
      ownerRead({
        sec_user_id: SEC_UID,
        posts: [
          {
            aweme_id: '1',
            desc: '',
            create_time: 0,
            cover_url: '',
            duration: null,
            aweme_type: 'video',
            digg_count: null,
            comment_count: null,
            downloaded: false,
            saved_count: null,
            media_count: null,
          },
        ],
      }),
    )
    store.togglePostSelection('1')

    const first = store.downloadSelectedPosts()
    await drain()
    await store.downloadAllPosts()

    expect(mockedAll).not.toHaveBeenCalled()

    pending.settle({ job_id: 'J', task_id: 'T' })
    await first
  })

  it('reopens once the action has finished', async () => {
    const { startOwnerAllDownload } = await import('../../src/api/owners')
    const mockedAll = vi.mocked(startOwnerAllDownload)
    mockedAll.mockClear()
    mockedAll.mockResolvedValue({ job_id: 'J', task_id: 'T' })
    const store = useCreatorsStore()
    store.adoptPostsFromOwnerRead(ownerRead({ sec_user_id: SEC_UID }))

    await store.downloadAllPosts()
    await store.downloadAllPosts()

    expect(mockedAll).toHaveBeenCalledTimes(2)
    expect(store.actionBusy).toBe(false)
  })
})
