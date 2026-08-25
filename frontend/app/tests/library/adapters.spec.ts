import { describe, expect, it, vi } from 'vitest'

import {
  listLibraryLives,
  listLibraryPosts,
  listLibraryRecordings,
} from '../../src/api/library'
import { getPersonWorks } from '../../src/api/people'

//
// Every adapter is checked against the exact request the backend expects. The
// library is a read model, so there is nothing to assert about bodies - what
// matters is that each filter lands in the query string under the name the
// server validates, and that nothing the browser invented is sent instead.
//

function stubFetch(data: unknown) {
  const fake = vi.fn(async () => ({
    ok: true,
    status: 200,
    json: async () => ({ status: 'success', code: 200, data }),
  }))
  vi.stubGlobal('fetch', fake)
  return fake
}

function callOf(fake: ReturnType<typeof stubFetch>) {
  const [url, init] = fake.mock.calls[0] as unknown as [string, RequestInit]
  return { url, method: init?.method, signal: init?.signal }
}

const emptyPostPage = { total: 0, page: 1, page_size: 25, items: [] }

describe('reading downloaded posts', () => {
  it('asks for the first page with no filters at all', async () => {
    const fake = stubFetch(emptyPostPage)

    await listLibraryPosts()

    expect(callOf(fake).url).toBe('/api/library/posts')
    expect(callOf(fake).method).toBe('GET')
  })

  it('sends every filter the backend validates', async () => {
    const fake = stubFetch(emptyPostPage)

    await listLibraryPosts({
      q: '绿萝',
      person_id: 12,
      owner_user_id: '58859666123',
      aweme_type: 'image',
      completion: 'partial',
      source: 'html',
      sort: 'nickname',
      order: 'asc',
      page: 2,
      page_size: 50,
    })

    const url = new URL(callOf(fake).url, 'http://localhost')
    expect(url.pathname).toBe('/api/library/posts')
    expect(url.searchParams.get('q')).toBe('绿萝')
    expect(url.searchParams.get('person_id')).toBe('12')
    expect(url.searchParams.get('owner_user_id')).toBe('58859666123')
    expect(url.searchParams.get('aweme_type')).toBe('image')
    expect(url.searchParams.get('completion')).toBe('partial')
    expect(url.searchParams.get('source')).toBe('html')
    expect(url.searchParams.get('sort')).toBe('nickname')
    expect(url.searchParams.get('order')).toBe('asc')
    expect(url.searchParams.get('page')).toBe('2')
    expect(url.searchParams.get('page_size')).toBe('50')
  })

  it('carries an abort signal so a superseded page can be dropped', async () => {
    const fake = stubFetch(emptyPostPage)
    const controller = new AbortController()

    await listLibraryPosts({}, controller.signal)

    expect(callOf(fake).signal).toBe(controller.signal)
  })

  it('hands back the page exactly as the server counted it', async () => {
    stubFetch({ total: 163, page: 2, page_size: 25, items: [{ aweme_id: '1' }] })

    const page = await listLibraryPosts({ page: 2 })

    expect(page.total).toBe(163)
    expect(page.page).toBe(2)
    expect(page.items).toHaveLength(1)
  })
})

describe('reading live records', () => {
  it('asks for the first page with no filters at all', async () => {
    const fake = stubFetch({ total: 0, page: 1, page_size: 25, items: [] })

    await listLibraryLives()

    expect(callOf(fake).url).toBe('/api/library/lives')
  })

  it('sends every filter the backend validates', async () => {
    const fake = stubFetch({ total: 0, page: 1, page_size: 25, items: [] })

    await listLibraryLives({
      q: '晚间',
      person_id: 3,
      owner_user_id: '5885',
      sort: 'start_time',
      order: 'asc',
      page: 4,
      page_size: 10,
    })

    const url = new URL(callOf(fake).url, 'http://localhost')
    expect(url.searchParams.get('q')).toBe('晚间')
    expect(url.searchParams.get('person_id')).toBe('3')
    expect(url.searchParams.get('owner_user_id')).toBe('5885')
    expect(url.searchParams.get('sort')).toBe('start_time')
    expect(url.searchParams.get('order')).toBe('asc')
    expect(url.searchParams.get('page')).toBe('4')
    expect(url.searchParams.get('page_size')).toBe('10')
  })

  it('carries an abort signal', async () => {
    const fake = stubFetch({ total: 0, page: 1, page_size: 25, items: [] })
    const controller = new AbortController()

    await listLibraryLives({}, controller.signal)

    expect(callOf(fake).signal).toBe(controller.signal)
  })
})

describe('reading persistent recordings', () => {
  it('uses the dedicated recording resource endpoint', async () => {
    const fake = stubFetch({ total: 0, page: 1, page_size: 25, items: [] })

    await listLibraryRecordings()

    expect(callOf(fake).url).toBe('/api/library/recordings')
  })

  it('passes the recording filter contract without a client-selected app user', async () => {
    const fake = stubFetch({ total: 0, page: 1, page_size: 25, items: [] })

    await listLibraryRecordings({
      q: '晚间',
      owner_user_id: '5885',
      protocol: 'hls',
      sort: 'created_at',
      order: 'asc',
      page: 2,
      page_size: 10,
    })

    const url = new URL(callOf(fake).url, 'http://localhost')
    expect(url.pathname).toBe('/api/library/recordings')
    expect(url.searchParams.get('q')).toBe('晚间')
    expect(url.searchParams.get('owner_user_id')).toBe('5885')
    expect(url.searchParams.get('protocol')).toBe('hls')
    expect(url.searchParams.get('sort')).toBe('created_at')
    expect(url.searchParams.get('order')).toBe('asc')
    expect(url.searchParams.get('page')).toBe('2')
    expect(url.searchParams.get('page_size')).toBe('10')
    expect(url.searchParams.has('app_user_id')).toBe(false)
  })
})

describe('reading what a photographer is associated with', () => {
  it('asks the person endpoint that already exists', async () => {
    //
    // Held back through the creators phase because it returns content rather
    // than identity. This is the phase that owns content, so it is wired now -
    // and to the endpoint as it stands, unchanged.
    //
    const fake = stubFetch({ works: [] })

    await getPersonWorks(7)

    expect(callOf(fake).url).toBe('/api/person/7/works')
    expect(callOf(fake).method).toBe('GET')
  })

  it('hands back the list under the key the endpoint uses', async () => {
    stubFetch({
      works: [
        {
          aweme_id: '1',
          desc: '一条作品',
          save_dir: '/data/某人',
          downloaded_at: '2026-08-15T09:30:15',
          owner_display_name: '被拍的人',
        },
      ],
    })

    const works = await getPersonWorks(7)

    expect(works).toHaveLength(1)
    expect(works[0].owner_display_name).toBe('被拍的人')
  })

  it('carries an abort signal', async () => {
    const fake = stubFetch({ works: [] })
    const controller = new AbortController()

    await getPersonWorks(7, controller.signal)

    expect(callOf(fake).signal).toBe(controller.signal)
  })
})
