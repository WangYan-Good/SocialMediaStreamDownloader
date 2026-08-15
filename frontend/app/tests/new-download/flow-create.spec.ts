import { describe, expect, it, vi } from 'vitest'

import { ApiError } from '../../src/api/client'
import { useNewDownloadFlow } from '../../src/composables/useNewDownloadFlow'
import type { CreatedTask, Task } from '../../src/types/task'
import { liveResolution, ownerResolution, postResolution } from './build-request.spec'

function deferred<T>() {
  let settle: (value: T) => void = () => {}
  const promise = new Promise<T>((resolve) => {
    settle = resolve
  })
  return { promise, settle }
}

function pendingTask(overrides: Partial<Task> = {}): Task {
  return {
    task_id: 'task-1',
    task_type: 'post_download',
    state: 'pending',
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

function buildFlow(overrides: Partial<Parameters<typeof useNewDownloadFlow>[0]> = {}) {
  const created: CreatedTask = {
    task_id: 'task-1',
    task_type: 'post_download',
    resolve_id: 'receipt-1',
  }
  const api = {
    resolveResource: vi.fn(async () => postResolution),
    createTask: vi.fn(async () => created),
    //
    // Left pending by default, so a create test observes the moment after
    // creation without a poll racing it to a terminal state.
    //
    getTask: vi.fn(async () => pendingTask()),
    ...overrides,
  }
  return { flow: useNewDownloadFlow(api), api }
}

async function resolvedFlow(overrides: Partial<Parameters<typeof useNewDownloadFlow>[0]> = {}) {
  const built = buildFlow(overrides)
  built.flow.input.value = 'https://v.douyin.com/abc/'
  await built.flow.resolve()
  return built
}

describe('creating a post download', () => {
  it('sends only the receipt and the task type', async () => {
    const { flow, api } = await resolvedFlow()

    await flow.create()

    expect(api.createTask).toHaveBeenCalledWith({
      resolve_id: 'receipt-1',
      task_type: 'post_download',
    })
  })

  it('never sends anything describing the resource', async () => {
    //
    // The browser holds the aweme id - it was on screen a moment ago - and must
    // still not be the one telling the server what to download.
    //
    const { flow, api } = await resolvedFlow()

    await flow.create()

    const sent = vi.mocked(api.createTask).mock.calls[0][0] as unknown as Record<string, unknown>
    for (const forbidden of [
      'aweme_id',
      'sec_user_id',
      'source_url',
      'resolved_url',
      'platform',
      'resource_type',
    ]) {
      expect(sent).not.toHaveProperty(forbidden)
    }
  })

  it('keeps the created task and starts tracking it', async () => {
    const { flow } = await resolvedFlow()

    await flow.create()

    expect(flow.createdTask.value).toEqual({
      task_id: 'task-1',
      task_type: 'post_download',
      resolve_id: 'receipt-1',
    })
    expect(flow.phase.value).toBe('tracking')
  })
})

describe('creating a recording', () => {
  it('sends the live task type with no options', async () => {
    const { flow, api } = await resolvedFlow({
      resolveResource: vi.fn(async () => liveResolution),
    })

    await flow.create()

    expect(api.createTask).toHaveBeenCalledWith({
      resolve_id: 'receipt-1',
      task_type: 'live_record',
    })
  })

  it('asks the platform nothing before creating', async () => {
    //
    // Whether the room is on air is the recording's own question. Probing here
    // would spend a request whose answer is stale by the time it is acted on.
    //
    const { flow, api } = await resolvedFlow({
      resolveResource: vi.fn(async () => liveResolution),
    })

    await flow.create()

    expect(api.resolveResource).toHaveBeenCalledTimes(1)
  })
})

describe('creating an owner batch', () => {
  it('will not create until the user has said so in words', async () => {
    //
    // An owner batch downloads an entire back catalogue. One misplaced click
    // should not start hours of work.
    //
    const { flow, api } = await resolvedFlow({
      resolveResource: vi.fn(async () => ownerResolution),
    })

    expect(flow.needsOwnerConfirmation.value).toBe(true)
    expect(flow.canCreate.value).toBe(false)

    await flow.create()
    expect(api.createTask).not.toHaveBeenCalled()
  })

  it('creates the whole-feed download once confirmed', async () => {
    const { flow, api } = await resolvedFlow({
      resolveResource: vi.fn(async () => ownerResolution),
    })

    flow.ownerConfirmed.value = true
    expect(flow.canCreate.value).toBe(true)
    await flow.create()

    expect(api.createTask).toHaveBeenCalledWith({
      resolve_id: 'receipt-1',
      task_type: 'owner_batch_download',
      options: { mode: 'all' },
    })
  })

  it('never offers the selected mode', async () => {
    const { flow, api } = await resolvedFlow({
      resolveResource: vi.fn(async () => ownerResolution),
    })
    flow.ownerConfirmed.value = true

    await flow.create()

    const sent = JSON.stringify(vi.mocked(api.createTask).mock.calls[0][0])
    expect(sent).not.toContain('selected')
    expect(sent).not.toContain('aweme_ids')
  })
})

describe('double submission', () => {
  it('creates one task however many times the button is pressed', async () => {
    const pending = deferred<CreatedTask>()
    const createTask = vi.fn(() => pending.promise)
    const { flow } = await resolvedFlow({ createTask })

    const first = flow.create()
    await flow.create()
    await flow.create()

    expect(createTask).toHaveBeenCalledTimes(1)
    expect(flow.canCreate.value).toBe(false)

    pending.settle({
      task_id: 'task-1',
      task_type: 'post_download',
      resolve_id: 'receipt-1',
    })
    await first
  })

  it('reports that it is creating while it does', async () => {
    const pending = deferred<CreatedTask>()
    const { flow } = await resolvedFlow({ createTask: vi.fn(() => pending.promise) })

    const running = flow.create()

    expect(flow.phase.value).toBe('creating')

    pending.settle({
      task_id: 'task-1',
      task_type: 'post_download',
      resolve_id: 'receipt-1',
    })
    await running
  })
})

describe('the receipt expired', () => {
  it('says so and offers to resolve again', async () => {
    const gone = new ApiError({
      kind: 'backend',
      status: 404,
      code: 404,
      message: '解析结果不存在或已过期，请重新解析',
    })
    const { flow } = await resolvedFlow({ createTask: vi.fn(async () => Promise.reject(gone)) })

    await flow.create()

    expect(flow.createError.value).toContain('重新解析')
    expect(flow.receiptExpired.value).toBe(true)
  })

  it('creates nothing and invents no identity of its own', async () => {
    const gone = new ApiError({
      kind: 'backend',
      status: 404,
      code: 404,
      message: '解析结果不存在或已过期，请重新解析',
    })
    const createTask = vi.fn(async () => Promise.reject(gone))
    const { flow, api } = await resolvedFlow({ createTask })

    await flow.create()

    expect(flow.createdTask.value).toBeNull()
    expect(flow.currentTask.value).toBeNull()
    expect(api.getTask).not.toHaveBeenCalled()
    expect(createTask).toHaveBeenCalledTimes(1)
  })

  it('leaves the user on the resolution so they can retry deliberately', async () => {
    const gone = new ApiError({ kind: 'backend', status: 404, code: 404, message: 'gone' })
    const { flow } = await resolvedFlow({ createTask: vi.fn(async () => Promise.reject(gone)) })

    await flow.create()

    expect(flow.phase.value).toBe('resolved')
    expect(flow.resolved.value).not.toBeNull()
  })
})

describe('other create failures', () => {
  it.each([
    [400, 'backend' as const],
    [503, 'backend' as const],
    [500, 'backend' as const],
  ])('stays on the resolution after a %i', async (status, kind) => {
    const error = new ApiError({ kind, status, code: status, message: `refused ${status}` })
    const { flow } = await resolvedFlow({ createTask: vi.fn(async () => Promise.reject(error)) })

    await flow.create()

    expect(flow.phase.value).toBe('resolved')
    expect(flow.createError.value).toBe(`refused ${status}`)
    expect(flow.receiptExpired.value).toBe(false)
  })

  it('does not pretend a task exists and failed', async () => {
    //
    // An http failure to create is not a failed task. There is no task at all,
    // and showing one would invent a record the server never made.
    //
    const error = new ApiError({ kind: 'network', status: null, code: null, message: 'offline' })
    const { flow } = await resolvedFlow({ createTask: vi.fn(async () => Promise.reject(error)) })

    await flow.create()

    expect(flow.createdTask.value).toBeNull()
    expect(flow.currentTask.value).toBeNull()
    expect(flow.phase.value).not.toBe('terminal')
  })

  it('allows a deliberate retry that really does call again', async () => {
    const error = new ApiError({ kind: 'network', status: null, code: null, message: 'offline' })
    const createTask = vi
      .fn<() => Promise<CreatedTask>>()
      .mockRejectedValueOnce(error)
      .mockResolvedValueOnce({
        task_id: 'task-1',
        task_type: 'post_download',
        resolve_id: 'receipt-1',
      })
    const { flow } = await resolvedFlow({ createTask })

    await flow.create()
    expect(flow.createError.value).toBe('offline')

    await flow.create()

    expect(createTask).toHaveBeenCalledTimes(2)
    expect(flow.createError.value).toBeNull()
    expect(flow.createdTask.value).not.toBeNull()
  })
})

describe('the input is frozen once a task exists', () => {
  it('keeps the created task even if the text changes afterwards', async () => {
    //
    // The task belongs to the resolution it was created from. Whatever the box
    // says now cannot change what is already running.
    //
    const { flow } = await resolvedFlow()
    await flow.create()

    flow.input.value = 'https://v.douyin.com/completely-different/'

    expect(flow.createdTask.value).not.toBeNull()
    expect(flow.phase.value).toBe('tracking')
  })

  it('says the input is locked while tracking', async () => {
    const { flow } = await resolvedFlow()

    expect(flow.inputLocked.value).toBe(false)
    await flow.create()

    expect(flow.inputLocked.value).toBe(true)
  })
})
