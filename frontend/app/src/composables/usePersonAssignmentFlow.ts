import { computed, ref, watch } from 'vue'

import { ApiError } from '@/api/client'
import { assignPersonAccount as defaultAssignPersonAccount } from '@/api/people'
import { resolveResource as defaultResolveResource } from '@/api/resolve'
import type {
  DemotedRole,
  PersonAssignmentConflict,
  PersonAssignmentRequest,
  PersonAssignmentResult,
  PersonRole,
} from '@/types/person'
import type { ResolvedResource } from '@/types/resolution'

//
// Adding an account, from a pasted link to a person holding it.
//
// Kept out of the people store on purpose. That store holds facts the server
// owns - who exists, what each person holds - and re-reads them after every
// write. This holds one unfinished intention: some text, a receipt, a target
// nobody has confirmed yet. Those have opposite lifetimes, and folding the
// second into the first is how a store becomes a state machine nobody can read.
//

// >>============================= the request =============================>>

export interface AssignmentDraft {
  resolveId: string
  targetKind: 'new' | 'existing'
  selectedPersonId: number | null
  displayName: string
  note: string
  role: PersonRole
  //
  // Both absent unless the user has been shown a conflict and answered it.
  // Neither has a default, and neither may be inferred: a move takes an account
  // away from somebody, and a replacement demotes a main to a role the user has
  // to pick.
  //
  allowMove?: true
  demoteMainTo?: DemotedRole
}

/**
 * Turn the draft on screen into exactly what the endpoint accepts.
 *
 * A pure function, and separate from the flow, because the wire shape is where
 * the receipt guarantee either holds or quietly stops holding - and that is
 * worth being able to assert without mounting anything.
 *
 * Blank optional fields are omitted rather than sent empty. The backend reads
 * "absent" as "you decide" and a blank string as a field error, so sending
 * `display_name: ''` would turn "I did not name them" into a refusal.
 */
export function buildPersonAssignmentRequest(
  draft: AssignmentDraft,
): PersonAssignmentRequest {
  const displayName = draft.displayName.trim()
  const note = draft.note.trim()

  const target: PersonAssignmentRequest['target'] =
    draft.targetKind === 'existing'
      ? //
        // By id alone. A name or a note here would be a rename happening as a
        // side effect of attaching an account, which is not what was asked and
        // not what the user would see; the backend refuses either field.
        //
        { kind: 'existing', person_id: draft.selectedPersonId as number }
      : {
          kind: 'new',
          ...(displayName ? { display_name: displayName } : {}),
          ...(note ? { note } : {}),
        }

  return {
    resolve_id: draft.resolveId,
    target,
    role: draft.role,
    ...(draft.allowMove ? { allow_move: true as const } : {}),
    ...(draft.demoteMainTo ? { replace_main: { demote_to: draft.demoteMainTo } } : {}),
  }
}

// >>============================= the refusals =============================>>

function personRef(value: unknown): { person_id: number; display_name: string | null } | null {
  if (typeof value !== 'object' || value === null) {
    return null
  }
  const record = value as Record<string, unknown>
  if (typeof record.person_id !== 'number') {
    return null
  }
  const name = record.display_name
  return {
    person_id: record.person_id,
    //
    // A person always has a name, but a malformed one is not worth crashing
    // over: the id is what the page acts on.
    //
    display_name: typeof name === 'string' ? name : null,
  }
}

function accountRef(value: unknown): { owner_user_id: string; nickname: string | null } | null {
  if (typeof value !== 'object' || value === null) {
    return null
  }
  const record = value as Record<string, unknown>
  if (typeof record.owner_user_id !== 'string' || !record.owner_user_id) {
    return null
  }
  const nickname = record.nickname
  return {
    owner_user_id: record.owner_user_id,
    //
    // Genuinely absent for an account nobody has downloaded. A real answer, not
    // a malformed one - the id is shown instead.
    //
    nickname: typeof nickname === 'string' ? nickname : null,
  }
}

