import { describe, expect, it } from 'vitest'
import { nextTick } from 'vue'

import { ApiError } from '../../src/api/client'
import { usePersonAssignmentFlow } from '../../src/composables/usePersonAssignmentFlow'
import type {
  PersonAssignmentRequest,
  PersonAssignmentResult,
  PersonIdentityInspection,
} from '../../src/types/person'
import type { ResolvedResource } from '../../src/types/resolution'

//
// Noticing a duplicate *before* the form, rather than after the confirm.
//
// The gap this closes: pasting an account added last month used to produce the
// full "create a new person / merge into an existing one / choose a role /
// confirm" sequence, and only the assignment at the end said the account was
// already filed. The obvious reading of that screen was "I must create this
// person again", which is exactly the duplicate the backend then refused.
//
// So resolving now runs an inspection of its own, and what it finds decides
// which of three states the card is in. What it must never do is decide
// anything the server decides: the inspection is a hint, the transaction is
// the authority.
//

const SEC_UID = 'MS4wLjABAAAAGZkW5n1EHZD_TFyQ-QiaISBPemtKFxVVdhLSeoXhh-U'

function ownerResolution(resolveId = 'receipt-1'): ResolvedResource {
  return {
    resolve_id: resolveId,
    platform: 'douyin',
    resource_type: 'owner',
    source_url: 'https://v.douyin.com/abc/',
    resolved_url: `https://www.douyin.com/user/${SEC_UID}`,
    identity: { sec_user_id: SEC_UID },
    expires_in_seconds: 600,
  }
}

/** Never seen. The only state in which creating a person is the right offer. */
function unknownAccount(): PersonIdentityInspection {
  return {
    owner: { owner_user_id: 'acc-9', sec_user_id: SEC_UID, nickname: '程儿' },
    known_account: false,
    assignment: null,
  }
}

/** Downloaded once, never filed. Common, and not a duplicate. */
function knownUnfiled(): PersonIdentityInspection {
  return {
    owner: { owner_user_id: 'acc-9', sec_user_id: SEC_UID, nickname: '程儿' },
    known_account: true,
    assignment: null,
  }
}

/** Already somebody's. Nothing to add. */
function knownFiled(
  overrides: Partial<PersonIdentityInspection['assignment'] & object> = {},
): PersonIdentityInspection {
  return {
    owner: { owner_user_id: 'acc-9', sec_user_id: SEC_UID, nickname: '程儿' },
    known_account: true,
    assignment: { person_id: 12, display_name: '程儿', role: 'main', ...overrides },
  }
}

function assigned(overrides: Partial<PersonAssignmentResult> = {}): PersonAssignmentResult {
  return {
    person_id: 12,
    owner_user_id: 'acc-9',
    role: 'alt',
    created_person: true,
    display_name: '程儿',
    ...overrides,
  }
}

interface Harness {
  resolveCalls: string[]
  inspectCalls: string[]
  assignCalls: PersonAssignmentRequest[]
}

function build(
  options: {
    resolve?: (input: string) => Promise<ResolvedResource>
    inspect?: (resolveId: string) => Promise<PersonIdentityInspection>
    assign?: (request: PersonAssignmentRequest) => Promise<PersonAssignmentResult>
    fixedPersonId?: number
  } = {},
) {
  const harness: Harness = { resolveCalls: [], inspectCalls: [], assignCalls: [] }

  const flow = usePersonAssignmentFlow({
    api: {
      resolveResource: (input: string) => {
        harness.resolveCalls.push(input)
        return options.resolve ? options.resolve(input) : Promise.resolve(ownerResolution())
      },
      inspectPersonAssignment: (resolveId: string) => {
        harness.inspectCalls.push(resolveId)
        return options.inspect
          ? options.inspect(resolveId)
          : Promise.resolve(unknownAccount())
      },
      assignPersonAccount: (request: PersonAssignmentRequest) => {
        harness.assignCalls.push(request)
        return options.assign ? options.assign(request) : Promise.resolve(assigned())
      },
    },
    ...(options.fixedPersonId === undefined ? {} : { fixedPersonId: options.fixedPersonId }),
  })

  return { flow, harness }
}

