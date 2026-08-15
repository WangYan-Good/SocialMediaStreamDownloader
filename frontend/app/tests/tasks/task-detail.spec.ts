import { mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { nextTick } from 'vue'

import { listTasks } from '../../src/api/tasks'
import { TASK_CENTER_POLL_INTERVAL_MS } from '../../src/stores/tasks'
import TasksView from '../../src/views/TasksView.vue'
import type { Task, TaskItemState } from '../../src/types/task'

vi.mock('../../src/api/tasks', () => ({
  listTasks: vi.fn(),
  getTask: vi.fn(),
}))

const mockedList = vi.mocked(listTasks)

function task(overrides: Partial<Task> = {}): Task {
  return {
    task_id: 'task-1',
    task_type: 'post_download',
    state: 'running',
    title: null,
    message: null,
    created_at: '2026-08-15T09:30:15.250',
    started_at: '2026-08-15T09:30:16.250',
    finished_at: null,
    progress: { current: 0, total: 1 },
    metadata: {},
    items: [],
    ...overrides,
  }
}

function page(items: Task[], total = items.length) {
  return { items, total }
}

async function settle() {
  for (let index = 0; index < 5; index += 1) {
    await Promise.resolve()
  }
  await nextTick()
}

async function openFirstTask(listed: Task[]) {
  mockedList.mockResolvedValue(page(listed))
  const wrapper = mount(TasksView)
  await settle()
  await wrapper.findAll('tbody button').at(0)?.trigger('click')
  await nextTick()
  return wrapper
}

beforeEach(() => {
  setActivePinia(createPinia())
  mockedList.mockReset()
  mockedList.mockResolvedValue(page([]))
  vi.useFakeTimers()
})

afterEach(() => {
  vi.useRealTimers()
})

describe('opening a task', () => {
  it('shows its detail beside the list', async () => {
    const wrapper = await openFirstTask([
      task({ task_id: 'A', title: '下载作品 7657271784144009946' }),
    ])

    const detail = wrapper.find('aside')
    expect(detail.exists()).toBe(true)
    expect(detail.text()).toContain('下载作品 7657271784144009946')
    expect(detail.text()).toContain('A')
  })

  it('gives the panel a heading', async () => {
    const wrapper = await openFirstTask([task({ task_id: 'A', title: '批量下载' })])

    const heading = wrapper.find('aside h2')
    expect(heading.exists()).toBe(true)
    expect(wrapper.find('aside').attributes('aria-labelledby')).toBe(heading.attributes('id'))
  })

  it('can be closed again', async () => {
    const wrapper = await openFirstTask([task({ task_id: 'A' })])

    await wrapper.findAll('button').find((b) => b.text() === '关闭详情')?.trigger('click')
    await nextTick()

    expect(wrapper.find('aside').exists()).toBe(false)
  })

  it('follows the same snapshot the list refreshes', async () => {
    //
    // The panel reads the task out of the list rather than keeping a copy, so a
    // poll that moves it from running to success updates both at once - and
    // there is no second copy left showing the old state.
    //
    const wrapper = await openFirstTask([task({ task_id: 'A', state: 'running' })])
    expect(wrapper.find('aside').text()).toContain('进行中')

    mockedList.mockResolvedValue(
      page([task({ task_id: 'A', state: 'success', message: '已保存 3 个媒体文件' })]),
    )
    await vi.advanceTimersByTimeAsync(TASK_CENTER_POLL_INTERVAL_MS)
    await nextTick()

    expect(wrapper.find('aside').text()).toContain('已完成')
    expect(wrapper.find('aside').text()).toContain('已保存 3 个媒体文件')
  })

  it('closes itself when the task leaves the list', async () => {
    const wrapper = await openFirstTask([task({ task_id: 'A' }), task({ task_id: 'B' })])
    expect(wrapper.find('aside').exists()).toBe(true)

    mockedList.mockResolvedValue(page([task({ task_id: 'B' })]))
    await vi.advanceTimersByTimeAsync(TASK_CENTER_POLL_INTERVAL_MS)
    await nextTick()

    expect(wrapper.find('aside').exists()).toBe(false)
  })
})

describe('metadata is shown from an allow list', () => {
  it('shows the fields this project knows the meaning of', async () => {
    const wrapper = await openFirstTask([
      task({
        task_id: 'A',
        metadata: {
          platform: 'douyin',
          source: 'task_api',
          resolve_id: 'receipt-1',
          aweme_id: '7657271784144009946',
          mode: 'all',
        },
      }),
    ])

    const detail = wrapper.find('aside').text()
    expect(detail).toContain('douyin')
    expect(detail).toContain('task_api')
    expect(detail).toContain('receipt-1')
    expect(detail).toContain('7657271784144009946')
  })

  it('shows nothing it has not been taught to show', async () => {
    //
    // The reason this is an allow list rather than a loop over the object: a
    // runner is free to record whatever helps it, and a future one recording a
    // signed url or an internal path must not put it on screen by default.
    //
    const wrapper = await openFirstTask([
      task({
        task_id: 'A',
        metadata: {
          platform: 'douyin',
          internal_cookie: 'sessionid=SECRET',
          signed_stream_url: 'https://pull.example/live.flv?sign=SECRET',
          debug_headers: { authorization: 'Bearer SECRET' },
        },
      }),
    ])

    const detail = wrapper.find('aside').text()
    expect(detail).toContain('douyin')
    expect(detail).not.toContain('SECRET')
    expect(detail).not.toContain('internal_cookie')
    expect(detail).not.toContain('signed_stream_url')
    expect(detail).not.toContain('authorization')
  })

  it('never dumps the whole object', async () => {
    const wrapper = await openFirstTask([
      task({ task_id: 'A', metadata: { platform: 'douyin', nested: { deep: [1, 2, 3] } } }),
    ])

    const detail = wrapper.find('aside').text()
    expect(detail).not.toContain('{')
    expect(detail).not.toContain('[')
  })

  it('links the urls safely', async () => {
    const wrapper = await openFirstTask([
      task({
        task_id: 'A',
        metadata: {
          source_url: 'https://v.douyin.com/abc/',
          resolved_url: 'https://www.douyin.com/video/7657271784144009946',
        },
      }),
    ])

    const links = wrapper.findAll('aside a')
    expect(links).toHaveLength(2)
    for (const link of links) {
      expect(link.attributes('target')).toBe('_blank')
      expect(link.attributes('rel')).toBe('noopener noreferrer')
    }
  })

  it('shows a known result summary', async () => {
    const wrapper = await openFirstTask([
      task({
        task_id: 'A',
        state: 'success',
        metadata: {
          platform: 'douyin',
          result: {
            ok: true,
            saved_count: 3,
            media_count: 3,
            save_dir: '/media/douyin/A/post',
            reason: null,
            internal_debug: 'SECRET',
          },
        },
      }),
    ])

    const detail = wrapper.find('aside').text()
    expect(detail).toContain('3')
    expect(detail).toContain('/media/douyin/A/post')
    expect(detail).not.toContain('SECRET')
  })

  it('renders booleans as words rather than as true/false', async () => {
    const wrapper = await openFirstTask([
      task({
        task_id: 'A',
        metadata: { result: { recorded: true, skipped: false, test_mode: true } },
      }),
    ])

    const detail = wrapper.find('aside').text()
    expect(detail).toContain('是')
    expect(detail).toContain('否')
  })
})

describe('work items', () => {
  it('lists them when a task has any', async () => {
    //
    // Mostly an owner batch or a live probe. A single post download has no
    // items - the task is the unit of work.
    //
    const wrapper = await openFirstTask([
      task({
        task_id: 'A',
        task_type: 'owner_batch_download',
        items: [
          { key: '7657271784144009946', state: 'success', message: null, metadata: {} },
          { key: '7657271784144009947', state: 'failed', message: '下载超时', metadata: {} },
        ],
      }),
    ])

    const detail = wrapper.find('aside').text()
    expect(detail).toContain('工作项（2）')
    expect(detail).toContain('7657271784144009946')
    expect(detail).toContain('下载超时')
  })

  it.each<[TaskItemState, string]>([
    ['pending', '排队中'],
    ['running', '进行中'],
    ['success', '已完成'],
    ['failed', '失败'],
    ['skipped', '已跳过'],
  ])('labels a %s item', async (state, label) => {
    const wrapper = await openFirstTask([
      task({
        task_id: 'A',
        items: [{ key: 'unit', state, message: null, metadata: {} }],
      }),
    ])

    expect(wrapper.find('.items__state').text()).toBe(label)
  })

  it('does not read a skipped item as a failure', async () => {
    //
    // In the owner walk `skipped` means the file is already on disk: the user's
    // goal is met. Reporting it as a failure would turn a success into a
    // problem.
    //
    const wrapper = await openFirstTask([
      task({
        task_id: 'A',
        items: [{ key: 'unit', state: 'skipped', message: '已经下载过', metadata: {} }],
      }),
    ])

    const detail = wrapper.find('aside').text()
    expect(detail).toContain('已跳过')
    expect(detail).not.toContain('失败')
  })

  it('shows no items section when there are none', async () => {
    const wrapper = await openFirstTask([task({ task_id: 'A', items: [] })])

    expect(wrapper.find('aside').text()).not.toContain('工作项')
  })

  it('does not dump item metadata', async () => {
    const wrapper = await openFirstTask([
      task({
        task_id: 'A',
        items: [
          {
            key: 'unit',
            state: 'success',
            message: null,
            metadata: { internal_path: '/srv/SECRET', headers: { cookie: 'SECRET' } },
          },
        ],
      }),
    ])

    expect(wrapper.find('aside').text()).not.toContain('SECRET')
  })
})

describe('urls are only linked when they are safe to link', () => {
  it('links an http and an https url', async () => {
    const wrapper = await openFirstTask([
      task({
        task_id: 'A',
        metadata: {
          source_url: 'http://v.douyin.com/abc/',
          resolved_url: 'https://www.douyin.com/video/1',
        },
      }),
    ])

    expect(wrapper.findAll('aside a')).toHaveLength(2)
  })

  it('never turns a javascript url into a link', async () => {
    //
    // rel="noopener noreferrer" does nothing about this: the scheme itself is
    // the payload, and clicking would run it. Metadata is arbitrary business
    // data written by runners, so the browser checks rather than trusts.
    //
    const wrapper = await openFirstTask([
      task({
        task_id: 'A',
        metadata: {
          source_url: 'javascript:alert(document.cookie)',
          resolved_url: 'https://www.douyin.com/video/1',
        },
      }),
    ])

    const hrefs = wrapper.findAll('aside a').map((link) => link.attributes('href'))
    expect(hrefs).toEqual(['https://www.douyin.com/video/1'])
  })

  it('still shows the refused value as text', async () => {
    //
    // Hiding it would be worse: an odd value in a task record is something
    // somebody needs to be able to see and explain.
    //
    const wrapper = await openFirstTask([
      task({ task_id: 'A', metadata: { source_url: 'javascript:alert(1)' } }),
    ])

    expect(wrapper.find('aside').text()).toContain('javascript:alert(1)')
    expect(wrapper.findAll('aside a')).toHaveLength(0)
  })

  it.each([
    'javascript:alert(1)',
    'JavaScript:alert(1)',
    '  javascript:alert(1)',
    'data:text/html,<script>alert(1)</script>',
    'vbscript:msgbox(1)',
    'file:///etc/passwd',
  ])('refuses to link %s', async (value) => {
    const wrapper = await openFirstTask([
      task({ task_id: 'A', metadata: { source_url: value } }),
    ])

    expect(wrapper.findAll('aside a')).toHaveLength(0)
  })
})
