import { mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { nextTick } from 'vue'
import { createMemoryHistory, createRouter } from 'vue-router'

import { ApiError } from '../../src/api/client'
import { listLibraryLives, listLibraryPosts } from '../../src/api/library'
import { getPersonWorks, listPeople } from '../../src/api/people'
import { routes } from '../../src/router'
import LibraryView from '../../src/views/LibraryView.vue'
import type { LibraryLive, LibraryPost } from '../../src/types/library'

vi.mock('../../src/api/library', () => ({
  listLibraryPosts: vi.fn(),
  listLibraryLives: vi.fn(),
}))
vi.mock('../../src/api/people', () => ({
  listPeople: vi.fn(),
  getPersonWorks: vi.fn(),
}))

const mockedPosts = vi.mocked(listLibraryPosts)
const mockedLives = vi.mocked(listLibraryLives)
const mockedPeople = vi.mocked(listPeople)
const mockedWorks = vi.mocked(getPersonWorks)

function post(overrides: Partial<LibraryPost> = {}): LibraryPost {
  return {
    platform: 'douyin',
    aweme_id: '7300000000000000001',
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
    media_count: 3,
    saved_count: 3,
    save_dir: '/mnt/video/主播',
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
    room_status: 2,
    start_time: null,
    finish_time: null,
    status_code: 0,
    ...overrides,
  }
}

async function settle() {
  for (let index = 0; index < 6; index += 1) {
    await Promise.resolve()
  }
  await nextTick()
}

async function openLibrary() {
  const router = createRouter({ history: createMemoryHistory(), routes })
  await router.push('/library')
  await router.isReady()
  const wrapper = mount(LibraryView, { global: { plugins: [router] } })
  await settle()
  return wrapper
}

function tabSaying(wrapper: Awaited<ReturnType<typeof openLibrary>>, text: string) {
  return wrapper.findAll('.library__tab').find((one) => one.text().includes(text))
}

function buttonSaying(wrapper: Awaited<ReturnType<typeof openLibrary>>, text: string) {
  return wrapper.findAll('button').find((one) => one.text().includes(text))
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
  mockedPosts.mockResolvedValue({ total: 0, page: 1, page_size: 25, items: [] })
  mockedLives.mockResolvedValue({ total: 0, page: 1, page_size: 25, items: [] })
  mockedPeople.mockResolvedValue([])
  mockedWorks.mockResolvedValue([])
})

describe('arriving at the library', () => {
  it('reads the downloads and nothing else', async () => {
    //
    // Three tabs, three separate queries against three different tables. Paying
    // for all of them because one is open would be the most expensive thing
    // this screen could do on arrival.
    //
    await openLibrary()

    expect(mockedPosts).toHaveBeenCalledTimes(1)
    expect(mockedLives).not.toHaveBeenCalled()
    expect(mockedWorks).not.toHaveBeenCalled()
  })

  it('reads live records only once that tab is opened', async () => {
    const wrapper = await openLibrary()

    await tabSaying(wrapper, '直播记录')?.trigger('click')
    await settle()

    expect(mockedLives).toHaveBeenCalledTimes(1)
  })

  it('does not read them again when the tab is revisited', async () => {
    const wrapper = await openLibrary()
    await tabSaying(wrapper, '直播记录')?.trigger('click')
    await settle()

    await tabSaying(wrapper, '已下载作品')?.trigger('click')
    await settle()
    await tabSaying(wrapper, '直播记录')?.trigger('click')
    await settle()

    expect(mockedLives).toHaveBeenCalledTimes(1)
  })
})