function deferred<T>() {
  let resolveIt: (value: T) => void = () => {}
  let rejectIt: (reason: unknown) => void = () => {}
  const promise = new Promise<T>((res, rej) => {
    resolveIt = res
    rejectIt = rej
  })
  return { promise, resolve: resolveIt, reject: rejectIt }
}

// >>============================= one continuous step =============================>>

describe('usePersonAssignmentFlow - resolving inspects too', () => {
  it('asks who the account is without the user pressing anything else', async () => {
    //
    // One click. Making the check a second button would mean the duplicate is
    // only caught by users who thought to look for it.
    //
    const { flow, harness } = build()
    flow.rawInput.value = 'https://v.douyin.com/abc/'

    await flow.resolve()

    expect(harness.inspectCalls).toEqual(['receipt-1'])
  })

  it('inspects by the receipt the resolve just produced', async () => {
    const { flow, harness } = build({
      resolve: () => Promise.resolve(ownerResolution('receipt-9')),
    })
    flow.rawInput.value = 'https://v.douyin.com/abc/'

    await flow.resolve()

    expect(harness.inspectCalls).toEqual(['receipt-9'])
  })

  it('does not inspect a link that failed to resolve', async () => {
    const { flow, harness } = build({
      resolve: () =>
        Promise.reject(
          new ApiError({ kind: 'backend', status: 400, code: 400, message: '没有找到可解析的链接' }),
        ),
    })
    flow.rawInput.value = 'nonsense'

    await flow.resolve()

    expect(harness.inspectCalls).toEqual([])
    expect(flow.phase.value).toBe('idle')
  })

  it('reports that it is still checking while the answer is in flight', async () => {
    //
    // Its own phase, so a test can tell "we have not asked yet" from "we asked
    // and the account is new" - the two look identical on screen and lead to
    // opposite offers.
    //
    const pending = deferred<PersonIdentityInspection>()
    const { flow } = build({ inspect: () => pending.promise })
    flow.rawInput.value = 'https://v.douyin.com/abc/'

    const running = flow.resolve()
    await nextTick()
    expect(flow.phase.value).toBe('inspecting')

    pending.resolve(unknownAccount())
    await running
    expect(flow.phase.value).toBe('resolved')
  })

  it('keeps the receipt, which the assignment still needs', async () => {
    const { flow } = build({ inspect: () => Promise.resolve(knownUnfiled()) })
    flow.rawInput.value = 'https://v.douyin.com/abc/'

    await flow.resolve()

    expect(flow.resolution.value?.resolve_id).toBe('receipt-1')
  })

  it('does not resolve the link a second time to inspect it', async () => {
    const { flow, harness } = build()
    flow.rawInput.value = 'https://v.douyin.com/abc/'

    await flow.resolve()

    expect(harness.resolveCalls).toHaveLength(1)
  })
})

// >>============================= the three states =============================>>

describe('usePersonAssignmentFlow - an account nobody has seen', () => {
  it('goes to the ordinary resolved state', async () => {
    const { flow } = build({ inspect: () => Promise.resolve(unknownAccount()) })
    flow.rawInput.value = 'https://v.douyin.com/abc/'

    await flow.resolve()

    expect(flow.phase.value).toBe('resolved')
    expect(flow.inspection.value?.known_account).toBe(false)
  })

  it('can still be submitted the normal way', async () => {
    const { flow, harness } = build()
    flow.rawInput.value = 'https://v.douyin.com/abc/'
    await flow.resolve()
    flow.role.value = 'main'

    await flow.submit()

    expect(harness.assignCalls).toHaveLength(1)
    expect(flow.phase.value).toBe('success')
  })
})

