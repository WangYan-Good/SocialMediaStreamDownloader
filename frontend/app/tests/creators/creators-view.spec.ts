import { mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { nextTick } from 'vue'
import { createMemoryHistory, createRouter } from 'vue-router'

import { listHistoryOwners, submitLiveProbe } from '../../src/api/history'
import { readOwner } from '../../src/api/owners'
import { resolveResource } from '../../src/api/resolve'
import { createTask } from '../../src/api/tasks'
import { routes } from '../../src/router'
import CreatorsView from '../../src/views/CreatorsView.vue'
import type { HistoryOwner } from '../../src/types/history'

vi.mock('../../src/api/history', () => ({
  listHistoryOwners: vi.fn(),
  listOwnerSessions: vi.fn(async () => ({ items: [] })),
  submitLiveProbe: vi.fn(),
  getLiveProbe: vi.fn(),
}))
vi.mock('../../src/api/owners', () => ({
  readOwner: vi.fn(),
  readOwnerPosts: vi.fn(async () => ({ posts: [], next_cursor: 0, has_more: false })),
  startOwnerSelectedDownload: vi.fn(),
  startOwnerAllDownload: vi.fn(),
}))
vi.mock('../../src/api/resolve', () => ({ resolveResource: vi.fn() }))
vi.mock('../../src/api/people', () => ({
  listPeople: vi.fn(async () => []),
  createPerson: vi.fn(),
  updatePerson: vi.fn(),
  deletePerson: vi.fn(),
  getPersonDetail: vi.fn(),
  searchAccounts: vi.fn(),
  attachAccount: vi.fn(),
  attachAccountByLink: vi.fn(),
  assignPersonAccount: vi.fn(),
  //
  // Resolving now inspects too, so the assignment card reaches for this while
  // it sets up. Left out, the whole tab fails to mount.
  //
  inspectPersonAssignment: vi.fn(),
  detachAccount: vi.fn(),
  addCollaboration: vi.fn(),
  removeCollaboration: vi.fn(),
}))
vi.mock('../../src/api/tasks', () => ({
  createTask: vi.fn(),
  listTasks: vi.fn(),
  getTask: vi.fn(),
}))

const mockedList = vi.mocked(listHistoryOwners)
const mockedProbe = vi.mocked(submitLiveProbe)
const mockedResolve = vi.mocked(resolveResource)
const mockedCreateTask = vi.mocked(createTask)
const mockedReadOwner = vi.mocked(readOwner)

const SEC_UID = 'MS4wLjABAAAAGZkW5n1EHZD_TFyQ-QiaISBPemtKFxVVdhLSeoXhh-U'
const SHORT_LINK = 'https://v.douyin.com/abc/'

function owner(overrides: Partial<HistoryOwner> = {}): HistoryOwner {
  return {
    owner_user_id: '58859666123',
    sec_user_id: SEC_UID,
    nickname: '主播',
    live_share_url: SHORT_LINK,
    directory_name: '主播',
    user_status: '正常',
    actived_count: 12,
    score: 80,
    favorite: true,
    last_live_status: 2,
    last_checked_at: '2026-08-15T09:30:15.250',
    last_room_id: '7123',
    ...overrides,
  }
}

function page(items: HistoryOwner[], total = items.length) {
  return { total, page: 1, page_size: 20, items }
}

async function settle() {
  for (let index = 0; index < 5; index += 1) {
    await Promise.resolve()
  }
  await nextTick()
}

async function mountCreators() {
  const router = createRouter({ history: createMemoryHistory(), routes })
  await router.push('/creators')
  await router.isReady()
  const wrapper = mount(CreatorsView, { global: { plugins: [router] } })
  await settle()
  return wrapper
}

function buttonSaying(wrapper: Awaited<ReturnType<typeof mountCreators>>, text: string) {
  return wrapper.findAll('button').find((one) => one.text().includes(text))
}

beforeEach(() => {
  setActivePinia(createPinia())
  vi.clearAllMocks()
  mockedList.mockResolvedValue(page([]))
  vi.useFakeTimers()
})

afterEach(() => {
  vi.useRealTimers()
})

describe('arriving at the workspace', () => {
  it('reads the account directory and nothing else', async () => {
    //
    // Sessions, posts and probes are all per-account and are read when the user
    // opens them. Reading them up front would be sixty requests for a page of
    // twenty accounts nobody has looked at yet.
    //
    await mountCreators()

    expect(mockedList).toHaveBeenCalledTimes(1)
    expect(mockedProbe).not.toHaveBeenCalled()
    expect(mockedResolve).not.toHaveBeenCalled()
    expect(mockedReadOwner).not.toHaveBeenCalled()
  })

  it('opens on accounts', async () => {
    const wrapper = await mountCreators()

    const tabs = wrapper.findAll('.creators__tab')
    expect(tabs.map((one) => one.text())).toEqual(['账号', '人物'])
    expect(tabs[0].classes()).toContain('creators__tab--active')
  })

  it('reads people only once that tab is opened', async () => {
    //
    // Somebody who came here to check a live account should not pay for the
    // identity list as well.
    //
    const { listPeople } = await import('../../src/api/people')
    const mockedPeople = vi.mocked(listPeople)
    mockedPeople.mockResolvedValue([])
    const wrapper = await mountCreators()

    expect(mockedPeople).not.toHaveBeenCalled()

    await wrapper.findAll('.creators__tab')[1].trigger('click')
    await settle()

    expect(mockedPeople).toHaveBeenCalledTimes(1)
    //
    // And the account directory is not read again by switching tabs.
    //
    expect(mockedList).toHaveBeenCalledTimes(1)
  })

  it('does not poll the directory on a timer', async () => {
    //
    // Only a probe the user started polls here. A directory that refreshed
    // itself would be a second permanent poller beside the task centre's.
    //
    await mountCreators()

    await vi.advanceTimersByTimeAsync(30_000)

    expect(mockedList).toHaveBeenCalledTimes(1)
  })
})

describe('the directory', () => {
  it('says what the database last saw, in the past tense', async () => {
    //
    // `last_live_status == 2` means "was broadcasting when last checked", not
    // "is broadcasting". Only a probe answers the present tense.
    //
    mockedList.mockResolvedValue(page([owner({ last_live_status: 2 })]))

    const wrapper = await mountCreators()

    expect(wrapper.text()).toContain('上次：直播中')
    expect(wrapper.text()).not.toContain('正在直播')
  })

  it('shows how many accounts there are', async () => {
    mockedList.mockResolvedValue(page([owner()], 73))

    const wrapper = await mountCreators()

    expect(wrapper.text()).toContain('共 73 个账号')
  })

  it('never claims the directory is empty when it could not be read', async () => {
    const { ApiError } = await import('../../src/api/client')
    mockedList.mockRejectedValue(
      new ApiError({ kind: 'network', status: null, code: null, message: 'offline' }),
    )

    const wrapper = await mountCreators()

    expect(wrapper.text()).not.toContain('没有符合条件的主播账号')
    expect(wrapper.find('[role="alert"]').exists()).toBe(true)
  })
})

describe('checking who is live', () => {
  it('refuses to check nothing', async () => {
    //
    // The legacy page read an empty selection as "check the whole page". A
    // probe is a real platform conversation per account, so that had to go.
    //
    mockedList.mockResolvedValue(page([owner()]))
    const wrapper = await mountCreators()

    const selected = buttonSaying(wrapper, '检查选中')
    expect(selected?.attributes('disabled')).toBeDefined()
  })

  it('says how many the page action will check', async () => {
    mockedList.mockResolvedValue(page([owner({ owner_user_id: 'A' }), owner({ owner_user_id: 'B' })]))
    const wrapper = await mountCreators()

    expect(buttonSaying(wrapper, '检查本页（2）')).toBeTruthy()
  })

  it('checks exactly the accounts that were ticked', async () => {
    mockedList.mockResolvedValue(
      page([owner({ owner_user_id: 'A' }), owner({ owner_user_id: 'B' })]),
    )
    mockedProbe.mockResolvedValue({ batch_id: 'B', done: true, items: [], task_id: null })
    const wrapper = await mountCreators()

    await wrapper.findAll('tbody input[type="checkbox"]')[1].trigger('change')
    await nextTick()
    await buttonSaying(wrapper, '检查选中')?.trigger('click')
    await settle()

    expect(mockedProbe).toHaveBeenCalledWith(['B'])
  })
})

describe('starting a recording', () => {
  it('goes through resolve and the task api, never the legacy endpoint', async () => {
    mockedList.mockResolvedValue(page([owner({ owner_user_id: 'A' })]))
    mockedProbe.mockResolvedValue({
      batch_id: 'B',
      done: true,
      task_id: null,
      items: [{ owner_user_id: 'A', state: 'living', live_share_url: SHORT_LINK }],
    })
    mockedResolve.mockResolvedValue({
      resolve_id: 'receipt-live',
      platform: 'douyin',
      resource_type: 'live',
      source_url: SHORT_LINK,
      resolved_url: 'https://live.douyin.com/123456',
      identity: {},
      expires_in_seconds: 600,
    })
    mockedCreateTask.mockResolvedValue({
      task_id: 'T-1',
      task_type: 'live_record',
      resolve_id: 'receipt-live',
    })
    const wrapper = await mountCreators()

    await buttonSaying(wrapper, '检查本页')?.trigger('click')
    await settle()
    await buttonSaying(wrapper, '查看')?.trigger('click')
    await nextTick()
    await wrapper.findAll('.panel__tab')[1].trigger('click')
    await settle()

    await buttonSaying(wrapper, '开始录制')?.trigger('click')
    await settle()

    expect(mockedResolve).toHaveBeenCalledWith(SHORT_LINK)
    expect(mockedCreateTask).toHaveBeenCalledWith({
      resolve_id: 'receipt-live',
      task_type: 'live_record',
    })
  })

  it('offers recording only when this probe said the room is live', async () => {
    //
    // Not from the database cache. An account last seen live an hour ago would
    // otherwise get a record button that starts a recording of nothing.
    //
    mockedList.mockResolvedValue(page([owner({ owner_user_id: 'A', last_live_status: 2 })]))
    const wrapper = await mountCreators()

    await buttonSaying(wrapper, '查看')?.trigger('click')
    await nextTick()
    await wrapper.findAll('.panel__tab')[1].trigger('click')
    await settle()

    expect(buttonSaying(wrapper, '开始录制')).toBeUndefined()
  })

  it('hands the user to the task centre afterwards', async () => {
    mockedList.mockResolvedValue(page([owner({ owner_user_id: 'A' })]))
    mockedProbe.mockResolvedValue({
      batch_id: 'B',
      done: true,
      task_id: null,
      items: [{ owner_user_id: 'A', state: 'living', live_share_url: SHORT_LINK }],
    })
    mockedResolve.mockResolvedValue({
      resolve_id: 'receipt-live',
      platform: 'douyin',
      resource_type: 'live',
      source_url: SHORT_LINK,
      resolved_url: 'https://live.douyin.com/1',
      identity: {},
      expires_in_seconds: 600,
    })
    mockedCreateTask.mockResolvedValue({
      task_id: 'T-7',
      task_type: 'live_record',
      resolve_id: 'receipt-live',
    })
    const wrapper = await mountCreators()

    await buttonSaying(wrapper, '检查本页')?.trigger('click')
    await settle()
    await buttonSaying(wrapper, '查看')?.trigger('click')
    await nextTick()
    await wrapper.findAll('.panel__tab')[1].trigger('click')
    await settle()
    await buttonSaying(wrapper, '开始录制')?.trigger('click')
    await settle()

    const link = wrapper.find('.creators__link')
    expect(link.exists()).toBe(true)
    expect(link.text()).toContain('T-7')
    expect(link.attributes('href')).toContain('/tasks')
  })
})

describe('opening a profile from a paste', () => {
  it('resolves before asking the owner api anything', async () => {
    mockedResolve.mockResolvedValue({
      resolve_id: 'receipt-owner',
      platform: 'douyin',
      resource_type: 'owner',
      source_url: SHORT_LINK,
      resolved_url: `https://www.douyin.com/user/${SEC_UID}`,
      identity: { sec_user_id: SEC_UID },
      expires_in_seconds: 600,
    })
    mockedReadOwner.mockResolvedValue({
      sec_user_id: SEC_UID,
      owner: null,
      owner_message: null,
      credential: { expires_in_days: 30 },
      posts: [],
      next_cursor: 0,
      has_more: false,
    })
    const wrapper = await mountCreators()

    await wrapper.find('.creators__input').setValue('4.33 复制打开抖音 ' + SHORT_LINK)
    await buttonSaying(wrapper, '打开')?.trigger('click')
    await settle()

    expect(mockedResolve).toHaveBeenCalledWith('4.33 复制打开抖音 ' + SHORT_LINK)
    expect(mockedReadOwner.mock.calls[0][0]).toBe(`https://www.douyin.com/user/${SEC_UID}`)
  })

  it('refuses a link that is not a profile, without calling the owner api', async () => {
    mockedResolve.mockResolvedValue({
      resolve_id: 'receipt-post',
      platform: 'douyin',
      resource_type: 'post',
      source_url: SHORT_LINK,
      resolved_url: 'https://www.douyin.com/video/1',
      identity: { aweme_id: '1' },
      expires_in_seconds: 600,
    })
    const wrapper = await mountCreators()

    await wrapper.find('.creators__input').setValue(SHORT_LINK)
    await buttonSaying(wrapper, '打开')?.trigger('click')
    await settle()

    expect(mockedReadOwner).not.toHaveBeenCalled()
    expect(wrapper.text()).toContain('主播主页')
  })
})
