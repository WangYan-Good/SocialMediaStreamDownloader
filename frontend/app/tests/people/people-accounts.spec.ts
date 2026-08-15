import { createPinia, setActivePinia } from 'pinia'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import { ApiError } from '../../src/api/client'
import {
  attachAccount,
  attachAccountByLink,
  detachAccount,
  listPeople,
  searchAccounts,
} from '../../src/api/people'
import { resolveResource } from '../../src/api/resolve'
import { usePeopleStore } from '../../src/stores/people'
import type { AccountSearchResult } from '../../src/types/person'
import type { ResolvedResource } from '../../src/types/resolution'
import { detail, person } from './fixtures'

vi.mock('../../src/api/people', () => ({
  listPeople: vi.fn(),
  createPerson: vi.fn(),
  updatePerson: vi.fn(),
  deletePerson: vi.fn(),
  getPersonDetail: vi.fn(),
  searchAccounts: vi.fn(),
  attachAccount: vi.fn(),
  attachAccountByLink: vi.fn(),
  detachAccount: vi.fn(),
  addCollaboration: vi.fn(),
  removeCollaboration: vi.fn(),
}))
vi.mock('../../src/api/resolve', () => ({ resolveResource: vi.fn() }))

const mockedList = vi.mocked(listPeople)
const mockedSearch = vi.mocked(searchAccounts)
const mockedAttach = vi.mocked(attachAccount)
const mockedAttachByLink = vi.mocked(attachAccountByLink)
const mockedDetach = vi.mocked(detachAccount)
const mockedResolve = vi.mocked(resolveResource)

const SHORT_LINK = 'https://v.douyin.com/abc/'
const RESOLVED_POST = 'https://www.douyin.com/video/7657271784144009946'