describe('usePersonAssignmentFlow - an account seen but never filed', () => {
  it('is resolved rather than existing, because nobody holds it', async () => {
    //
    // The distinction the whole endpoint rests on. A `share_url` row means a
    // download happened, not that a person was created - telling the user
    // "this person already exists" would be false and would leave them with no
    // way to file the account at all.
    //
    const { flow } = build({ inspect: () => Promise.resolve(knownUnfiled()) })
    flow.rawInput.value = 'https://v.douyin.com/abc/'

    await flow.resolve()

    expect(flow.phase.value).toBe('resolved')
    expect(flow.inspection.value?.known_account).toBe(true)
    expect(flow.inspection.value?.assignment).toBeNull()
  })

  it('still allows the account to be filed', async () => {
    const { flow, harness } = build({ inspect: () => Promise.resolve(knownUnfiled()) })
    flow.rawInput.value = 'https://v.douyin.com/abc/'
    await flow.resolve()
    flow.role.value = 'alt'

    await flow.submit()

    expect(harness.assignCalls).toHaveLength(1)
    expect(harness.assignCalls[0].target).toEqual({ kind: 'new' })
  })
})

describe('usePersonAssignmentFlow - an account somebody already holds', () => {
  it('stops at an existing state instead of offering a form', async () => {
    const { flow } = build({ inspect: () => Promise.resolve(knownFiled()) })
    flow.rawInput.value = 'https://v.douyin.com/abc/'

    await flow.resolve()

    expect(flow.phase.value).toBe('existing')
  })

  it('names the person, the role and the account', async () => {
    const { flow } = build({ inspect: () => Promise.resolve(knownFiled()) })
    flow.rawInput.value = 'https://v.douyin.com/abc/'

    await flow.resolve()

    expect(flow.inspection.value?.assignment).toEqual({
      person_id: 12,
      display_name: '程儿',
      role: 'main',
    })
    expect(flow.inspection.value?.owner.nickname).toBe('程儿')
    expect(flow.inspection.value?.owner.owner_user_id).toBe('acc-9')
  })

  it('is not reported as a successful assignment, because nothing was written', async () => {
    const { flow } = build({ inspect: () => Promise.resolve(knownFiled()) })
    flow.rawInput.value = 'https://v.douyin.com/abc/'

    await flow.resolve()

    expect(flow.phase.value).not.toBe('success')
    expect(flow.result.value).toBeNull()
  })

  it('submits nothing on its own', async () => {
    //
    // Not even the same assignment again. The backend is idempotent, but a
    // request would make the screen say "adding…" about something that was
    // added months ago.
    //
    const { flow, harness } = build({ inspect: () => Promise.resolve(knownFiled()) })
    flow.rawInput.value = 'https://v.douyin.com/abc/'

    await flow.resolve()
    await flow.submit()

    expect(harness.assignCalls).toEqual([])
  })

  it('shows the account under its current nickname and the person under theirs', async () => {
    //
    // A streamer who renamed themselves. The person keeps the name somebody
    // typed - renaming is its own operation - so the two legitimately differ
    // and the page shows both rather than reconciling them.
    //
    const renamed: PersonIdentityInspection = {
      owner: { owner_user_id: 'acc-9', sec_user_id: SEC_UID, nickname: '程小程' },
      known_account: true,
      assignment: { person_id: 12, display_name: '程儿', role: 'main' },
    }
    const { flow } = build({ inspect: () => Promise.resolve(renamed) })
    flow.rawInput.value = 'https://v.douyin.com/abc/'

    await flow.resolve()

    expect(flow.inspection.value?.owner.nickname).toBe('程小程')
    expect(flow.inspection.value?.assignment?.display_name).toBe('程儿')
  })

  it('reports the person by id, so two people sharing a name stay apart', async () => {
    const { flow } = build({
      inspect: () => Promise.resolve(knownFiled({ person_id: 2, display_name: '小明' })),
    })
    flow.rawInput.value = 'https://v.douyin.com/abc/'

    await flow.resolve()

    expect(flow.inspection.value?.assignment?.person_id).toBe(2)
  })
})

// >>============================= a late answer =============================>>

