import { createPinia, setActivePinia } from 'pinia'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import { ApiError } from '../../src/api/client'
import {
  createPerson,
  deletePerson,
  getPersonDetail,
  listPeople,
  updatePerson,
} from '../../src/api/people'
import { usePeopleStore } from '../../src/stores/people'
import type { PersonDetail } from '../../src/types/person'
import { detail, person } from './fixtures'

vi.mock('../../src/api/people', () => ({
  listPeople: vi.fn(),
  createPerson: vi.fn(),
  updatePerson: vi.fn(),
  deletePerson: vi.fn(),
  getPersonDetail: vi.fn(),
  searchAccounts: vi.fn(),
  attachAccount: vi.fn(),
  attachAccountByLink: vi.fn(),
  detachAccount: vi.fn(),
  addCollaboration: vi.fn(),
  removeCollaboration: vi.fn(),
}))
vi.mock('../../src/api/resolve', () => ({ resolveResource: vi.fn() }))

const mockedList = vi.mocked(listPeople)
const mockedCreate = vi.mocked(createPerson)
const mockedUpdate = vi.mocked(updatePerson)
const mockedDelete = vi.mocked(deletePerson)
const mockedDetail = vi.mocked(getPersonDetail)

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
  for (let index = 0; index < 5; index += 1) {
    await Promise.resolve()
  }
}

beforeEach(() => {
  setActivePinia(createPinia())
  vi.clearAllMocks()
  mockedList.mockResolvedValue([])
  mockedDetail.mockResolvedValue(detail())
})

describe('initial state', () => {
  it('has read nothing until asked', () => {
    const store = usePeopleStore()

    expect(store.people).toEqual([])
    expect(store.selectedPersonId).toBeNull()
    expect(store.hasLoadedPeople).toBe(false)
    expect(mockedList).not.toHaveBeenCalled()
  })
})

describe('reading the list', () => {
  it('keeps what the server sent, in its order', async () => {
    mockedList.mockResolvedValue([
      person({ person_id: 3, display_name: 'C' }),
      person({ person_id: 1, display_name: 'A' }),
    ])
    const store = usePeopleStore()

    await store.loadPeople()

    expect(store.people.map((one) => one.person_id)).toEqual([3, 1])
    expect(store.hasLoadedPeople).toBe(true)
  })

  it('keeps the last list when a read fails', async () => {
    //
    // A failed read is not evidence that there are no people. Emptying the list
    // would turn a network blip into "everybody disappeared".
    //
    mockedList.mockResolvedValueOnce([person({ person_id: 1 })])
    const store = usePeopleStore()
    await store.loadPeople()

    mockedList.mockRejectedValue(
      new ApiError({ kind: 'network', status: null, code: null, message: 'offline' }),
    )
    await store.loadPeople()

    expect(store.people).toHaveLength(1)
    expect(store.peopleError).toContain('offline')
  })

  it('does not claim the list is empty after a first failure', async () => {
    mockedList.mockRejectedValue(
      new ApiError({ kind: 'network', status: null, code: null, message: 'offline' }),
    )
    const store = usePeopleStore()

    await store.loadPeople()

    expect(store.hasLoadedPeople).toBe(false)
    expect(store.peopleError).toBeTruthy()
  })
})

