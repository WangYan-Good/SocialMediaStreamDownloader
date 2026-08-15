import { mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { nextTick } from 'vue'

import { getTask, listTasks } from '../../src/api/tasks'
import { TASK_CENTER_POLL_INTERVAL_MS } from '../../src/stores/tasks'
import TasksView from '../../src/views/TasksView.vue'
import type { Task, TaskState, TaskType } from '../../src/types/task'

vi.mock('../../src/api/tasks', () => ({
  listTasks: vi.fn(),
  getTask: vi.fn(),
}))

const mockedList = vi.mocked(listTasks)
const mockedGet = vi.mocked(getTask)

export function task(overrides: Partial<Task> = {}): Task {
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

export function page(items: Task[], total = items.length) {
  return { items, total }
}

export async function settle() {
  for (let index = 0; index < 5; index += 1) {
    await Promise.resolve()
  }
  await nextTick()
}

export async function mountTasks() {
  const wrapper = mount(TasksView)
  await settle()
  return wrapper
}

beforeEach(() => {
  setActivePinia(createPinia())
  mockedList.mockReset()
  mockedGet.mockReset()
  mockedList.mockResolvedValue(page([]))
  vi.useFakeTimers()
})

afterEach(() => {
  vi.useRealTimers()
})

describe('opening the task centre', () => {
  it('reads the task list straight away', async () => {
    //
    // Unlike every other screen so far, arriving here is itself a request: the
    // whole point is to show what the server is doing right now.
    //
    await mountTasks()

    expect(mockedList).toHaveBeenCalledTimes(1)
  })

  it('keeps reading while it stays open', async () => {
    await mountTasks()

    await vi.advanceTimersByTimeAsync(TASK_CENTER_POLL_INTERVAL_MS)
    expect(mockedList).toHaveBeenCalledTimes(2)

    await vi.advanceTimersByTimeAsync(TASK_CENTER_POLL_INTERVAL_MS)
    expect(mockedList).toHaveBeenCalledTimes(3)
  })

  it('stops reading once it is closed', async () => {
    const wrapper = await mountTasks()
    const before = mockedList.mock.calls.length

    wrapper.unmount()
    await vi.advanceTimersByTimeAsync(TASK_CENTER_POLL_INTERVAL_MS * 5)

    expect(mockedList).toHaveBeenCalledTimes(before)
  })

  it('starts exactly one loop when opened again', async () => {
    const first = await mountTasks()
    first.unmount()

    await mountTasks()
    const afterRemount = mockedList.mock.calls.length

    await vi.advanceTimersByTimeAsync(TASK_CENTER_POLL_INTERVAL_MS)

    expect(mockedList.mock.calls.length).toBe(afterRemount + 1)
  })

  it('reads again on reopening rather than trusting what it already had', async () => {
    mockedList.mockResolvedValue(page([task({ task_id: 'A' })]))
    const first = await mountTasks()
    first.unmount()
    const beforeRemount = mockedList.mock.calls.length

    await mountTasks()

    expect(mockedList.mock.calls.length).toBe(beforeRemount + 1)
  })
})

describe('the list is read whole, never task by task', () => {
  it('never asks for a single task', async () => {
    //
    // Every item in the list response is already a complete task snapshot, so
    // there is nothing a per-row read could add - only fifty more requests.
    //
    mockedList.mockResolvedValue(
      page([task({ task_id: 'A' }), task({ task_id: 'B' }), task({ task_id: 'C' })]),
    )

    await mountTasks()

    expect(mockedGet).not.toHaveBeenCalled()
  })

  it('does not ask for one when a row is opened either', async () => {
    mockedList.mockResolvedValue(page([task({ task_id: 'A' }), task({ task_id: 'B' })]))
    const wrapper = await mountTasks()

    await wrapper.findAll('button').find((b) => b.text() === '查看')?.trigger('click')
    await nextTick()

    expect(mockedGet).not.toHaveBeenCalled()
  })

  it('keeps asking only for the list as it polls', async () => {
    mockedList.mockResolvedValue(page([task({ task_id: 'A' })]))
    await mountTasks()

    await vi.advanceTimersByTimeAsync(TASK_CENTER_POLL_INTERVAL_MS * 3)

    expect(mockedGet).not.toHaveBeenCalled()
  })
})

describe('every kind of task is displayed', () => {
  it.each<[TaskType, string]>([
    ['post_download', '作品下载'],
    ['live_record', '直播录制'],
    ['owner_batch_download', '主播批量下载'],
    ['live_probe', '直播探测'],
  ])('shows a %s', async (type, label) => {
    //
    // live_probe cannot be created through the task api, but the history page
    // still produces them - so the task centre has to be able to show one.
    //
    mockedList.mockResolvedValue(page([task({ task_id: 'A', task_type: type })]))

    const wrapper = await mountTasks()

    expect(wrapper.text()).toContain(label)
  })

  it('shows all four together', async () => {
    mockedList.mockResolvedValue(
      page([
        task({ task_id: 'A', task_type: 'post_download' }),
        task({ task_id: 'B', task_type: 'live_record' }),
        task({ task_id: 'C', task_type: 'owner_batch_download' }),
        task({ task_id: 'D', task_type: 'live_probe' }),
      ]),
    )

    const wrapper = await mountTasks()

    expect(wrapper.findAll('tbody tr')).toHaveLength(4)
  })
})

describe('every state reads as words', () => {
  it.each<[TaskState, string]>([
    ['pending', '排队中'],
    ['running', '进行中'],
    ['success', '已完成'],
    ['partial', '部分完成'],
    ['failed', '失败'],
    ['cancelled', '已停止'],
  ])('labels %s', async (state, label) => {
    //
    // Never colour alone: a badge distinguished only by hue is unreadable to a
    // good number of people and invisible in a pasted screenshot.
    //
    mockedList.mockResolvedValue(page([task({ task_id: 'A', state })]))

    const wrapper = await mountTasks()

    expect(wrapper.find('.badge').text()).toBe(label)
  })
})

describe('rows', () => {
  it('keeps the order the server sent', async () => {
    mockedList.mockResolvedValue(
      page([
        task({ task_id: 'C', title: '第三' }),
        task({ task_id: 'A', title: '第一' }),
        task({ task_id: 'B', title: '第二' }),
      ]),
    )

    const wrapper = await mountTasks()

    const titles = wrapper.findAll('tbody tr .table__title').map((cell) => cell.text())
    expect(titles).toEqual(['第三', '第一', '第二'])
  })

  it('falls back to the type when a task has no title', async () => {
    mockedList.mockResolvedValue(
      page([task({ task_id: 'A', title: null, task_type: 'live_record' })]),
    )

    const wrapper = await mountTasks()

    expect(wrapper.find('.table__title').text()).toBe('直播录制')
  })

  it('gives every row a real button rather than making the row clickable', async () => {
    //
    // A row cannot be focused or announced as an action; a button can.
    //
    mockedList.mockResolvedValue(page([task({ task_id: 'A' })]))

    const wrapper = await mountTasks()

    const view = wrapper.findAll('tbody button')
    expect(view).toHaveLength(1)
    expect(view[0].text()).toBe('查看')
  })

  it('uses a real table with headers', async () => {
    mockedList.mockResolvedValue(page([task({ task_id: 'A' })]))

    const wrapper = await mountTasks()

    expect(wrapper.find('table').exists()).toBe(true)
    const headers = wrapper.findAll('th').map((header) => header.text())
    expect(headers).toContain('状态')
    expect(headers).toContain('类型')
    expect(headers).toContain('进度')
    for (const header of wrapper.findAll('th')) {
      expect(header.attributes('scope')).toBe('col')
    }
  })
})