describe('usePersonAssignmentFlow - an inspection belongs to the text that asked', () => {
  //
  // The inspection is the second half of one question, so it lives under the
  // same generation as the resolve that started it. A second guard would be a
  // second opinion about what "current" means, and the two would disagree.
  //

  it('drops an inspection that finished after the box was edited', async () => {
    //
    // Without this: paste A, resolve A, edit to B, and A's answer arrives to
    // announce that B "already exists" - naming a person who has nothing to do
    // with what is on screen.
    //
    const pending = deferred<PersonIdentityInspection>()
    const { flow } = build({ inspect: () => pending.promise })
    flow.rawInput.value = 'https://v.douyin.com/a/'

    const running = flow.resolve()
    await nextTick()
    flow.rawInput.value = 'https://v.douyin.com/b/'
    await nextTick()

    pending.resolve(knownFiled())
    await running

    expect(flow.inspection.value).toBeNull()
    expect(flow.phase.value).toBe('idle')
  })

  it('drops a late inspection failure too', async () => {
    const pending = deferred<PersonIdentityInspection>()
    const { flow } = build({ inspect: () => pending.promise })
    flow.rawInput.value = 'https://v.douyin.com/a/'

    const running = flow.resolve()
    await nextTick()
    flow.rawInput.value = 'https://v.douyin.com/b/'
    await nextTick()

    pending.reject(new ApiError({ kind: 'backend', status: 503, code: 503, message: '查不了' }))
    await running

    expect(flow.inspectError.value).toBeNull()
    expect(flow.phase.value).toBe('idle')
  })

  it('cannot let one link inspection overwrite another link resolve', async () => {
    //
    // Resolve A finishes, its inspection is still in flight, and a resolve for
    // B starts and finishes. A's answer must not arrive and rename B's account.
    //
    const first = deferred<PersonIdentityInspection>()
    let call = 0
    const { flow } = build({
      resolve: (input) =>
        Promise.resolve(ownerResolution(input.includes('/b/') ? 'receipt-b' : 'receipt-a')),
      inspect: () => {
        call += 1
        return call === 1 ? first.promise : Promise.resolve(unknownAccount())
      },
    })

    flow.rawInput.value = 'https://v.douyin.com/a/'
    const firstRun = flow.resolve()
    await nextTick()

    flow.rawInput.value = 'https://v.douyin.com/b/'
    await nextTick()
    await flow.resolve()

    first.resolve(knownFiled())
    await firstRun

    expect(flow.resolution.value?.resolve_id).toBe('receipt-b')
    expect(flow.phase.value).toBe('resolved')
    expect(flow.inspection.value?.known_account).toBe(false)
  })

  it('ignores an inspection that lands after the flow was thrown away', async () => {
    const pending = deferred<PersonIdentityInspection>()
    const { flow } = build({ inspect: () => pending.promise })
    flow.rawInput.value = 'https://v.douyin.com/a/'

    const running = flow.resolve()
    await nextTick()
    flow.dispose()

    pending.resolve(knownFiled())
    await running

    expect(flow.inspection.value).toBeNull()
  })

  it('keeps only the last of two resolves of the same text', async () => {
    const { flow, harness } = build()
    flow.rawInput.value = 'https://v.douyin.com/a/'

    await flow.resolve()
    await flow.resolve()

    expect(harness.inspectCalls).toEqual(['receipt-1', 'receipt-1'])
    expect(flow.phase.value).toBe('resolved')
  })

  it('forgets an existing account when the box is edited', async () => {
    const { flow } = build({ inspect: () => Promise.resolve(knownFiled()) })
    flow.rawInput.value = 'https://v.douyin.com/a/'
    await flow.resolve()
    expect(flow.phase.value).toBe('existing')

    flow.rawInput.value = 'https://v.douyin.com/b/'
    await nextTick()

    expect(flow.inspection.value).toBeNull()
    expect(flow.phase.value).toBe('idle')
  })

  it('forgets an existing account when the card is reset', async () => {
    const { flow } = build({ inspect: () => Promise.resolve(knownFiled()) })
    flow.rawInput.value = 'https://v.douyin.com/a/'
    await flow.resolve()

    flow.reset()

    expect(flow.inspection.value).toBeNull()
    expect(flow.phase.value).toBe('idle')
  })
})

// >>============================= when the check itself fails =============================>>

