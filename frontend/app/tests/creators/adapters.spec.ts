import { describe, expect, it, vi } from 'vitest'

import {
  getLiveProbe,
  listHistoryOwners,
  listOwnerSessions,
  submitLiveProbe,
  updateOwnerPreference,
} from '../../src/api/history'
import {
  readOwner,
  readOwnerPosts,
  startOwnerAllDownload,
  startOwnerSelectedDownload,
} from '../../src/api/owners'
import {
  addCollaboration,
  attachAccount,
  attachAccountByLink,
  createPerson,
  deletePerson,
  detachAccount,
  getPersonDetail,
  listPeople,
  removeCollaboration,
  searchAccounts,
  updatePerson,
} from '../../src/api/people'
import { resolveResources } from '../../src/api/resolve'

//
// Every adapter is checked against the exact request the backend expects: the
// url, the method, and the body. These are the only places in the application
// that know a backend url, so a mistake here is invisible everywhere else until
// it reaches a running server.
//

function stubFetch(data: unknown, status = 200) {
  const fake = vi.fn((_url: string, _init?: RequestInit) =>
    Promise.resolve(
      new Response(JSON.stringify({ status: 'success', code: status, data }), {
        status,
        headers: { 'Content-Type': 'application/json' },
      }),
    ),
  )
  vi.stubGlobal('fetch', fake)
  return fake
}

function callOf(fake: ReturnType<typeof stubFetch>) {
  const [url, init] = fake.mock.calls[0]
  const options = init ?? {}
  return {
    url,
    method: options.method,
    body: options.body ? JSON.parse(String(options.body)) : undefined,
    signal: options.signal,
  }
}

describe('history: listing accounts', () => {
  it('reads the history endpoint with no filters', async () => {
    const fake = stubFetch({ total: 0, page: 1, page_size: 20, items: [] })

    await listHistoryOwners({})

    expect(callOf(fake).url).toBe('/api/history/owners')
  })

  it('sends every filter the backend understands', async () => {
    const fake = stubFetch({ total: 0, page: 1, page_size: 20, items: [] })

    await listHistoryOwners({
      q: '主播',
      favorite: true,
      score_min: 10,
      score_max: 90,
      last_live_within: '24h',
      user_status: '正常',
      sort: 'score',
      order: 'asc',
      page: 3,
      page_size: 50,
    })

    const { url } = callOf(fake)
    expect(url).toContain('q=%E4%B8%BB%E6%92%AD')
    expect(url).toContain('favorite=true')
    expect(url).toContain('score_min=10')
    expect(url).toContain('score_max=90')
    expect(url).toContain('last_live_within=24h')
    expect(url).toContain('user_status=%E6%AD%A3%E5%B8%B8')
    expect(url).toContain('sort=score')
    expect(url).toContain('order=asc')
    expect(url).toContain('page=3')
    expect(url).toContain('page_size=50')
  })

  it('omits the filters that were not set', async () => {
    const fake = stubFetch({ total: 0, page: 1, page_size: 20, items: [] })

    await listHistoryOwners({ page: 2 })

    expect(callOf(fake).url).toBe('/api/history/owners?page=2')
  })

  it('sends favorite=false rather than dropping it', async () => {
    //
    // `false` is a real choice here - "not favourited" - and the query builder
    // must not treat it like an unset field.
    //
    const fake = stubFetch({ total: 0, page: 1, page_size: 20, items: [] })

    await listHistoryOwners({ favorite: false })

    expect(callOf(fake).url).toBe('/api/history/owners?favorite=false')
  })

  it('passes an abort signal down', async () => {
    const fake = stubFetch({ total: 0, page: 1, page_size: 20, items: [] })
    const controller = new AbortController()

    await listHistoryOwners({}, controller.signal)

    expect(callOf(fake).signal).toBe(controller.signal)
  })
})

