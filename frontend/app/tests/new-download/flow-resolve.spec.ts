import { beforeEach, describe, expect, it, vi } from 'vitest'

import { ApiError } from '../../src/api/client'
import { useNewDownloadFlow } from '../../src/composables/useNewDownloadFlow'
import { ownerResolution, postResolution } from './build-request.spec'

//
// Every test drives injected api functions. The composable never touches
// `fetch` itself, so a flow test says what the flow does and nothing about how
// a Response is parsed - that is the client's own suite.
//

function deferred<T>() {
  let settle: (value: T) => void = () => {}
  let fail: (reason: unknown) => void = () => {}
  const promise = new Promise<T>((resolve, reject) => {
    settle = resolve
    fail = reject
  })
  return { promise, settle, fail }
}

function buildFlow(overrides: Partial<Parameters<typeof useNewDownloadFlow>[0]> = {}) {
  const api = {
    resolveResource: vi.fn(async () => postResolution),
    createTask: vi.fn(async () => ({
      task_id: 'task-1',
      task_type: 'post_download' as const,
      resolve_id: 'receipt-1',
    })),
    getTask: vi.fn(async () => ({
      task_id: 'task-1',
      task_type: 'post_download' as const,
      state: 'success' as const,
      title: null,
      message: null,
      created_at: '2026-08-15T09:30:15.250',
      started_at: null,
      finished_at: null,
      progress: { current: 1, total: 1 },
      metadata: {},
      items: [],
    })),
    ...overrides,
  }
  return { flow: useNewDownloadFlow(api), api }
}

beforeEach(() => {
  vi.useRealTimers()
})

describe('initial state', () => {
  it('starts editing with nothing resolved and nothing running', () => {
    const { flow, api } = buildFlow()

    expect(flow.phase.value).toBe('editing')
    expect(flow.resolved.value).toBeNull()
    expect(flow.createdTask.value).toBeNull()
    expect(flow.currentTask.value).toBeNull()
    expect(flow.resolveError.value).toBeNull()
    expect(api.resolveResource).not.toHaveBeenCalled()
    expect(api.createTask).not.toHaveBeenCalled()
    expect(api.getTask).not.toHaveBeenCalled()
  })

  it('refuses to resolve nothing', () => {
    const { flow } = buildFlow()

    expect(flow.canResolve.value).toBe(false)
    flow.input.value = '   \n  '
    expect(flow.canResolve.value).toBe(false)
  })

  it('allows resolving once there is something to send', () => {
    const { flow } = buildFlow()

    flow.input.value = 'https://v.douyin.com/abc/'

    expect(flow.canResolve.value).toBe(true)
  })
})

describe('resolving', () => {
  it('sends whatever the user pasted, untouched', async () => {
    //
    // Extracting the link out of a share sentence is the server's job, and it
    // has tests for the punctuation cases. A regex copied into the browser
    // would be a second opinion that eventually disagrees.
    //
    const { flow, api } = buildFlow()
    const pasted = '4.33 复制打开抖音，看看【xxx的作品】 https://v.douyin.com/abc/ :0pm'
    flow.input.value = pasted

    await flow.resolve()

    expect(api.resolveResource).toHaveBeenCalledWith(pasted)
  })

  it('moves through resolving and lands on resolved', async () => {
    const pending = deferred<typeof postResolution>()
    const { flow } = buildFlow({ resolveResource: vi.fn(() => pending.promise) })
    flow.input.value = 'https://v.douyin.com/abc/'

    const running = flow.resolve()
    expect(flow.phase.value).toBe('resolving')

    pending.settle(postResolution)
    await running

    expect(flow.phase.value).toBe('resolved')
    expect(flow.resolved.value).toEqual(postResolution)
  })

  it('never reports resolved without a resolution', async () => {
    //
    // The illegal combination this phase model exists to prevent.
    //
    const { flow } = buildFlow()
    flow.input.value = 'https://v.douyin.com/abc/'

    await flow.resolve()

    expect(flow.phase.value).toBe('resolved')
    expect(flow.resolved.value).not.toBeNull()
  })

  it('will not resolve twice at once', async () => {
    const pending = deferred<typeof postResolution>()
    const resolveResource = vi.fn(() => pending.promise)
    const { flow } = buildFlow({ resolveResource })
    flow.input.value = 'https://v.douyin.com/abc/'

    const first = flow.resolve()
    await flow.resolve()
    await flow.resolve()

    expect(resolveResource).toHaveBeenCalledTimes(1)
    expect(flow.canResolve.value).toBe(false)

    pending.settle(postResolution)
    await first
  })
})