describe('usePersonAssignmentFlow - the check could not be made', () => {
  //
  // "We could not ask" is not "this account is new". The backend answers 503
  // rather than an empty result for exactly that reason, and the page has to
  // pass the distinction on rather than quietly presenting the safe-looking
  // half of it.
  //

  it('says so, rather than presenting the account as new', async () => {
    const { flow } = build({
      inspect: () =>
        Promise.reject(
          new ApiError({
            kind: 'backend',
            status: 503,
            code: 503,
            message: '暂时无法确认该账号的归属，请稍后重试',
            backendKind: 'person_lookup_unavailable',
          }),
        ),
    })
    flow.rawInput.value = 'https://v.douyin.com/a/'

    await flow.resolve()

    expect(flow.inspectError.value).toBe('暂时无法确认该账号的归属，请稍后重试')
    expect(flow.inspection.value).toBeNull()
  })

  it('keeps the receipt, so the check can be retried without re-pasting', async () => {
    //
    // The resolve worked; only the check did not. Throwing the receipt away
    // would make the user paste the link again to retry something that was
    // never their fault - so it is kept, and 解析 re-runs the check.
    //
    // What is *not* kept is permission to submit: see the block below, where
    // an unanswered check blocks filing until it is answered.
    //
    const { flow } = build({
      inspect: () => Promise.reject(new ApiError({ kind: 'network', status: 0, code: 0, message: '网络异常' })),
    })
    flow.rawInput.value = 'https://v.douyin.com/a/'

    await flow.resolve()

    expect(flow.resolution.value).not.toBeNull()
    expect(flow.canResolve.value).toBe(true)
  })

  it('clears the warning once a later check succeeds', async () => {
    let call = 0
    const { flow } = build({
      inspect: () => {
        call += 1
        return call === 1
          ? Promise.reject(new ApiError({ kind: 'network', status: 0, code: 0, message: '网络异常' }))
          : Promise.resolve(knownFiled())
      },
    })
    flow.rawInput.value = 'https://v.douyin.com/a/'
    await flow.resolve()
    expect(flow.inspectError.value).not.toBeNull()

    await flow.resolve()

    expect(flow.inspectError.value).toBeNull()
    expect(flow.phase.value).toBe('existing')
  })
})

// >>============================= changing an existing one =============================>>

