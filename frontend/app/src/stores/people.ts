import { defineStore } from 'pinia'
import { computed, ref } from 'vue'

import { ApiError } from '@/api/client'
import {
  addCollaboration as apiAddCollaboration,
  attachAccountByLink as apiAttachAccountByLink,
  attachAccount as apiAttachAccount,
  createPerson as apiCreatePerson,
  deletePerson as apiDeletePerson,
  detachAccount as apiDetachAccount,
  getPersonDetail,
  listPeople,
  removeCollaboration as apiRemoveCollaboration,
  searchAccounts as apiSearchAccounts,
  updatePerson as apiUpdatePerson,
} from '@/api/people'
import { resolveResource } from '@/api/resolve'
import type {
  AccountSearchResult,
  AttachAccountPayload,
  CreatePersonPayload,
  PersonAccount,
  PersonDetail,
  PersonRole,
  PersonSummaryItem,
  UpdatePersonFields,
} from '@/types/person'

/**
 * Which way round a collaboration goes, said from the current person's side.
 *
 * `shot` - they held the camera. `shotBy` - they were in front of it.
 */
export interface CollaborationRequest {
  direction: 'shot' | 'shotBy'
  otherPersonId: number
  note?: string
}

/**
 * The manual identity layer: which accounts belong to the same real person.
 *
 * Kept apart from the creators store because the two hold different kinds of
 * fact. That one mixes local history with what the platform says right now and
 * is entirely re-read; this one is written by hand and changes only when
 * somebody changes it - which is also why every write here re-reads rather than
 * patching the list optimistically. The database decides what a person looks
 * like: a directory name, for instance, arrives with the first main account
 * rather than from anything this screen sends.
 */