describe('the downloaded posts table', () => {
  it('says how many records match, not how many are shown', async () => {
    mockedPosts.mockResolvedValue({
      total: 163,
      page: 1,
      page_size: 25,
      items: [post()],
    })

    const wrapper = await openLibrary()

    expect(wrapper.text()).toContain('163')
  })

  it('shows a save directory as text and never as something to open', async () => {
    //
    // This server serves no files. A link, an image source or anything that
    // opens would promise a capability the phase deliberately does not have -
    // and would be built from a path the browser was handed.
    //
    mockedPosts.mockResolvedValue({
      total: 1,
      page: 1,
      page_size: 25,
      items: [post({ save_dir: '/mnt/video/主播' })],
    })

    const wrapper = await openLibrary()
    const html = wrapper.html()

    expect(wrapper.text()).toContain('/mnt/video/主播')
    expect(html).not.toContain('href="/mnt/video/主播"')
    expect(html).not.toContain('file://')
    expect(wrapper.findAll('a').length).toBe(0)
  })

  it('describes a partial download as a record rather than as missing files', async () => {
    mockedPosts.mockResolvedValue({
      total: 1,
      page: 1,
      page_size: 25,
      items: [post({ saved_count: 1, media_count: 3 })],
    })

    const wrapper = await openLibrary()

    expect(wrapper.text()).toContain('部分 1 / 3')
    expect(wrapper.text()).not.toContain('文件丢失')
    expect(wrapper.text()).not.toContain('下载失败')
  })

  it('shows the rows in the order the server sent them', async () => {
    mockedPosts.mockResolvedValue({
      total: 3,
      page: 1,
      page_size: 25,
      items: [
        post({ aweme_id: '1', desc: '第一' }),
        post({ aweme_id: '2', desc: '第二' }),
        post({ aweme_id: '3', desc: '第三' }),
      ],
    })

    const wrapper = await openLibrary()
    const text = wrapper.find('tbody').text()

    expect(text.indexOf('第一')).toBeLessThan(text.indexOf('第二'))
    expect(text.indexOf('第二')).toBeLessThan(text.indexOf('第三'))
  })

  it('never claims the library is empty when the read failed', async () => {
    mockedPosts.mockRejectedValue(offline)

    const wrapper = await openLibrary()

    expect(wrapper.text()).not.toContain('没有符合条件的下载记录')
    expect(wrapper.find('[role="alert"]').exists()).toBe(true)
  })

  it('sends a filter to the server rather than narrowing the loaded rows', async () => {
    mockedPosts.mockResolvedValue({
      total: 2,
      page: 1,
      page_size: 25,
      items: [post({ aweme_id: '1' }), post({ aweme_id: '2' })],
    })
    const wrapper = await openLibrary()

    const select = wrapper.findAll('select').find((one) =>
      one.findAll('option').some((option) => option.text().includes('部分记录')),
    )
    await select?.setValue('partial')
    await settle()

    expect(mockedPosts).toHaveBeenLastCalledWith(
      expect.objectContaining({ completion: 'partial' }),
      expect.anything(),
    )
  })

  it('opens a detail from the row already loaded, without asking again', async () => {
    mockedPosts.mockResolvedValue({
      total: 1,
      page: 1,
      page_size: 25,
      items: [post({ aweme_id: '7300000000000000001' })],
    })
    const wrapper = await openLibrary()
    const before = mockedPosts.mock.calls.length

    await buttonSaying(wrapper, '查看')?.trigger('click')
    await settle()

    expect(wrapper.find('aside').exists()).toBe(true)
    expect(wrapper.find('aside').text()).toContain('7300000000000000001')
    expect(mockedPosts.mock.calls.length).toBe(before)
  })
})