describe('usePersonAssignmentFlow - adjusting who holds an account', () => {
  //
  // The escape hatch. Pasting an account that is already filed is usually a
  // duplicate, but sometimes it is somebody promoting their spare to main or
  // moving it to the right person - so the form is reachable, just not the
  // default.
  //
  // Everything past the first click is the flow that already existed, with
  // every refusal it already had. The inspection tells the user where the
  // account is; it does not agree to anything on their behalf.
  //

  async function existing(inspection = knownFiled()) {
    const built = build({ inspect: () => Promise.resolve(inspection) })
    built.flow.rawInput.value = 'https://v.douyin.com/a/'
    await built.flow.resolve()
    return built
  }

  it('opens the form only when asked', async () => {
    const { flow } = await existing()

    expect(flow.phase.value).toBe('existing')
    flow.adjustAssignment()

    expect(flow.phase.value).toBe('resolved')
  })

  it('starts from where the account already is', async () => {
    //
    // So the first thing the user sees is the truth, and any change they make
    // is a change they chose. Starting from "create a new person" would put the
    // duplicate back one click away.
    //
    const { flow } = await existing()

    flow.adjustAssignment()

    expect(flow.targetKind.value).toBe('existing')
    expect(flow.selectedPersonId.value).toBe(12)
    expect(flow.role.value).toBe('main')
  })

  it('will not re-send the assignment it is already showing', async () => {
    //
    // The backend is idempotent about this, so nothing would break - but the
    // screen would say "adding…" about a thing that is already added, which is
    // the impression this whole step exists to remove.
    //
    const { flow, harness } = await existing()
    flow.adjustAssignment()

    expect(flow.canSubmit.value).toBe(false)
    await flow.submit()

    expect(harness.assignCalls).toEqual([])
  })

  it('submits once the role actually changes', async () => {
    const { flow, harness } = await existing()
    flow.adjustAssignment()

    flow.role.value = 'alt'
    expect(flow.canSubmit.value).toBe(true)
    await flow.submit()

    expect(harness.assignCalls).toHaveLength(1)
    expect(harness.assignCalls[0]).toEqual({
      resolve_id: 'receipt-1',
      target: { kind: 'existing', person_id: 12 },
      role: 'alt',
    })
  })

  it('submits once the person actually changes', async () => {
    const { flow, harness } = await existing()
    flow.adjustAssignment()

    flow.selectedPersonId.value = 20
    await flow.submit()

    expect(harness.assignCalls[0].target).toEqual({ kind: 'existing', person_id: 20 })
  })

  it('never agrees to the move on the user behalf', async () => {
    //
    // The decisive one. The inspection has just told the page who holds the
    // account, and filling `allow_move` in on the strength of that would take
    // it away from them on the basis of a screen the user only read.
    //
    const { flow, harness } = await existing()
    flow.adjustAssignment()
    flow.selectedPersonId.value = 20

    await flow.submit()

    expect(harness.assignCalls[0].allow_move).toBeUndefined()
  })

  it('still asks before moving, exactly as it did before', async () => {
    //
    // The inspection changed which screen the user starts on, and nothing else.
    // A move is still two requests with a refusal in between, and the consent
    // still comes from the user pressing the button - not from the fact that
    // the page happened to already know who held the account.
    //
    let attempt = 0
    const { flow, harness } = build({
      inspect: () => Promise.resolve(knownFiled()),
      assign: () => {
        attempt += 1
        return attempt === 1
          ? Promise.reject(
              new ApiError({
                kind: 'backend',
                status: 409,
                code: 409,
                message: '该账号已归属其他人物',
                backendKind: 'account_already_attached',
                details: { current_person: { person_id: 12, display_name: '程儿' } },
              }),
            )
          : Promise.resolve(assigned({ person_id: 20 }))
      },
    })
    flow.rawInput.value = 'https://v.douyin.com/a/'
    await flow.resolve()
    flow.adjustAssignment()
    flow.selectedPersonId.value = 20

    await flow.submit()
    expect(flow.phase.value).toBe('conflict')
    expect(flow.conflict.value?.kind).toBe('account_already_attached')
    expect(harness.assignCalls[0].allow_move).toBeUndefined()

    await flow.confirmMove()

    expect(harness.assignCalls).toHaveLength(2)
    expect(harness.assignCalls[1].allow_move).toBe(true)
  })

  it('can be abandoned, going back to the existing state', async () => {
    const { flow } = await existing()
    flow.adjustAssignment()

    flow.cancelAdjustment()

    expect(flow.phase.value).toBe('existing')
    expect(flow.inspection.value?.assignment?.person_id).toBe(12)
  })

  it('does nothing when there is nothing to adjust', async () => {
    const { flow } = build({ inspect: () => Promise.resolve(knownUnfiled()) })
    flow.rawInput.value = 'https://v.douyin.com/a/'
    await flow.resolve()

    flow.adjustAssignment()

    expect(flow.phase.value).toBe('resolved')
  })
})

describe('usePersonAssignmentFlow - a fixed person that already holds it', () => {
  //
  // The detail panel's own paste box. The target is whichever person is open,
  // so the interesting question is whether the pasted account is already one of
  // theirs - and if it is, there is nothing at all to do.
  //

  it('reports the account as already under this very person', async () => {
    const { flow } = build({
      inspect: () => Promise.resolve(knownFiled()),
      fixedPersonId: 12,
    })
    flow.rawInput.value = 'https://v.douyin.com/a/'

    await flow.resolve()

    expect(flow.phase.value).toBe('existing')
    expect(flow.heldByFixedPerson.value).toBe(true)
  })

  it('reports an account belonging to somebody else as somebody else', async () => {
    const { flow } = build({
      inspect: () => Promise.resolve(knownFiled({ person_id: 20, display_name: '别人' })),
      fixedPersonId: 12,
    })
    flow.rawInput.value = 'https://v.douyin.com/a/'

    await flow.resolve()

    expect(flow.phase.value).toBe('existing')
    expect(flow.heldByFixedPerson.value).toBe(false)
  })

  it('still requires an explicit move to take it from somebody else', async () => {
    const { flow, harness } = build({
      inspect: () => Promise.resolve(knownFiled({ person_id: 20, display_name: '别人' })),
      fixedPersonId: 12,
    })
    flow.rawInput.value = 'https://v.douyin.com/a/'
    await flow.resolve()

    flow.adjustAssignment()
    flow.role.value = 'alt'
    await flow.submit()

    expect(harness.assignCalls[0].target).toEqual({ kind: 'existing', person_id: 12 })
    expect(harness.assignCalls[0].allow_move).toBeUndefined()
  })
})

