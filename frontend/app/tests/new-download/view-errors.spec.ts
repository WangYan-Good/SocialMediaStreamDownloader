import { mount } from '@vue/test-utils'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { nextTick } from 'vue'

import { ApiError } from '../../src/api/client'
import { TASK_POLL_INTERVAL_MS } from '../../src/composables/useNewDownloadFlow'
import NewDownloadView from '../../src/views/NewDownloadView.vue'
import type { CreatedTask, Task, TaskState } from '../../src/types/task'
import { postResolution } from './build-request.spec'

function taskIn(state: TaskState, overrides: Partial<Task> = {}): Task {
  return {
    task_id: 'task-1',
    task_type: 'post_download',
    state,
    title: null,
    message: null,
    created_at: '2026-08-15T09:30:15.250',
    started_at: null,
    finished_at: null,
    progress: { current: 0, total: 1 },
    metadata: {},
    items: [],
    ...overrides,
  }
}

const CREATED: CreatedTask = {
  task_id: 'task-1',
  task_type: 'post_download',
  resolve_id: 'receipt-1',
}

function mountView(api: Record<string, unknown> = {}) {
  const spies = {
    resolveResource: vi.fn(async () => postResolution),
    createTask: vi.fn(async () => CREATED),
    getTask: vi.fn(async () => taskIn('pending')),
    ...api,
  }
  const wrapper = mount(NewDownloadView, { props: { api: spies } })
  return { wrapper, spies }
}

async function settle() {
  for (let index = 0; index < 4; index += 1) {
    await Promise.resolve()
  }
  await nextTick()
}

function buttonSaying(wrapper: ReturnType<typeof mount>, text: string) {
  return wrapper.findAll('button').find((button) => button.text().includes(text))
}

async function resolved(api: Record<string, unknown> = {}) {
  const built = mountView(api)
  await built.wrapper.find('textarea').setValue('https://v.douyin.com/abc/')
  await built.wrapper.find('button').trigger('click')
  await settle()
  return built
}

async function tracking(api: Record<string, unknown> = {}) {
  const built = await resolved(api)
  await buttonSaying(built.wrapper, '下载该作品')?.trigger('click')
  await settle()
  return built
}

beforeEach(() => {
  vi.useFakeTimers()
})

afterEach(() => {
  vi.useRealTimers()
})

describe('resolving fails', () => {
  it('keeps the text and says why, in the page', async () => {
    const refused = new ApiError({
      kind: 'backend',
      status: 400,
      code: 400,
      message: '一次只能解析一个链接',
    })
    const { wrapper } = mountView({
      resolveResource: vi.fn(async () => Promise.reject(refused)),
    })
    await wrapper.find('textarea').setValue('a https://v.douyin.com/a/ b https://v.douyin.com/b/')

    await wrapper.find('button').trigger('click')
    await settle()

    expect(wrapper.find('[role="alert"]').text()).toContain('一次只能解析一个链接')
    expect(wrapper.find('textarea').element.value).toContain('https://v.douyin.com/a/')
    expect(wrapper.text()).not.toContain('确认资源')
  })

  it.each([
    [502, '无法解析该短链接，请稍后重试'],
    [500, '服务器内部错误，请稍后重试'],
  ])('shows a backend %i in words', async (status, message) => {
    const refused = new ApiError({ kind: 'backend', status, code: status, message })
    const { wrapper } = mountView({
      resolveResource: vi.fn(async () => Promise.reject(refused)),
    })
    await wrapper.find('textarea').setValue('https://v.douyin.com/abc/')

    await wrapper.find('button').trigger('click')
    await settle()

    expect(wrapper.find('[role="alert"]').text()).toContain(message)
  })

  it('shows a transport failure without leaking internals', async () => {
    const offline = new ApiError({
      kind: 'network',
      status: null,
      code: null,
      message: 'Failed to fetch',
    })
    const { wrapper } = mountView({
      resolveResource: vi.fn(async () => Promise.reject(offline)),
    })
    await wrapper.find('textarea').setValue('https://v.douyin.com/abc/')

    await wrapper.find('button').trigger('click')
    await settle()

    const alert = wrapper.find('[role="alert"]')
    expect(alert.exists()).toBe(true)
    expect(alert.text()).not.toContain('Response')
    expect(alert.text()).not.toContain('at ')
  })

  it('lets the user try again', async () => {
    const refused = new ApiError({ kind: 'backend', status: 400, code: 400, message: 'bad' })
    const resolveResource = vi
      .fn<() => Promise<typeof postResolution>>()
      .mockRejectedValueOnce(refused)
      .mockResolvedValueOnce(postResolution)
    const { wrapper } = mountView({ resolveResource })
    await wrapper.find('textarea').setValue('https://v.douyin.com/abc/')

    await wrapper.find('button').trigger('click')
    await settle()
    await wrapper.find('button').trigger('click')
    await settle()

    expect(resolveResource).toHaveBeenCalledTimes(2)
    expect(wrapper.text()).toContain('确认资源')
  })
})

