import { createPinia, setActivePinia } from 'pinia'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import { ApiError } from '../../src/api/client'
import {
  addCollaboration,
  getPersonDetail,
  listPeople,
  removeCollaboration,
} from '../../src/api/people'
import { usePeopleStore } from '../../src/stores/people'
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
const mockedDetail = vi.mocked(getPersonDetail)
const mockedAdd = vi.mocked(addCollaboration)
const mockedRemove = vi.mocked(removeCollaboration)

function deferred<T>() {
  let settle: (value: T) => void = () => {}
  const promise = new Promise<T>((resolve) => {
    settle = resolve
  })
  return { promise, settle }
}

async function drain() {
  for (let index = 0; index < 5; index += 1) {
    await Promise.resolve()
  }
}

async function storeWith(currentId = 7) {
  mockedList.mockResolvedValue([
    person({ person_id: currentId, display_name: '当前' }),
    person({ person_id: 9, display_name: '对方' }),
  ])
  mockedDetail.mockResolvedValue(detail())
  const store = usePeopleStore()
  await store.loadPeople()
  await store.selectPerson(currentId)
  return store
}

beforeEach(() => {
  setActivePinia(createPinia())
  vi.clearAllMocks()
  mockedList.mockResolvedValue([])
  mockedDetail.mockResolvedValue(detail())
})

describe('recording who filmed whom', () => {
  //
  // The relation is directed. "A filmed B" and "B filmed A" are different
  // facts, and the endpoint takes them as two named ids rather than a pair -
  // so getting the order wrong records the opposite of what the user said.
  //

  it('puts the current person in the photographer seat when they did the filming', async () => {
    mockedAdd.mockResolvedValue({ photographer_id: 7, subject_id: 9 })
    const store = await storeWith(7)

    await store.addCollaboration({ direction: 'shot', otherPersonId: 9, note: '外拍' })

    expect(mockedAdd).toHaveBeenCalledWith({
      photographer_id: 7,
      subject_id: 9,
      note: '外拍',
    })
  })

  it('puts them in the subject seat when they were filmed', async () => {
    mockedAdd.mockResolvedValue({ photographer_id: 9, subject_id: 7 })
    const store = await storeWith(7)

    await store.addCollaboration({ direction: 'shotBy', otherPersonId: 9 })

    expect(mockedAdd).toHaveBeenCalledWith({ photographer_id: 9, subject_id: 7 })
  })

  it('carries a note when one was written', async () => {
    mockedAdd.mockResolvedValue({ photographer_id: 7, subject_id: 9 })
    const store = await storeWith(7)

    await store.addCollaboration({ direction: 'shot', otherPersonId: 9, note: '棚拍' })

    expect(mockedAdd.mock.calls[0][0].note).toBe('棚拍')
  })

  it('omits an empty note rather than sending an empty string', async () => {
    mockedAdd.mockResolvedValue({ photographer_id: 7, subject_id: 9 })
    const store = await storeWith(7)

    await store.addCollaboration({ direction: 'shot', otherPersonId: 9, note: '   ' })

    expect('note' in mockedAdd.mock.calls[0][0]).toBe(false)
  })

  it('refuses to relate somebody to themselves', async () => {
    //
    // The backend refuses it too, but a candidate list that offered it would be
    // asking the user to make a mistake.
    //
    const store = await storeWith(7)

    await store.addCollaboration({ direction: 'shot', otherPersonId: 7 })

    expect(mockedAdd).not.toHaveBeenCalled()
  })

  it('leaves the current person out of the candidates', async () => {
    const store = await storeWith(7)

    expect(store.collaborationCandidates.map((one) => one.person_id)).toEqual([9])
  })

  it('re-reads the detail so both directions stay current', async () => {
    mockedAdd.mockResolvedValue({ photographer_id: 7, subject_id: 9 })
    const store = await storeWith(7)
    const before = mockedDetail.mock.calls.length

    await store.addCollaboration({ direction: 'shot', otherPersonId: 9 })

    expect(mockedDetail.mock.calls.length).toBeGreaterThan(before)
  })

  it('cannot be submitted twice', async () => {
    const pending = deferred<{ photographer_id: number; subject_id: number }>()
    mockedAdd.mockReturnValue(pending.promise)
    const store = await storeWith(7)

    const first = store.addCollaboration({ direction: 'shot', otherPersonId: 9 })
    await drain()
    await store.addCollaboration({ direction: 'shot', otherPersonId: 9 })

    expect(mockedAdd).toHaveBeenCalledTimes(1)

    pending.settle({ photographer_id: 7, subject_id: 9 })
    await first
  })

  it('reports a failure without pretending it worked', async () => {
    mockedAdd.mockRejectedValue(
      new ApiError({ kind: 'backend', status: 502, code: 502, message: '记录合作关系失败' }),
    )
    const store = await storeWith(7)

    await store.addCollaboration({ direction: 'shot', otherPersonId: 9 })

    expect(store.mutationError).toContain('记录合作关系失败')
  })
})

describe('removing a collaboration', () => {
  it('removes the direction where the current person filmed', async () => {
    //
    // From the "subjects" list: the current person is the photographer, and the
    // relation being removed is theirs.
    //
    mockedRemove.mockResolvedValue({ photographer_id: 7, subject_id: 9 })
    const store = await storeWith(7)

    await store.removeCollaboration({ direction: 'shot', otherPersonId: 9 })

    expect(mockedRemove).toHaveBeenCalledWith(7, 9)
  })

  it('removes the direction where the current person was filmed', async () => {
    //
    // From the "photographers" list: the ids go the other way round. Swapping
    // them here would delete a different relation, or none at all.
    //
    mockedRemove.mockResolvedValue({ photographer_id: 9, subject_id: 7 })
    const store = await storeWith(7)

    await store.removeCollaboration({ direction: 'shotBy', otherPersonId: 9 })

    expect(mockedRemove).toHaveBeenCalledWith(9, 7)
  })

  it('never removes the mirror image of what was asked', async () => {
    mockedRemove.mockResolvedValue({ photographer_id: 7, subject_id: 9 })
    const store = await storeWith(7)

    await store.removeCollaboration({ direction: 'shot', otherPersonId: 9 })

    expect(mockedRemove).not.toHaveBeenCalledWith(9, 7)
  })

  it('re-reads the detail afterwards', async () => {
    mockedRemove.mockResolvedValue({ photographer_id: 7, subject_id: 9 })
    const store = await storeWith(7)
    const before = mockedDetail.mock.calls.length

    await store.removeCollaboration({ direction: 'shot', otherPersonId: 9 })

    expect(mockedDetail.mock.calls.length).toBeGreaterThan(before)
  })

  it('cannot be submitted twice', async () => {
    const pending = deferred<{ photographer_id: number; subject_id: number }>()
    mockedRemove.mockReturnValue(pending.promise)
    const store = await storeWith(7)

    const first = store.removeCollaboration({ direction: 'shot', otherPersonId: 9 })
    await drain()
    await store.removeCollaboration({ direction: 'shot', otherPersonId: 9 })

    expect(mockedRemove).toHaveBeenCalledTimes(1)

    pending.settle({ photographer_id: 7, subject_id: 9 })
    await first
  })
})