function account(overrides: Partial<AccountSearchResult> = {}): AccountSearchResult {
  return {
    owner_user_id: '58859666123',
    nickname: '主播',
    directory_name: '主播',
    person_id: null,
    role: null,
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

async function storeWithPerson(personId = 7) {
  mockedList.mockResolvedValue([person({ person_id: personId })])
  const { getPersonDetail } = await import('../../src/api/people')
  vi.mocked(getPersonDetail).mockResolvedValue(detail())
  const store = usePeopleStore()
  await store.loadPeople()
  await store.selectPerson(personId)
  return store
}

beforeEach(() => {
  setActivePinia(createPinia())
  vi.clearAllMocks()
  mockedList.mockResolvedValue([])
  mockedSearch.mockResolvedValue([])
})

describe('searching known accounts', () => {
  it('searches by the keyword it was given', async () => {
    const store = usePeopleStore()

    await store.searchAccounts('绿萝')

    expect(mockedSearch).toHaveBeenCalledWith('绿萝')
  })

  it('does not search for nothing', async () => {
    const store = usePeopleStore()

    await store.searchAccounts('   ')

    expect(mockedSearch).not.toHaveBeenCalled()
  })

  it('keeps what the server returned', async () => {
    mockedSearch.mockResolvedValue([
      account({ owner_user_id: 'A', person_id: 3, role: 'alt' }),
    ])
    const store = usePeopleStore()

    await store.searchAccounts('a')

    expect(store.accountSearchResults).toHaveLength(1)
    expect(store.accountSearchResults[0].person_id).toBe(3)
  })

  it('cannot be crossed by an earlier keyword answering late', async () => {
    //
    // Type "a", then "ab". The answer for "a" arriving afterwards would list
    // accounts that do not match what is in the box.
    //
    const slow = deferred<AccountSearchResult[]>()
    const fast = deferred<AccountSearchResult[]>()
    mockedSearch.mockReturnValueOnce(slow.promise).mockReturnValueOnce(fast.promise)
    const store = usePeopleStore()

    const first = store.searchAccounts('a')
    const second = store.searchAccounts('ab')

    fast.settle([account({ owner_user_id: 'FROM-AB' })])
    await second
    await drain()

    slow.settle([account({ owner_user_id: 'FROM-A' })])
    await first
    await drain()

    expect(store.accountSearchResults.map((one) => one.owner_user_id)).toEqual(['FROM-AB'])
  })
})

describe('attaching a known account', () => {
  it('sends only the three fields the endpoint reads', async () => {
    //
    // A nickname or a directory name sent from here would be the browser
    // asserting something the database already knows better.
    //
    mockedAttach.mockResolvedValue({ owner_user_id: '1', person_id: 7 })
    const store = await storeWithPerson(7)

    await store.attachAccount({ owner_user_id: '1', person_id: 7, role: 'alt' })

    expect(mockedAttach).toHaveBeenCalledWith({
      owner_user_id: '1',
      person_id: 7,
      role: 'alt',
    })
  })

  it('sends the role as a wire value, never a label', async () => {
    mockedAttach.mockResolvedValue({ owner_user_id: '1', person_id: 7 })
    const store = await storeWithPerson(7)

    await store.attachAccount({ owner_user_id: '1', person_id: 7, role: 'main' })

    const sent = JSON.stringify(mockedAttach.mock.calls[0][0])
    expect(sent).toContain('"role":"main"')
    expect(sent).not.toContain('主号')
  })

  it('re-reads the list, the detail and the search afterwards', async () => {
    //
    // All three show the same fact from different angles, and leaving any of
    // them stale would show an account in two places at once.
    //
    mockedAttach.mockResolvedValue({ owner_user_id: '1', person_id: 7 })
    mockedSearch.mockResolvedValue([account({ owner_user_id: '1', person_id: 7 })])
    const store = await storeWithPerson(7)
    await store.searchAccounts('主播')
    const listBefore = mockedList.mock.calls.length
    const searchBefore = mockedSearch.mock.calls.length

    await store.attachAccount({ owner_user_id: '1', person_id: 7, role: 'alt' })

    expect(mockedList.mock.calls.length).toBeGreaterThan(listBefore)
    expect(mockedSearch.mock.calls.length).toBeGreaterThan(searchBefore)
  })

  it('cannot be submitted twice', async () => {
    const pending = deferred<{ owner_user_id: string; person_id: number }>()
    mockedAttach.mockReturnValue(pending.promise)
    const store = await storeWithPerson(7)

    const first = store.attachAccount({ owner_user_id: '1', person_id: 7, role: 'alt' })
    await drain()
    await store.attachAccount({ owner_user_id: '1', person_id: 7, role: 'alt' })

    expect(mockedAttach).toHaveBeenCalledTimes(1)

    pending.settle({ owner_user_id: '1', person_id: 7 })
    await first
  })
})

describe('knowing when an attachment is really a move', () => {
  it('says nothing is being moved for an unattached account', () => {
    const store = usePeopleStore()

    expect(store.movesAccountFrom(account({ person_id: null }), 7)).toBeNull()
  })

  it('says nothing is being moved when it already belongs here', () => {
    const store = usePeopleStore()

    expect(store.movesAccountFrom(account({ person_id: 7 }), 7)).toBeNull()
  })

  it('names the person it would be taken from', () => {
    //
    // The backend upserts, so attaching an account that belongs to somebody
    // else silently *moves* it. The interface has to say so first - the api
    // will not ask.
    //
    const store = usePeopleStore()

    expect(store.movesAccountFrom(account({ person_id: 3 }), 7)).toBe(3)
  })
})

describe('detaching an account', () => {
  it('sends the owner id', async () => {
    mockedDetach.mockResolvedValue({ owner_user_id: '1' })
    const store = await storeWithPerson(7)

    await store.detachAccount('1')

    expect(mockedDetach).toHaveBeenCalledWith('1')
  })

  it('re-reads everything that shows the attachment', async () => {
    mockedDetach.mockResolvedValue({ owner_user_id: '1' })
    const store = await storeWithPerson(7)
    const before = mockedList.mock.calls.length

    await store.detachAccount('1')

    expect(mockedList.mock.calls.length).toBeGreaterThan(before)
  })

  it('cannot be submitted twice', async () => {
    const pending = deferred<{ owner_user_id: string }>()
    mockedDetach.mockReturnValue(pending.promise)
    const store = await storeWithPerson(7)

    const first = store.detachAccount('1')
    await drain()
    await store.detachAccount('1')

    expect(mockedDetach).toHaveBeenCalledTimes(1)

    pending.settle({ owner_user_id: '1' })
    await first
  })
})

describe('attaching by a pasted link', () => {
  function resolution(overrides: Partial<ResolvedResource> = {}): ResolvedResource {
    return {
      resolve_id: 'receipt-1',
      platform: 'douyin',
      resource_type: 'post',
      source_url: SHORT_LINK,
      resolved_url: RESOLVED_POST,
      identity: { aweme_id: '7657271784144009946' },
      expires_in_seconds: 600,
      ...overrides,
    } as ResolvedResource
  }

  it('resolves the paste before the person api sees it', async () => {
    //
    // The person endpoint follows a link itself to find whose account it is.
    // Handing it an already-resolved url means the short link was followed once,
    // by the resolver, under its host allow list and hop limit - rather than a
    // second time by an older path that never had those checks.
    //
    mockedResolve.mockResolvedValue(resolution())
    mockedAttachByLink.mockResolvedValue({ owner_user_id: '1', person_id: 7 })
    const store = await storeWithPerson(7)

    await store.attachAccountByLink(SHORT_LINK, 7, 'alt')

    expect(mockedResolve).toHaveBeenCalledWith(SHORT_LINK)
    expect(mockedAttachByLink).toHaveBeenCalledWith({
      url: RESOLVED_POST,
      person_id: 7,
      role: 'alt',
    })
  })

  it('never sends the raw paste or the source url', async () => {
    mockedResolve.mockResolvedValue(resolution())
    mockedAttachByLink.mockResolvedValue({ owner_user_id: '1', person_id: 7 })
    const store = await storeWithPerson(7)

    await store.attachAccountByLink('4.33 复制打开抖音 ' + SHORT_LINK, 7, 'main')

    const sent = mockedAttachByLink.mock.calls[0][0].url
    expect(sent).toBe(RESOLVED_POST)
    expect(sent).not.toContain('v.douyin.com')
  })

  it.each(['post', 'owner', 'live'] as const)(
    'accepts a resolved %s, because the endpoint finds the owner either way',
    async (resourceType) => {
      //
      // Deliberately not restricted to owner links. The person endpoint can
      // identify the account behind a post or a live room too; the resolver's
      // job here is only to make the url safe to hand over.
      //
      mockedResolve.mockResolvedValue(resolution({ resource_type: resourceType }))
      mockedAttachByLink.mockResolvedValue({ owner_user_id: '1', person_id: 7 })
      const store = await storeWithPerson(7)

      await store.attachAccountByLink(SHORT_LINK, 7, 'alt')

      expect(mockedAttachByLink).toHaveBeenCalledTimes(1)
    },
  )

  it('attaches nothing when the paste cannot be resolved', async () => {
    mockedResolve.mockRejectedValue(
      new ApiError({ kind: 'backend', status: 400, code: 400, message: '没有找到可解析的链接' }),
    )
    const store = await storeWithPerson(7)

    await store.attachAccountByLink('这段文字里没有链接', 7, 'alt')

    expect(mockedAttachByLink).not.toHaveBeenCalled()
    expect(store.mutationError).toContain('没有找到可解析的链接')
  })

  it('refuses a second paste while the first is still being resolved', async () => {
    //
    // Two link attachments cannot overlap at all: this is a write, and the
    // in-flight guard turns "paste A, change to B, click again" into one
    // attachment rather than a race to decide which url wins.
    //
    // The generation check inside the action is a second lock on the same door
    // - see the store - and is deliberately unreachable while this guard holds.
    //
    const slow = deferred<ResolvedResource>()
    mockedResolve.mockReturnValueOnce(slow.promise)
    mockedAttachByLink.mockResolvedValue({ owner_user_id: '1', person_id: 7 })
    const store = await storeWithPerson(7)

    const first = store.attachAccountByLink('A', 7, 'alt')
    await drain()
    await store.attachAccountByLink('B', 7, 'alt')

    expect(mockedResolve).toHaveBeenCalledTimes(1)

    slow.settle(resolution({ resolved_url: 'https://www.douyin.com/video/FROM-A' }))
    await first
    await drain()

    const urls = mockedAttachByLink.mock.calls.map((call) => call[0].url)
    expect(urls).toEqual(['https://www.douyin.com/video/FROM-A'])
  })

  it('cannot be submitted twice', async () => {
    const pending = deferred<ResolvedResource>()
    mockedResolve.mockReturnValue(pending.promise)
    const store = await storeWithPerson(7)

    const first = store.attachAccountByLink(SHORT_LINK, 7, 'alt')
    await drain()
    await store.attachAccountByLink(SHORT_LINK, 7, 'alt')

    expect(mockedResolve).toHaveBeenCalledTimes(1)

    pending.settle(resolution())
    mockedAttachByLink.mockResolvedValue({ owner_user_id: '1', person_id: 7 })
    await first
  })
})

//
// One person, one main account.
//
// The backend does not constrain this: the role column takes any value and
// nothing stops two rows saying 'main'. But the folder a person's downloads
// land in is resolved by joining on role = 'main' and taking LIMIT 1 with no
// ordering, and the query that copies the main folder onto the other accounts
// deliberately skips main rows - so two mains means two folders and a
// non-deterministic answer about which one an alt account downloads into.
//
// Guarded here rather than in the schema: this phase does not touch the
// backend, and the interface is where the second main would be created.
//
async function storeHolding(accounts: { owner_user_id: string; nickname: string | null; role: 'main' | 'alt' | 'matrix' }[]) {
  mockedList.mockResolvedValue([person({ person_id: 7 })])
  const { getPersonDetail } = await import('../../src/api/people')
  vi.mocked(getPersonDetail).mockResolvedValue(detail({ accounts }))
  const store = usePeopleStore()
  await store.loadPeople()
  await store.selectPerson(7)
  return store
}

describe('a person may hold only one main account', () => {
  it('accepts a main when there is none yet', async () => {
    const store = await storeHolding([{ owner_user_id: 'A', nickname: '甲', role: 'alt' }])
    mockedAttach.mockResolvedValue({ owner_user_id: 'B', person_id: 7 })

    await store.attachAccount({ owner_user_id: 'B', person_id: 7, role: 'main' })

    expect(mockedAttach).toHaveBeenCalledWith({
      owner_user_id: 'B',
      person_id: 7,
      role: 'main',
    })
    expect(store.mutationError).toBeNull()
  })

  it('refuses a second main and names the one already there', async () => {
    const store = await storeHolding([{ owner_user_id: 'A', nickname: '甲', role: 'main' }])

    await store.attachAccount({ owner_user_id: 'B', person_id: 7, role: 'main' })

    expect(store.mutationError).toContain('甲')
    expect(store.mutationError).toContain('主号')
  })

  it('writes nothing at all when it refuses', async () => {
    //
    // The whole point: no request leaves the browser, so there is no window in
    // which the database holds two mains.
    //
    const store = await storeHolding([{ owner_user_id: 'A', nickname: '甲', role: 'main' }])

    await store.attachAccount({ owner_user_id: 'B', person_id: 7, role: 'main' })

    expect(mockedAttach).not.toHaveBeenCalled()
  })

  it('lets the existing main be re-attached as main', async () => {
    //
    // Not a second main - the same one. Refusing this would make the current
    // state unreachable, so a role could never be re-confirmed.
    //
    const store = await storeHolding([{ owner_user_id: 'A', nickname: '甲', role: 'main' }])
    mockedAttach.mockResolvedValue({ owner_user_id: 'A', person_id: 7 })

    await store.attachAccount({ owner_user_id: 'A', person_id: 7, role: 'main' })

    expect(mockedAttach).toHaveBeenCalledWith({
      owner_user_id: 'A',
      person_id: 7,
      role: 'main',
    })
    expect(store.mutationError).toBeNull()
  })

  it('leaves the other roles alone', async () => {
    const store = await storeHolding([{ owner_user_id: 'A', nickname: '甲', role: 'main' }])
    mockedAttach.mockResolvedValue({ owner_user_id: 'B', person_id: 7 })

    await store.attachAccount({ owner_user_id: 'B', person_id: 7, role: 'alt' })

    expect(mockedAttach).toHaveBeenCalled()
    expect(store.mutationError).toBeNull()
  })

  it('holds the same line for a pasted link', async () => {
    //
    // Which account is behind the link is not known until the person endpoint
    // reads it, so an existing main cannot be ruled out as "the same one" -
    // and this refuses rather than resolving and hoping.
    //
    const store = await storeHolding([{ owner_user_id: 'A', nickname: '甲', role: 'main' }])

    await store.attachAccountByLink(SHORT_LINK, 7, 'main')

    expect(mockedResolve).not.toHaveBeenCalled()
    expect(mockedAttachByLink).not.toHaveBeenCalled()
    expect(store.mutationError).toContain('主号')
  })

  it('still attaches a pasted link under another role', async () => {
    const store = await storeHolding([{ owner_user_id: 'A', nickname: '甲', role: 'main' }])
    mockedResolve.mockResolvedValue({
      resolve_id: 'R-1',
      resource_type: 'post',
      resolved_url: RESOLVED_POST,
    } as ResolvedResource)
    mockedAttachByLink.mockResolvedValue({ owner_user_id: 'B', person_id: 7 })

    await store.attachAccountByLink(SHORT_LINK, 7, 'alt')

    expect(mockedAttachByLink).toHaveBeenCalledWith({
      url: RESOLVED_POST,
      person_id: 7,
      role: 'alt',
    })
  })
})

describe('a main attached before the detail has arrived', () => {
  it('refuses rather than guessing', async () => {
    //
    // The guard reads the person's accounts to know whether a main already
    // exists. While that read is still in flight there is nothing to read, and
    // the two outcomes are not symmetric: a wrong refusal is undone by clicking
    // again, a wrong acceptance leaves two mains and a download folder that is
    // decided by whichever row the database happens to return first.
    //
    const { getPersonDetail } = await import('../../src/api/people')
    const pending = deferred<never>()
    vi.mocked(getPersonDetail).mockReturnValue(pending.promise)
    mockedList.mockResolvedValue([person({ person_id: 7 })])
    const store = usePeopleStore()
    await store.loadPeople()
    void store.selectPerson(7)
    await drain()

    await store.attachAccount({ owner_user_id: 'B', person_id: 7, role: 'main' })

    expect(mockedAttach).not.toHaveBeenCalled()
    expect(store.mutationError).toContain('人物详情')
  })

  it('still allows the other roles through', async () => {
    //
    // Only main is constrained. Blocking an alt because a detail read is slow
    // would be a guard inventing work for itself.
    //
    const { getPersonDetail } = await import('../../src/api/people')
    const pending = deferred<never>()
    vi.mocked(getPersonDetail).mockReturnValue(pending.promise)
    mockedList.mockResolvedValue([person({ person_id: 7 })])
    mockedAttach.mockResolvedValue({ owner_user_id: 'B', person_id: 7 })
    const store = usePeopleStore()
    await store.loadPeople()
    void store.selectPerson(7)
    await drain()

    //
    // Not awaited to completion: the write succeeds and then re-reads the
    // detail, which is the very read being held open here. What matters is that
    // it was sent at all.
    //
    void store.attachAccount({ owner_user_id: 'B', person_id: 7, role: 'alt' })
    await drain()

    expect(mockedAttach).toHaveBeenCalled()
  })
})