describe('the receipt expired before the user confirmed', () => {
  const gone = new ApiError({
    kind: 'backend',
    status: 404,
    code: 404,
    message: '解析结果不存在或已过期，请重新解析',
  })

  it('says so and offers to resolve again', async () => {
    const { wrapper } = await resolved({
      createTask: vi.fn(async () => Promise.reject(gone)),
    })

    await buttonSaying(wrapper, '下载该作品')?.trigger('click')
    await settle()

    expect(wrapper.text()).toContain('重新解析')
    expect(buttonSaying(wrapper, '重新解析')).toBeTruthy()
  })

  it('creates no task and starts no tracking', async () => {
    const { wrapper, spies } = await resolved({
      createTask: vi.fn(async () => Promise.reject(gone)),
    })

    await buttonSaying(wrapper, '下载该作品')?.trigger('click')
    await settle()

    expect(wrapper.text()).not.toContain('当前任务')
    expect(spies.getTask).not.toHaveBeenCalled()
  })

  it('returns to the form with the text intact when asked to resolve again', async () => {
    //
    // Deliberately back to the form rather than silently resolving: the server
    // has forgotten the receipt, and the browser must not carry on with the
    // identity it still happens to hold.
    //
    const { wrapper } = await resolved({
      createTask: vi.fn(async () => Promise.reject(gone)),
    })
    await buttonSaying(wrapper, '下载该作品')?.trigger('click')
    await settle()

    await buttonSaying(wrapper, '重新解析')?.trigger('click')
    await nextTick()

    expect(wrapper.text()).not.toContain('确认资源')
    expect(wrapper.find('textarea').element.value).toBe('https://v.douyin.com/abc/')
    expect(wrapper.find('button').text()).toContain('解析')
  })
})

describe('creating fails for another reason', () => {
  it.each([400, 503, 500])('stays on the resolution after a %i', async (status) => {
    const refused = new ApiError({
      kind: 'backend',
      status,
      code: status,
      message: `refused ${status}`,
    })
    const { wrapper } = await resolved({
      createTask: vi.fn(async () => Promise.reject(refused)),
    })

    await buttonSaying(wrapper, '下载该作品')?.trigger('click')
    await settle()

    expect(wrapper.text()).toContain('确认资源')
    expect(wrapper.text()).toContain(`refused ${status}`)
    //
    // No task was created, so no task is shown. Rendering one as failed would
    // invent a record the server never made.
    //
    expect(wrapper.text()).not.toContain('当前任务')
  })

  it('lets the user press download again', async () => {
    const offline = new ApiError({
      kind: 'network',
      status: null,
      code: null,
      message: 'offline',
    })
    const createTask = vi
      .fn<() => Promise<CreatedTask>>()
      .mockRejectedValueOnce(offline)
      .mockResolvedValueOnce(CREATED)
    const { wrapper } = await resolved({ createTask })

    await buttonSaying(wrapper, '下载该作品')?.trigger('click')
    await settle()
    await buttonSaying(wrapper, '下载该作品')?.trigger('click')
    await settle()

    expect(createTask).toHaveBeenCalledTimes(2)
    expect(wrapper.text()).toContain('当前任务')
  })
})

