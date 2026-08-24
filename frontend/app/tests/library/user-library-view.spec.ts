import { mount } from '@vue/test-utils'
import type { VueWrapper } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { nextTick } from 'vue'
import { createMemoryHistory, createRouter } from 'vue-router'

import { ApiError } from '../../src/api/client'
import { listLibraryLives, listLibraryPosts } from '../../src/api/library'
import { getPersonWorks, listPeople } from '../../src/api/people'
import { routes } from '../../src/router'
import type { LibraryLive, LibraryPost } from '../../src/types/library'
import UserLibraryView from '../../src/views/UserLibraryView.vue'

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

const AWEME_ID = '7300000000000000001'
const OWNER_USER_ID = '5885'
const SAVE_DIR = '/mnt/video/主播'

function post(overrides: Partial<LibraryPost> = {}): LibraryPost {
  return {
    platform: 'douyin',
    aweme_id: AWEME_ID,
    owner_user_id: OWNER_USER_ID,
    sec_user_id: 'MS4w',
    nickname: '某位主播',
    directory_name: '某位主播',
    person_id: null,
    person_display_name: null,
    aweme_type: 'video',
    desc: '一条作品',
    create_time: '2026-08-14T20:00:00',
    downloaded_at: '2026-08-15T09:30:15.250',
    media_count: 3,
    saved_count: 3,
    save_dir: SAVE_DIR,
    source: 'api',
    ...overrides,
  }
}

function live(overrides: Partial<LibraryLive> = {}): LibraryLive {
  return {
    observed_at: '2026-08-15T09:30:15.250',
    platform: 'douyin',
    room_id: '7123456789',
    owner_user_id: OWNER_USER_ID,
    nickname: '某位主播',
    directory_name: '某位主播',
    person_id: null,
    person_display_name: null,
    title: '晚间直播',
    room_status: 4,
    start_time: '2026-08-15T20:00:00',
    finish_time: '2026-08-15T22:00:00',
    status_code: 0,
    ...overrides,
  }
}

function postPage(items: LibraryPost[], overrides = {}) {
  return { total: items.length, page: 1, page_size: 25, items, ...overrides }
}

function livePage(items: LibraryLive[], overrides = {}) {
  return { total: items.length, page: 1, page_size: 25, items, ...overrides }
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
  const wrapper = mount(UserLibraryView, { global: { plugins: [router] } })
  await settle()
  return wrapper
}

function tabSaying(wrapper: VueWrapper, text: string) {
  return wrapper.findAll('button').find((button) => button.text().trim() === text)
}

async function openLives(wrapper: VueWrapper) {
  await tabSaying(wrapper, '直播记录')?.trigger('click')
  await settle()
}

beforeEach(() => {
  setActivePinia(createPinia())
  vi.clearAllMocks()
  mockedPosts.mockResolvedValue(postPage([post()]))
  mockedLives.mockResolvedValue(livePage([live()]))
  mockedPeople.mockResolvedValue([])
  mockedWorks.mockResolvedValue([])
})

describe('what the library offers a user', () => {
  it('shows downloads and recordings, and nothing about people', async () => {
    const wrapper = await openLibrary()

    expect(tabSaying(wrapper, '已下载作品')).toBeTruthy()
    expect(tabSaying(wrapper, '直播记录')).toBeTruthy()
    //
    // The collaboration tab is management, not a way of finding your own
    // downloads. It is still in the application, on /admin/library.
    //
    expect(tabSaying(wrapper, '拍摄关系关联')).toBeUndefined()
    expect(wrapper.text()).not.toContain('拍摄关系')
  })

  it('calls itself by what it holds rather than where it is stored', async () => {
    const wrapper = await openLibrary()
    const text = wrapper.text()

    expect(text).toContain('我的资源')
    for (const internal of ['数据库', 'schema', '索引', 'Schema']) {
      expect(text).not.toContain(internal)
    }
  })

  it('is honest that a record is not proof of a file', async () => {
    //
    // The one thing this screen must not become is a file manager. Nothing
    // here has checked the disk, so it may not imply the media is still there.
    //
    const wrapper = await openLibrary()
    const text = wrapper.text()

    expect(text).toContain('记录')
    for (const overclaim of ['都可以打开', '一定存在', '播放']) {
      expect(text).not.toContain(overclaim)
    }
  })

  it('never asks for the person list to show a user their downloads', async () => {
    //
    // The person filter is an admin capability. Reading the roster here would
    // be a request for a list this screen has no control that uses.
    //
    await openLibrary()

    expect(mockedPosts).toHaveBeenCalledTimes(1)
    expect(mockedPeople).not.toHaveBeenCalled()
    expect(mockedWorks).not.toHaveBeenCalled()
  })

  it('reads live records only when that tab is opened', async () => {
    const wrapper = await openLibrary()
    expect(mockedLives).not.toHaveBeenCalled()

    await openLives(wrapper)

    expect(mockedLives).toHaveBeenCalledTimes(1)
  })
})

describe('the downloaded works list', () => {
  it('keeps identifiers and paths off the screen', async () => {
    const wrapper = await openLibrary()
    const text = wrapper.text()

    for (const internal of [
      AWEME_ID,
      OWNER_USER_ID,
      SAVE_DIR,
      '作品 ID',
      '保存目录',
      '人物',
      '未归并',
      '来源',
    ]) {
      expect(text).not.toContain(internal)
    }
  })

  it('shows what a user came to recognise the download by', async () => {
    const wrapper = await openLibrary()
    const text = wrapper.text()

    expect(text).toContain('一条作品')
    expect(text).toContain('某位主播')
    expect(text).toContain('视频')
  })

  it('says the creator is unknown rather than falling back to an account id', async () => {
    //
    // The old table printed owner_user_id when a nickname was missing. That is
    // an internal identifier standing where a name should be, and it leaks
    // precisely when there is nothing useful to say.
    //
    mockedPosts.mockResolvedValue(postPage([post({ nickname: null })]))
    const wrapper = await openLibrary()

    expect(wrapper.text()).toContain('未知创作者')
    expect(wrapper.text()).not.toContain(OWNER_USER_ID)
  })
})

