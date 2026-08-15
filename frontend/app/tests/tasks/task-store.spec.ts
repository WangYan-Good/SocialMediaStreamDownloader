import { createPinia, setActivePinia } from 'pinia'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import { listTasks } from '../../src/api/tasks'
import { useTaskStore } from '../../src/stores/tasks'
import type { Task } from '../../src/types/task'

vi.mock('../../src/api/tasks', () => ({
  listTasks: vi.fn(),
}))

const mockedList = vi.mocked(listTasks)

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

function page(items: Task[], total = items.length) {
  return { items, total }
}

/** The filters the most recent call was made with. */
function lastFilters() {
  const call = mockedList.mock.calls.at(-1)
  if (!call) {
    throw new Error('listTasks was never called')
  }
  //
  // `filters` has a default, so the recorded argument is optional; an omitted
  // one means the same thing as an empty object here.
  //
  return call[0] ?? {}
}

beforeEach(() => {
  setActivePinia(createPinia())
  mockedList.mockReset()
  mockedList.mockResolvedValue(page([]))
})

describe('initial state', () => {
  it('starts empty, unfiltered and having asked nothing', () => {
    const store = useTaskStore()

    expect(store.tasks).toEqual([])
    expect(store.total).toBe(0)
    expect(store.stateFilter).toBeNull()
    expect(store.typeFilter).toBeNull()
    expect(store.limit).toBe(50)
    expect(store.selectedTaskId).toBeNull()
    expect(store.refreshError).toBeNull()
    expect(store.lastUpdatedAt).toBeNull()
    expect(store.pollingActive).toBe(false)
    expect(mockedList).not.toHaveBeenCalled()
  })

  it('has not loaded anything yet', () => {
    //
    // Distinct from "loaded and found nothing". The empty state must not be
    // shown until a read has actually succeeded.
    //
    const store = useTaskStore()

    expect(store.hasLoaded).toBe(false)
  })
})

describe('refreshing', () => {
  it('asks for everything when nothing is filtered', async () => {
    const store = useTaskStore()

    await store.refresh()

    expect(mockedList).toHaveBeenCalledTimes(1)
    expect(lastFilters().state).toBeUndefined()
    expect(lastFilters().type).toBeUndefined()
    expect(lastFilters().limit).toBe(50)
  })

  it('keeps the order the server sent', async () => {
    //
    // The backend sorts newest-first and the total is bound to that ordering.
    // Re-sorting here - by a parsed date, say - would quietly disagree with the
    // server about which task is the newest.
    //
    const server = [
      task({ task_id: 'C', created_at: '2026-08-15T09:00:00.000' }),
      task({ task_id: 'A', created_at: '2026-08-15T11:00:00.000' }),
      task({ task_id: 'B', created_at: '2026-08-15T10:00:00.000' }),
    ]
    mockedList.mockResolvedValue(page(server))
    const store = useTaskStore()

    await store.refresh()

    expect(store.tasks.map((one) => one.task_id)).toEqual(['C', 'A', 'B'])
  })

  it('keeps the server total apart from how many arrived', async () => {
    //
    // `total` counts everything matching the filters; `items` is what fitted
    // inside the limit. Conflating them would tell the user there are 50 tasks
    // when there are 73.
    //
    const items = Array.from({ length: 50 }, (_unused, index) =>
      task({ task_id: `task-${index}` }),
    )
    mockedList.mockResolvedValue(page(items, 73))
    const store = useTaskStore()

    await store.refresh()

    expect(store.tasks).toHaveLength(50)
    expect(store.total).toBe(73)
    expect(store.isTruncated).toBe(true)
  })

  it('knows when nothing was left out', async () => {
    mockedList.mockResolvedValue(page([task()], 1))
    const store = useTaskStore()

    await store.refresh()

    expect(store.isTruncated).toBe(false)
  })

  it('records when it last succeeded', async () => {
    const store = useTaskStore()

    await store.refresh()

    expect(store.lastUpdatedAt).toBeInstanceOf(Date)
    expect(store.hasLoaded).toBe(true)
  })

  it('reports the first load separately from later ones', async () => {
    let settle: (value: { items: Task[]; total: number }) => void = () => {}
    mockedList.mockReturnValue(
      new Promise((resolve) => {
        settle = resolve
      }),
    )
    const store = useTaskStore()

    const first = store.refresh()
    expect(store.initialLoading).toBe(true)
    expect(store.refreshing).toBe(true)

    settle(page([]))
    await first

    expect(store.initialLoading).toBe(false)
    expect(store.refreshing).toBe(false)

    //
    // A later refresh is not an initial load: the list is already on screen and
    // replacing it with a spinner would make a background poll look like a
    // page reload.
    //
    const second = store.refresh()
    expect(store.initialLoading).toBe(false)
    expect(store.refreshing).toBe(true)
    await second
  })
})