describe('history: one account sessions', () => {
  it('reads the sessions of one account', async () => {
    const fake = stubFetch({ items: [] })

    await listOwnerSessions('58859666123')

    expect(callOf(fake).url).toBe('/api/history/owners/58859666123/sessions')
  })

  it('sends a limit when asked for one', async () => {
    const fake = stubFetch({ items: [] })

    await listOwnerSessions('58859666123', { limit: 20 })

    expect(callOf(fake).url).toBe('/api/history/owners/58859666123/sessions?limit=20')
  })

  it('escapes an id that would otherwise change the path', async () => {
    const fake = stubFetch({ items: [] })

    await listOwnerSessions('../secret')

    expect(callOf(fake).url).toContain('%2F')
  })
})

describe('history: owner preference', () => {
  it('patches the encoded History account with the exact discriminated payload', async () => {
    const fake = stubFetch({
      owner_user_id: '../owner',
      favorite: true,
      score: 0,
    })

    await updateOwnerPreference('../owner', { favorite: true, score: 0 })

    const call = callOf(fake)
    expect(call.url).toBe('/api/history/owners/..%2Fowner/preference')
    expect(call.method).toBe('PATCH')
    expect(call.body).toEqual({ favorite: true, score: 0 })
  })

  it('removes a preference without inventing a score', async () => {
    const fake = stubFetch({ owner_user_id: 'owner-1', favorite: false, score: null })

    await updateOwnerPreference('owner-1', { favorite: false })

    expect(callOf(fake).body).toEqual({ favorite: false })
  })
})

describe('resolve: batch', () => {
  it('sends the complete pasted input for server-side extraction', async () => {
    const fake = stubFetch({
      total: 0,
      resolved_count: 0,
      failed_count: 0,
      items: [],
    })
    const input = '分享 A https://v.douyin.com/A/\n分享 B https://v.douyin.com/B/'

    await resolveResources(input)

    expect(callOf(fake)).toMatchObject({
      url: '/api/resolve/batch',
      method: 'POST',
      body: { input },
    })
  })
})

describe('history: live probe', () => {
  it('submits exactly the ids it was given', async () => {
    const fake = stubFetch({ batch_id: 'B', task_id: 'T', done: false, items: [] }, 202)

    await submitLiveProbe(['1', '2', '3'])

    const call = callOf(fake)
    expect(call.url).toBe('/api/live/probe')
    expect(call.method).toBe('POST')
    expect(call.body).toEqual({ owner_user_ids: ['1', '2', '3'] })
  })

  it('accepts the 202 the backend answers', async () => {
    stubFetch({ batch_id: 'B', task_id: 'T', done: true, items: [] }, 202)

    await expect(submitLiveProbe(['1'])).resolves.toEqual({
      batch_id: 'B',
      task_id: 'T',
      done: true,
      items: [],
    })
  })

  it('reads one batch back', async () => {
    const fake = stubFetch({ batch_id: 'B', done: false, items: [] })

    await getLiveProbe('B')

    expect(callOf(fake).url).toBe('/api/live/probe/B')
  })
})

describe('owner: reading a profile', () => {
  it('reads the owner endpoint with the url it was given', async () => {
    const fake = stubFetch({ sec_user_id: 'MS4w', owner: null, posts: [] })

    await readOwner('https://www.douyin.com/user/MS4w')

    expect(callOf(fake).url).toBe(
      '/api/owner?url=https%3A%2F%2Fwww.douyin.com%2Fuser%2FMS4w',
    )
  })

  it('reads a page of posts by cursor', async () => {
    const fake = stubFetch({ posts: [], next_cursor: 0, has_more: false })

    await readOwnerPosts('MS4w', 0)

    expect(callOf(fake).url).toBe('/api/owner/posts?sec_user_id=MS4w&cursor=0')
  })

  it('sends a non-zero cursor', async () => {
    const fake = stubFetch({ posts: [], next_cursor: 0, has_more: false })

    await readOwnerPosts('MS4w', 1712484087000)

    expect(callOf(fake).url).toContain('cursor=1712484087000')
  })
})

