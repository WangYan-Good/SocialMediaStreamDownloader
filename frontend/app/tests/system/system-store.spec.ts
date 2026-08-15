import { createPinia, setActivePinia } from 'pinia'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import { ApiError } from '../../src/api/client'
import { getSystemStatus } from '../../src/api/system'
import { useSystemStore } from '../../src/stores/system'
import type { SystemDatabaseState, SystemStatus } from '../../src/types/system'

vi.mock('../../src/api/system', () => ({ getSystemStatus: vi.fn() }))

const mockedStatus = vi.mocked(getSystemStatus)

export function status(overrides: Partial<SystemStatus> = {}): SystemStatus {
  return {
    database: {
      enabled: true,
      state: 'ready',
      write_ready: true,
      message: '数据库架构已就绪',
    },
    settings: {
      server: { debug_mode: false },
      logging: { enabled: true, level: 'INFO', save_enabled: true },
      download: {
        test_mode: false,
        folderize: true,
        listening: false,
        user_login: false,
      },
      history: { page_size_limit: 10 },
      douyin: {
        aweme: {
          concurrency: 3,
          html_fallback: true,
          skip_downloaded: true,
          video_quality: 'highest',
          media: { video: true, images: true, music: true, cover: true },
        },
        owner: { page_size: 18, download_concurrency: 3 },
        live_probe: { max_batch_size: 10, concurrency: 3, cache_ttl_seconds: 60 },
      },
    },
    ...overrides,
  }
}

function withDatabase(state: SystemDatabaseState, message: string): SystemStatus {
  return status({
    database: {
      enabled: true,
      state,
      write_ready: state === 'ready',
      message,
    },
  })
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
  for (let index = 0; index < 6; index += 1) {
    await Promise.resolve()
  }
}

const offline = new ApiError({
  kind: 'network',
  status: null,
  code: null,
  message: 'offline',
})

beforeEach(() => {
  setActivePinia(createPinia())
  vi.clearAllMocks()
  mockedStatus.mockResolvedValue(status())
})

afterEach(() => {
  vi.useRealTimers()
})

describe('reading the system status', () => {
  it('asks for nothing until it is told to', () => {
    useSystemStore()

    expect(mockedStatus).not.toHaveBeenCalled()
  })

  it('keeps what the server answered', async () => {
    const store = useSystemStore()

    await store.load()

    expect(store.status?.database.state).toBe('ready')
    expect(store.status?.settings.logging.level).toBe('INFO')
    expect(store.hasLoaded).toBe(true)
    expect(store.error).toBeNull()
  })

  it('records when the browser received it', async () => {
    //
    // A local time, because the server's own check time is a monotonic reading
    // that means nothing here. "When this page last heard back" is the honest
    // claim, and the only one this side can make.
    //
    const store = useSystemStore()

    await store.load()

    expect(store.lastUpdatedAt).toBeInstanceOf(Date)
  })

  it('carries every degraded database state through unchanged', async () => {
    for (const state of ['unavailable', 'blocked', 'disabled', 'unknown'] as const) {
      mockedStatus.mockResolvedValue(withDatabase(state, `状态 ${state}`))
      setActivePinia(createPinia())
      const store = useSystemStore()

      await store.load()

      expect(store.status?.database.state).toBe(state)
      expect(store.error).toBeNull()
    }
  })
})

describe('a first read that failed', () => {
  it('reports the failure rather than an all-clear', async () => {
    //
    // Nothing is known, so nothing is claimed. Green badges built on no
    // evidence are worse than an error.
    //
    mockedStatus.mockRejectedValue(offline)
    const store = useSystemStore()

    await store.load()

    expect(store.status).toBeNull()
    expect(store.hasLoaded).toBe(false)
    expect(store.error).not.toBeNull()
  })
})

describe('a refresh that failed', () => {
  it('keeps the snapshot it already had', async () => {
    //
    // A failed refresh says the server could not be reached now. It says
    // nothing about whether what was read before was true.
    //
    const store = useSystemStore()
    await store.load()

    mockedStatus.mockRejectedValue(offline)
    await store.load()

    expect(store.status?.database.state).toBe('ready')
    expect(store.error).not.toBeNull()
    expect(store.hasLoaded).toBe(true)
  })

  it('leaves the previous update time alone', async () => {
    const store = useSystemStore()
    await store.load()
    const first = store.lastUpdatedAt

    mockedStatus.mockRejectedValue(offline)
    await store.load()

    expect(store.lastUpdatedAt).toBe(first)
  })
})

describe('repeated refreshes', () => {
  it('never has two reads in flight at once', async () => {
    //
    // Each read makes the server refresh its schema guard. Three impatient
    // clicks must not become three database probes.
    //
    const pending = deferred<SystemStatus>()
    mockedStatus.mockReturnValue(pending.promise)
    const store = useSystemStore()

    void store.load()
    void store.load()
    void store.load()
    await drain()

    expect(mockedStatus).toHaveBeenCalledTimes(1)

    pending.settle(status())
    await drain()
  })

  it('can be read again once the first one finished', async () => {
    const store = useSystemStore()
    await store.load()

    await store.load()

    expect(mockedStatus).toHaveBeenCalledTimes(2)
  })
})

describe('leaving the page', () => {
  it('abandons a read that is still in flight', async () => {
    const pending = deferred<SystemStatus>()
    mockedStatus.mockReturnValue(pending.promise)
    const store = useSystemStore()
    void store.load()
    await drain()

    store.abandon()
    pending.settle(status({ database: { enabled: true, state: 'blocked', write_ready: false, message: '晚到' } }))
    await drain()

    expect(store.status).toBeNull()
    expect(store.loading).toBe(false)
  })

  it('does not record a failure from a read nobody is waiting for', async () => {
    const pending = deferred<SystemStatus>()
    mockedStatus.mockReturnValue(pending.promise)
    const store = useSystemStore()
    void store.load()
    await drain()

    store.abandon()
    pending.fail(offline)
    await drain()

    expect(store.error).toBeNull()
  })
})

describe('the system store on its own', () => {
  it('never starts a timer', async () => {
    //
    // System state changes when somebody changes the server, and the schema
    // guard already caches its own checks. A poller here would be a database
    // probe every few seconds for an answer that almost never moves.
    //
    vi.useFakeTimers()
    const store = useSystemStore()
    await store.load()

    await vi.advanceTimersByTimeAsync(10_000)
    await vi.advanceTimersByTimeAsync(60_000)
    await vi.advanceTimersByTimeAsync(600_000)

    expect(mockedStatus).toHaveBeenCalledTimes(1)
  })
})
