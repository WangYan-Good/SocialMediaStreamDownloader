import { mount } from '@vue/test-utils'
import type { VueWrapper } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { nextTick } from 'vue'
import { createMemoryHistory, createRouter } from 'vue-router'

import { ApiError } from '../../src/api/client'
import { listTasks } from '../../src/api/tasks'
import { routes } from '../../src/router'
import { TASK_CENTER_POLL_INTERVAL_MS } from '../../src/stores/tasks'
import type { Task, TaskState } from '../../src/types/task'
import UserTasksView from '../../src/views/UserTasksView.vue'

vi.mock('../../src/api/tasks', () => ({ listTasks: vi.fn() }))

const mockedTasks = vi.mocked(listTasks)

const TASK_ID = 'a1b2c3d4-0000-4000-8000-000000000001'
const RESOLVE_ID = 'receipt-9f8e7d'
const AWEME_ID = '7657271784144009946'
const SEC_USER_ID = 'MS4wLjABAAAA-somebody'
const SAVE_DIR = '/mnt/video/某位主播'
const RESOLVED_URL = 'https://www.douyin.com/video/7657271784144009946'
const SOURCE_URL = 'https://v.douyin.com/M-kmspLye0o/'

function task(overrides: Partial<Task> = {}): Task {
  return {
    task_id: TASK_ID,
    task_type: 'post_download',
    state: 'running',
    title: '下载作品',
    message: '正在保存媒体文件',
    created_at: '2026-08-24T10:00:00',
    started_at: '2026-08-24T10:00:01',
    finished_at: null,
    progress: { current: 1, total: 3 },
    metadata: {
      platform: 'douyin',
      resolve_id: RESOLVE_ID,
      aweme_id: AWEME_ID,
      sec_user_id: SEC_USER_ID,
      legacy_job_id: 'job-77',
      source_url: SOURCE_URL,
      resolved_url: RESOLVED_URL,
      result: {
        saved_count: 1,
        media_count: 3,
        partial: true,
        save_dir: SAVE_DIR,
        protocol: 'flv',
        test_mode: false,
        owner_user_id: '5885',
      },
    },
    items: [],
    ...overrides,
  }
}

function page(items: Task[], total = items.length) {
  return { items, total }
}

async function settle() {
  for (let index = 0; index < 6; index += 1) {
    await Promise.resolve()
  }
  await nextTick()
}

async function openTasks() {
  const router = createRouter({ history: createMemoryHistory(), routes })
  await router.push('/tasks')
  await router.isReady()
  const wrapper = mount(UserTasksView, { global: { plugins: [router] } })
  await settle()
  return wrapper
}

function buttonSaying(wrapper: VueWrapper, text: string) {
  return wrapper.findAll('button').find((one) => one.text().includes(text))
}

async function openDetail(wrapper: VueWrapper) {
  await buttonSaying(wrapper, '查看')?.trigger('click')
  await settle()
}

beforeEach(() => {
  setActivePinia(createPinia())
  vi.clearAllMocks()
  mockedTasks.mockResolvedValue(page([task()]))
})

afterEach(() => {
  vi.useRealTimers()
})