describe('owner: starting downloads', () => {
  it('sends only the ids for a selected download', async () => {
    //
    // The payloads themselves stay on the server, in its own cache. The browser
    // says which posts, never what they contain.
    //
    const fake = stubFetch({ job_id: 'J', task_id: 'T' })

    await startOwnerSelectedDownload(['1', '2'])

    const call = callOf(fake)
    expect(call.url).toBe('/api/owner/download')
    expect(call.method).toBe('POST')
    expect(call.body).toEqual({ aweme_ids: ['1', '2'] })
  })

  it('carries a share url when there is one', async () => {
    const fake = stubFetch({ job_id: 'J', task_id: 'T' })

    await startOwnerSelectedDownload(['1'], 'https://v.douyin.com/abc/')

    expect(callOf(fake).body).toEqual({
      aweme_ids: ['1'],
      share_url: 'https://v.douyin.com/abc/',
    })
  })

  it('asks for everything by owner id, not by listing ids', async () => {
    const fake = stubFetch({ job_id: 'J', task_id: 'T' })

    await startOwnerAllDownload('MS4w')

    expect(callOf(fake).body).toEqual({ all: true, sec_user_id: 'MS4w' })
  })
})

describe('people: reading', () => {
  it('lists people', async () => {
    //
    // The stub answers with the shape the backend actually sends. It used to
    // answer with a bare array, which no endpoint here has ever returned - so
    // this asserted the request and silently agreed with the adapter about a
    // response neither of them had ever seen.
    //
    const fake = stubFetch({ persons: [] })

    await listPeople()

    expect(callOf(fake).url).toBe('/api/person')
  })

  it('unwraps the persons the envelope carries', async () => {
    //
    // `request` unwraps the envelope's `data` and stops there. Everything past
    // that is this adapter's job, and getting it wrong is invisible to any test
    // that mocks this module: the store sees whatever the mock promised rather
    // than what the server sends.
    //
    stubFetch({
      persons: [
        { person_id: 1, display_name: '甲', directory_name: null, note: null, account_count: 1 },
        { person_id: 2, display_name: '乙', directory_name: null, note: null, account_count: 0 },
      ],
    })

    const people = await listPeople()

    expect(Array.isArray(people)).toBe(true)
    expect(people.map((one) => one.person_id)).toEqual([1, 2])
  })

  it('reads one person detail', async () => {
    const fake = stubFetch({ accounts: [], summary: {}, subjects: [], photographers: [] })

    await getPersonDetail(7)

    expect(callOf(fake).url).toBe('/api/person/7/detail')
  })

  it('searches known accounts by keyword', async () => {
    const fake = stubFetch({ accounts: [] })

    await searchAccounts('绿萝')

    expect(callOf(fake).url).toBe('/api/person/accounts?keyword=%E7%BB%BF%E8%90%9D')
  })

  it('unwraps the accounts the envelope carries', async () => {
    stubFetch({
      accounts: [
        {
          owner_user_id: '58859666123',
          nickname: '绿萝',
          directory_name: '绿萝',
          person_id: null,
          role: null,
        },
      ],
    })

    const accounts = await searchAccounts('绿萝')

    expect(Array.isArray(accounts)).toBe(true)
    expect(accounts.map((one) => one.owner_user_id)).toEqual(['58859666123'])
  })
})