describe('selecting a person', () => {
  beforeEach(() => {
    mockedList.mockResolvedValue([person({ person_id: 1 }), person({ person_id: 2 })])
  })

  it('reads the summary out of the list rather than copying it', async () => {
    const store = usePeopleStore()
    await store.loadPeople()

    await store.selectPerson(2)

    expect(store.selectedPerson?.person_id).toBe(2)
  })

  it('reads the detail when one is selected', async () => {
    const store = usePeopleStore()
    await store.loadPeople()

    await store.selectPerson(2)

    expect(mockedDetail).toHaveBeenCalledWith(2)
    expect(store.selectedDetail).not.toBeNull()
  })

  it('reads identity alone, never content', async () => {
    //
    // Browsing what somebody filmed is content, and content belongs to the
    // library stage. This screen is about identity: who is who, and who worked
    // with whom.
    //
    // Stated as the full list of what ran rather than the absence of one name:
    // anything new the store starts reading - a works endpoint most of all -
    // has to appear here to pass, instead of slipping past an assertion that
    // only knew to look for the name somebody thought of first.
    //
    const people = await import('../../src/api/people')
    const store = usePeopleStore()
    await store.loadPeople()

    await store.selectPerson(1)

    const called = Object.entries(people)
      .filter(([, value]) => vi.isMockFunction(value) && value.mock.calls.length > 0)
      .map(([name]) => name)
      .sort()
    expect(called).toEqual(['getPersonDetail', 'listPeople'])
  })

  it('follows the list as it is re-read', async () => {
    const store = usePeopleStore()
    await store.loadPeople()
    await store.selectPerson(2)

    mockedList.mockResolvedValue([
      person({ person_id: 1 }),
      person({ person_id: 2, display_name: '改名了' }),
    ])
    await store.loadPeople()

    expect(store.selectedPerson?.display_name).toBe('改名了')
  })

  it('forgets a selection the list no longer contains', async () => {
    const store = usePeopleStore()
    await store.loadPeople()
    await store.selectPerson(2)

    mockedList.mockResolvedValue([person({ person_id: 1 })])
    await store.loadPeople()

    expect(store.selectedPersonId).toBeNull()
    expect(store.selectedDetail).toBeNull()
  })
})

describe('a detail that arrives after somebody else was selected', () => {
  it('cannot overwrite the person now on screen', async () => {
    //
    // Click one person, change your mind, click another. The first detail is
    // about somebody the panel is no longer showing.
    //
    const slow = deferred<PersonDetail>()
    const fast = deferred<PersonDetail>()
    mockedList.mockResolvedValue([person({ person_id: 1 }), person({ person_id: 2 })])
    mockedDetail.mockReturnValueOnce(slow.promise).mockReturnValueOnce(fast.promise)
    const store = usePeopleStore()
    await store.loadPeople()

    const first = store.selectPerson(1)
    const second = store.selectPerson(2)

    fast.settle(detail({ summary: { aweme_count: 22, live_count: 2 } }))
    await second
    await drain()

    slow.settle(detail({ summary: { aweme_count: 11, live_count: 1 } }))
    await first
    await drain()

    expect(store.selectedPersonId).toBe(2)
    expect(store.selectedDetail?.summary.aweme_count).toBe(22)
  })

  it('cannot report its error against the new person either', async () => {
    const slow = deferred<PersonDetail>()
    const fast = deferred<PersonDetail>()
    mockedList.mockResolvedValue([person({ person_id: 1 }), person({ person_id: 2 })])
    mockedDetail.mockReturnValueOnce(slow.promise).mockReturnValueOnce(fast.promise)
    const store = usePeopleStore()
    await store.loadPeople()

    const first = store.selectPerson(1)
    const second = store.selectPerson(2)

    fast.settle(detail())
    await second
    await drain()
    slow.fail(new ApiError({ kind: 'network', status: null, code: null, message: 'x' }))
    await first
    await drain()

    expect(store.detailError).toBeNull()
  })
})

describe('creating a person', () => {
  it('sends the name and the note', async () => {
    mockedCreate.mockResolvedValue({ person_id: 9 })
    mockedList.mockResolvedValue([person({ person_id: 9 })])
    const store = usePeopleStore()

    await store.createPerson({ display_name: '新人物', note: '备注' })

    expect(mockedCreate).toHaveBeenCalledWith({ display_name: '新人物', note: '备注' })
  })

  it('re-reads the list rather than inventing a row', async () => {
    //
    // The database decides what a person looks like - a directory name arrives
    // with the first main account, for one - so the list is read again rather
    // than optimistically patched with something the server never said.
    //
    mockedCreate.mockResolvedValue({ person_id: 9 })
    mockedList.mockResolvedValue([person({ person_id: 9, display_name: '新人物' })])
    const store = usePeopleStore()

    await store.createPerson({ display_name: '新人物' })

    expect(mockedList).toHaveBeenCalled()
    expect(store.people.map((one) => one.person_id)).toEqual([9])
  })

  it('selects the person it just created', async () => {
    mockedCreate.mockResolvedValue({ person_id: 9 })
    mockedList.mockResolvedValue([person({ person_id: 9 })])
    const store = usePeopleStore()

    await store.createPerson({ display_name: '新人物' })

    expect(store.selectedPersonId).toBe(9)
  })

  it('cannot be submitted twice', async () => {
    const pending = deferred<{ person_id: number }>()
    mockedCreate.mockReturnValue(pending.promise)
    const store = usePeopleStore()

    const first = store.createPerson({ display_name: '新人物' })
    await drain()
    await store.createPerson({ display_name: '新人物' })

    expect(mockedCreate).toHaveBeenCalledTimes(1)

    pending.settle({ person_id: 9 })
    await first
  })

  it('reports a failure without touching the list', async () => {
    mockedList.mockResolvedValueOnce([person({ person_id: 1 })])
    const store = usePeopleStore()
    await store.loadPeople()
    mockedCreate.mockRejectedValue(
      new ApiError({ kind: 'backend', status: 502, code: 502, message: '创建人物失败' }),
    )

    await store.createPerson({ display_name: 'x' })

    expect(store.people).toHaveLength(1)
    expect(store.mutationError).toContain('创建人物失败')
  })
})