/**
 * Read a 409 into something the page can offer a next step for, or `null`.
 *
 * Three of these conflicts are 409 and their remedies are different: one needs
 * `allow_move`, one needs `replace_main`, and one has no confirmation at all
 * because what it prevents is not recoverable. Telling them apart by matching
 * the Chinese message would break the first time somebody improved the wording.
 *
 * `null` for anything whose details did not arrive in the expected shape. The
 * caller then shows the message alone and offers nothing to confirm - because
 * there is nothing to confirm *against*, and a button that sends `allow_move`
 * on the strength of a malformed body is worse than no button.
 */
export function readAssignmentConflict(caught: unknown): PersonAssignmentConflict | null {
  if (!(caught instanceof ApiError) || caught.kind !== 'backend' || caught.status !== 409) {
    return null
  }
  const details = caught.details ?? {}

  if (caught.backendKind === 'assignment_raced') {
    //
    // Carries nothing, and needs nothing: the account changed hands mid-request
    // and the answer is to look again, not to confirm anything.
    //
    return { kind: 'assignment_raced' }
  }

  if (caught.backendKind === 'account_already_attached') {
    const currentPerson = personRef(details.current_person)
    return currentPerson === null
      ? null
      : { kind: 'account_already_attached', current_person: currentPerson }
  }

  if (caught.backendKind === 'main_account_conflict') {
    const currentMain = accountRef(details.current_main)
    return currentMain === null
      ? null
      : { kind: 'main_account_conflict', current_main: currentMain }
  }

  if (caught.backendKind === 'last_main_removal_conflict') {
    const sourcePerson = personRef(details.source_person)
    const currentMain = accountRef(details.current_main)
    return sourcePerson === null || currentMain === null
      ? null
      : {
          kind: 'last_main_removal_conflict',
          source_person: sourcePerson,
          current_main: currentMain,
        }
  }

  return null
}

// >>============================= the flow =============================>>

export type PersonAssignmentPhase =
  | 'idle'
  | 'resolving'
  | 'resolved'
  | 'submitting'
  | 'conflict'
  | 'success'
  | 'failed'

export interface PersonAssignmentApi {
  resolveResource: (input: string) => Promise<ResolvedResource>
  assignPersonAccount: (request: PersonAssignmentRequest) => Promise<PersonAssignmentResult>
}

export interface PersonAssignmentFlowOptions {
  api?: Partial<PersonAssignmentApi>
  /**
   * Re-read whatever the write may have changed.
   *
   * Called with the result after a successful assignment, and with `null` after
   * a race - where nothing was written here but something was written by
   * somebody else, so what is on screen is out of date either way.
   */
  onPeopleChanged?: (result: PersonAssignmentResult | null) => Promise<void>
  /**
   * A person chosen by context rather than by the user.
   *
   * The detail panel's own paste box works this way: the target is whichever
   * person is open, so there is no "create a new one" to offer.
   */
  fixedPersonId?: number
}

function messageOf(caught: unknown, fallback: string): string {
  return caught instanceof ApiError && caught.message ? caught.message : fallback
}

/**
 * Paste a link, choose who it belongs to and in what role, once.
 *
 * The receipt is the whole design. `/api/resolve` decides what a link names,
 * and everything after that refers to it by id - so this file never sends an
 * account id, a nickname or a url, and never re-resolves on the user's behalf.
 * The two places that would have been tempting are the conflict confirmations,
 * and both deliberately re-send the *same* receipt: asking the platform again
 * could legitimately name a different resource, minutes after the user looked
 * at the first one.
 */
