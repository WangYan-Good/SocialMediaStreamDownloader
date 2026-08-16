import { describe, expect, it, vi } from 'vitest'
import { nextTick } from 'vue'

import { ApiError } from '../../src/api/client'
import { useBatchDownloadFlow } from '../../src/composables/useBatchDownloadFlow'
import type { BatchResolveResult, ResolvedResource } from '../../src/types/resolution'
import type { CreatedTask } from '../../src/types/task'


function resolution(
  index: number,
  resourceType: 'post' | 'live' | 'owner',
): ResolvedResource {
  const base = {
    resolve_id: `R-${index}`,
    platform: 'douyin',
    source_url: `https://www.douyin.com/${resourceType}/${index}`,
    resolved_url: `https://www.douyin.com/${resourceType}/${index}`,
    expires_in_seconds: 600,
  }
  if (resourceType === 'post') {
    return { ...base, resource_type: 'post', identity: { aweme_id: String(index) } }
  }
  if (resourceType === 'owner') {
    return { ...base, resource_type: 'owner', identity: { sec_user_id: String(index) } }
  }
  return { ...base, resource_type: 'live', identity: {} }
}

function batch(types: Array<'post' | 'live' | 'owner'>): BatchResolveResult {
  return {
    total: types.length,
    resolved_count: types.length,
    failed_count: 0,
    items: types.map((type, index) => ({
      index,
      status: 'resolved' as const,
      resolution: resolution(index, type),
    })),
  }
}

function deferred<T>() {
  let settle: (value: T) => void = () => {}
  let fail: (reason: unknown) => void = () => {}
  const promise = new Promise<T>((resolve, reject) => {
    settle = resolve
    fail = reject
  })
  return { promise, settle, fail }
}

async function drain() {
  for (let index = 0; index < 5; index += 1) await Promise.resolve()
}

function created(index: number): CreatedTask {
  return {
    task_id: `T-${index}`,
    task_type: 'post_download',
    resolve_id: `R-${index}`,
  }
}

describe('batch resolve state', () => {
  it('selects post/live by default and leaves each owner unselected', async () => {
    const flow = useBatchDownloadFlow({
      resolveResources: vi.fn(async () => batch(['post', 'live', 'owner'])),
    })
    flow.input.value = 'three links'

    await flow.resolve()

    expect(flow.items.value.map((item) => item.status === 'resolved' && item.selected)).toEqual([
      true,
      true,
      false,
    ])
  })

  it('invalidates review immediately when input changes', async () => {
    const flow = useBatchDownloadFlow({
      resolveResources: vi.fn(async () => batch(['post'])),
    })
    flow.input.value = 'A'
    await flow.resolve()

    flow.input.value = 'B'

    expect(flow.phase.value).toBe('editing')
    expect(flow.items.value).toEqual([])
  })

  it('ignores an older response after a new input resolves', async () => {
    const a = deferred<BatchResolveResult>()
    const resolveResources = vi
      .fn()
      .mockReturnValueOnce(a.promise)
      .mockResolvedValueOnce(batch(['live']))
    const flow = useBatchDownloadFlow({ resolveResources })
    flow.input.value = 'A'
    const first = flow.resolve()
    flow.input.value = 'B'
    await flow.resolve()

    a.settle(batch(['post']))
    await first

    expect(flow.items.value[0].status).toBe('resolved')
    if (flow.items.value[0].status === 'resolved') {
      expect(flow.items.value[0].resolution.resource_type).toBe('live')
    }
  })
})

describe('batch task creation', () => {
  it('requires confirmation for every selected owner', async () => {
    const flow = useBatchDownloadFlow({
      resolveResources: vi.fn(async () => batch(['owner'])),
    })
    flow.input.value = 'owner'
    await flow.resolve()

    flow.setSelected(0, true)
    expect(flow.canCreate.value).toBe(false)
    flow.setOwnerConfirmed(0, true)
    expect(flow.canCreate.value).toBe(true)
  })

  it('creates in input order and never starts the second before the first answers', async () => {
    const first = deferred<CreatedTask>()
    const createTask = vi
      .fn()
      .mockReturnValueOnce(first.promise)
      .mockResolvedValueOnce(created(1))
    const flow = useBatchDownloadFlow({
      resolveResources: vi.fn(async () => batch(['post', 'live'])),
      createTask,
    })
    flow.input.value = 'two'
    await flow.resolve()

    const creating = flow.createSelected()
    await drain()
    expect(createTask).toHaveBeenCalledTimes(1)
    first.settle(created(0))
    await creating

    expect(createTask.mock.calls.map((call) => call[0].resolve_id)).toEqual(['R-0', 'R-1'])
  })

  it('guards double create and preserves successes across later failures', async () => {
    const first = deferred<CreatedTask>()
    const createTask = vi
      .fn()
      .mockReturnValueOnce(first.promise)
      .mockRejectedValueOnce(
        new ApiError({ kind: 'backend', status: 404, code: 404, message: 'missing' }),
      )
    const flow = useBatchDownloadFlow({
      resolveResources: vi.fn(async () => batch(['post', 'post'])),
      createTask,
    })
    flow.input.value = 'two'
    await flow.resolve()

    const one = flow.createSelected()
    const duplicate = flow.createSelected()
    first.settle(created(0))
    await Promise.all([one, duplicate])

    expect(createTask).toHaveBeenCalledTimes(2)
    const resolved = flow.items.value.filter((item) => item.status === 'resolved')
    expect(resolved[0].taskId).toBe('T-0')
    expect(resolved[0].createState).toBe('created')
    expect(resolved[1].createState).toBe('failed')
    expect(resolved[1].createError).toContain('已过期')
    expect(flow.createdCount.value).toBe(1)
  })

  it('stopping navigation prevents every not-yet-requested creation', async () => {
    const first = deferred<CreatedTask>()
    const createTask = vi.fn().mockReturnValue(first.promise)
    const flow = useBatchDownloadFlow({
      resolveResources: vi.fn(async () => batch(['post', 'post'])),
      createTask,
    })
    flow.input.value = 'two'
    await flow.resolve()

    const creating = flow.createSelected()
    await drain()
    flow.stop()
    first.settle(created(0))
    await creating
    await nextTick()

    expect(createTask).toHaveBeenCalledTimes(1)
    expect(flow.createdCount.value).toBe(1)
  })

  it('does not poll tasks after creating them', async () => {
    const fetch = vi.fn(() => Promise.reject(new Error('batch must not poll')))
    vi.stubGlobal('fetch', fetch)
    const flow = useBatchDownloadFlow({
      resolveResources: vi.fn(async () => batch(['post'])),
      createTask: vi.fn(async () => created(0)),
    })
    flow.input.value = 'one'
    await flow.resolve()

    await flow.createSelected()
    await drain()

    expect(fetch).not.toHaveBeenCalled()
  })
})