describe('the task screen as a user reads it', () => {
  it('is about downloads rather than about the server', async () => {
    const wrapper = await openTasks()
    const text = wrapper.text()

    expect(text).toContain('下载任务')
    for (const internal of ['服务实例', '保留期', '任务中心']) {
      expect(text).not.toContain(internal)
    }
  })

  it('keeps every internal identifier out of the list', async () => {
    const wrapper = await openTasks()
    const text = wrapper.text()

    for (const internal of [
      TASK_ID,
      RESOLVE_ID,
      AWEME_ID,
      SEC_USER_ID,
      'job-77',
      SAVE_DIR,
      RESOLVED_URL,
      '任务 ID',
    ]) {
      expect(text).not.toContain(internal)
    }
  })

  it('shows the state, the progress and what the task last said', async () => {
    const wrapper = await openTasks()
    const text = wrapper.text()

    expect(text).toContain('进行中')
    expect(text).toContain('1 / 3')
    expect(text).toContain('正在保存媒体文件')
  })

  it('names the task type in words rather than as its wire value', async () => {
    const wrapper = await openTasks()

    expect(wrapper.text()).toContain('作品下载')
    expect(wrapper.text()).not.toContain('post_download')
  })

  it('falls back to the type when a task has no title of its own', async () => {
    //
    // The existing taskDisplayTitle rule, reused rather than restated. Nothing
    // is fetched to invent a nicer title, and no identity is guessed out of
    // metadata.
    //
    mockedTasks.mockResolvedValue(page([task({ title: null })]))
    const wrapper = await openTasks()

    expect(wrapper.text()).toContain('作品下载')
    expect(wrapper.text()).not.toContain(AWEME_ID)
  })

  it('offers no limit control', async () => {
    //
    // How much of the newest list to read is an api parameter, not a decision a
    // user should have to have an opinion about. The store keeps its default.
    //
    const wrapper = await openTasks()

    expect(wrapper.text()).not.toContain('显示条数')
    const options = wrapper.findAll('option').map((one) => one.text())
    for (const limit of ['25', '50', '100']) {
      expect(options).not.toContain(limit)
    }
    expect(mockedTasks.mock.calls[0][0]).toMatchObject({ limit: 50 })
  })

  it('still lets a user narrow the list by state', async () => {
    const wrapper = await openTasks()
    mockedTasks.mockClear()

    const stateSelect = wrapper.findAll('select').find((one) =>
      one.findAll('option').some((option) => option.text() === '已完成'),
    )
    expect(stateSelect).toBeTruthy()
    await stateSelect?.setValue('success')
    await settle()

    expect(mockedTasks.mock.calls[0][0]).toMatchObject({ state: 'success' })
  })
})

describe('one task in detail', () => {
  it('shows what happened without the machinery behind it', async () => {
    const wrapper = await openTasks()
    await openDetail(wrapper)
    const text = wrapper.text()

    expect(text).toContain('作品下载')
    expect(text).toContain('创建时间')
    expect(text).toContain('开始时间')
    expect(text).toContain('1 / 3')

    for (const internal of [
      TASK_ID,
      RESOLVE_ID,
      AWEME_ID,
      SEC_USER_ID,
      'job-77',
      SAVE_DIR,
      RESOLVED_URL,
      '解析凭证',
      '作品 ID',
      '主播 ID',
      '兼容任务 ID',
      '解析后链接',
      '保存目录',
      '协议',
      '测试模式',
    ]) {
      expect(text).not.toContain(internal)
    }
  })

  it('reports the counts a user understands from the recorded result', async () => {
    const wrapper = await openTasks()
    await openDetail(wrapper)

    expect(wrapper.text()).toContain('已保存')
    expect(wrapper.text()).toContain('媒体总数')
  })

  it('links the original share url and nothing else', async () => {
    const wrapper = await openTasks()
    await openDetail(wrapper)

    const link = wrapper.findAll('a').find((one) => one.text().includes(SOURCE_URL))
    expect(link).toBeTruthy()
    expect(link?.attributes('href')).toBe(SOURCE_URL)
    expect(link?.attributes('rel')).toBe('noopener noreferrer')
    expect(wrapper.text()).not.toContain(RESOLVED_URL)
  })

  it('refuses to make a non-http share value clickable', async () => {
    //
    // metadata is arbitrary. A value that is not plainly http(s) stays text -
    // the existing isLinkableUrl rule, not a second opinion about it.
    //
    mockedTasks.mockResolvedValue(
      page([
        task({
          metadata: { ...task().metadata, source_url: 'javascript:alert(1)' },
        }),
      ]),
    )
    const wrapper = await openTasks()
    await openDetail(wrapper)

    const hrefs = wrapper.findAll('a').map((one) => one.attributes('href'))
    expect(hrefs).not.toContain('javascript:alert(1)')
  })

  it('summarises batch work items by state instead of listing their ids', async () => {
    mockedTasks.mockResolvedValue(
      page([
        task({
          task_type: 'owner_batch_download',
          items: [
            { key: AWEME_ID, state: 'success', message: null, metadata: {} },
            { key: '7300000000000000002', state: 'failed', message: null, metadata: {} },
          ],
        }),
      ]),
    )
    const wrapper = await openTasks()
    await openDetail(wrapper)
    const text = wrapper.text()

    expect(text).toContain('已完成')
    expect(text).toContain('失败')
    expect(text).not.toContain(AWEME_ID)
    expect(text).not.toContain('7300000000000000002')
  })
})