describe('resolve failure', () => {
  it('keeps what the user typed and shows why', async () => {
    const error = new ApiError({
      kind: 'backend',
      status: 400,
      code: 400,
      message: '一次只能解析一个链接',
    })
    const { flow } = buildFlow({ resolveResource: vi.fn(async () => Promise.reject(error)) })
    flow.input.value = 'a b'

    await flow.resolve()

    expect(flow.phase.value).toBe('editing')
    expect(flow.input.value).toBe('a b')
    expect(flow.resolveError.value).toBe('一次只能解析一个链接')
    expect(flow.resolved.value).toBeNull()
  })

  it.each([
    [400, '请求有误'],
    [502, '上游失败'],
    [500, '服务器错误'],
  ])('surfaces a backend %i', async (status, message) => {
    const error = new ApiError({ kind: 'backend', status, code: status, message })
    const { flow } = buildFlow({ resolveResource: vi.fn(async () => Promise.reject(error)) })
    flow.input.value = 'x'

    await flow.resolve()

    expect(flow.resolveError.value).toBe(message)
  })

  it('surfaces a transport failure in words', async () => {
    const error = new ApiError({
      kind: 'network',
      status: null,
      code: null,
      message: 'Failed to fetch',
    })
    const { flow } = buildFlow({ resolveResource: vi.fn(async () => Promise.reject(error)) })
    flow.input.value = 'x'

    await flow.resolve()

    expect(flow.resolveError.value).toBeTruthy()
    expect(flow.phase.value).toBe('editing')
  })

  it('does not leak anything but the message', async () => {
    const error = new ApiError({
      kind: 'malformed',
      status: 502,
      code: null,
      message: '服务器返回了无法解析的响应（HTTP 502）',
    })
    const { flow } = buildFlow({ resolveResource: vi.fn(async () => Promise.reject(error)) })
    flow.input.value = 'x'

    await flow.resolve()

    expect(typeof flow.resolveError.value).toBe('string')
    expect(flow.resolveError.value).not.toContain('Response')
    expect(flow.resolveError.value).not.toContain('at ')
  })

  it('clears the previous failure on the next attempt', async () => {
    const failing = new ApiError({ kind: 'backend', status: 400, code: 400, message: 'bad' })
    const resolveResource = vi
      .fn<(input: string) => Promise<typeof postResolution>>()
      .mockRejectedValueOnce(failing)
      .mockResolvedValueOnce(postResolution)
    const { flow } = buildFlow({ resolveResource })
    flow.input.value = 'x'

    await flow.resolve()
    expect(flow.resolveError.value).toBe('bad')

    await flow.resolve()
    expect(flow.resolveError.value).toBeNull()
    expect(flow.phase.value).toBe('resolved')
  })
})

describe('editing the input invalidates the receipt', () => {
  //
  // The invariant this whole flow is built around.
  //
  // Without it: paste A, resolve A, edit the box to B, press download - and a
  // task is created for A while the screen shows B. The user would have no way
  // to tell, and the server would be entirely within its rights, because the
  // receipt it was handed really was A's.
  //
  async function resolvedFlow() {
    const { flow, api } = buildFlow()
    flow.input.value = 'https://v.douyin.com/A/'
    await flow.resolve()
    return { flow, api }
  }

  it('drops the resolution the moment the text changes', async () => {
    const { flow } = await resolvedFlow()
    expect(flow.resolved.value).not.toBeNull()

    flow.input.value = 'https://v.douyin.com/B/'

    expect(flow.resolved.value).toBeNull()
    expect(flow.phase.value).toBe('editing')
  })

  it('withdraws the ability to create', async () => {
    const { flow } = await resolvedFlow()
    expect(flow.canCreate.value).toBe(true)

    flow.input.value = 'https://v.douyin.com/B/'

    expect(flow.canCreate.value).toBe(false)
  })

  it('creates nothing even if create is called anyway', async () => {
    const { flow, api } = await resolvedFlow()

    flow.input.value = 'https://v.douyin.com/B/'
    await flow.create()

    expect(api.createTask).not.toHaveBeenCalled()
    expect(flow.createdTask.value).toBeNull()
  })

  it('forgets the owner confirmation too', async () => {
    const { flow } = buildFlow({ resolveResource: vi.fn(async () => ownerResolution) })
    flow.input.value = 'https://v.douyin.com/A/'
    await flow.resolve()
    flow.ownerConfirmed.value = true

    flow.input.value = 'https://v.douyin.com/B/'

    expect(flow.ownerConfirmed.value).toBe(false)
  })

  it('clears a create failure as well', async () => {
    const error = new ApiError({ kind: 'backend', status: 404, code: 404, message: 'gone' })
    const { flow } = buildFlow({ createTask: vi.fn(async () => Promise.reject(error)) })
    flow.input.value = 'https://v.douyin.com/A/'
    await flow.resolve()
    await flow.create()
    expect(flow.createError.value).toBeTruthy()

    flow.input.value = 'https://v.douyin.com/B/'

    expect(flow.createError.value).toBeNull()
  })

  it('ignores a change that is only whitespace either side', async () => {
    //
    // Trimmed comparison, so a stray newline from a paste does not silently
    // throw away a resolution the user is still looking at.
    //
    const { flow } = await resolvedFlow()

    flow.input.value = '  https://v.douyin.com/A/  '

    expect(flow.resolved.value).not.toBeNull()
    expect(flow.phase.value).toBe('resolved')
  })
})