describe('usePersonAssignmentFlow - the text came back but the question did not', () => {
  it('ignores an inspection for a receipt that was thrown away, even when the box reads the same', async () => {
    //
    // The case the text comparison alone cannot catch, which is why the
    // generation is bumped when a check is abandoned rather than only when a
    // resolve is.
    //
    // Paste A, let it resolve and start checking, edit the box, then undo the
    // edit. The receipt was discarded by the first edit, so there is nothing to
    // submit - but the box now reads exactly what the in-flight check was asked
    // about. Compared on text alone, that answer looks current, and it would
    // announce "this account already exists" on a card holding no resolution at
    // all - with a 调整归属 button that could not send anything.
    //
    const pending = deferred<PersonIdentityInspection>()
    const { flow } = build({ inspect: () => pending.promise })

    flow.rawInput.value = 'https://v.douyin.com/a/'
    const running = flow.resolve()
    await nextTick()
    expect(flow.phase.value).toBe('inspecting')

    flow.rawInput.value = 'https://v.douyin.com/b/'
    await nextTick()
    flow.rawInput.value = 'https://v.douyin.com/a/'
    await nextTick()

    pending.resolve(knownFiled())
    await running

    expect(flow.inspection.value).toBeNull()
    expect(flow.phase.value).toBe('idle')
    //
    // Stated separately: an existing-account panel without a receipt behind it
    // is the specific wreckage this prevents.
    //
    expect(flow.resolution.value).toBeNull()
  })
})

// >>============================= a new link is a new question =============================>>

describe('usePersonAssignmentFlow - the draft does not outlive the link it was for', () => {
  it('does not aim a new link at the previous account person and role', async () => {
    //
    // Found in review. `adjustAssignment` fills the target in from whichever
    // account was inspected, and a link edit used to discard the receipt while
    // leaving that target behind. So: paste an account filed under 张三 as
    // main, press 调整归属, change your mind and paste a *different* account -
    // and the form comes up already aimed at 张三 as main, submittable in one
    // click. The receipt would be the new account's and the target the old
    // one's, which is a real attachment nobody chose.
    //
    let call = 0
    const { flow, harness } = build({
      resolve: () => Promise.resolve(ownerResolution(call === 0 ? 'r-a' : 'r-b')),
      inspect: () => {
        call += 1
        return Promise.resolve(call === 1 ? knownFiled() : unknownAccount())
      },
    })

    flow.rawInput.value = 'https://v.douyin.com/a/'
    await flow.resolve()
    flow.adjustAssignment()
    expect(flow.selectedPersonId.value).toBe(12)
    expect(flow.role.value).toBe('main')

    flow.rawInput.value = 'https://v.douyin.com/b/'
    await nextTick()
    await flow.resolve()

    expect(flow.inspection.value?.known_account).toBe(false)
    expect(flow.selectedPersonId.value).toBeNull()
    expect(flow.role.value).toBeNull()
    expect(flow.canSubmit.value).toBe(false)
    expect(harness.assignCalls).toEqual([])
  })

  it('clears a name typed for the previous link', async () => {
    const { flow } = build()
    flow.rawInput.value = 'https://v.douyin.com/a/'
    await flow.resolve()
    flow.displayName.value = '张三'
    flow.note.value = '备注'

    flow.rawInput.value = 'https://v.douyin.com/b/'
    await nextTick()

    expect(flow.displayName.value).toBe('')
    expect(flow.note.value).toBe('')
  })

  it('returns a fixed-person card to its own person rather than to nobody', async () => {
    //
    // The detail panel's card has no "create a new person" to fall back to, so
    // clearing the target means returning it to the person whose panel this is.
    //
    const { flow } = build({
      inspect: () => Promise.resolve(knownFiled({ person_id: 20, display_name: '别人' })),
      fixedPersonId: 12,
    })
    flow.rawInput.value = 'https://v.douyin.com/a/'
    await flow.resolve()
    flow.adjustAssignment()

    flow.rawInput.value = 'https://v.douyin.com/b/'
    await nextTick()

    expect(flow.targetKind.value).toBe('existing')
    expect(flow.selectedPersonId.value).toBe(12)
    expect(flow.role.value).toBeNull()
  })
})

