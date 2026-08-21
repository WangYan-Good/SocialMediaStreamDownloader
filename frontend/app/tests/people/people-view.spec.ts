import { mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { nextTick } from 'vue'
import { createMemoryHistory, createRouter } from 'vue-router'

import {
  addCollaboration,
  attachAccount,
  deletePerson,
  getPersonDetail,
  listPeople,
  removeCollaboration,
  searchAccounts,
} from '../../src/api/people'
import { routes } from '../../src/router'
import CreatorsView from '../../src/views/CreatorsView.vue'
import { detail, person } from './fixtures'

vi.mock('../../src/api/history', () => ({
  listHistoryOwners: vi.fn(async () => ({ total: 0, page: 1, page_size: 20, items: [] })),
  listOwnerSessions: vi.fn(),
  submitLiveProbe: vi.fn(),
  getLiveProbe: vi.fn(),
}))
vi.mock('../../src/api/owners', () => ({
  readOwner: vi.fn(),
  readOwnerPosts: vi.fn(),
  startOwnerSelectedDownload: vi.fn(),
  startOwnerAllDownload: vi.fn(),
}))
vi.mock('../../src/api/resolve', () => ({ resolveResource: vi.fn() }))
vi.mock('../../src/api/tasks', () => ({ createTask: vi.fn(), listTasks: vi.fn(), getTask: vi.fn() }))
vi.mock('../../src/api/people', () => ({
  listPeople: vi.fn(),
  createPerson: vi.fn(),
  updatePerson: vi.fn(),
  deletePerson: vi.fn(),
  getPersonDetail: vi.fn(),
  searchAccounts: vi.fn(),
  attachAccount: vi.fn(),
  attachAccountByLink: vi.fn(),
  assignPersonAccount: vi.fn(),
  detachAccount: vi.fn(),
  addCollaboration: vi.fn(),
  removeCollaboration: vi.fn(),
}))

const mockedList = vi.mocked(listPeople)
const mockedDetail = vi.mocked(getPersonDetail)
const mockedSearch = vi.mocked(searchAccounts)
const mockedAttach = vi.mocked(attachAccount)
const mockedDelete = vi.mocked(deletePerson)
const mockedAdd = vi.mocked(addCollaboration)
const mockedRemove = vi.mocked(removeCollaboration)

async function settle() {
  for (let index = 0; index < 6; index += 1) {
    await Promise.resolve()
  }
  await nextTick()
}

async function openPeople() {
  const router = createRouter({ history: createMemoryHistory(), routes })
  await router.push('/creators')
  await router.isReady()
  const wrapper = mount(CreatorsView, { global: { plugins: [router] } })
  await settle()
  await wrapper.findAll('.creators__tab')[1].trigger('click')
  await settle()
  return wrapper
}

function buttonSaying(wrapper: Awaited<ReturnType<typeof openPeople>>, text: string) {
  return wrapper.findAll('button').find((one) => one.text().includes(text))
}

//
// Found by what the options say rather than by position, so re-ordering the
// panel's fields does not quietly point these at a different control.
//
function selectOffering(wrapper: Awaited<ReturnType<typeof openPeople>>, optionText: string) {
  return wrapper
    .findAll('aside select')
    .find((one) => one.findAll('option').some((option) => option.text().includes(optionText)))
}

//
// Exact, because "添加" is also the tail of "按链接添加" and a substring match
// finds that one first - and finds it disabled, so the click lands nowhere and
// the test passes or fails for reasons that have nothing to do with the form.
//
function buttonExactly(wrapper: Awaited<ReturnType<typeof openPeople>>, text: string) {
  return wrapper.findAll('button').find((one) => one.text().trim() === text)
}

/** Pick an option by the words on it, whatever value is bound behind them. */
async function choose(
  select: ReturnType<typeof selectOffering>,
  optionText: string,
): Promise<void> {
  const option = select?.findAll('option').find((one) => one.text().includes(optionText))
  await select?.setValue((option?.element as HTMLOptionElement).value)
}

beforeEach(() => {
  setActivePinia(createPinia())
  vi.clearAllMocks()
  mockedList.mockResolvedValue([])
  mockedDetail.mockResolvedValue(detail())
  mockedSearch.mockResolvedValue([])
})

describe('the people list', () => {
  it('says when a person has no folder yet', async () => {
    //
    // A directory comes from the account marked main. Inventing one here would
    // create a folder the backend never agreed to.
    //
    mockedList.mockResolvedValue([person({ directory_name: null })])

    const wrapper = await openPeople()

    expect(wrapper.text()).toContain('尚未由大号确定目录')
  })

  it('never claims there are no people when the read failed', async () => {
    const { ApiError } = await import('../../src/api/client')
    mockedList.mockRejectedValue(
      new ApiError({ kind: 'network', status: null, code: null, message: 'offline' }),
    )

    const wrapper = await openPeople()

    expect(wrapper.text()).not.toContain('还没有人物')
    expect(wrapper.find('[role="alert"]').exists()).toBe(true)
  })
})

describe('a person detail', () => {
  beforeEach(() => {
    mockedList.mockResolvedValue([person({ person_id: 7, display_name: '当前' })])
  })

  it('shows the account roles in words', async () => {
    mockedDetail.mockResolvedValue(
      detail({
        accounts: [
          { owner_user_id: '1', nickname: '主号', role: 'main' },
          { owner_user_id: '2', nickname: '小号', role: 'alt' },
          { owner_user_id: '3', nickname: '矩阵', role: 'matrix' },
        ],
      }),
    )
    const wrapper = await openPeople()

    await buttonSaying(wrapper, '查看')?.trigger('click')
    await settle()

    const text = wrapper.find('aside').text()
    expect(text).toContain('主号')
    expect(text).toContain('小号')
    expect(text).toContain('矩阵号')
  })

  it('keeps the two collaboration directions apart', async () => {
    //
    // "Filmed" and "was filmed by" are different facts. Merging them would hide
    // which way round every relation goes.
    //
    mockedDetail.mockResolvedValue(
      detail({
        subjects: [{ person_id: 9, display_name: '被拍的人', note: null }],
        photographers: [{ person_id: 3, display_name: '拍我的人', note: null }],
      }),
    )
    const wrapper = await openPeople()

    await buttonSaying(wrapper, '查看')?.trigger('click')
    await settle()

    const text = wrapper.find('aside').text()
    expect(text).toContain('TA 拍摄过')
    expect(text).toContain('拍摄过 TA')
    expect(text).toContain('被拍的人')
    expect(text).toContain('拍我的人')
  })

  it('removes each direction with the ids in the right order', async () => {
    mockedDetail.mockResolvedValue(
      detail({
        subjects: [{ person_id: 9, display_name: '被拍的人', note: null }],
        photographers: [{ person_id: 3, display_name: '拍我的人', note: null }],
      }),
    )
    mockedRemove.mockResolvedValue({ photographer_id: 7, subject_id: 9 })
    const wrapper = await openPeople()
    await buttonSaying(wrapper, '查看')?.trigger('click')
    await settle()

    const removeButtons = wrapper.findAll('aside .rows__row button')
    await removeButtons[0].trigger('click')
    await settle()

    //
    // From the "filmed" list, the current person is the photographer.
    //
    expect(mockedRemove).toHaveBeenCalledWith(7, 9)
  })

  it('never offers the current person as their own collaborator', async () => {
    mockedList.mockResolvedValue([
      person({ person_id: 7, display_name: '当前' }),
      person({ person_id: 9, display_name: '对方' }),
    ])
    const wrapper = await openPeople()

    await buttonSaying(wrapper, '查看')?.trigger('click')
    await settle()

    const options = wrapper
      .findAll('aside select')
      .flatMap((select) => select.findAll('option'))
      .map((option) => option.text())
    expect(options).toContain('对方')
    expect(options).not.toContain('当前')
  })
})

describe('recording a collaboration from the panel', () => {
  //
  // The store already proves that a named direction becomes the right pair of
  // ids. What is only decidable here is which direction each option on the
  // dropdown *means* - swapping the two option values would record every
  // relation backwards, silently, and no store test would notice.
  //
  beforeEach(() => {
    mockedList.mockResolvedValue([
      person({ person_id: 7, display_name: '当前' }),
      person({ person_id: 9, display_name: '对方' }),
    ])
    mockedAdd.mockResolvedValue({ photographer_id: 7, subject_id: 9 })
  })

  async function openPanel() {
    const wrapper = await openPeople()
    await buttonSaying(wrapper, '查看')?.trigger('click')
    await settle()
    return wrapper
  }

  it('puts the current person behind the camera when they did the filming', async () => {
    const wrapper = await openPanel()

    await choose(selectOffering(wrapper, '当前人物拍摄了'), '当前人物拍摄了')
    await choose(selectOffering(wrapper, '请选择'), '对方')
    await buttonExactly(wrapper, '添加')?.trigger('click')
    await settle()

    expect(mockedAdd).toHaveBeenCalledWith({ photographer_id: 7, subject_id: 9 })
  })

  it('puts them in front of it when they were the one filmed', async () => {
    const wrapper = await openPanel()

    await choose(selectOffering(wrapper, '当前人物被'), '当前人物被')
    await choose(selectOffering(wrapper, '请选择'), '对方')
    await buttonExactly(wrapper, '添加')?.trigger('click')
    await settle()

    expect(mockedAdd).toHaveBeenCalledWith({ photographer_id: 9, subject_id: 7 })
  })

  it('carries a note the user wrote alongside the direction', async () => {
    const wrapper = await openPanel()

    await choose(selectOffering(wrapper, '当前人物拍摄了'), '当前人物拍摄了')
    await choose(selectOffering(wrapper, '请选择'), '对方')
    const noteInputs = wrapper.findAll('aside input[type="text"]')
    await noteInputs[noteInputs.length - 1].setValue('外景')
    await buttonExactly(wrapper, '添加')?.trigger('click')
    await settle()

    expect(mockedAdd).toHaveBeenCalledWith({
      photographer_id: 7,
      subject_id: 9,
      note: '外景',
    })
  })
})

describe('a searched account', () => {
  beforeEach(() => {
    mockedList.mockResolvedValue([person({ person_id: 7 })])
  })

  async function search(result: Parameters<typeof mockedSearch.mockResolvedValue>[0]) {
    mockedSearch.mockResolvedValue(result)
    const wrapper = await openPeople()
    await buttonSaying(wrapper, '查看')?.trigger('click')
    await settle()
    await wrapper.find('aside input[type="search"]').setValue('某')
    await buttonSaying(wrapper, '搜索')?.trigger('click')
    await settle()
    return wrapper
  }

  it('shows the folder it already downloads into', async () => {
    //
    // Nicknames repeat and change; the folder is what tells two similar-looking
    // accounts apart, and it is the thing a mistaken attachment would go on to
    // fill with somebody else's downloads.
    //
    const wrapper = await search([
      {
        owner_user_id: '1',
        nickname: '某号',
        directory_name: '某某目录',
        person_id: null,
        role: null,
      },
    ])

    expect(wrapper.find('aside').text()).toContain('某某目录')
  })

  it('says so plainly when it has no folder yet', async () => {
    const wrapper = await search([
      {
        owner_user_id: '1',
        nickname: '某号',
        directory_name: null,
        person_id: null,
        role: null,
      },
    ])

    expect(wrapper.find('aside').text()).toContain('尚未由大号确定目录')
  })
})

describe('moving an account that belongs to somebody else', () => {
  beforeEach(() => {
    mockedList.mockResolvedValue([person({ person_id: 7 })])
  })

  it('asks first, and does nothing when refused', async () => {
    //
    // The backend upserts, so this silently takes the account away from whoever
    // has it. A click should not be able to do that unannounced.
    //
    mockedSearch.mockResolvedValue([
      { owner_user_id: '1', nickname: '某号', directory_name: null, person_id: 3, role: 'alt' },
    ])
    const confirm = vi.spyOn(window, 'confirm').mockReturnValue(false)
    const wrapper = await openPeople()
    await buttonSaying(wrapper, '查看')?.trigger('click')
    await settle()

    await wrapper.find('aside input[type="search"]').setValue('某')
    await buttonSaying(wrapper, '搜索')?.trigger('click')
    await settle()
    await buttonSaying(wrapper, '挂到此人')?.trigger('click')
    await settle()

    expect(confirm).toHaveBeenCalled()
    expect(String(confirm.mock.calls[0][0])).toContain('移动')
    expect(mockedAttach).not.toHaveBeenCalled()
    confirm.mockRestore()
  })

  it('goes ahead once confirmed', async () => {
    mockedSearch.mockResolvedValue([
      { owner_user_id: '1', nickname: '某号', directory_name: null, person_id: 3, role: 'alt' },
    ])
    mockedAttach.mockResolvedValue({ owner_user_id: '1', person_id: 7 })
    const confirm = vi.spyOn(window, 'confirm').mockReturnValue(true)
    const wrapper = await openPeople()
    await buttonSaying(wrapper, '查看')?.trigger('click')
    await settle()

    await wrapper.find('aside input[type="search"]').setValue('某')
    await buttonSaying(wrapper, '搜索')?.trigger('click')
    await settle()
    await buttonSaying(wrapper, '挂到此人')?.trigger('click')
    await settle()

    expect(mockedAttach).toHaveBeenCalledWith({
      owner_user_id: '1',
      person_id: 7,
      role: 'alt',
    })
    confirm.mockRestore()
  })

  it('asks nothing for an account that belongs to nobody', async () => {
    mockedSearch.mockResolvedValue([
      { owner_user_id: '1', nickname: '某号', directory_name: null, person_id: null, role: null },
    ])
    mockedAttach.mockResolvedValue({ owner_user_id: '1', person_id: 7 })
    const confirm = vi.spyOn(window, 'confirm').mockReturnValue(true)
    const wrapper = await openPeople()
    await buttonSaying(wrapper, '查看')?.trigger('click')
    await settle()

    await wrapper.find('aside input[type="search"]').setValue('某')
    await buttonSaying(wrapper, '搜索')?.trigger('click')
    await settle()
    await buttonSaying(wrapper, '挂到此人')?.trigger('click')
    await settle()

    expect(confirm).not.toHaveBeenCalled()
    expect(mockedAttach).toHaveBeenCalled()
    confirm.mockRestore()
  })
})

describe('deleting a person', () => {
  beforeEach(() => {
    mockedList.mockResolvedValue([person({ person_id: 7 })])
  })

  it('asks first and says what it does not touch', async () => {
    const confirm = vi.spyOn(window, 'confirm').mockReturnValue(false)
    const wrapper = await openPeople()
    await buttonSaying(wrapper, '查看')?.trigger('click')
    await settle()

    await buttonSaying(wrapper, '删除人物')?.trigger('click')
    await settle()

    const asked = String(confirm.mock.calls[0][0])
    expect(asked).toContain('不会移动或删除已经下载的文件')
    expect(mockedDelete).not.toHaveBeenCalled()
    confirm.mockRestore()
  })

  it('deletes once confirmed', async () => {
    mockedDelete.mockResolvedValue({ person_id: 7 })
    const confirm = vi.spyOn(window, 'confirm').mockReturnValue(true)
    const wrapper = await openPeople()
    await buttonSaying(wrapper, '查看')?.trigger('click')
    await settle()

    await buttonSaying(wrapper, '删除人物')?.trigger('click')
    await settle()

    expect(mockedDelete).toHaveBeenCalledWith(7)
    confirm.mockRestore()
  })
})

describe('the identity screen stays out of the library', () => {
  it('offers nothing that browses what somebody filmed', async () => {
    //
    // Works belong to the library stage. This screen answers who is who.
    //
    mockedList.mockResolvedValue([person({ person_id: 7 })])
    const wrapper = await openPeople()
    await buttonSaying(wrapper, '查看')?.trigger('click')
    await settle()

    const text = wrapper.find('aside').text()
    expect(text).not.toContain('浏览作品')
    expect(text).not.toContain('查看作品')
    expect(buttonSaying(wrapper, '作品列表')).toBeUndefined()
  })
})

// >>============================= link-first is the way in =============================>>

describe('CreatorsView - the people tab opens on a link box', () => {
  //
  // The tab used to open with "name a person, press create". That asked for a
  // decision - what to call somebody - before the information needed to make it
  // existed, and left the account still to be attached in a second place.
  //

  it('offers the assignment card', async () => {
    mockedList.mockResolvedValue([])
    const wrapper = await openPeople()

    expect(wrapper.find('[data-test="assignment-input"]').exists()).toBe(true)
  })

  it('no longer asks for a person name up front', async () => {
    mockedList.mockResolvedValue([])
    const wrapper = await openPeople()

    //
    // The old form's own control, found by its exact label so the assignment
    // card's optional name field is not mistaken for it.
    //
    expect(buttonExactly(wrapper, '创建')).toBeUndefined()
    expect(wrapper.text()).not.toContain('新建人物')
  })

  it('never calls the empty-person endpoint from this tab', async () => {
    mockedList.mockResolvedValue([])
    const { createPerson } = await import('../../src/api/people')
    vi.mocked(createPerson).mockClear()

    await openPeople()

    expect(vi.mocked(createPerson)).not.toHaveBeenCalled()
  })

  it('tells an empty workspace to paste a link, not to create a person', async () => {
    mockedList.mockResolvedValue([])
    const wrapper = await openPeople()

    const text = wrapper.text()
    expect(text).toContain('还没有人物')
    expect(text).toContain('链接')
    //
    // The old copy advertised the two-step flow it no longer does.
    //
    expect(text).not.toContain('可以先创建一个')
  })
})