describe('the live records table', () => {
  async function openLives() {
    const wrapper = await openLibrary()
    await tabSaying(wrapper, '直播记录')?.trigger('click')
    await settle()
    return wrapper
  }

  it('never says somebody is broadcasting now', async () => {
    //
    // status 2 means the room was live when the row was written. Whether it is
    // live at this moment is only answerable by a probe, which lives on the
    // creators screen and costs a real platform request.
    //
    mockedLives.mockResolvedValue({
      total: 1,
      page: 1,
      page_size: 25,
      items: [live({ room_status: 2 })],
    })

    const wrapper = await openLives()

    expect(wrapper.text()).toContain('记录时：直播中')
    expect(wrapper.text()).not.toContain('正在直播中')
  })

  it('offers nothing that plays or opens a file', async () => {
    //
    // live_record has no output path at all, so any control here would act on a
    // path this page guessed.
    //
    mockedLives.mockResolvedValue({
      total: 1,
      page: 1,
      page_size: 25,
      items: [live()],
    })

    const wrapper = await openLives()

    expect(buttonSaying(wrapper, '播放')).toBeUndefined()
    expect(buttonSaying(wrapper, '打开')).toBeUndefined()
    expect(wrapper.find('video').exists()).toBe(false)
    expect(wrapper.findAll('a').length).toBe(0)
  })

  it('keeps the rows in the order the server sent them', async () => {
    mockedLives.mockResolvedValue({
      total: 2,
      page: 1,
      page_size: 25,
      items: [live({ title: '先出现' }), live({ room_id: '9', title: '后出现' })],
    })

    const wrapper = await openLives()
    const text = wrapper.find('tbody').text()

    expect(text.indexOf('先出现')).toBeLessThan(text.indexOf('后出现'))
  })

  it('never claims there are no records when the read failed', async () => {
    mockedLives.mockRejectedValue(offline)

    const wrapper = await openLives()

    expect(wrapper.text()).not.toContain('没有符合条件的直播记录')
    expect(wrapper.find('[role="alert"]').exists()).toBe(true)
  })

  it('shows a recorded observation without inventing an output path', async () => {
    mockedLives.mockResolvedValue({
      total: 1,
      page: 1,
      page_size: 25,
      items: [live()],
    })
    const wrapper = await openLives()

    await buttonSaying(wrapper, '查看')?.trigger('click')
    await settle()

    const panel = wrapper.find('aside')
    expect(panel.text()).toContain('7123')
    expect(panel.text()).toContain('不代表现在是否正在直播')
    expect(panel.text()).not.toContain('output_path')
  })
})

describe('the photographer association tab', () => {
  async function openWorks() {
    const wrapper = await openLibrary()
    await tabSaying(wrapper, '拍摄关系关联')?.trigger('click')
    await settle()
    return wrapper
  }

  it('reads nothing until somebody is chosen', async () => {
    await openWorks()

    expect(mockedWorks).not.toHaveBeenCalled()
  })

  it('says what the list is and is not', async () => {
    //
    // The backend records collaboration between people, not against posts. A
    // heading claiming these were shot by this person would be an attribution
    // nothing in the data supports.
    //
    const wrapper = await openWorks()
    const text = wrapper.text()

    expect(text).toContain('基于人物级合作关系')
    expect(text).toContain('并不表示每条作品都已逐条确认由该人物拍摄')
  })

  it('reads the chosen photographer and shows the association', async () => {
    mockedPeople.mockResolvedValue([
      {
        person_id: 7,
        display_name: '摄影师',
        directory_name: null,
        note: null,
        account_count: 1,
      },
    ])
    mockedWorks.mockResolvedValue([
      {
        aweme_id: '1',
        desc: '一条',
        save_dir: '/mnt/video/被拍的人',
        downloaded_at: '2026-08-15T09:30:15',
        owner_display_name: '被拍的人',
      },
    ])
    const wrapper = await openWorks()

    const select = wrapper.find('select')
    await select.setValue('7')
    await settle()

    expect(mockedWorks).toHaveBeenCalledWith(7, expect.anything())
    expect(wrapper.text()).toContain('被拍的人')
  })

  it('shows an associated path as text only', async () => {
    mockedPeople.mockResolvedValue([
      {
        person_id: 7,
        display_name: '摄影师',
        directory_name: null,
        note: null,
        account_count: 1,
      },
    ])
    mockedWorks.mockResolvedValue([
      {
        aweme_id: '1',
        desc: null,
        save_dir: '/mnt/video/被拍的人',
        downloaded_at: null,
        owner_display_name: '被拍的人',
      },
    ])
    const wrapper = await openWorks()

    await wrapper.find('select').setValue('7')
    await settle()

    expect(wrapper.text()).toContain('/mnt/video/被拍的人')
    expect(wrapper.findAll('a').length).toBe(0)
  })
})

describe('the library as a whole', () => {
  it('never creates work or asks a platform anything', async () => {
    //
    // An index of records has no business starting downloads or going back to
    // the platform to decorate rows. The modules that could are simply not
    // imported by this screen.
    //
    const wrapper = await openLibrary()
    const text = wrapper.text()

    expect(buttonSaying(wrapper, '重新下载')).toBeUndefined()
    expect(buttonSaying(wrapper, '删除')).toBeUndefined()
    expect(text).not.toContain('取消任务')
  })
})