describe('editing a person', () => {
  beforeEach(() => {
    mockedList.mockResolvedValue([person({ person_id: 1, display_name: 'A', note: '旧' })])
  })

  it('sends only what changed', async () => {
    mockedUpdate.mockResolvedValue({ person_id: 1 })
    const store = usePeopleStore()
    await store.loadPeople()

    await store.updatePerson(1, { note: '新的备注' })

    expect(mockedUpdate).toHaveBeenCalledWith(1, { note: '新的备注' })
  })

  it('does not call the api when nothing changed', async () => {
    const store = usePeopleStore()
    await store.loadPeople()

    await store.updatePerson(1, {})

    expect(mockedUpdate).not.toHaveBeenCalled()
  })

  it('re-reads the list afterwards', async () => {
    mockedUpdate.mockResolvedValue({ person_id: 1 })
    const store = usePeopleStore()
    await store.loadPeople()
    const before = mockedList.mock.calls.length

    await store.updatePerson(1, { display_name: 'B' })

    expect(mockedList.mock.calls.length).toBeGreaterThan(before)
  })

  it('cannot be submitted twice', async () => {
    const pending = deferred<{ person_id: number }>()
    mockedUpdate.mockReturnValue(pending.promise)
    const store = usePeopleStore()
    await store.loadPeople()

    const first = store.updatePerson(1, { note: 'x' })
    await drain()
    await store.updatePerson(1, { note: 'x' })

    expect(mockedUpdate).toHaveBeenCalledTimes(1)

    pending.settle({ person_id: 1 })
    await first
  })
})

describe('deleting a person', () => {
  beforeEach(() => {
    mockedList.mockResolvedValue([person({ person_id: 1 }), person({ person_id: 2 })])
  })

  it('removes the record and clears the selection', async () => {
    mockedDelete.mockResolvedValue({ person_id: 1 })
    const store = usePeopleStore()
    await store.loadPeople()
    await store.selectPerson(1)

    mockedList.mockResolvedValue([person({ person_id: 2 })])
    await store.deletePerson(1)

    expect(mockedDelete).toHaveBeenCalledWith(1)
    expect(store.selectedPersonId).toBeNull()
    expect(store.selectedDetail).toBeNull()
  })

  it('cannot be submitted twice', async () => {
    const pending = deferred<{ person_id: number }>()
    mockedDelete.mockReturnValue(pending.promise)
    const store = usePeopleStore()
    await store.loadPeople()

    const first = store.deletePerson(1)
    await drain()
    await store.deletePerson(1)

    expect(mockedDelete).toHaveBeenCalledTimes(1)

    pending.settle({ person_id: 1 })
    await first
  })

  it('leaves everything alone when it fails', async () => {
    const store = usePeopleStore()
    await store.loadPeople()
    await store.selectPerson(1)
    mockedDelete.mockRejectedValue(
      new ApiError({ kind: 'backend', status: 502, code: 502, message: '删除人物失败' }),
    )

    await store.deletePerson(1)

    expect(store.selectedPersonId).toBe(1)
    expect(store.mutationError).toContain('删除人物失败')
  })
})