describe('the status cannot be read', () => {
  const offline = new ApiError({
    kind: 'network',
    status: null,
    code: null,
    message: 'Failed to fetch',
  })

  async function trackingThenOffline() {
    let call = 0
    const getTask = vi.fn(async () => {
      call += 1
      if (call === 1) {
        return taskIn('running')
      }
      throw offline
    })
    const built = await tracking({ getTask })
    await vi.advanceTimersByTimeAsync(TASK_POLL_INTERVAL_MS)
    await nextTick()
    return { ...built, getTask }
  }

  it('says the status is unavailable, not that the download failed', async () => {
    const { wrapper } = await trackingThenOffline()

    const text = wrapper.text()
    expect(text).toContain('暂时无法获取任务状态')
    expect(text).not.toContain('任务失败')
    expect(text).not.toContain('下载失败')
  })

  it('keeps showing the last state it did see', async () => {
    const { wrapper } = await trackingThenOffline()

    expect(wrapper.text()).toContain('进行中')
  })

  it('stops polling and offers a retry', async () => {
    const { wrapper, getTask } = await trackingThenOffline()
    const afterFailure = getTask.mock.calls.length

    await vi.advanceTimersByTimeAsync(TASK_POLL_INTERVAL_MS * 5)

    expect(getTask).toHaveBeenCalledTimes(afterFailure)
    expect(buttonSaying(wrapper, '重试获取状态')).toBeTruthy()
  })

  it('reads the same task again when retried', async () => {
    const { wrapper, getTask } = await trackingThenOffline()
    const before = getTask.mock.calls.length

    await buttonSaying(wrapper, '重试获取状态')?.trigger('click')
    await settle()

    expect(getTask.mock.calls.length).toBe(before + 1)
    expect(getTask).toHaveBeenLastCalledWith('task-1')
  })
})

describe('the task record is gone', () => {
  const missing = new ApiError({
    kind: 'backend',
    status: 404,
    code: 404,
    message: '任务不存在或已过期',
  })

  it('says the record expired rather than that the work failed', async () => {
    //
    // The store reclaims finished tasks on its own schedule. "I cannot find the
    // record" and "the download failed" are different facts, and only the first
    // one is known here.
    //
    const { wrapper } = await tracking({
      getTask: vi.fn(async () => Promise.reject(missing)),
    })

    const text = wrapper.text()
    expect(text).toContain('任务记录不存在或已过期')
    expect(text).not.toContain('下载失败')
    expect(text).not.toContain('任务失败')
  })

  it('stops polling a record that is not there', async () => {
    const getTask = vi.fn(async () => Promise.reject(missing))
    await tracking({ getTask })
    const calls = getTask.mock.calls.length

    await vi.advanceTimersByTimeAsync(TASK_POLL_INTERVAL_MS * 5)

    expect(getTask).toHaveBeenCalledTimes(calls)
  })

  it('offers a fresh start rather than a pointless retry', async () => {
    const { wrapper } = await tracking({
      getTask: vi.fn(async () => Promise.reject(missing)),
    })

    expect(buttonSaying(wrapper, '重试获取状态')).toBeUndefined()
    expect(buttonSaying(wrapper, '新建另一个')).toBeTruthy()
  })
})

describe('terminal outcomes', () => {
  it.each<[TaskState, string]>([
    ['success', '任务已完成'],
    ['partial', '任务部分完成'],
    ['failed', '任务失败'],
    ['cancelled', '任务已停止'],
  ])('reports %s in words', async (state, expected) => {
    const { wrapper } = await tracking({ getTask: vi.fn(async () => taskIn(state)) })

    expect(wrapper.text()).toContain(expected)
  })

  it('prefers what the task itself said', async () => {
    const { wrapper } = await tracking({
      getTask: vi.fn(async () => taskIn('failed', { message: '作品已被删除' })),
    })

    expect(wrapper.text()).toContain('作品已被删除')
  })

  it('stops polling on every terminal state', async () => {
    for (const state of ['success', 'partial', 'failed', 'cancelled'] as TaskState[]) {
      const getTask = vi.fn(async () => taskIn(state))
      await tracking({ getTask })

      expect(getTask).toHaveBeenCalledTimes(1)
      await vi.advanceTimersByTimeAsync(TASK_POLL_INTERVAL_MS * 5)
      expect(getTask).toHaveBeenCalledTimes(1)
    }
  })
})