describe('filters', () => {
  it('sends the state filter as the wire value', async () => {
    const store = useTaskStore()

    await store.setStateFilter('running')

    expect(lastFilters().state).toBe('running')
  })

  it('sends the type filter as the wire value', async () => {
    const store = useTaskStore()

    await store.setTypeFilter('live_probe')

    expect(lastFilters().type).toBe('live_probe')
  })

  it('sends both together', async () => {
    const store = useTaskStore()

    await store.setStateFilter('failed')
    await store.setTypeFilter('owner_batch_download')

    expect(lastFilters().state).toBe('failed')
    expect(lastFilters().type).toBe('owner_batch_download')
  })

  it('clears a filter with null rather than an empty string', async () => {
    //
    // The backend validates these against its own vocabulary, and '' is not in
    // it. Null means "do not narrow"; an empty enum would be a bad request.
    //
    const store = useTaskStore()
    await store.setStateFilter('running')

    await store.setStateFilter(null)

    expect(lastFilters().state).toBeUndefined()
    expect(store.stateFilter).toBeNull()
  })

  it('refreshes at once rather than waiting for the next poll', async () => {
    const store = useTaskStore()
    const before = mockedList.mock.calls.length

    await store.setStateFilter('running')

    expect(mockedList.mock.calls.length).toBe(before + 1)
  })

  it('offers only the limits the ui knows about', async () => {
    const store = useTaskStore()

    await store.setLimit(100)
    expect(lastFilters().limit).toBe(100)

    await store.setLimit(25)
    expect(lastFilters().limit).toBe(25)
  })

  it('never filters the list again in the browser', async () => {
    //
    // The server has already applied the filters, and its total is bound to
    // them. Filtering again here would produce two different ideas of how many
    // tasks match.
    //
    const server = [
      task({ task_id: 'A', state: 'running' }),
      task({ task_id: 'B', state: 'success' }),
    ]
    mockedList.mockResolvedValue(page(server, 2))
    const store = useTaskStore()

    await store.setStateFilter('running')

    expect(store.tasks.map((one) => one.task_id)).toEqual(['A', 'B'])
  })
})

describe('selection', () => {
  const listed = [task({ task_id: 'A' }), task({ task_id: 'B' })]

  beforeEach(() => {
    mockedList.mockResolvedValue(page(listed))
  })

  it('reads the selected task out of the list rather than copying it', async () => {
    const store = useTaskStore()
    await store.refresh()

    store.select('B')

    expect(store.selectedTask?.task_id).toBe('B')
  })

  it('follows the list as it refreshes', async () => {
    //
    // The detail panel is a view of the same snapshot the row came from, so a
    // poll that moves a task from running to success updates both at once - and
    // there is no second copy to go stale.
    //
    const store = useTaskStore()
    await store.refresh()
    store.select('B')
    expect(store.selectedTask?.state).toBe('running')

    mockedList.mockResolvedValue(
      page([task({ task_id: 'A' }), task({ task_id: 'B', state: 'success' })]),
    )
    await store.refresh()

    expect(store.selectedTask?.state).toBe('success')
  })

  it('forgets a selection the list no longer contains', async () => {
    const store = useTaskStore()
    await store.refresh()
    store.select('B')

    mockedList.mockResolvedValue(page([task({ task_id: 'A' })]))
    await store.refresh()

    expect(store.selectedTaskId).toBeNull()
    expect(store.selectedTask).toBeNull()
  })

  it('drops the selection when the filters change', async () => {
    //
    // A task selected under one filter has no context under another: the panel
    // would describe something the list beside it no longer shows.
    //
    const store = useTaskStore()
    await store.refresh()
    store.select('B')

    await store.setStateFilter('failed')

    expect(store.selectedTaskId).toBeNull()
  })

  it('drops the selection when the limit changes', async () => {
    const store = useTaskStore()
    await store.refresh()
    store.select('B')

    await store.setLimit(25)

    expect(store.selectedTaskId).toBeNull()
  })

  it('can be cleared deliberately', async () => {
    const store = useTaskStore()
    await store.refresh()
    store.select('A')

    store.clearSelection()

    expect(store.selectedTaskId).toBeNull()
  })
})
