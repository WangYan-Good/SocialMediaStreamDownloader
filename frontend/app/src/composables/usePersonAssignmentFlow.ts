import { computed, ref, watch } from 'vue'

import { ApiError } from '@/api/client'
import {
  assignPersonAccount as defaultAssignPersonAccount,
  inspectPersonAssignment as defaultInspectPersonAssignment,
} from '@/api/people'
import { resolveResource as defaultResolveResource } from '@/api/resolve'
import type {
  DemotedRole,
  PersonAssignmentConflict,
  PersonAssignmentRequest,
  PersonAssignmentResult,
  PersonIdentityInspection,
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
  //
  // Resolved, and now asking whether this server already holds the account.
  // Its own phase rather than part of `resolving`, because "we have not asked
  // yet" and "we asked and it is new" look identical on screen and lead to
  // opposite offers - so a late answer has to be distinguishable from no
  // answer.
  //
  | 'inspecting'
  | 'resolved'
  //
  // Somebody already holds this account. Not a form and not a success: nothing
  // was written, and there is nothing here to add.
  //
  | 'existing'
  | 'submitting'
  | 'conflict'
  | 'success'
  | 'failed'

export interface PersonAssignmentApi {
  resolveResource: (input: string) => Promise<ResolvedResource>
  //
  // Runs straight after the resolve, on its receipt. Deliberately not a second
  // button: a check performed only by the users who thought to look for it is
  // not a check.
  //
  inspectPersonAssignment: (resolveId: string) => Promise<PersonIdentityInspection>
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
    inspectPersonAssignment:
      options.api?.inspectPersonAssignment ?? defaultInspectPersonAssignment,
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

  //
  // What the server already knows about the account this receipt names, or
  // `null` when nothing has been asked or the answer did not arrive.
  //
  // Held apart from `resolution` because the two say different things: a
  // resolution is what the *link* is, and survives being unable to reach the
  // person tables at all. This is who the account turns out to *be*.
  //
  const inspection = ref<PersonIdentityInspection | null>(null)
  //
  // Set when the check itself failed, which is not the same as the account
  // being new - the backend answers 503 rather than an empty result for
  // exactly that reason. Shown as a warning beside a form that still works:
  // the assignment refuses a duplicate inside its own transaction either way,
  // so a failed check costs a caution rather than the whole operation.
  //
  const inspectError = ref<string | null>(null)

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
    //
    // The inspection describes the account that receipt named, so it goes when
    // the receipt does. Left behind, it would announce that the link now in
    // the box "already exists" while naming somebody else's person.
    //
    inspection.value = null
    inspectError.value = null
    resolvedFrom.value = null
    resolvingFrom.value = null
    submittedDraft.value = null
    conflict.value = null
    confirmation.value = {}
    result.value = null
    assignmentError.value = null
    refreshWarning.value = null
  }

  /**
   * Put the target back to what it is before anybody has chosen anything.
   *
   * A draft is about one account. `adjustAssignment` in particular fills it in
   * from whichever account was just inspected, so carrying it across a link
   * change would aim a stranger's receipt at a person the user picked for
   * somebody else - and, with the role already set, leave it one click from
   * being written.
   *
   * A fixed-person card returns to its own person rather than to nobody: there
   * is no "create a new person" there to fall back to.
   */
  function clearDraftTarget(): void {
    targetKind.value = fixedPersonId === null ? 'new' : 'existing'
    selectedPersonId.value = fixedPersonId
    role.value = null
    displayName.value = ''
    note.value = ''
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
    if (phase.value === 'resolving' || phase.value === 'inspecting') {
      //
      // Abandon the answer nobody is waiting for any more, rather than holding
      // the button hostage until it arrives.
      //
      // `inspecting` counts, and has to: the receipt has already arrived by
      // then, so without this the generation would never move and a late
      // inspection of link A would land on a screen showing link B - announcing
      // that B already belongs to a person who has never held it.
      //
      resolveGeneration += 1
      resolvingFrom.value = null
    }
    if (resolution.value !== null || phase.value !== 'idle') {
      discardResolution()
      //
      // The target goes with it. The receipt and the person it was going to
      // were chosen together, about one account; keeping the second after
      // throwing away the first is how a new link ends up aimed at the last
      // link's person.
      //
      clearDraftTarget()
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
      phase.value !== 'inspecting' &&
      phase.value !== 'submitting',
  )

  /**
   * Whether the draft describes exactly the attachment already on record.
   *
   * Only ever true after an inspection found one, so it cannot suppress a
   * submission the user has not already been shown the result of.
   *
   * The backend is idempotent about this - it refreshes the identity and
   * returns - so nothing would break by sending it. What would break is the
   * impression: a screen that has just said "this is already added" would then
   * say "submitting…" and "added", which is the exact confusion this step
   * exists to remove.
   */
  const unchangedAssignment = computed(() => {
    const current = inspection.value?.assignment ?? null
    if (current === null) {
      return false
    }
    return (
      targetKind.value === 'existing' &&
      selectedPersonId.value === current.person_id &&
      role.value === current.role
    )
  })

  /**
   * Whether the pasted account is already held by the person this card is
   * fixed to - the detail panel's case, where there is nothing at all to do.
   */
  const heldByFixedPerson = computed(
    () =>
      fixedPersonId !== null &&
      (inspection.value?.assignment?.person_id ?? null) === fixedPersonId,
  )

  const canSubmit = computed(() => {
    if (resolution.value === null || role.value === null) {
      return false
    }
    if (phase.value === 'submitting' || phase.value === 'success') {
      return false
    }
    if (phase.value === 'inspecting' || phase.value === 'existing') {
      //
      // Nothing may be sent while the answer is still coming, and nothing needs
      // sending once it says the account is filed. Reaching the form from there
      // is a deliberate act - see `adjustAssignment`.
      //
      return false
    }
    if (inspectError.value !== null) {
      //
      // The check did not answer, so whether this account is already filed is
      // unknown - and "unknown" must not be offered as "new". During a person
      // lookup outage every pasted link would otherwise read as a fresh
      // account with 创建新人物 preselected, which is precisely the screen
      // this step exists to stop showing.
      //
      // Nothing corrupt could be written either way - the assignment
      // transaction refuses a genuine duplicate on its own - but the page must
      // not invite the attempt. Resolving again re-runs the check, so the way
      // forward is one click rather than a re-paste.
      //
      return false
    }
    if (unchangedAssignment.value) {
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
      phase.value = 'inspecting'
      //
      // One click, two questions. Asking who the account is only when the user
      // presses a second button would mean the duplicate is caught by whoever
      // thought to look for it - which is nobody, because the whole reason they
      // are pasting is that they do not remember adding it.
      //
      await inspectResolved(answer.resolve_id, submitted, generation)
    } catch (caught) {
      if (disposed || generation !== resolveGeneration) {
        return
      }
      resolvingFrom.value = null
      resolveError.value = messageOf(caught, '解析失败，请稍后重试')
      phase.value = 'idle'
    }
  }

  /**
   * Ask whether this server already holds the account the receipt names.
   *
   * Never throws. It runs inside `resolve`'s own `try`, and letting a failed
   * check surface there would report "解析失败" for a link that resolved
   * perfectly well - throwing away a receipt that is still good.
   *
   * Guarded by the *resolve* generation rather than one of its own. This is the
   * second half of one question, so there is one answer to "which question is
   * current"; a second counter would be a second opinion, and the two would
   * disagree the first time a user edited the box mid-check.
   */
  async function inspectResolved(
    resolveId: string,
    submitted: string,
    generation: number,
  ): Promise<void> {
    try {
      const found = await api.inspectPersonAssignment(resolveId)
      if (disposed || generation !== resolveGeneration) {
        return
      }
      if (rawInput.value.trim() !== submitted.trim()) {
        return
      }
      inspection.value = found
      inspectError.value = null
      //
      // The one decision this makes. An account nobody holds goes to the
      // ordinary form - including one this server has merely downloaded before,
      // which is not a duplicate and still needs filing. An account somebody
      // holds needs no form at all.
      //
      phase.value = found.assignment === null ? 'resolved' : 'existing'
    } catch (caught) {
      if (disposed || generation !== resolveGeneration) {
        return
      }
      if (rawInput.value.trim() !== submitted.trim()) {
        return
      }
      //
      // Left null rather than filled in as "new". "We could not ask" and "this
      // account is new" lead to opposite actions, and the second one invites a
      // duplicate person - so the page says it could not check and lets the
      // transaction stay the thing that refuses.
      //
      inspection.value = null
      inspectError.value = messageOf(caught, '暂时无法确认该账号的归属，请稍后重试')
      phase.value = 'resolved'
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

  /**
   * Open the form on an account somebody already holds.
   *
   * The escape hatch, and deliberately not the default. Pasting a filed account
   * is usually a duplicate, but sometimes it is a spare being promoted to main
   * or an account being moved to the right person - so the form is reachable in
   * one click rather than unreachable.
   *
   * It starts from where the account already is, so the first thing on screen is
   * the truth and any change is one the user chose. Starting from "create a new
   * person" would put the duplicate back one click away, which is where it was
   * before any of this.
   *
   * Nothing is agreed to here. A move still needs `allow_move` and a main still
   * needs `replace_main`, both after their own refusal: knowing who holds an
   * account is not the same as consenting to take it from them.
   */
  function adjustAssignment(): void {
    const current = inspection.value?.assignment ?? null
    if (current === null) {
      return
    }
    targetKind.value = 'existing'
    //
    // The fixed person wins, where there is one. This card is open inside their
    // panel, so "adjust" there means "put it under this person" - the account's
    // current holder is who it would be taken *from*.
    //
    selectedPersonId.value = fixedPersonId ?? current.person_id
    role.value = current.role
    conflict.value = null
    confirmation.value = {}
    assignmentError.value = null
    phase.value = 'resolved'
  }

  /** Go back to reading the existing assignment, having changed nothing. */
  function cancelAdjustment(): void {
    if ((inspection.value?.assignment ?? null) === null) {
      return
    }
    conflict.value = null
    confirmation.value = {}
    assignmentError.value = null
    phase.value = 'existing'
  }

  return {
    rawInput,
    resolution,
    inspection,
    inspectError,
    unchangedAssignment,
    heldByFixedPerson,
    adjustAssignment,
    cancelAdjustment,
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