export const usePeopleStore = defineStore('people', () => {
  const people = ref<PersonSummaryItem[]>([])
  const peopleLoading = ref(false)
  const peopleError = ref<string | null>(null)
  const hasLoadedPeople = ref(false)

  const selectedPersonId = ref<number | null>(null)
  const selectedDetail = ref<PersonDetail | null>(null)
  const detailLoading = ref(false)
  const detailError = ref<string | null>(null)

  //
  // One writer at a time. These are not reads: a second click does not cost an
  // extra request, it creates a second person or moves an account twice.
  //
  const mutating = ref(false)
  const mutationError = ref<string | null>(null)

  //
  // Which person the panel is about. Bumped by every selection, so a detail for
  // somebody the user has clicked away from is dropped rather than shown under
  // the new name.
  //
  let detailGeneration = 0

  //
  // Searching known accounts, so one can be put under a person.
  //
  const accountSearchKeyword = ref('')
  const accountSearchResults = ref<AccountSearchResult[]>([])
  const searching = ref(false)
  const searchError = ref<string | null>(null)
  let searchGeneration = 0

  //
  // Which paste the link attachment is working from. A write, so a stale answer
  // here would not merely display the wrong thing - it would attach the wrong
  // account to a person.
  //
  let linkGeneration = 0

  //
  // Which way round a collaboration goes, from the current person's point of
  // view. Named rather than passed as two ids so a caller cannot quietly swap
  // them: "filmed" and "was filmed by" are different facts, and recording the
  // wrong one is silent - the relation still exists, just backwards.
  //
  const selectedPerson = computed(
    () => people.value.find((one) => one.person_id === selectedPersonId.value) ?? null,
  )

  /**
   * Turn "the current person filmed / was filmed by somebody" into the two ids
   * the endpoint takes, in the order it takes them.
   *
   * One place decides this, and both adding and removing go through it: the two
   * getting out of step would mean a relation that can be created and then not
   * deleted, because the delete asks about the mirror image.
   */
  function directedIds(
    currentPersonId: number,
    request: CollaborationRequest,
  ): { photographer_id: number; subject_id: number } {
    return request.direction === 'shot'
      ? { photographer_id: currentPersonId, subject_id: request.otherPersonId }
      : { photographer_id: request.otherPersonId, subject_id: currentPersonId }
  }

  function describeFailure(caught: unknown, fallback: string): string {
    return caught instanceof ApiError ? caught.message || fallback : fallback
  }

  /**
   * The account already holding `main` for this person, unless it is the very
   * one being attached.
   *
   * A person may have only one. Nothing in the database says so - the role
   * column takes any string and no constraint counts them - but the folder a
   * person's downloads land in is resolved by joining on `role = 'main'` and
   * taking `LIMIT 1` with no ordering, while the query that copies the main
   * folder onto the sibling accounts deliberately skips main rows. Two mains
   * therefore means two folders and no fixed answer about which one an alt
   * account downloads into.
   *
   * Enforced here because this is where a second main would be created, and
   * because this phase does not touch the backend. It is a guard, not a
   * constraint: it holds for this interface, not for the database.
   */
  function conflictingMain(
    personId: number,
    ownerUserId: string | null,
  ): PersonAccount | 'unverifiable' | null {
    if (selectedPersonId.value !== personId || selectedDetail.value === null) {
      //
      // No accounts to read - a different person, or a detail still in flight.
      // Refused rather than allowed: the two mistakes are not symmetric. A
      // wrong refusal is undone by clicking again once the detail lands; a
      // wrong acceptance leaves two mains behind, and which folder the person's
      // other accounts download into then depends on which row the database
      // happens to return first.
      //
      return 'unverifiable'
    }
    const existing = selectedDetail.value.accounts.find((one) => one.role === 'main')
    if (existing === undefined) {
      return null
    }
    if (ownerUserId !== null && existing.owner_user_id === ownerUserId) {
      //
      // The same account being re-confirmed, not a second one. Refusing it
      // would make the current state unreachable.
      //
      return null
    }
    return existing
  }

  function mainConflictMessage(clash: PersonAccount | 'unverifiable'): string {
    if (clash === 'unverifiable') {
      return '尚未读取到该人物详情，暂时无法确认是否已有主号，请稍后重试。'
    }
    return `该人物已有主号 ${clash.nickname ?? clash.owner_user_id}。请先解除或调整现有主号，再设置新的主号。`
  }

  async function loadPeople(): Promise<void> {
    peopleLoading.value = true
    try {
      const answer = await listPeople()
      people.value = answer
      hasLoadedPeople.value = true
      peopleError.value = null

      if (
        selectedPersonId.value !== null &&
        !answer.some((one) => one.person_id === selectedPersonId.value)
      ) {
        //
        // The selected person is gone - deleted here or elsewhere. The panel
        // must not keep describing a record the list no longer has.
        //
        selectedPersonId.value = null
        selectedDetail.value = null
      }
    } catch (caught) {
      //
      // Whatever was last read stays. A failed read says nothing about how many
      // people there are.
      //
      peopleError.value = describeFailure(caught, '暂时无法读取人物列表')
    } finally {
      peopleLoading.value = false
    }
  }

  async function loadDetail(personId: number): Promise<void> {
    const mine = ++detailGeneration
    detailLoading.value = true
    try {
      const answer = await getPersonDetail(personId)
      if (mine !== detailGeneration) {
        return
      }
      selectedDetail.value = answer
      detailError.value = null
    } catch (caught) {
      if (mine !== detailGeneration) {
        return
      }
      detailError.value = describeFailure(caught, '暂时无法读取人物详情')
    } finally {
      if (mine === detailGeneration) {
        detailLoading.value = false
      }
    }
  }

  async function selectPerson(personId: number): Promise<void> {
    selectedPersonId.value = personId
    selectedDetail.value = null
    detailError.value = null
    await loadDetail(personId)
  }

  /** Re-read the list and, if one is open, the person on screen. */
  async function refreshAll(): Promise<void> {
    await loadPeople()
    if (selectedPersonId.value !== null) {
      await loadDetail(selectedPersonId.value)
    }
  }

  return {
    people,
    peopleLoading,
    peopleError,
    hasLoadedPeople,
    selectedPersonId,
    selectedPerson,
    selectedDetail,
    detailLoading,
    detailError,
    mutating,
    mutationError,
    loadPeople,
    loadDetail,
    selectPerson,
    refreshAll,

    clearSelection(): void {
      detailGeneration += 1
      selectedPersonId.value = null
      selectedDetail.value = null
      detailError.value = null
    },

    accountSearchKeyword,
    accountSearchResults,
    searching,
    searchError,

    async searchAccounts(keyword: string): Promise<void> {
      const trimmed = keyword.trim()
      accountSearchKeyword.value = trimmed
      if (!trimmed) {
        accountSearchResults.value = []
        return
      }
      const mine = ++searchGeneration
      searching.value = true
      try {
        const answer = await apiSearchAccounts(trimmed)
        if (mine !== searchGeneration) {
          return
        }
        accountSearchResults.value = answer
        searchError.value = null
      } catch (caught) {
        if (mine !== searchGeneration) {
          return
        }
        searchError.value = describeFailure(caught, '搜索账号失败，请稍后重试')
      } finally {
        if (mine === searchGeneration) {
          searching.value = false
        }
      }
    },

    /**
     * Which person an account would be taken *from*, or null when nothing is
     * being taken.
     *
     * The backend upserts, so attaching an account that already belongs to
     * somebody else moves it rather than copying it. The interface has to say
     * that out loud before doing it; the api will not ask.
     */
    movesAccountFrom(candidate: AccountSearchResult, targetPersonId: number): number | null {
      if (candidate.person_id === null || candidate.person_id === targetPersonId) {
        return null
      }
      return candidate.person_id
    },

    /** Re-read everything that shows an attachment, so none of it goes stale. */
    async refreshAttachments(): Promise<void> {
      await refreshAll()
      if (accountSearchKeyword.value) {
        const keyword = accountSearchKeyword.value
        const mine = ++searchGeneration
        try {
          const answer = await apiSearchAccounts(keyword)
          if (mine === searchGeneration) {
            accountSearchResults.value = answer
          }
        } catch {
          //
          // The attachment itself succeeded; a stale search list is a much
          // smaller problem than reporting the write as failed.
          //
        }
      }
    },

    async attachAccount(payload: AttachAccountPayload): Promise<void> {
      if (mutating.value) {
        return
      }
      if (payload.role === 'main') {
        const clash = conflictingMain(payload.person_id, payload.owner_user_id)
        if (clash !== null) {
          //
          // Refused before anything is sent, so there is no window in which the
          // database holds two mains. Deliberately not "demote the old one and
          // promote this one": that is two writes with no transaction between
          // them, and a failure after the first leaves the person with none.
          //
          mutationError.value = mainConflictMessage(clash)
          return
        }
      }
      mutating.value = true
      mutationError.value = null
      try {
        await apiAttachAccount(payload)
        await this.refreshAttachments()
      } catch (caught) {
        mutationError.value = describeFailure(caught, '归并账号失败，请稍后重试')
      } finally {
        mutating.value = false
      }
    },

    async detachAccount(ownerUserId: string): Promise<void> {
      if (mutating.value) {
        return
      }
      mutating.value = true
      mutationError.value = null
      try {
        await apiDetachAccount(ownerUserId)
        await this.refreshAttachments()
      } catch (caught) {
        mutationError.value = describeFailure(caught, '解除归并失败，请稍后重试')
      } finally {
        mutating.value = false
      }
    },

    /**
     * Attach whichever account a pasted link belongs to.
     *
     * Resolved first, always. The person endpoint follows a link itself to find
     * the owner; handing it an already-resolved url means the short link was
     * followed once, by the resolver, under its host allow list and hop limit -
     * rather than a second time by an older path that never had those checks.
     *
     * No particular resource type is required: the endpoint identifies the
     * account behind a profile, a post or a live room alike.
     */
    async attachAccountByLink(
      rawInput: string,
      personId: number,
      role: PersonRole,
    ): Promise<void> {
      if (mutating.value) {
        return
      }
      if (role === 'main') {
        //
        // Which account is behind the link is not known until the person
        // endpoint reads it, so an existing main cannot be ruled out as "the
        // same one". Refused rather than resolved and hoped about - and refused
        // before the resolve, so a link that cannot be attached is never
        // followed at all.
        //
        const clash = conflictingMain(personId, null)
        if (clash !== null) {
          mutationError.value = mainConflictMessage(clash)
          return
        }
      }
      const mine = ++linkGeneration
      mutating.value = true
      mutationError.value = null
      try {
        const resolution = await resolveResource(rawInput)
        if (mine !== linkGeneration) {
          //
          // A later paste took over. Attaching this one would write the wrong
          // account against the person.
          //
          return
        }
        await apiAttachAccountByLink({
          url: resolution.resolved_url,
          person_id: personId,
          role,
        })
        if (mine !== linkGeneration) {
          return
        }
        await this.refreshAttachments()
      } catch (caught) {
        if (mine !== linkGeneration) {
          return
        }
        mutationError.value = describeFailure(caught, '按链接归并账号失败，请稍后重试')
      } finally {
        if (mine === linkGeneration) {
          mutating.value = false
        }
      }
    },

    /** Everybody except the person on screen; nobody collaborates with themselves. */
    collaborationCandidates: computed(() =>
      people.value.filter((one) => one.person_id !== selectedPersonId.value),
    ),

    async addCollaboration(request: CollaborationRequest): Promise<void> {
      const current = selectedPersonId.value
      if (mutating.value || current === null || request.otherPersonId === current) {
        return
      }
      mutating.value = true
      mutationError.value = null
      try {
        const note = (request.note ?? '').trim()
        await apiAddCollaboration({
          ...directedIds(current, request),
          //
          // Omitted rather than sent empty: the backend turns a blank note into
          // null anyway, and sending one would record an edit nobody made.
          //
          ...(note ? { note } : {}),
        })
        await refreshAll()
      } catch (caught) {
        mutationError.value = describeFailure(caught, '记录合作关系失败，请稍后重试')
      } finally {
        mutating.value = false
      }
    },

    async removeCollaboration(request: CollaborationRequest): Promise<void> {
      const current = selectedPersonId.value
      if (mutating.value || current === null) {
        return
      }
      mutating.value = true
      mutationError.value = null
      try {
        const { photographer_id, subject_id } = directedIds(current, request)
        await apiRemoveCollaboration(photographer_id, subject_id)
        await refreshAll()
      } catch (caught) {
        mutationError.value = describeFailure(caught, '解除合作关系失败，请稍后重试')
      } finally {
        mutating.value = false
      }
    },

    async createPerson(payload: CreatePersonPayload): Promise<void> {
      if (mutating.value) {
        return
      }
      mutating.value = true
      mutationError.value = null
      try {
        const created = await apiCreatePerson(payload)
        await loadPeople()
        //
        // Selected by the id the server answered with, not by matching on the
        // name that was typed: two people may legitimately share one.
        //
        selectedPersonId.value = created.person_id
        await loadDetail(created.person_id)
      } catch (caught) {
        mutationError.value = describeFailure(caught, '创建人物失败，请稍后重试')
      } finally {
        mutating.value = false
      }
    },

    async updatePerson(personId: number, fields: UpdatePersonFields): Promise<void> {
      if (mutating.value || Object.keys(fields).length === 0) {
        //
        // Nothing changed. Sending an empty patch would be a write with no
        // meaning, and the backend would rightly refuse it.
        //
        return
      }
      mutating.value = true
      mutationError.value = null
      try {
        await apiUpdatePerson(personId, fields)
        await refreshAll()
      } catch (caught) {
        mutationError.value = describeFailure(caught, '保存人物失败，请稍后重试')
      } finally {
        mutating.value = false
      }
    },

    async deletePerson(personId: number): Promise<void> {
      if (mutating.value) {
        return
      }
      mutating.value = true
      mutationError.value = null
      try {
        await apiDeletePerson(personId)
        detailGeneration += 1
        selectedPersonId.value = null
        selectedDetail.value = null
        await loadPeople()
      } catch (caught) {
        //
        // Nothing was removed, so nothing here changes either - the person the
        // user was looking at is still there.
        //
        mutationError.value = describeFailure(caught, '删除人物失败，请稍后重试')
      } finally {
        mutating.value = false
      }
    },
  }
})
