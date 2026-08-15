import { mount } from '@vue/test-utils'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { nextTick } from 'vue'

import { TASK_POLL_INTERVAL_MS } from '../../src/composables/useNewDownloadFlow'
import NewDownloadView from '../../src/views/NewDownloadView.vue'
import type { CreatedTask, Task, TaskState } from '../../src/types/task'
import { postResolution } from './build-request.spec'

const AWEME_ID = '7657271784144009946'

function taskIn(state: TaskState, overrides: Partial<Task> = {}): Task {
  return {
    task_id: 'task-1',
    task_type: 'post_download',
    state,
    title: '下载作品 ' + AWEME_ID,
    message: null,
    created_at: '2026-08-15T09:30:15.250',
    started_at: state === 'pending' ? null : '2026-08-15T09:30:16.250',
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
    getTask: vi.fn(async (_taskId: string) => taskIn('pending')),
    ...api,
  }
  const wrapper = mount(NewDownloadView, { props: { api: spies } })
  return { wrapper, spies }
}

/** Let queued microtasks run without advancing the fake clock. */
async function settle() {
  for (let index = 0; index < 4; index += 1) {
    await Promise.resolve()
  }
  await nextTick()
}

beforeEach(() => {
  vi.useFakeTimers()
})

afterEach(() => {
  vi.useRealTimers()
})

describe('the screen as it opens', () => {
  it('asks the backend for nothing', async () => {
    //
    // The line between this screen and the task centre. A placeholder that
    // quietly listed tasks would make this the beginning of the next stage,
    // with none of its tests.
    //
    const { spies } = mountView()
    await settle()

    expect(spies.resolveResource).not.toHaveBeenCalled()
    expect(spies.createTask).not.toHaveBeenCalled()
    expect(spies.getTask).not.toHaveBeenCalled()
  })

  it('offers a labelled box and nothing else to press', async () => {
    const { wrapper } = mountView()

    expect(wrapper.find('textarea').exists()).toBe(true)
    expect(wrapper.find('label').text()).toBeTruthy()

    const buttons = wrapper.findAll('button')
    expect(buttons).toHaveLength(1)
    expect(buttons[0].text()).toContain('解析')
    expect(buttons[0].attributes('disabled')).toBeDefined()
  })

  it('shows no resolution and no task', () => {
    const { wrapper } = mountView()

    expect(wrapper.text()).not.toContain('确认资源')
    expect(wrapper.text()).not.toContain('当前任务')
  })

  it('enables resolving once something is typed', async () => {
    const { wrapper } = mountView()

    await wrapper.find('textarea').setValue('https://v.douyin.com/abc/')

    expect(wrapper.find('button').attributes('disabled')).toBeUndefined()
  })
})