describe('the polling loop this screen owns', () => {
  it('starts reading when the screen opens', async () => {
    await openTasks()

    expect(mockedTasks).toHaveBeenCalledTimes(1)
  })

  it('stops reading when the screen closes', async () => {
    vi.useFakeTimers()
    const wrapper = await openTasks()
    const before = mockedTasks.mock.calls.length

    wrapper.unmount()
    await vi.advanceTimersByTimeAsync(TASK_CENTER_POLL_INTERVAL_MS * 5)

    expect(mockedTasks).toHaveBeenCalledTimes(before)
  })

  it('keeps the last known list on screen when a refresh fails', async () => {
    //
    // A read that failed says nothing about the tasks themselves. Replacing the
    // list with an error would report the backend's silence as the user's work
    // having disappeared.
    //
    const wrapper = await openTasks()
    expect(wrapper.text()).toContain('下载作品')

    mockedTasks.mockRejectedValue(
      new ApiError({
        kind: 'backend',
        status: 500,
        code: 500,
        message: 'sqlalchemy.exc.OperationalError: database is locked',
      }),
    )
    await buttonSaying(wrapper, '刷新')?.trigger('click')
    await settle()

    expect(wrapper.text()).toContain('下载作品')
    expect(wrapper.text()).toContain('暂时无法读取任务，请重试。')
    for (const internal of ['sqlalchemy', 'OperationalError', 'database']) {
      expect(wrapper.text()).not.toContain(internal)
    }
  })
})

describe('when there is nothing to show', () => {
  it('says there are no downloads yet', async () => {
    mockedTasks.mockResolvedValue(page([]))
    const wrapper = await openTasks()

    expect(wrapper.text()).toContain('还没有下载任务。')
  })

  it('says a filter matched nothing once one is set', async () => {
    mockedTasks.mockResolvedValue(page([]))
    const wrapper = await openTasks()

    const stateSelect = wrapper.findAll('select').find((one) =>
      one.findAll('option').some((option) => option.text() === '已完成'),
    )
    await stateSelect?.setValue('success')
    await settle()

    expect(wrapper.text()).toContain('没有符合条件的任务。')
  })

  it('never reports a failed first read as an empty list', async () => {
    //
    // Nothing has been learned about how many tasks there are, so "no tasks"
    // would be a claim the browser is in no position to make.
    //
    mockedTasks.mockRejectedValue(
      new ApiError({ kind: 'network', status: null, code: null, message: 'Failed to fetch' }),
    )
    const wrapper = await openTasks()

    expect(wrapper.text()).not.toContain('还没有下载任务。')
    expect(wrapper.text()).toContain('暂时无法读取任务，请重试。')
  })
})

describe('every state a task can be in', () => {
  it.each<[TaskState, string]>([
    ['pending', '排队中'],
    ['running', '进行中'],
    ['success', '已完成'],
    ['partial', '部分完成'],
    ['failed', '失败'],
    ['cancelled', '已停止'],
  ])('shows %s in the words the app already uses', async (state, label) => {
    //
    // The existing state vocabulary, reused. Two states are never merged:
    // partial and success mean different things to whoever has to decide
    // whether to download something again.
    //
    mockedTasks.mockResolvedValue(page([task({ state })]))
    const wrapper = await openTasks()

    expect(wrapper.text()).toContain(label)
  })
})
