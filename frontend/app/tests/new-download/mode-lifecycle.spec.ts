import { mount } from '@vue/test-utils'
import { afterEach, describe, expect, it, vi } from 'vitest'
import { nextTick } from 'vue'
import { createMemoryHistory, createRouter } from 'vue-router'

import { TASK_POLL_INTERVAL_MS } from '../../src/composables/useNewDownloadFlow'
import { routes } from '../../src/router'
import NewDownloadView from '../../src/views/NewDownloadView.vue'
import type { BatchResolveResult, ResolvedResource } from '../../src/types/resolution'
import type { CreatedTask, Task } from '../../src/types/task'

function deferred<T>() {
  let settle: (value: T) => void = () => {}
  const promise = new Promise<T>((resolve) => {
    settle = resolve
  })
  return { promise, settle }
}

const postResolution: ResolvedResource = {
  resolve_id: 'receipt-1',
  platform: 'douyin',
  resource_type: 'post',
  source_url: 'https://v.douyin.com/M-kmspLye0o/',
  resolved_url: 'https://www.douyin.com/video/7657271784144009946',
  identity: { aweme_id: '7657271784144009946' },
  expires_in_seconds: 600,
}

const secondPost: ResolvedResource = {
  ...postResolution,
  resolve_id: 'receipt-2',
  source_url: 'https://www.douyin.com/video/2',
  resolved_url: 'https://www.douyin.com/video/2',
  identity: { aweme_id: '2' },
}

const batchResult: BatchResolveResult = {
  total: 2,
  resolved_count: 2,
  failed_count: 0,
  items: [
    { index: 0, status: 'resolved', resolution: postResolution },
    { index: 1, status: 'resolved', resolution: secondPost },
  ],
}

function created(resolveId: string): CreatedTask {
  return {
    task_id: `task-${resolveId}`,
    task_type: 'post_download',
    resolve_id: resolveId,
  }
}

function runningTask(): Task {
  return {
    task_id: 'task-receipt-1',
    task_type: 'post_download',
    state: 'running',
    title: '下载作品',
    message: null,
    created_at: '2026-08-16T12:00:00',
    started_at: '2026-08-16T12:00:01',
    finished_at: null,
    progress: { current: 0, total: 1 },
    metadata: {},
    items: [],
  }
}

async function settle() {
  for (let index = 0; index < 6; index += 1) {
    await Promise.resolve()
  }
  await nextTick()
}

async function mountView({
  resolveResources = vi.fn(async () => batchResult),
  batchCreateTask = vi.fn(async (request) => created(request.resolve_id)),
  singleCreateTask = vi.fn(async (request) => created(request.resolve_id)),
  getTask = vi.fn(async (_taskId: string, _signal?: AbortSignal) => runningTask()),
} = {}) {
  const router = createRouter({ history: createMemoryHistory(), routes })
  await router.push('/new')
  await router.isReady()
  const wrapper = mount(NewDownloadView, {
    props: {
      api: {
        resolveResource: vi.fn(async () => postResolution),
        createTask: singleCreateTask,
        getTask,
      },
      batchApi: { resolveResources, createTask: batchCreateTask },
    },
    global: { plugins: [router] },
  })
  return { wrapper, resolveResources, batchCreateTask, singleCreateTask, getTask }
}

afterEach(() => {
  vi.useRealTimers()
})

describe('new-download mode lifecycle', () => {
  it('stops not-yet-requested batch creations when single mode hides the flow', async () => {
    const first = deferred<CreatedTask>()
    const batchCreateTask = vi
      .fn()
      .mockReturnValueOnce(first.promise)
      .mockResolvedValueOnce(created('receipt-2'))
    const { wrapper } = await mountView({ batchCreateTask })
    await wrapper.get('[data-mode="batch"]').trigger('click')
    await wrapper.get('.batch-input textarea').setValue('two links')
    await wrapper.get('.batch-input button').trigger('click')
    await settle()

    await wrapper.get('.batch-review__create').trigger('click')
    await settle()
    expect(batchCreateTask).toHaveBeenCalledTimes(1)

    await wrapper.get('[data-mode="single"]').trigger('click')
    first.settle(created('receipt-1'))
    await settle()

    expect(batchCreateTask).toHaveBeenCalledTimes(1)
  })

  it('drops a late batch resolution after switching to single mode', async () => {
    const pending = deferred<BatchResolveResult>()
    const resolveResources = vi.fn(() => pending.promise)
    const { wrapper } = await mountView({ resolveResources })
    await wrapper.get('[data-mode="batch"]').trigger('click')
    await wrapper.get('.batch-input textarea').setValue('two links')
    await wrapper.get('.batch-input button').trigger('click')
    await settle()

    await wrapper.get('[data-mode="single"]').trigger('click')
    pending.settle(batchResult)
    await settle()
    await wrapper.get('[data-mode="batch"]').trigger('click')
    await settle()

    expect(wrapper.find('.batch-review').exists()).toBe(false)
  })

  it('does not start hidden polling when task creation finishes after mode switch', async () => {
    const pendingCreate = deferred<CreatedTask>()
    const singleCreateTask = vi.fn(() => pendingCreate.promise)
    const getTask = vi.fn(async () => runningTask())
    const { wrapper } = await mountView({ singleCreateTask, getTask })
    await wrapper.get('textarea').setValue('https://v.douyin.com/abc/')
    await wrapper.get('button').trigger('click')
    await settle()
    await wrapper
      .findAll('button')
      .find((button) => button.text().includes('开始下载'))
      ?.trigger('click')
    await settle()
    expect(singleCreateTask).toHaveBeenCalledTimes(1)

    await wrapper.get('[data-mode="batch"]').trigger('click')
    pendingCreate.settle(created('receipt-1'))
    await settle()

    expect(getTask).not.toHaveBeenCalled()
  })

  it('aborts and invalidates an in-flight single-task poll when batch mode hides it', async () => {
    vi.useFakeTimers()
    const pending = deferred<Task>()
    const signals: AbortSignal[] = []
    const getTask = vi.fn((_taskId: string, signal?: AbortSignal) => {
      if (signal) {
        signals.push(signal)
      }
      return pending.promise
    })
    const { wrapper } = await mountView({ getTask })
    await wrapper.get('textarea').setValue('https://v.douyin.com/abc/')
    await wrapper.get('button').trigger('click')
    await settle()
    await wrapper
      .findAll('button')
      .find((button) => button.text().includes('开始下载'))
      ?.trigger('click')
    await settle()
    expect(getTask).toHaveBeenCalledTimes(1)
    expect(signals).toHaveLength(1)
    expect(signals[0].aborted).toBe(false)

    await wrapper.get('[data-mode="batch"]').trigger('click')
    expect(signals[0].aborted).toBe(true)

    pending.settle({
      ...runningTask(),
      state: 'success',
      title: 'stale single-task result',
      finished_at: '2026-08-16T12:01:00',
      progress: { current: 1, total: 1 },
    })
    await settle()
    const visibleCalls = getTask.mock.calls.length
    await vi.advanceTimersByTimeAsync(TASK_POLL_INTERVAL_MS * 5)

    expect(getTask).toHaveBeenCalledTimes(visibleCalls)

    await wrapper.get('[data-mode="single"]').trigger('click')
    await settle()
    expect(wrapper.text()).not.toContain('stale single-task result')
    expect(wrapper.text()).not.toContain('下载已完成')
  })
})
