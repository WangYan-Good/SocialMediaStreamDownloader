import { mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { nextTick } from 'vue'

import { ApiError } from '../../src/api/client'
import { listTasks } from '../../src/api/tasks'
import {
  progressPercent,
  progressText,
  formatTaskTime,
} from '../../src/components/tasks/taskPresentation'
import { TASK_CENTER_POLL_INTERVAL_MS } from '../../src/stores/tasks'
import TasksView from '../../src/views/TasksView.vue'
import type { Task } from '../../src/types/task'

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

async function mountTasks() {
  const wrapper = mount(TasksView)
  await settle()
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

describe('how many there are', () => {
  it('says what was shown and what exists when they differ', async () => {
    //
    // The api applies the limit after filtering, so `total` is how many match
    // and `items` is how many fitted. Reporting only the second would tell the
    // user there are 50 tasks when there are 73.
    //
    const items = Array.from({ length: 50 }, (_unused, index) =>
      task({ task_id: `task-${index}` }),
    )
    mockedList.mockResolvedValue(page(items, 73))

    const wrapper = await mountTasks()

    expect(wrapper.text()).toContain('显示最新 50 条，共 73 条')
  })

  it('says just the count when nothing was left out', async () => {
    mockedList.mockResolvedValue(page([task({ task_id: 'A' }), task({ task_id: 'B' })], 2))

    const wrapper = await mountTasks()

    expect(wrapper.text()).toContain('共 2 条')
    expect(wrapper.text()).not.toContain('显示最新')
  })

  it('offers no page numbers', async () => {
    //
    // The api takes a limit and has no offset, so a "page 2" control would be a
    // button that cannot go anywhere.
    //
    const items = Array.from({ length: 25 }, (_unused, index) =>
      task({ task_id: `task-${index}` }),
    )
    mockedList.mockResolvedValue(page(items, 99))

    const wrapper = await mountTasks()

    expect(wrapper.text()).not.toContain('下一页')
    expect(wrapper.text()).not.toContain('第 1')
  })
})

describe('nothing to show, or nothing read', () => {
  it('says the list is empty only after a successful read', async () => {
    mockedList.mockResolvedValue(page([]))

    const wrapper = await mountTasks()

    expect(wrapper.text()).toContain('当前没有任务')
  })

  it('suggests loosening the filters when some are set', async () => {
    mockedList.mockResolvedValue(page([]))
    const wrapper = await mountTasks()

    await wrapper.findAll('select')[0].setValue('failed')
    await settle()

    expect(wrapper.text()).toContain('调整筛选条件')
  })

  it('never claims the list is empty when it could not be read', async () => {
    //
    // "Nothing was read" and "there is nothing" are different facts. Showing
    // the empty state on a failed first load asserts the second one on no
    // evidence at all.
    //
    mockedList.mockRejectedValue(
      new ApiError({ kind: 'network', status: null, code: null, message: 'offline' }),
    )

    const wrapper = await mountTasks()

    expect(wrapper.text()).not.toContain('当前没有任务')
    expect(wrapper.find('[role="alert"]').exists()).toBe(true)
  })
})

describe('when a refresh fails', () => {
  const offline = new ApiError({
    kind: 'network',
    status: null,
    code: null,
    message: 'Failed to fetch',
  })

  async function loadedThenOffline() {
    mockedList.mockResolvedValueOnce(page([task({ task_id: 'A', state: 'running' })]))
    const wrapper = await mountTasks()
    mockedList.mockRejectedValue(offline)
    await vi.advanceTimersByTimeAsync(TASK_CENTER_POLL_INTERVAL_MS)
    await nextTick()
    return wrapper
  }

  it('keeps showing what it last saw', async () => {
    const wrapper = await loadedThenOffline()

    expect(wrapper.findAll('tbody tr')).toHaveLength(1)
    expect(wrapper.find('.badge').text()).toBe('进行中')
  })

  it('says the list could not be refreshed, not that anything failed', async () => {
    const wrapper = await loadedThenOffline()

    const alert = wrapper.find('[role="alert"]')
    expect(alert.text()).toContain('无法刷新任务列表')
    expect(alert.text()).not.toContain('任务失败')
  })

  it('offers a retry that reads again', async () => {
    const wrapper = await loadedThenOffline()
    mockedList.mockResolvedValue(page([task({ task_id: 'A', state: 'success' })]))
    const before = mockedList.mock.calls.length

    await wrapper.findAll('button').find((b) => b.text() === '重试')?.trigger('click')
    await settle()

    expect(mockedList.mock.calls.length).toBeGreaterThan(before)
    expect(wrapper.find('[role="alert"]').exists()).toBe(false)
    expect(wrapper.find('.badge').text()).toBe('已完成')
  })
})

describe('progress', () => {
  it('shows a fraction and a percentage', async () => {
    mockedList.mockResolvedValue(
      page([task({ task_id: 'A', progress: { current: 2, total: 5 } })]),
    )

    const wrapper = await mountTasks()

    expect(wrapper.find('.progress').text()).toContain('2 / 5')
    expect(wrapper.find('.progress').text()).toContain('40%')
  })

  it('says the total is unknown rather than dividing by it', async () => {
    mockedList.mockResolvedValue(
      page([
        task({
          task_id: 'A',
          task_type: 'live_record',
          progress: { current: 97, total: null },
        }),
      ]),
    )

    const wrapper = await mountTasks()

    const text = wrapper.find('.progress').text()
    expect(text).toContain('已处理 97')
    expect(text).toContain('总量未知')
    expect(text).not.toContain('NaN')
    expect(text).not.toContain('Infinity')
  })

  it('survives a zero total', async () => {
    mockedList.mockResolvedValue(
      page([task({ task_id: 'A', progress: { current: 0, total: 0 } })]),
    )

    const wrapper = await mountTasks()

    const text = wrapper.find('.progress').text()
    expect(text).toContain('0 / 0')
    expect(text).not.toContain('NaN')
    expect(text).not.toContain('%')
  })

  it('never draws a bar past its container', async () => {
    //
    // A runner reporting more finished units than it declared would otherwise
    // push the fill outside the track.
    //
    mockedList.mockResolvedValue(
      page([task({ task_id: 'A', progress: { current: 7, total: 5 } })]),
    )

    const wrapper = await mountTasks()

    expect(wrapper.find('.progress').text()).toContain('100%')
    expect(wrapper.find('.progress__fill').attributes('style')).toContain('width: 100%')
  })

  it('is called progress and never a success rate', async () => {
    //
    // `current` counts units dealt with, whatever the outcome: a failed post
    // still advances it. Calling it a success rate would report a batch where
    // everything failed as entirely successful.
    //
    mockedList.mockResolvedValue(page([task({ task_id: 'A' })]))

    const wrapper = await mountTasks()

    expect(wrapper.findAll('th').map((h) => h.text())).toContain('进度')
    expect(wrapper.text()).not.toContain('成功率')
    expect(wrapper.text()).not.toContain('成功进度')
  })
})

describe('the presentation helpers on their own', () => {
  it.each([
    [2, 5, 40],
    [0, 5, 0],
    [5, 5, 100],
    [7, 5, 100],
  ])('turns %i of %i into %i%%', (current, total, expected) => {
    expect(progressPercent(current, total)).toBe(expected)
  })

  it.each([
    [0, null],
    [3, 0],
  ])('has no percentage for %i of %s', (current, total) => {
    expect(progressPercent(current, total)).toBeNull()
  })

  it('words an unknown total', () => {
    expect(progressText(97, null)).toBe('已处理 97')
    expect(progressText(2, 5)).toBe('2 / 5')
  })

  it('falls back to the raw string for an unparseable time', () => {
    //
    // A bad timestamp is one bad cell, not a broken page - and leaving the odd
    // value visible is what lets somebody explain it later.
    //
    expect(formatTaskTime('not a date')).toBe('not a date')
    expect(formatTaskTime(null)).toBe('—')
    expect(formatTaskTime('2026-08-15T09:30:15.250')).not.toBe('—')
  })
})

describe('filters reach the api as wire values', () => {
  it('sends what was chosen', async () => {
    const wrapper = await mountTasks()

    await wrapper.findAll('select')[0].setValue('running')
    await settle()
    await wrapper.findAll('select')[1].setValue('live_record')
    await settle()
    await wrapper.findAll('select')[2].setValue('25')
    await settle()

    const [filters] = mockedList.mock.calls.at(-1) ?? []
    expect(filters?.state).toBe('running')
    expect(filters?.type).toBe('live_record')
    expect(filters?.limit).toBe(25)
  })

  it('sends nothing at all for "all"', async () => {
    const wrapper = await mountTasks()
    await wrapper.findAll('select')[0].setValue('running')
    await settle()

    await wrapper.findAll('select')[0].setValue('')
    await settle()

    const [filters] = mockedList.mock.calls.at(-1) ?? []
    expect(filters?.state).toBeUndefined()
  })

  it('labels every filter', async () => {
    const wrapper = await mountTasks()

    const labels = wrapper.findAll('.filters__label').map((one) => one.text())
    expect(labels).toEqual(['状态', '类型', '显示条数'])
  })
})
