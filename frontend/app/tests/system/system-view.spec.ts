import { mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { nextTick } from 'vue'
import { createMemoryHistory, createRouter } from 'vue-router'

import { ApiError } from '../../src/api/client'
import { getSystemStatus } from '../../src/api/system'
import { routes } from '../../src/router'
import { useSystemStore } from '../../src/stores/system'
import SystemView from '../../src/views/SystemView.vue'
import type { SystemDatabaseState, SystemStatus } from '../../src/types/system'

vi.mock('../../src/api/system', () => ({ getSystemStatus: vi.fn() }))

const mockedStatus = vi.mocked(getSystemStatus)

function status(overrides: Partial<SystemStatus> = {}): SystemStatus {
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
    database: { enabled: state !== 'disabled', state, write_ready: state === 'ready', message },
  })
}

async function settle() {
  for (let index = 0; index < 6; index += 1) {
    await Promise.resolve()
  }
  await nextTick()
}

async function openSystem() {
  const router = createRouter({ history: createMemoryHistory(), routes })
  await router.push('/system')
  await router.isReady()
  const wrapper = mount(SystemView, { global: { plugins: [router] } })
  await settle()
  return wrapper
}

function buttonSaying(wrapper: Awaited<ReturnType<typeof openSystem>>, text: string) {
  return wrapper.findAll('button').find((one) => one.text().includes(text))
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

describe('arriving at the system page', () => {
  it('asks the system endpoint once and nothing else', async () => {
    //
    // The one request this screen makes. Reaching for tasks, the library or the
    // person api "for context" would make a status page depend on the very
    // subsystems it is meant to report on.
    //
    const fetched = vi.fn()
    vi.stubGlobal('fetch', fetched)

    await openSystem()

    expect(mockedStatus).toHaveBeenCalledTimes(1)
    expect(fetched).not.toHaveBeenCalled()
    vi.unstubAllGlobals()
  })

  it('says when the browser last heard back', async () => {
    const wrapper = await openSystem()

    expect(wrapper.text()).toContain('最近刷新')
  })
})

describe('the database card', () => {
  const cases: Array<[SystemDatabaseState, string]> = [
    ['ready', '已就绪'],
    ['unavailable', '当前不可用'],
    ['blocked', '架构状态阻止写入'],
    ['disabled', '数据库持久化已禁用'],
    ['unknown', '无法确认'],
  ]

  it.each(cases)('reads %s as words rather than only a colour', async (state, label) => {
    mockedStatus.mockResolvedValue(withDatabase(state, `服务端说明 ${state}`))

    const wrapper = await openSystem()

    expect(wrapper.text()).toContain(label)
    expect(wrapper.text()).toContain(`服务端说明 ${state}`)
  })

  it('warns which features depend on the database when it is not ready', async () => {
    mockedStatus.mockResolvedValue(withDatabase('unavailable', '数据库当前不可用'))

    const wrapper = await openSystem()

    expect(wrapper.text()).toContain('依赖数据库的功能可能受影响')
  })

  it('says nothing of the sort when the schema is ready', async () => {
    const wrapper = await openSystem()

    expect(wrapper.text()).not.toContain('依赖数据库的功能可能受影响')
  })

  it('never shows where the database lives', async () => {
    const wrapper = await openSystem()
    const text = wrapper.text()

    for (const forbidden of ['host', '3306', 'username', 'password']) {
      expect(text.toLowerCase()).not.toContain(forbidden)
    }
  })
})

describe('the warnings', () => {
  it('flags debug mode when it is on', async () => {
    mockedStatus.mockResolvedValue(
      status({
        settings: { ...status().settings, server: { debug_mode: true } },
      }),
    )

    const wrapper = await openSystem()

    expect(wrapper.text()).toContain('不建议用于正式对外环境')
  })

  it('says nothing about debug mode when it is off', async () => {
    const wrapper = await openSystem()

    expect(wrapper.text()).not.toContain('不建议用于正式对外环境')
  })

  it('flags test mode when it is on, without promising what it does', async () => {
    //
    // "行为可能不同" is as far as the page can honestly go. Claiming nothing
    // gets written would be a guarantee it cannot check.
    //
    const base = status()
    mockedStatus.mockResolvedValue(
      status({
        settings: {
          ...base.settings,
          download: { ...base.settings.download, test_mode: true },
        },
      }),
    )

    const wrapper = await openSystem()

    expect(wrapper.text()).toContain('下载行为可能与正常模式不同')
    expect(wrapper.text()).not.toContain('不会写任何文件')
  })

  it('says nothing about test mode when it is off', async () => {
    const wrapper = await openSystem()

    expect(wrapper.text()).not.toContain('下载行为可能与正常模式不同')
  })
})

describe('the logging card', () => {
  it('summarises the logger without pointing at a file', async () => {
    const wrapper = await openSystem()
    const text = wrapper.text()

    expect(text).toContain('INFO')
    expect(text).toContain('不读取或展示日志文件内容')
    expect(text).not.toContain('.log')
    expect(text).not.toContain('log_file_path')
  })
})

describe('the page as a whole', () => {
  it('offers nothing that changes anything', async () => {
    //
    // Configuration is loaded once per process. A control that appeared to save
    // would report success while every worker kept the old values.
    //
    const wrapper = await openSystem()

    for (const label of ['保存', '应用', '重载', '重启']) {
      expect(buttonSaying(wrapper, label)).toBeUndefined()
    }
  })

  it('says the configuration cannot be edited here', async () => {
    const wrapper = await openSystem()

    expect(wrapper.text()).toContain('需在服务器侧完成')
  })

  it('never dumps the response as json', async () => {
    //
    // Every field is rendered by a named component. A dump would publish
    // whatever the backend adds next, with nobody deciding it belongs here.
    //
    const wrapper = await openSystem()
    const html = wrapper.html()

    expect(wrapper.find('pre').exists()).toBe(false)
    expect(html).not.toContain('write_ready')
    expect(html).not.toContain('page_size_limit')
  })

  it('shows no field the contract does not name, even if one arrives', async () => {
    //
    // Defence in depth: a backend that started sending a secret would still not
    // reach the dom, because no component reads anything it was not written to.
    //
    const smuggled = {
      ...status(),
      settings: {
        ...status().settings,
        server: {
          debug_mode: false,
          password: 'SECRET_PASSWORD',
          save_path: 'SECRET_SAVE_PATH',
          log_file_path: 'SECRET_LOG_PATH',
          cookie: 'SECRET_COOKIE',
        },
      },
    } as unknown as SystemStatus
    mockedStatus.mockResolvedValue(smuggled)

    const wrapper = await openSystem()

    expect(wrapper.html()).not.toContain('SECRET')
  })
})

describe('refreshing', () => {
  it('reads again when asked', async () => {
    const wrapper = await openSystem()

    await buttonSaying(wrapper, '刷新状态')?.trigger('click')
    await settle()

    expect(mockedStatus).toHaveBeenCalledTimes(2)
  })

  it('keeps the last good snapshot when a refresh fails', async () => {
    const wrapper = await openSystem()

    mockedStatus.mockRejectedValue(offline)
    await buttonSaying(wrapper, '刷新状态')?.trigger('click')
    await settle()

    expect(wrapper.text()).toContain('暂时无法刷新系统状态')
    expect(wrapper.text()).toContain('已就绪')
  })

  it('claims nothing is healthy when the first read failed', async () => {
    mockedStatus.mockRejectedValue(offline)

    const wrapper = await openSystem()
    const text = wrapper.text()

    expect(text).toContain('暂时无法刷新系统状态')
    expect(text).not.toContain('已就绪')
    expect(text).not.toContain('数据库架构已就绪')
  })
})

describe('the system page over time', () => {
  it('never polls', async () => {
    vi.useFakeTimers()
    await openSystem()

    await vi.advanceTimersByTimeAsync(10_000)
    await vi.advanceTimersByTimeAsync(60_000)
    await vi.advanceTimersByTimeAsync(600_000)

    expect(mockedStatus).toHaveBeenCalledTimes(1)
  })

  it('drops an answer that arrives after the page is gone', async () => {
    //
    // Asserted against the store rather than the markup: an unmounted wrapper
    // keeps returning its last render, so checking the html would pass whether
    // or not the late answer was written.
    //
    let settleRead: (value: SystemStatus) => void = () => {}
    mockedStatus.mockReturnValue(
      new Promise<SystemStatus>((resolve) => {
        settleRead = resolve
      }),
    )
    const wrapper = await openSystem()
    const store = useSystemStore()
    expect(store.status).toBeNull()

    wrapper.unmount()
    settleRead(status())
    await settle()

    expect(store.status).toBeNull()
    expect(store.loading).toBe(false)
  })
})