export function usePersonAssignmentFlow(options: PersonAssignmentFlowOptions = {}) {
  const api: PersonAssignmentApi = {
    resolveResource: options.api?.resolveResource ?? defaultResolveResource,
    assignPersonAccount: options.api?.assignPersonAccount ?? defaultAssignPersonAccount,
  }
  const fixedPersonId = options.fixedPersonId ?? null

  const rawInput = ref('')
  const resolution = ref<ResolvedResource | null>(null)
  const targetKind = ref<'new' | 'existing'>(fixedPersonId === null ? 'new' : 'existing')
  const selectedPersonId = ref<number | null>(fixedPersonId)
  const displayName = ref('')
  const note = ref('')
  //
  // Never defaulted. Which account is somebody's main decides the folder every
  // account of theirs files under, so it is a decision the user makes rather
  // than one this screen makes quietly on their behalf.
  //
  const role = ref<PersonRole | null>(null)

  const phase = ref<PersonAssignmentPhase>('idle')
  const resolveError = ref<string | null>(null)
  const assignmentError = ref<string | null>(null)
  const refreshWarning = ref<string | null>(null)
  const result = ref<PersonAssignmentResult | null>(null)
  const conflict = ref<PersonAssignmentConflict | null>(null)

  //
  // What the user has explicitly agreed to about *this* attempt. Held apart
  // from the draft because it is answer-shaped rather than intention-shaped:
  // it exists only between a conflict and the retry that answers it, and it is
  // dropped the moment anything about the request changes underneath it.
  //
  const confirmation = ref<{ allowMove?: true; demoteMainTo?: DemotedRole }>({})

  //
  // Which question each half of the flow is waiting on. A late answer to an
  // abandoned one is dropped rather than written in - for a resolve that would
  // show one link's identity beside another link's text, and for a submission
  // it would report somebody else's account as the one just added.
  //
  let resolveGeneration = 0
  let submitGeneration = 0
  let disposed = false

  //
  // The text the current receipt was produced from, so a later edit can be
  // recognised as one.
  //
  const resolvedFrom = ref<string | null>(null)
  //
  // And the text a resolve in flight was started from.
  //
  // Needed because the watcher below runs a tick after the box changes, which
  // is *after* a resolve launched from that same change has already started.
  // Without something to compare against, the edit that began a resolve would
  // be read as an edit abandoning it, and the answer would be dropped as stale
  // the moment it arrived.
  //
  const resolvingFrom = ref<string | null>(null)
  //
  // And the draft the in-flight submission was built from, for the same reason:
  // the watcher below runs a tick after a field changes, which is after a
  // submission launched from that same change has already started. Compared
  // against, so the edit that *began* a submission is not read as one
  // abandoning it.
  //
  const submittedDraft = ref<string | null>(null)

  function draftKey(): string {
    return JSON.stringify([
      targetKind.value,
      selectedPersonId.value,
      role.value,
      displayName.value.trim(),
      note.value.trim(),
    ])
  }

  function discardResolution(): void {
    resolution.value = null
    resolvedFrom.value = null
    resolvingFrom.value = null
    submittedDraft.value = null
    conflict.value = null
    confirmation.value = {}
    result.value = null
    assignmentError.value = null
    refreshWarning.value = null
  }

  watch(rawInput, () => {
    //
    // Editing the box invalidates the receipt, immediately.
    //
    // Without this: paste A, resolve A, edit to B, press confirm - and an
    // account belonging to A is attached while the screen shows B. The server
    // would be right to accept it, because the receipt really was A's; the
    // mistake is entirely this screen's, and the user would never see it.
    //
    if (phase.value === 'submitting' || phase.value === 'success') {
      //
      // A write is in flight or has already happened. It belongs to the
      // resolution it was made from, whatever the box says now.
      //
      return
    }
    const settled = resolvingFrom.value ?? resolvedFrom.value
    if (settled !== null && rawInput.value.trim() === settled.trim()) {
      //
      // The same text, arriving late. Nothing has been abandoned.
      //
      return
    }
    if (phase.value === 'resolving') {
      //
      // Abandon the answer nobody is waiting for any more, rather than holding
      // the button hostage until it arrives.
      //
      resolveGeneration += 1
      resolvingFrom.value = null
    }
    if (resolution.value !== null || phase.value !== 'idle') {
      discardResolution()
      resolveError.value = null
      phase.value = 'idle'
    }
  })

  //
  // An answer belongs to the request that asked for it.
  //
  // The role and person controls stay usable while a submission is in flight -
  // there is no reason to freeze the form, and the submit button is disabled
  // anyway. But a refusal describes the request that was *sent*: shown against
  // a draft that has moved on since, it explains one thing while the button
  // beneath it would do another. Concretely - submit for person 12, change the
  // picker to 20, and the 409 about 12 arrives with a "confirm move" button
  // that would send `allow_move` for 20. The backend would still check
  // everything, so nothing invalid gets written; what is wrong is that the user
  // agreed to a different sentence than the one carried out.
  //
  // So changing any part of the draft abandons whatever was asked about the
  // previous one. The write itself is not cancellable - it may well have
  // happened - but the caller is still told to re-read the people, because it
  // may have.
  //
  watch([targetKind, selectedPersonId, role, displayName, note], () => {
    if (phase.value !== 'submitting' && phase.value !== 'conflict') {
      return
    }
    if (submittedDraft.value === null || draftKey() === submittedDraft.value) {
      //
      // The same draft, arriving late. Nothing has been abandoned.
      //
      return
    }
    submitGeneration += 1
    submittedDraft.value = null
    conflict.value = null
    confirmation.value = {}
    assignmentError.value = null
    phase.value = resolution.value === null ? 'idle' : 'resolved'
    void refreshPeople(null)
  })

  watch(targetKind, (next) => {
    //
    // The receipt and the role survive the switch: they are facts about the
    // link and about the account, and neither changed. What does not survive is
    // whatever belonged only to the shape being left behind.
    //
    conflict.value = null
    confirmation.value = {}
    assignmentError.value = null
    if (next === 'existing') {
      displayName.value = ''
      note.value = ''
      if (fixedPersonId !== null) {
        selectedPersonId.value = fixedPersonId
      }
    } else {
      selectedPersonId.value = null
    }
  })

  const canResolve = computed(
    () =>
      rawInput.value.trim().length > 0 &&
      phase.value !== 'resolving' &&
      phase.value !== 'submitting',
  )

  const canSubmit = computed(() => {
    if (resolution.value === null || role.value === null) {
      return false
    }
    if (phase.value === 'submitting' || phase.value === 'success') {
      return false
    }
    return targetKind.value === 'new' || selectedPersonId.value !== null
  })

  async function resolve(): Promise<void> {
    if (!canResolve.value) {
      return
    }
    const submitted = rawInput.value
    const generation = ++resolveGeneration
    phase.value = 'resolving'
    resolveError.value = null
    discardResolution()
    resolvingFrom.value = submitted

    try {
      //
      // Sent exactly as typed. Pulling the link out of a share sentence is the
      // server's job, and a regex copied into the browser would be a second
      // opinion that eventually disagrees with it.
      //
      const answer = await api.resolveResource(submitted)
      if (disposed || generation !== resolveGeneration) {
        return
      }
      if (rawInput.value.trim() !== submitted.trim()) {
        //
        // The box changed without another resolve being launched. This answer
        // is about something the screen is no longer asking about.
        //
        return
      }
      resolution.value = answer
      resolvedFrom.value = submitted
      resolvingFrom.value = null
      phase.value = 'resolved'
    } catch (caught) {
      if (disposed || generation !== resolveGeneration) {
        return
      }
      resolvingFrom.value = null
      resolveError.value = messageOf(caught, '解析失败，请稍后重试')
      phase.value = 'idle'
    }
  }

  async function refreshPeople(assignment: PersonAssignmentResult | null): Promise<void> {
    if (!options.onPeopleChanged) {
      return
    }
    try {
      await options.onPeopleChanged(assignment)
    } catch {
      //
      // The write itself succeeded. Reporting it as a failure would send the
      // user back to do it again, and the second attempt would hit a conflict
      // caused by the first one having worked.
      //
      if (!disposed) {
        refreshWarning.value = '账号已添加，但人物列表暂时无法刷新，请稍后重试。'
      }
    }
  }

  async function send(): Promise<void> {
    if (resolution.value === null || role.value === null) {
      return
    }
    const generation = ++submitGeneration
    submittedDraft.value = draftKey()
    phase.value = 'submitting'
    assignmentError.value = null
    refreshWarning.value = null

    const request = buildPersonAssignmentRequest({
      resolveId: resolution.value.resolve_id,
      targetKind: targetKind.value,
      selectedPersonId: selectedPersonId.value,
      displayName: displayName.value,
      note: note.value,
      role: role.value,
      ...confirmation.value,
    })

    try {
      const answer = await api.assignPersonAccount(request)
      if (disposed || generation !== submitGeneration) {
        return
      }
      result.value = answer
      conflict.value = null
      confirmation.value = {}
      submittedDraft.value = null
      phase.value = 'success'
      await refreshPeople(answer)
    } catch (caught) {
      if (disposed || generation !== submitGeneration) {
        return
      }
      await handleRefusal(caught)
    }
  }

  async function handleRefusal(caught: unknown): Promise<void> {
    const named = readAssignmentConflict(caught)

    if (named?.kind === 'assignment_raced') {
      //
      // Somebody else moved this account between the checks and the write.
      // Nothing was written, and every confirmation the user gave was about a
      // state that has since changed - so they are dropped rather than carried
      // into a retry that would be agreeing to something else.
      //
      confirmation.value = {}
      conflict.value = null
      phase.value = 'resolved'
      assignmentError.value = '账号归属在提交过程中发生了变化，请重新确认后再试。'
      await refreshPeople(null)
      return
    }

    if (named !== null) {
      conflict.value = named
      phase.value = 'conflict'
      return
    }

    if (caught instanceof ApiError && caught.backendKind === 'resolution_not_found') {
      //
      // Thrown away rather than quietly resolved again: re-resolving would mean
      // this screen deciding what the user meant, minutes after they asked,
      // which is the one thing the receipt exists to prevent.
      //
      discardResolution()
      phase.value = 'idle'
      assignmentError.value = '解析结果已过期，请重新解析链接。'
      return
    }

    conflict.value = null
    phase.value = 'failed'
    assignmentError.value = messageOf(caught, '添加账号失败，请稍后重试')
  }

  return {
    rawInput,
    resolution,
    targetKind,
    selectedPersonId,
    displayName,
    note,
    role,
    phase,
    resolveError,
    assignmentError,
    refreshWarning,
    result,
    conflict,
    canResolve,
    canSubmit,
    resolve,

    async submit(): Promise<void> {
      //
      // The single guard against a double submission. Not a debounce: a second
      // click does not cost an extra request, it creates a second person or
      // moves an account twice.
      //
      if (!canSubmit.value) {
        return
      }
      await send()
    },

    /** Answer an `account_already_attached` by agreeing to take the account. */
    async confirmMove(): Promise<void> {
      if (conflict.value?.kind !== 'account_already_attached') {
        //
        // Deliberately not a general "force". A stranded-main conflict reaches
        // this same button in the UI and must fall through it: what it prevents
        // is not recoverable, so there is no version of it to agree to.
        //
        return
      }
      confirmation.value = { ...confirmation.value, allowMove: true }
      await send()
    },

    /** Answer a `main_account_conflict` by saying where the old main goes. */
    async confirmReplaceMain(demoteTo: DemotedRole | null): Promise<void> {
      if (conflict.value?.kind !== 'main_account_conflict' || demoteTo === null) {
        //
        // No default. Demoting somebody's main to a role they did not pick is
        // not a detail this screen may decide.
        //
        return
      }
      confirmation.value = { ...confirmation.value, demoteMainTo: demoteTo }
      await send()
    },

    cancelConflict(): void {
      conflict.value = null
      confirmation.value = {}
      assignmentError.value = null
      phase.value = resolution.value === null ? 'idle' : 'resolved'
    },

    reset(): void {
      resolveGeneration += 1
      submitGeneration += 1
      rawInput.value = ''
      discardResolution()
      resolveError.value = null
      role.value = null
      displayName.value = ''
      note.value = ''
      targetKind.value = fixedPersonId === null ? 'new' : 'existing'
      selectedPersonId.value = fixedPersonId
      phase.value = 'idle'
    },

    /** Stop writing into state that is about to be thrown away. */
    dispose(): void {
      disposed = true
      resolveGeneration += 1
      submitGeneration += 1
    },
  }
}