// >>============================= an unknown existing state =============================>>

describe('usePersonAssignmentFlow - nothing may be filed while the check is unknown', () => {
  //
  // Found in review. "We could not ask" was letting the ordinary form through,
  // with 创建新人物 preselected - which is the one screen this whole step
  // exists to stop showing for an account that may well already be filed.
  //
  // The backend transaction would still refuse a genuine duplicate, so nothing
  // corrupt could be written. What was wrong is that the page invited the
  // attempt: during a person-lookup outage every pasted link reads as new.
  //

  function unavailable() {
    return new ApiError({
      kind: 'backend',
      status: 503,
      code: 503,
      message: '暂时无法确认该账号的归属，请稍后重试',
      backendKind: 'person_lookup_unavailable',
    })
  }

  it('refuses to submit when the lookup was unavailable', async () => {
    const { flow, harness } = build({ inspect: () => Promise.reject(unavailable()) })
    flow.rawInput.value = 'https://v.douyin.com/a/'
    await flow.resolve()

    flow.role.value = 'alt'

    expect(flow.inspectError.value).not.toBeNull()
    expect(flow.canSubmit.value).toBe(false)
    await flow.submit()
    expect(harness.assignCalls).toEqual([])
  })

  it('refuses to submit when the check failed for any other reason', async () => {
    const { flow } = build({
      inspect: () =>
        Promise.reject(new ApiError({ kind: 'network', status: 0, code: 0, message: '网络异常' })),
    })
    flow.rawInput.value = 'https://v.douyin.com/a/'
    await flow.resolve()
    flow.role.value = 'alt'

    expect(flow.canSubmit.value).toBe(false)
  })

  it('keeps the receipt, so retrying the check is one click rather than a re-paste', async () => {
    let call = 0
    const { flow, harness } = build({
      inspect: () => {
        call += 1
        return call === 1 ? Promise.reject(unavailable()) : Promise.resolve(unknownAccount())
      },
    })
    flow.rawInput.value = 'https://v.douyin.com/a/'
    await flow.resolve()
    expect(flow.canResolve.value).toBe(true)

    await flow.resolve()

    expect(flow.inspectError.value).toBeNull()
    flow.role.value = 'alt'
    expect(flow.canSubmit.value).toBe(true)
    await flow.submit()
    expect(harness.assignCalls).toHaveLength(1)
  })
})

describe('usePersonAssignmentFlow - editing the link clears the whole existing state', () => {
  it('leaves nothing of the previous account behind', async () => {
    //
    // Everything the previous link produced goes at once: the receipt, the
    // inspection, the person and role it implied, and any refusal that had been
    // raised about it. A single survivor is enough to describe one account on a
    // screen that is now about another.
    //
    const { flow } = build({
      inspect: () => Promise.resolve(knownFiled()),
      assign: () =>
        Promise.reject(
          new ApiError({
            kind: 'backend',
            status: 409,
            code: 409,
            message: '该账号已归属其他人物',
            backendKind: 'account_already_attached',
            details: { current_person: { person_id: 12, display_name: '程儿' } },
          }),
        ),
    })
    flow.rawInput.value = 'https://v.douyin.com/a/'
    await flow.resolve()
    flow.adjustAssignment()
    flow.selectedPersonId.value = 20
    await flow.submit()
    expect(flow.conflict.value?.kind).toBe('account_already_attached')

    flow.rawInput.value = 'https://v.douyin.com/b/'
    await nextTick()

    expect(flow.phase.value).toBe('idle')
    expect(flow.resolution.value).toBeNull()
    expect(flow.inspection.value).toBeNull()
    expect(flow.inspectError.value).toBeNull()
    expect(flow.conflict.value).toBeNull()
    expect(flow.selectedPersonId.value).toBeNull()
    expect(flow.role.value).toBeNull()
    expect(flow.canSubmit.value).toBe(false)
  })
})
