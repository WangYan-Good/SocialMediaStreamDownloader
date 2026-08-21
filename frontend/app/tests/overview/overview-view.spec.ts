import { mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { nextTick } from 'vue'
import { createMemoryHistory, createRouter } from 'vue-router'

import { ApiError } from '../../src/api/client'
import { listHistoryOwners } from '../../src/api/history'
import { listLibraryLives, listLibraryPosts } from '../../src/api/library'
import { getSystemStatus } from '../../src/api/system'
import { listTasks } from '../../src/api/tasks'
import { routes } from '../../src/router'
import { useOverviewStore } from '../../src/stores/overview'
import OverviewView from '../../src/views/OverviewView.vue'
import { historyOwner, libraryLive, libraryPost, systemStatus, task } from './fixtures'

vi.mock('../../src/api/system', () => ({ getSystemStatus: vi.fn() }))
vi.mock('../../src/api/tasks', () => ({ listTasks: vi.fn(), getTask: vi.fn(), createTask: vi.fn() }))
vi.mock('../../src/api/history', () => ({
  listHistoryOwners: vi.fn(),
  listOwnerSessions: vi.fn(),
  submitLiveProbe: vi.fn(),
  getLiveProbe: vi.fn(),
}))
vi.mock('../../src/api/library', () => ({
  listLibraryPosts: vi.fn(),
  listLibraryLives: vi.fn(),
}))
vi.mock('../../src/api/resolve', () => ({ resolveResource: vi.fn() }))
vi.mock('../../src/api/owners', () => ({
  readOwner: vi.fn(),
  readOwnerPosts: vi.fn(),
  startOwnerSelectedDownload: vi.fn(),
  startOwnerAllDownload: vi.fn(),
}))
vi.mock('../../src/api/people', () => ({
  listPeople: vi.fn(),
  getPersonWorks: vi.fn(),
  getPersonDetail: vi.fn(),
  createPerson: vi.fn(),
  updatePerson: vi.fn(),
  deletePerson: vi.fn(),
  searchAccounts: vi.fn(),
  attachAccount: vi.fn(),
  attachAccountByLink: vi.fn(),
  assignPersonAccount: vi.fn(),
  detachAccount: vi.fn(),
  addCollaboration: vi.fn(),
  removeCollaboration: vi.fn(),
}))

const mockedSystem = vi.mocked(getSystemStatus)
const mockedTasks = vi.mocked(listTasks)
const mockedOwners = vi.mocked(listHistoryOwners)
const mockedPosts = vi.mocked(listLibraryPosts)
const mockedLives = vi.mocked(listLibraryLives)

async function settle() {
  for (let index = 0; index < 8; index += 1) {
    await Promise.resolve()
  }
  await nextTick()
}

async function openOverview() {
  const router = createRouter({ history: createMemoryHistory(), routes })
  await router.push('/overview')
  await router.isReady()
  const wrapper = mount(OverviewView, { global: { plugins: [router] } })
  await settle()
  return wrapper
}

function buttonSaying(wrapper: Awaited<ReturnType<typeof openOverview>>, text: string) {
  return wrapper.findAll('button').find((one) => one.text().includes(text))
}

const unavailable = new ApiError({
  kind: 'backend',
  status: 503,
  code: 503,
  message: '媒体库需要启用数据库',
})

beforeEach(() => {
  setActivePinia(createPinia())
  vi.clearAllMocks()
  mockedSystem.mockResolvedValue(systemStatus())
  mockedTasks.mockResolvedValue({ items: [task()], total: 37 })
  mockedOwners.mockResolvedValue({ total: 128, page: 1, page_size: 1, items: [historyOwner()] })
  mockedPosts.mockResolvedValue({ total: 4210, page: 1, page_size: 1, items: [libraryPost()] })
  mockedLives.mockResolvedValue({ total: 96, page: 1, page_size: 1, items: [libraryLive()] })
})

afterEach(() => {
  vi.useRealTimers()
})

describe('what arriving at the overview costs', () => {
  it('reads the five existing read models and nothing else', async () => {
    const fetched = vi.fn()
    vi.stubGlobal('fetch', fetched)

    await openOverview()

    expect(mockedSystem).toHaveBeenCalledTimes(1)
    expect(mockedTasks).toHaveBeenCalledTimes(1)
    expect(mockedOwners).toHaveBeenCalledTimes(1)
    expect(mockedPosts).toHaveBeenCalledTimes(1)
    expect(mockedLives).toHaveBeenCalledTimes(1)
    //
    // Nothing reached the network directly either: every call went through an
    // adapter this test can see.
    //
    expect(fetched).not.toHaveBeenCalled()
    vi.unstubAllGlobals()
  })

  it('never writes, never resolves and never asks a platform anything', async () => {
    //
    // A landing page that could start work would be a landing page that can
    // fail in ways nobody is watching. Every action lives on the screen that
    // owns it.
    //
    const resolve = await import('../../src/api/resolve')
    const owners = await import('../../src/api/owners')
    const people = await import('../../src/api/people')
    const tasks = await import('../../src/api/tasks')
    const history = await import('../../src/api/history')

    await openOverview()

    expect(vi.mocked(resolve.resolveResource)).not.toHaveBeenCalled()
    expect(vi.mocked(tasks.createTask)).not.toHaveBeenCalled()
    expect(vi.mocked(tasks.getTask)).not.toHaveBeenCalled()
    expect(vi.mocked(history.submitLiveProbe)).not.toHaveBeenCalled()
    expect(vi.mocked(history.getLiveProbe)).not.toHaveBeenCalled()
    expect(vi.mocked(owners.readOwner)).not.toHaveBeenCalled()
    expect(vi.mocked(owners.readOwnerPosts)).not.toHaveBeenCalled()
    expect(vi.mocked(owners.startOwnerAllDownload)).not.toHaveBeenCalled()
    expect(vi.mocked(people.listPeople)).not.toHaveBeenCalled()
    expect(vi.mocked(people.getPersonWorks)).not.toHaveBeenCalled()
  })
})

describe('the statistics', () => {
  it('shows the totals the server counted', async () => {
    const wrapper = await openOverview()
    const text = wrapper.text()

    expect(text).toContain('128')
    expect(text).toContain('4210')
    expect(text).toContain('96')
    expect(text).toContain('37')
  })

  it('counts tasks by the api total rather than the rows it displayed', async () => {
    //
    // Five rows out of thirty-seven. Using the page length would say five, and
    // the page would understate the process's own record by a factor of seven.
    //
    mockedTasks.mockResolvedValue({
      items: [task({ task_id: '1' }), task({ task_id: '2' })],
      total: 37,
    })

    const wrapper = await openOverview()

    expect(wrapper.text()).toContain('37')
    expect(wrapper.text()).toContain('当前进程共 37 条任务记录')
  })

  it('says a failed read is unavailable rather than zero', async () => {
    //
    // "Could not read" and "there are none" are different facts, and a zero
    // states the second while meaning the first.
    //
    mockedPosts.mockRejectedValue(unavailable)

    const wrapper = await openOverview()
    const text = wrapper.text()

    expect(text).toContain('暂不可用')
    expect(text).not.toContain('已下载作品0')
  })

  it('calls the account count a local database fact', async () => {
    const wrapper = await openOverview()

    expect(wrapper.text()).toContain('数据库已记录的账号数')
    expect(wrapper.text()).not.toContain('全平台')
  })

  it('calls the task count a per-process record', async () => {
    //
    // The task store lives in this process and is subject to retention, so it
    // is not a lifetime total and must not be labelled as one.
    //
    const wrapper = await openOverview()

    expect(wrapper.text()).toContain('当前进程的任务记录数')
    expect(wrapper.text()).not.toContain('累计任务')
    expect(wrapper.text()).not.toContain('历史任务总数')
  })
})

describe('when the database is down', () => {
  it('keeps the half of the page that still works', async () => {
    //
    // The realistic degraded case, and the one this page is most useful in:
    // everything that reads the database fails while the system status and the
    // in-process task record answer perfectly well.
    //
    mockedSystem.mockResolvedValue(
      systemStatus({
        database: {
          enabled: true,
          state: 'unavailable',
          write_ready: false,
          message: '数据库当前不可用',
        },
      }),
    )
    mockedOwners.mockRejectedValue(unavailable)
    mockedPosts.mockRejectedValue(unavailable)
    mockedLives.mockRejectedValue(unavailable)

    const wrapper = await openOverview()
    const text = wrapper.text()

    expect(text).toContain('当前不可用')
    expect(text).toContain('数据库当前不可用')
    //
    // The task card is untouched by its neighbours' failure.
    //
    expect(text).toContain('一条作品')
    expect(text).toContain('37')
    expect(text).toContain('暂时无法读取账号统计')
    expect(text).toContain('暂时无法读取作品统计')
  })

  it('does not turn one section failing into a failed page', async () => {
    mockedPosts.mockRejectedValue(unavailable)

    const wrapper = await openOverview()

    expect(wrapper.text()).toContain('128')
    expect(wrapper.text()).toContain('96')
    expect(wrapper.text()).toContain('服务正在响应')
  })
})

describe('the recent tasks card', () => {
  it('keeps the order the task api produced', async () => {
    mockedTasks.mockResolvedValue({
      items: [
        task({ task_id: '1', title: '第一' }),
        task({ task_id: '2', title: '第二' }),
        task({ task_id: '3', title: '第三' }),
      ],
      total: 3,
    })

    const wrapper = await openOverview()
    const text = wrapper.text()

    expect(text.indexOf('第一')).toBeLessThan(text.indexOf('第二'))
    expect(text.indexOf('第二')).toBeLessThan(text.indexOf('第三'))
  })

  it('links to the task centre rather than watching tasks itself', async () => {
    const wrapper = await openOverview()

    const link = wrapper.findAll('a').find((one) => one.text().includes('前往任务中心'))
    expect(link?.attributes('href')).toBe('/tasks')
  })
})

describe('the recent content card', () => {
  it('never claims a recorded broadcast is live now', async () => {
    //
    // room_status 2 means the room was live when the row was written. Only a
    // probe can answer the present tense, and this page never runs one.
    //
    mockedLives.mockResolvedValue({
      total: 1,
      page: 1,
      page_size: 1,
      items: [libraryLive({ room_status: 2 })],
    })

    const wrapper = await openOverview()

    expect(wrapper.text()).toContain('记录时：直播中')
    expect(wrapper.text()).not.toContain('正在直播中')
  })

  it('describes a download as a record rather than as files', async () => {
    const wrapper = await openOverview()

    expect(wrapper.text()).toContain('记录完成 3 / 3')
    expect(wrapper.text()).not.toContain('文件')
  })

  it('shows no cover and asks no platform for one', async () => {
    const wrapper = await openOverview()

    expect(wrapper.find('img').exists()).toBe(false)
  })
})

describe('the quick actions', () => {
  it('links to every screen that owns an action', async () => {
    const wrapper = await openOverview()
    const hrefs = wrapper.findAll('a').map((one) => one.attributes('href'))

    for (const path of ['/new', '/creators', '/library', '/tasks', '/system']) {
      expect(hrefs).toContain(path)
    }
  })

  it('offers nothing that acts on its own', async () => {
    const wrapper = await openOverview()

    for (const label of ['开始下载', '检查直播', '新建人物', '删除']) {
      expect(buttonSaying(wrapper, label)).toBeUndefined()
    }
  })
})

describe('refreshing the overview', () => {
  it('reads all five again when asked', async () => {
    const wrapper = await openOverview()

    await buttonSaying(wrapper, '刷新总览')?.trigger('click')
    await settle()

    expect(mockedSystem).toHaveBeenCalledTimes(2)
    expect(mockedPosts).toHaveBeenCalledTimes(2)
  })

  it('keeps every section that had already succeeded', async () => {
    const wrapper = await openOverview()

    mockedPosts.mockRejectedValue(unavailable)
    await buttonSaying(wrapper, '刷新总览')?.trigger('click')
    await settle()

    expect(wrapper.text()).toContain('4210')
    expect(wrapper.text()).toContain('暂时无法读取作品统计')
  })
})

describe('the overview over time', () => {
  it('never polls', async () => {
    vi.useFakeTimers()
    await openOverview()

    await vi.advanceTimersByTimeAsync(10_000)
    await vi.advanceTimersByTimeAsync(60_000)
    await vi.advanceTimersByTimeAsync(600_000)

    expect(mockedSystem).toHaveBeenCalledTimes(1)
    expect(mockedTasks).toHaveBeenCalledTimes(1)
    expect(mockedPosts).toHaveBeenCalledTimes(1)
  })

  it('drops a batch that arrives after the page is gone', async () => {
    //
    // Asserted against the store: an unmounted wrapper keeps returning its last
    // render, so checking the markup would pass either way.
    //
    let settleTasks: (value: { items: []; total: number }) => void = () => {}
    mockedTasks.mockReturnValue(
      new Promise((resolve) => {
        settleTasks = resolve
      }),
    )
    const wrapper = await openOverview()
    const store = useOverviewStore()

    wrapper.unmount()
    settleTasks({ items: [], total: 999 })
    await settle()

    expect(store.taskTotal).toBeNull()
    expect(store.loading).toBe(false)
  })
})