describe('people: writing', () => {
  it('creates a person', async () => {
    const fake = stubFetch({ person_id: 7 })

    await createPerson({ display_name: '某人', note: '备注' })

    const call = callOf(fake)
    expect(call.url).toBe('/api/person')
    expect(call.method).toBe('POST')
    expect(call.body).toEqual({ display_name: '某人', note: '备注' })
  })

  it('patches only what changed', async () => {
    const fake = stubFetch({ person_id: 7 })

    await updatePerson(7, { note: '新的备注' })

    const call = callOf(fake)
    expect(call.url).toBe('/api/person/7')
    expect(call.method).toBe('PATCH')
    expect(call.body).toEqual({ note: '新的备注' })
  })

  it('deletes a person with no body', async () => {
    const fake = stubFetch({ person_id: 7 })

    await deletePerson(7)

    const call = callOf(fake)
    expect(call.url).toBe('/api/person/7')
    expect(call.method).toBe('DELETE')
    expect(call.body).toBeUndefined()
  })
})

describe('people: accounts', () => {
  it('attaches a known account by id', async () => {
    //
    // Only the three fields the endpoint reads. A nickname sent from here would
    // be the browser asserting something the database already knows better.
    //
    const fake = stubFetch({ owner_user_id: '1', person_id: 7 })

    await attachAccount({ owner_user_id: '1', person_id: 7, role: 'alt' })

    const call = callOf(fake)
    expect(call.url).toBe('/api/person/account')
    expect(call.method).toBe('POST')
    expect(call.body).toEqual({ owner_user_id: '1', person_id: 7, role: 'alt' })
  })

  it('attaches by an already-resolved link', async () => {
    const fake = stubFetch({ owner_user_id: '1', person_id: 7 })

    await attachAccountByLink({
      url: 'https://www.douyin.com/video/7657271784144009946',
      person_id: 7,
      role: 'main',
    })

    const call = callOf(fake)
    expect(call.url).toBe('/api/person/account/by-link')
    expect(call.body).toEqual({
      url: 'https://www.douyin.com/video/7657271784144009946',
      person_id: 7,
      role: 'main',
    })
  })

  it('detaches by owner id in the query string', async () => {
    const fake = stubFetch({ owner_user_id: '1' })

    await detachAccount('58859666123')

    const call = callOf(fake)
    expect(call.url).toBe('/api/person/account?owner_user_id=58859666123')
    expect(call.method).toBe('DELETE')
    expect(call.body).toBeUndefined()
  })
})

describe('people: collaboration', () => {
  it('records a direction, not a pairing', async () => {
    const fake = stubFetch({ photographer_id: 3, subject_id: 9 })

    await addCollaboration({ photographer_id: 3, subject_id: 9, note: '外拍' })

    const call = callOf(fake)
    expect(call.url).toBe('/api/person/collaboration')
    expect(call.method).toBe('POST')
    expect(call.body).toEqual({ photographer_id: 3, subject_id: 9, note: '外拍' })
  })

  it('removes the exact direction it was told to', async () => {
    const fake = stubFetch({ photographer_id: 3, subject_id: 9 })

    await removeCollaboration(3, 9)

    const call = callOf(fake)
    expect(call.url).toBe('/api/person/collaboration?photographer_id=3&subject_id=9')
    expect(call.method).toBe('DELETE')
  })
})

describe('the identity adapters stop where the library begins', () => {
  it('reads a person without reading what they filmed', async () => {
    //
    // Through the creators phase this asserted that no works reader existed at
    // all. The library phase wired one deliberately - `/person/<id>/works`
    // returns content, and content is that phase's business - so the claim
    // moved rather than disappeared: the adapter may exist, and the identity
    // screen still must not call it.
    //
    // Where each half now lives:
    //   the adapter's own contract  -> tests/library/adapters.spec.ts
    //   the identity store's reach  -> tests/people/people-store.spec.ts
    //
    // What remains true here is the shape of a person read: one detail call,
    // and nothing that walks their downloads.
    //
    const fake = stubFetch({ accounts: [], summary: {}, subjects: [], photographers: [] })

    await getPersonDetail(7)

    expect(fake).toHaveBeenCalledTimes(1)
    expect(callOf(fake).url).toBe('/api/person/7/detail')
  })
})
