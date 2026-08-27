import { createPinia, setActivePinia } from 'pinia'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import { readOwner } from '../../src/api/owners'
import { inspectPersonAssignment } from '../../src/api/people'
import { resolveResource } from '../../src/api/resolve'
import { useCreatorLookupStore } from '../../src/stores/creatorLookup'
import type { OwnerRead } from '../../src/types/owner'
import type { PersonIdentityInspection } from '../../src/types/person'
import type { ResolvedResource } from '../../src/types/resolution'

vi.mock('../../src/api/owners', () => ({ readOwner: vi.fn() }))
vi.mock('../../src/api/people', () => ({ inspectPersonAssignment: vi.fn() }))
vi.mock('../../src/api/resolve', () => ({ resolveResource: vi.fn() }))

const mockedReadOwner = vi.mocked(readOwner)
const mockedInspect = vi.mocked(inspectPersonAssignment)
const mockedResolve = vi.mocked(resolveResource)

const SEC_UID_A = 'MS4wLjABAAAA-owner-a'
const SEC_UID_B = 'MS4wLjABAAAA-owner-b'

function ownerResolution(
  resolveId = 'receipt-a',
  secUserId = SEC_UID_A,
): ResolvedResource {
  return {
    resolve_id: resolveId,
    platform: 'douyin',
    resource_type: 'owner',
    source_url: 'https://v.douyin.com/share/',
    resolved_url: `https://www.douyin.com/user/${secUserId}`,
    identity: { sec_user_id: secUserId },
    expires_in_seconds: 600,
  }
}

function postResolution(): ResolvedResource {
  return {
    resolve_id: 'receipt-post',
    platform: 'douyin',
    resource_type: 'post',
    source_url: 'https://v.douyin.com/post/',
    resolved_url: 'https://www.douyin.com/video/7657271784144009946',
    identity: { aweme_id: '7657271784144009946' },
    expires_in_seconds: 600,
  }
}

function ownerRead(nickname = '平台昵称 A', secUserId = SEC_UID_A): OwnerRead {
  return {
    sec_user_id: secUserId,
    owner: {
      sec_user_id: secUserId,
      uid: 'platform-uid',
      nickname,
      unique_id: 'douyin-name',
      signature: '平台签名',
      avatar_url: 'https://example.test/avatar.jpg',
      follower_count: 1200,
      following_count: 33,
      aweme_count: 87,
      total_favorited: 9900,
    },
    owner_message: null,
    credential: { expires_in_days: 12 },
    posts: [
      {
        aweme_id: '7657271784144009946',
        desc: 'the lookup must discard this post',
        create_time: 1,
        cover_url: 'https://example.test/cover.jpg',
        duration: 15,
        aweme_type: 'video',
        digg_count: 3,
        comment_count: 1,
        downloaded: false,
        saved_count: 0,
        media_count: 1,
      },
    ],
    next_cursor: 1,
    has_more: true,
  }
}

function inspection(
  nickname = '本地昵称 A',
  personId = 17,
): PersonIdentityInspection {
  return {
    owner: {
      owner_user_id: `local-owner-${personId}`,
      sec_user_id: SEC_UID_A,
      nickname,
    },
    known_account: true,
    assignment: { person_id: personId, display_name: `人物 ${personId}`, role: 'main' },
  }
}

function deferred<T>() {
  let resolve!: (value: T) => void
  let reject!: (reason?: unknown) => void
  const promise = new Promise<T>((yes, no) => {
    resolve = yes
    reject = no
  })
  return { promise, resolve, reject }
}

async function settle() {
  for (let index = 0; index < 6; index += 1) {
    await Promise.resolve()
  }
}

beforeEach(() => {
  setActivePinia(createPinia())
  vi.clearAllMocks()
})

describe('the creator lookup trust boundary', () => {
  it('resolves raw input, then reads platform and local facts in parallel from server answers', async () => {
    const resolution = ownerResolution()
    mockedResolve.mockResolvedValue(resolution)
    mockedReadOwner.mockResolvedValue(ownerRead())
    mockedInspect.mockResolvedValue(inspection())
    const store = useCreatorLookupStore()

    await store.lookup('复制打开抖音 https://v.douyin.com/share/')

    expect(mockedResolve).toHaveBeenCalledWith(
      '复制打开抖音 https://v.douyin.com/share/',
      expect.any(AbortSignal),
    )
    expect(mockedReadOwner).toHaveBeenCalledWith(resolution.resolved_url, expect.any(AbortSignal))
    expect(mockedInspect).toHaveBeenCalledWith('receipt-a', expect.any(AbortSignal))
    expect(store.platformProfile?.nickname).toBe('平台昵称 A')
    expect(store.localInspection?.owner.nickname).toBe('本地昵称 A')
    expect(store.platformCredential).toEqual({ expires_in_days: 12 })
    expect('posts' in store).toBe(false)
    expect('nextCursor' in store).toBe(false)
    expect('hasMore' in store).toBe(false)
  })

  it('stops after a non-owner resolution without touching either downstream API', async () => {
    mockedResolve.mockResolvedValue(postResolution())
    const store = useCreatorLookupStore()

    await store.lookup('https://v.douyin.com/post/')

    expect(store.queryError).toBe('该链接不是主播主页，请粘贴主播主页分享链接。')
    expect(mockedReadOwner).not.toHaveBeenCalled()
    expect(mockedInspect).not.toHaveBeenCalled()
  })

  it('stops after resolution failure without touching either downstream API', async () => {
    mockedResolve.mockRejectedValue(new Error('resolver offline'))
    const store = useCreatorLookupStore()

    await store.lookup('https://v.douyin.com/broken/')

    expect(store.queryError).toBe('无法解析主播链接')
    expect(mockedReadOwner).not.toHaveBeenCalled()
    expect(mockedInspect).not.toHaveBeenCalled()
  })
})