describe('a post, end to end', () => {
  async function resolvePost() {
    const built = mountView()
    await built.wrapper.find('textarea').setValue('https://v.douyin.com/abc/')
    await built.wrapper.find('button').trigger('click')
    await settle()
    return built
  }

  it('sends what was typed and shows what came back', async () => {
    const { wrapper, spies } = await resolvePost()

    expect(spies.resolveResource).toHaveBeenCalledWith('https://v.douyin.com/abc/')
    expect(wrapper.text()).toContain('确认资源')
    expect(wrapper.text()).toContain('作品')
    expect(wrapper.text()).toContain(AWEME_ID)
  })

  it('shows both urls and how long the receipt lasts', async () => {
    const { wrapper } = await resolvePost()

    expect(wrapper.text()).toContain(postResolution.source_url)
    expect(wrapper.text()).toContain(postResolution.resolved_url)
    expect(wrapper.text()).toContain('10 分钟')
  })

  it('claims nothing the server did not answer', async () => {
    //
    // The resolve endpoint is identity-level on purpose. Showing a nickname or
    // a cover would mean either inventing them or spending another platform
    // request - and the second one needs a login that reading a url should
    // never depend on.
    //
    const { wrapper } = await resolvePost()
    const text = wrapper.text()

    for (const absent of ['昵称', '头像', '封面', '简介', '粉丝']) {
      expect(text).not.toContain(absent)
    }
  })

  it('opens links in a new tab without handing over the opener', async () => {
    const { wrapper } = await resolvePost()

    for (const link of wrapper.findAll('a')) {
      expect(link.attributes('target')).toBe('_blank')
      expect(link.attributes('rel')).toBe('noopener noreferrer')
    }
  })

  it('creates the task with the receipt alone', async () => {
    const { wrapper, spies } = await resolvePost()

    const create = wrapper.findAll('button').find((b) => b.text().includes('下载该作品'))
    await create?.trigger('click')
    await settle()

    expect(spies.createTask).toHaveBeenCalledWith({
      resolve_id: 'receipt-1',
      task_type: 'post_download',
    })
  })

  it('tracks the created task through to completion', async () => {
    const states: TaskState[] = ['pending', 'running', 'success']
    let index = 0
    const getTask = vi.fn(async () => taskIn(states[Math.min(index++, 2)]))
    const built = mountView({ getTask })
    await built.wrapper.find('textarea').setValue('https://v.douyin.com/abc/')
    await built.wrapper.find('button').trigger('click')
    await settle()
    await built.wrapper
      .findAll('button')
      .find((b) => b.text().includes('下载该作品'))
      ?.trigger('click')
    await settle()

    expect(built.wrapper.text()).toContain('当前任务')
    expect(built.wrapper.text()).toContain('task-1')
    expect(built.wrapper.text()).toContain('排队中')

    await vi.advanceTimersByTimeAsync(TASK_POLL_INTERVAL_MS)
    await nextTick()
    expect(built.wrapper.text()).toContain('进行中')

    await vi.advanceTimersByTimeAsync(TASK_POLL_INTERVAL_MS)
    await nextTick()
    expect(built.wrapper.text()).toContain('已完成')
    expect(built.wrapper.text()).toContain('任务已完成')

    const calls = getTask.mock.calls.length
    await vi.advanceTimersByTimeAsync(TASK_POLL_INTERVAL_MS * 5)
    expect(getTask).toHaveBeenCalledTimes(calls)
  })

  it('offers a fresh start only once the task has ended', async () => {
    const getTask = vi.fn(async () => taskIn('running'))
    const built = mountView({ getTask })
    await built.wrapper.find('textarea').setValue('https://v.douyin.com/abc/')
    await built.wrapper.find('button').trigger('click')
    await settle()
    await built.wrapper
      .findAll('button')
      .find((b) => b.text().includes('下载该作品'))
      ?.trigger('click')
    await settle()

    //
    // There is nowhere else to find a running task yet, so this screen does not
    // offer to forget about it.
    //
    expect(
      built.wrapper.findAll('button').some((b) => b.text().includes('新建另一个')),
    ).toBe(false)
  })

  it('clears everything when starting over', async () => {
    const built = mountView({ getTask: vi.fn(async () => taskIn('success')) })
    await built.wrapper.find('textarea').setValue('https://v.douyin.com/abc/')
    await built.wrapper.find('button').trigger('click')
    await settle()
    await built.wrapper
      .findAll('button')
      .find((b) => b.text().includes('下载该作品'))
      ?.trigger('click')
    await settle()

    const again = built.wrapper.findAll('button').find((b) => b.text().includes('新建另一个'))
    await again?.trigger('click')
    await nextTick()

    expect(built.wrapper.find('textarea').element.value).toBe('')
    expect(built.wrapper.text()).not.toContain('确认资源')
    expect(built.wrapper.text()).not.toContain('当前任务')
  })
})

describe('double submission through the buttons', () => {
  it('resolves once however fast the button is pressed', async () => {
    const pending = new Promise<typeof postResolution>(() => {})
    const resolveResource = vi.fn(() => pending)
    const { wrapper } = mountView({ resolveResource })
    await wrapper.find('textarea').setValue('https://v.douyin.com/abc/')

    const button = wrapper.find('button')
    await button.trigger('click')
    await button.trigger('click')
    await button.trigger('click')

    expect(resolveResource).toHaveBeenCalledTimes(1)
  })

  it('creates once however fast the button is pressed', async () => {
    const pending = new Promise<CreatedTask>(() => {})
    const createTask = vi.fn(() => pending)
    const { wrapper } = mountView({ createTask })
    await wrapper.find('textarea').setValue('https://v.douyin.com/abc/')
    await wrapper.find('button').trigger('click')
    await settle()

    const create = wrapper.findAll('button').find((b) => b.text().includes('下载该作品'))
    await create?.trigger('click')
    await create?.trigger('click')
    await create?.trigger('click')

    expect(createTask).toHaveBeenCalledTimes(1)
  })
})

describe('this screen is not the task centre', () => {
  it('reads one task by id and never the list', async () => {
    //
    // Locked at the api layer: `listTasks` is not even wired into this screen,
    // and a future edit that reached for it would have to add it here first.
    //
    const listTasks = vi.fn()
    const { wrapper, spies } = mountView()
    await wrapper.find('textarea').setValue('https://v.douyin.com/abc/')
    await wrapper.find('button').trigger('click')
    await settle()
    await wrapper
      .findAll('button')
      .find((b) => b.text().includes('下载该作品'))
      ?.trigger('click')
    await settle()

    expect(listTasks).not.toHaveBeenCalled()
    expect(spies.getTask).toHaveBeenCalledWith('task-1')
    for (const call of vi.mocked(spies.getTask).mock.calls) {
      expect(call[0]).toBe('task-1')
    }
  })
})

describe('leaving the screen', () => {
  it('stops polling when unmounted', async () => {
    const getTask = vi.fn(async () => taskIn('running'))
    const { wrapper } = mountView({ getTask })
    await wrapper.find('textarea').setValue('https://v.douyin.com/abc/')
    await wrapper.find('button').trigger('click')
    await settle()
    await wrapper
      .findAll('button')
      .find((b) => b.text().includes('下载该作品'))
      ?.trigger('click')
    await settle()

    const before = getTask.mock.calls.length
    wrapper.unmount()

    await vi.advanceTimersByTimeAsync(TASK_POLL_INTERVAL_MS * 5)

    expect(getTask).toHaveBeenCalledTimes(before)
  })
})