describe('finding something in the list', () => {
  it('offers keyword, type, status and order, but never a person filter', async () => {
    const wrapper = await openLibrary()
    const labels = wrapper.findAll('label').map((one) => one.text())

    expect(labels.some((one) => one.includes('关键词'))).toBe(true)
    expect(labels.some((one) => one.includes('人物'))).toBe(false)
    expect(wrapper.text()).not.toContain('人物')
  })

  it('points the keyword box at what a user remembers', async () => {
    const wrapper = await openLibrary()
    const placeholder = wrapper.get('input[type="search"]').attributes('placeholder') ?? ''

    expect(placeholder).toContain('文案')
    expect(placeholder).not.toContain('作品 ID')
    expect(placeholder).not.toContain('人物')
  })

  it('filters at the server rather than narrowing the rows already loaded', async () => {
    const wrapper = await openLibrary()
    mockedPosts.mockClear()

    await wrapper.get('input[type="search"]').setValue('海边')
    await settle()

    expect(mockedPosts).toHaveBeenCalledTimes(1)
    expect(mockedPosts.mock.calls[0][0]).toMatchObject({ q: '海边', page: 1 })
  })
})

describe('paging through what is there', () => {
  it('moves through pages of downloads at the server', async () => {
    mockedPosts.mockResolvedValue(postPage([post()], { total: 60, page: 1 }))
    const wrapper = await openLibrary()

    expect(wrapper.text()).toContain('第 1 / 3 页')
    mockedPosts.mockResolvedValue(postPage([post()], { total: 60, page: 2 }))

    await wrapper.findAll('button').find((one) => one.text() === '下一页')?.trigger('click')
    await settle()

    expect(mockedPosts.mock.calls[1][0]).toMatchObject({ page: 2 })
    expect(wrapper.text()).toContain('第 2 / 3 页')
  })

  it('moves through pages of recordings at the server', async () => {
    mockedLives.mockResolvedValue(livePage([live()], { total: 60, page: 1 }))
    const wrapper = await openLibrary()
    await openLives(wrapper)

    expect(wrapper.text()).toContain('第 1 / 3 页')
    mockedLives.mockResolvedValue(livePage([live()], { total: 60, page: 2 }))

    await wrapper.findAll('button').find((one) => one.text() === '下一页')?.trigger('click')
    await settle()

    expect(mockedLives.mock.calls[1][0]).toMatchObject({ page: 2 })
  })
})

describe('looking at one record', () => {
  it('opens a download from the row already loaded, without asking again', async () => {
    const wrapper = await openLibrary()
    mockedPosts.mockClear()

    await wrapper.findAll('button').find((one) => one.text() === '查看')?.trigger('click')
    await settle()

    expect(mockedPosts).not.toHaveBeenCalled()
    expect(wrapper.text()).toContain('发布时间')
  })

  it('keeps the download detail free of identifiers and paths', async () => {
    const wrapper = await openLibrary()
    await wrapper.findAll('button').find((one) => one.text() === '查看')?.trigger('click')
    await settle()

    const text = wrapper.text()
    for (const internal of [AWEME_ID, SAVE_DIR, OWNER_USER_ID, '作品 ID', '保存目录', '人物', '来源']) {
      expect(text).not.toContain(internal)
    }
  })

  it('describes a recording without its status code, directory or person', async () => {
    const wrapper = await openLibrary()
    await openLives(wrapper)
    await wrapper.findAll('button').find((one) => one.text() === '查看')?.trigger('click')
    await settle()

    const text = wrapper.text()
    expect(text).toContain('晚间直播')
    expect(text).toContain('某位主播')
    for (const internal of ['状态码', '目录名', '人物', '未归并', OWNER_USER_ID]) {
      expect(text).not.toContain(internal)
    }
  })

  it('never claims a recorded observation is happening now', async () => {
    mockedLives.mockResolvedValue(livePage([live({ room_status: 2 })]))
    const wrapper = await openLibrary()
    await openLives(wrapper)

    expect(wrapper.text()).not.toContain('正在直播')
  })
})

describe('when there is nothing to show', () => {
  it('says the shelf is empty rather than that a filter matched nothing', async () => {
    mockedPosts.mockResolvedValue(postPage([]))
    const wrapper = await openLibrary()

    expect(wrapper.text()).toContain('还没有下载作品。')
  })

  it('says a filter matched nothing once one is set', async () => {
    mockedPosts.mockResolvedValue(postPage([]))
    const wrapper = await openLibrary()

    await wrapper.get('input[type="search"]').setValue('不存在的东西')
    await settle()

    expect(wrapper.text()).toContain('没有符合条件的内容。')
  })

  it('says there are no recordings yet', async () => {
    mockedLives.mockResolvedValue(livePage([]))
    const wrapper = await openLibrary()
    await openLives(wrapper)

    expect(wrapper.text()).toContain('还没有直播记录。')
  })

  it('reports a failed read as something to retry, without the internals', async () => {
    mockedPosts.mockRejectedValue(
      new ApiError({
        kind: 'backend',
        status: 500,
        code: 500,
        message: 'database unavailable: schema library missing',
      }),
    )
    const wrapper = await openLibrary()

    expect(wrapper.text()).toContain('暂时无法读取资源，请重试。')
    for (const internal of ['database', 'schema', 'unavailable']) {
      expect(wrapper.text()).not.toContain(internal)
    }
  })
})