describe('independent platform and local facts', () => {
  it('keeps local facts when the platform read fails', async () => {
    mockedResolve.mockResolvedValue(ownerResolution())
    mockedReadOwner.mockRejectedValue(new Error('platform offline'))
    mockedInspect.mockResolvedValue(inspection())
    const store = useCreatorLookupStore()

    await store.lookup('owner')

    expect(store.platformError).toBe('平台资料暂时无法读取')
    expect(store.localInspection?.assignment?.display_name).toBe('人物 17')
    expect(store.localError).toBeNull()
  })

  it('keeps platform facts when local inspection fails', async () => {
    mockedResolve.mockResolvedValue(ownerResolution())
    mockedReadOwner.mockResolvedValue(ownerRead())
    mockedInspect.mockRejectedValue(new Error('database unavailable'))
    const store = useCreatorLookupStore()

    await store.lookup('owner')

    expect(store.platformProfile?.nickname).toBe('平台昵称 A')
    expect(store.localError).toBe('暂时无法确认本地账号归属')
    expect(store.localInspection).toBeNull()
  })

  it('retains the safe owner message without turning a missing profile into a query failure', async () => {
    mockedResolve.mockResolvedValue(ownerResolution())
    mockedReadOwner.mockResolvedValue({
      ...ownerRead(),
      owner: null,
      owner_message: '主播详情暂时不可用',
    })
    mockedInspect.mockResolvedValue(inspection())
    const store = useCreatorLookupStore()

    await store.lookup('owner')

    expect(store.platformProfile).toBeNull()
    expect(store.platformMessage).toBe('主播详情暂时不可用')
    expect(store.platformError).toBeNull()
    expect(store.localInspection?.known_account).toBe(true)
  })
})

describe('stale result protection', () => {
  it('keeps query B when slower query A completes last', async () => {
    const resolveA = deferred<ResolvedResource>()
    const ownerA = deferred<OwnerRead>()
    const inspectA = deferred<PersonIdentityInspection>()
    mockedResolve.mockImplementationOnce(() => resolveA.promise)
    mockedReadOwner.mockImplementationOnce(() => ownerA.promise)
    mockedInspect.mockImplementationOnce(() => inspectA.promise)
    const store = useCreatorLookupStore()

    const queryA = store.lookup('A')
    resolveA.resolve(ownerResolution('receipt-a', SEC_UID_A))
    await settle()

    mockedResolve.mockResolvedValueOnce(ownerResolution('receipt-b', SEC_UID_B))
    mockedReadOwner.mockResolvedValueOnce(ownerRead('平台昵称 B', SEC_UID_B))
    mockedInspect.mockResolvedValueOnce(inspection('本地昵称 B', 29))
    const queryB = store.lookup('B')
    expect(mockedResolve.mock.calls[0]?.[1]?.aborted).toBe(true)
    await queryB

    ownerA.resolve(ownerRead('平台昵称 A', SEC_UID_A))
    inspectA.resolve(inspection('本地昵称 A', 17))
    await queryA

    expect(store.platformProfile?.nickname).toBe('平台昵称 B')
    expect(store.localInspection?.owner.nickname).toBe('本地昵称 B')
    expect(store.localInspection?.assignment?.person_id).toBe(29)
  })

  it('stays empty when input editing invalidates query A and A settles late', async () => {
    const lateResolution = deferred<ResolvedResource>()
    mockedResolve.mockImplementationOnce(() => lateResolution.promise)
    const store = useCreatorLookupStore()

    const queryA = store.lookup('A')
    store.invalidate()
    expect(mockedResolve.mock.calls[0]?.[1]?.aborted).toBe(true)
    lateResolution.resolve(ownerResolution())
    await queryA

    expect(store.hasResult).toBe(false)
    expect(store.queryError).toBeNull()
    expect(store.platformProfile).toBeNull()
    expect(store.localInspection).toBeNull()
    expect(mockedReadOwner).not.toHaveBeenCalled()
    expect(mockedInspect).not.toHaveBeenCalled()
  })
})
