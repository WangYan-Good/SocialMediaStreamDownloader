import { mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { nextTick } from 'vue'

import { listHistoryOwners } from '../../src/api/history'
import { readOwner } from '../../src/api/owners'
import {
  getPersonDetail,
  inspectPersonAssignment,
  listPeople,
} from '../../src/api/people'
import { resolveResource } from '../../src/api/resolve'
import CreatorsView from '../../src/views/CreatorsView.vue'
import type { OwnerRead } from '../../src/types/owner'
import type { PersonIdentityInspection } from '../../src/types/person'
import type { ResolvedResource } from '../../src/types/resolution'

vi.mock('../../src/api/history', () => ({
  listHistoryOwners: vi.fn(),
  listOwnerSessions: vi.fn(async () => ({ items: [] })),
  submitLiveProbe: vi.fn(),
  getLiveProbe: vi.fn(),
  updateOwnerPreference: vi.fn(),
}))
vi.mock('../../src/api/owners', () => ({
  readOwner: vi.fn(),
  readOwnerPosts: vi.fn(async () => ({ posts: [], next_cursor: 0, has_more: false })),
  startOwnerSelectedDownload: vi.fn(),
  startOwnerAllDownload: vi.fn(),
}))
vi.mock('../../src/api/resolve', () => ({ resolveResource: vi.fn() }))
vi.mock('../../src/api/people', () => ({
  listPeople: vi.fn(),
  createPerson: vi.fn(),
  updatePerson: vi.fn(),
  deletePerson: vi.fn(),
  getPersonDetail: vi.fn(),
  searchAccounts: vi.fn(async () => []),
  attachAccount: vi.fn(),
  attachAccountByLink: vi.fn(),
  assignPersonAccount: vi.fn(),
  inspectPersonAssignment: vi.fn(),
  detachAccount: vi.fn(),
  addCollaboration: vi.fn(),
  removeCollaboration: vi.fn(),
  getPersonWorks: vi.fn(),
}))
vi.mock('../../src/api/tasks', () => ({
  createTask: vi.fn(),
  listTasks: vi.fn(),
  getTask: vi.fn(),
}))

const mockedListOwners = vi.mocked(listHistoryOwners)
const mockedReadOwner = vi.mocked(readOwner)
const mockedListPeople = vi.mocked(listPeople)
const mockedGetDetail = vi.mocked(getPersonDetail)
const mockedInspect = vi.mocked(inspectPersonAssignment)
const mockedResolve = vi.mocked(resolveResource)

const SEC_UID = 'MS4wLjABAAAA-lookup-owner'

function resolution(): ResolvedResource {
  return {
    resolve_id: 'lookup-receipt',
    platform: 'douyin',
    resource_type: 'owner',
    source_url: 'https://v.douyin.com/lookup/',
    resolved_url: `https://www.douyin.com/user/${SEC_UID}`,
    identity: { sec_user_id: SEC_UID },
    expires_in_seconds: 600,
  }
}

function platformRead(overrides: Partial<OwnerRead> = {}): OwnerRead {
  return {
    sec_user_id: SEC_UID,
    owner: {
      sec_user_id: SEC_UID,
      uid: 'platform-uid',
      nickname: '当前平台昵称',
      unique_id: 'current-platform-id',
      signature: '这是当前平台简介',
      avatar_url: null,
      follower_count: 1234,
      following_count: 56,
      aweme_count: 78,
      total_favorited: 9012,
    },
    owner_message: null,
    credential: { expires_in_days: 12 },
    posts: [],
    next_cursor: 0,
    has_more: false,
    ...overrides,
  }
}

function localInspection(
  overrides: Partial<PersonIdentityInspection> = {},
): PersonIdentityInspection {
  return {
    owner: {
      owner_user_id: 'local-owner-id',
      sec_user_id: SEC_UID,
      nickname: '本地记录昵称',
    },
    known_account: true,
    assignment: { person_id: 17, display_name: '人物记录名', role: 'alt' },
    ...overrides,
  }
}

async function settle() {
  for (let index = 0; index < 8; index += 1) {
    await Promise.resolve()
  }
  await nextTick()
}

async function mountLookup() {
  const wrapper = mount(CreatorsView, {
    global: {
      plugins: [createPinia()],
      stubs: { RouterLink: { template: '<a><slot /></a>' } },
    },
  })
  await settle()
  const lookupTab = wrapper.findAll('.creators__tab')[2]
  await lookupTab.trigger('click')
  await settle()
  return wrapper
}

async function submit(wrapper: Awaited<ReturnType<typeof mountLookup>>, value = 'owner share text') {
  await wrapper.get('input[name="creator-lookup"]').setValue(value)
  await wrapper.get('form').trigger('submit')
  await settle()
}

beforeEach(() => {
  setActivePinia(createPinia())
  vi.clearAllMocks()
  mockedListOwners.mockResolvedValue({ total: 0, page: 1, page_size: 20, items: [] })
  mockedResolve.mockResolvedValue(resolution())
  mockedReadOwner.mockResolvedValue(platformRead())
  mockedInspect.mockResolvedValue(localInspection())
  mockedListPeople.mockResolvedValue([
    { person_id: 17, display_name: '人物记录名', directory_name: 'person-17', note: null, account_count: 1 },
  ])
  mockedGetDetail.mockResolvedValue({
    accounts: [],
    summary: { aweme_count: 0, live_count: 0 },
    subjects: [],
    photographers: [],
  })
})

describe('creator lookup presentation', () => {
  it('does not submit blank or whitespace-only input', async () => {
    const wrapper = await mountLookup()
    const submitButton = wrapper.get('button[type="submit"]')

    expect(submitButton.attributes('disabled')).toBeDefined()
    await wrapper.get('input[name="creator-lookup"]').setValue('   ')
    await wrapper.get('form').trigger('submit')
    await settle()

    expect(mockedResolve).not.toHaveBeenCalled()
    expect(submitButton.attributes('disabled')).toBeDefined()
  })

  it('shows current platform, local account and Person facts without merging their nicknames', async () => {
    const wrapper = await mountLookup()

    await submit(wrapper)

    expect(wrapper.text()).toContain('当前平台信息')
    expect(wrapper.text()).toContain('当前平台昵称')
    expect(wrapper.text()).toContain('current-platform-id')
    expect(wrapper.text()).toContain('这是当前平台简介')
    expect(wrapper.text()).toContain('1,234')
    expect(wrapper.text()).toContain('本地记录')
    expect(wrapper.text()).toContain('本地记录昵称')
    expect(wrapper.text()).toContain('本地已记录')
    expect(wrapper.text()).toContain('人物归属')
    expect(wrapper.text()).toContain('人物记录名')
    expect(wrapper.text()).toContain('备用账号')
  })

  it('represents a successful unknown-account answer without offering mutations', async () => {
    mockedInspect.mockResolvedValue(
      localInspection({ known_account: false, assignment: null }),
    )
    const wrapper = await mountLookup()

    await submit(wrapper)

    expect(wrapper.text()).toContain('本地尚无记录')
    expect(wrapper.text()).toContain('尚未归属人物')
    const buttonText = wrapper.findAll('button').map((button) => button.text()).join(' ')
    expect(buttonText).not.toMatch(/下载|录制|收藏|评分|创建人物|挂载|解绑|移动|修改|协作/)
  })

  it('shows a known but unassigned account without offering Person mutations', async () => {
    mockedInspect.mockResolvedValue(
      localInspection({ known_account: true, assignment: null }),
    )
    const wrapper = await mountLookup()

    await submit(wrapper)

    expect(wrapper.text()).toContain('本地已记录')
    expect(wrapper.text()).toContain('尚未归属人物')
    expect(wrapper.text()).not.toContain('查看人物')
    const buttonText = wrapper.findAll('button').map((button) => button.text()).join(' ')
    expect(buttonText).not.toMatch(/创建人物|挂载|解绑|移动|修改|协作/)
  })

  it('keeps platform facts but makes no local claims when inspection is unavailable', async () => {
    mockedInspect.mockRejectedValue(new Error('database unavailable'))
    const wrapper = await mountLookup()

    await submit(wrapper)

    expect(wrapper.text()).toContain('当前平台昵称')
    expect(wrapper.text()).toContain('暂时无法确认本地账号归属')
    expect(wrapper.text()).not.toContain('本地尚无记录')
    expect(wrapper.text()).not.toContain('尚未归属人物')
  })

  it('keeps local facts when the whole platform request fails', async () => {
    mockedReadOwner.mockRejectedValue(new Error('platform unavailable'))
    const wrapper = await mountLookup()

    await submit(wrapper)

    expect(wrapper.text()).toContain('平台资料暂时无法读取')
    expect(wrapper.text()).toContain('本地记录昵称')
    expect(wrapper.text()).toContain('人物记录名')
  })

  it('shows a safe owner message while preserving local facts when owner detail is partial', async () => {
    mockedReadOwner.mockResolvedValue(
      platformRead({ owner: null, owner_message: '主播详情暂时不可用，请稍后重试' }),
    )
    const wrapper = await mountLookup()

    await submit(wrapper)

    expect(wrapper.text()).toContain('主播详情暂时不可用，请稍后重试')
    expect(wrapper.text()).toContain('本地记录昵称')
    expect(wrapper.text()).toContain('人物记录名')
  })

  it('clears a completed result as soon as the input describes something else', async () => {
    const wrapper = await mountLookup()
    await submit(wrapper, 'A')
    expect(wrapper.text()).toContain('当前平台昵称')

    await wrapper.get('input[name="creator-lookup"]').setValue('B')
    await settle()

    expect(wrapper.text()).not.toContain('当前平台昵称')
    expect(wrapper.text()).not.toContain('本地记录昵称')
    expect(wrapper.text()).not.toContain('人物记录名')
  })
})

describe('viewing an assigned person', () => {
  it('loads People before selecting and opening the assigned person', async () => {
    const wrapper = await mountLookup()
    await submit(wrapper)

    const viewPerson = wrapper.findAll('button').find((button) => button.text() === '查看人物')
    await viewPerson?.trigger('click')
    await settle()

    expect(mockedListPeople).toHaveBeenCalledTimes(1)
    expect(mockedGetDetail).toHaveBeenCalledWith(17)
    expect(wrapper.findAll('.creators__tab')[1].classes()).toContain('creators__tab--active')
  })

  it('does not pretend to open a person when the People list cannot be loaded', async () => {
    mockedListPeople.mockRejectedValue(new Error('database unavailable'))
    const wrapper = await mountLookup()
    await submit(wrapper)

    const viewPerson = wrapper.findAll('button').find((button) => button.text() === '查看人物')
    await viewPerson?.trigger('click')
    await settle()

    expect(mockedGetDetail).not.toHaveBeenCalled()
    expect(wrapper.findAll('.creators__tab')[1].classes()).toContain('creators__tab--active')
    expect(wrapper.text()).toContain('暂时无法读取人物列表')
  })

  it('opens the assigned person even when an already-loaded list is stale', async () => {
    mockedListPeople
      .mockResolvedValueOnce([])
      .mockResolvedValueOnce([
        { person_id: 17, display_name: '人物记录名', directory_name: 'person-17', note: null, account_count: 1 },
      ])
    const wrapper = await mountLookup()
    // Load the People tab first, before the assignment appears in its cached
    // list. A lookup receipt remains the authority for which person to open.
    await wrapper.findAll('.creators__tab')[1].trigger('click')
    await settle()
    await wrapper.findAll('.creators__tab')[2].trigger('click')
    await submit(wrapper)

    const viewPerson = wrapper.findAll('button').find((button) => button.text() === '查看人物')
    await viewPerson?.trigger('click')
    await settle()

    expect(mockedListPeople).toHaveBeenCalledTimes(2)
    expect(mockedGetDetail).toHaveBeenCalledWith(17)
    expect(wrapper.get('#person-panel-heading').text()).toBe('人物记录名')
  })
})
