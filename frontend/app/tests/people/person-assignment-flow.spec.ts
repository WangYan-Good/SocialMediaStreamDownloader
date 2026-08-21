import { describe, expect, it } from 'vitest'

import { ApiError } from '../../src/api/client'
import {
  buildPersonAssignmentRequest,
  readAssignmentConflict,
} from '../../src/composables/usePersonAssignmentFlow'

//
// The two pure halves of the flow, tested without a component or a clock.
//
// `buildPersonAssignmentRequest` is what decides the wire shape, and the wire
// shape is where the receipt guarantee either holds or quietly stops holding.
// `readAssignmentConflict` is what turns a 409 into something the page can act
// on without reading Chinese prose.
//

function refusal(status: number, kind: string, details: Record<string, unknown> = {}) {
  return new ApiError({
    kind: 'backend',
    status,
    code: status,
    message: '拒绝',
    backendKind: kind,
    details: Object.keys(details).length ? details : null,
  })
}

describe('buildPersonAssignmentRequest', () => {
  it('names the account by its receipt and nothing else', () => {
    const request = buildPersonAssignmentRequest({
      resolveId: 'receipt-1',
      targetKind: 'new',
      selectedPersonId: null,
      displayName: '',
      note: '',
      role: 'alt',
    })

    expect(request).toEqual({
      resolve_id: 'receipt-1',
      target: { kind: 'new' },
      role: 'alt',
    })
  })

  it.each(['owner_user_id', 'sec_user_id', 'nickname', 'resolved_url'])(
    'never sends %s',
    (field) => {
      const request = buildPersonAssignmentRequest({
        resolveId: 'receipt-1',
        targetKind: 'new',
        selectedPersonId: null,
        displayName: '张三',
        note: '',
        role: 'main',
      })

      expect(JSON.stringify(request)).not.toContain(field)
    },
  )

  it('omits a blank name rather than sending an empty string', () => {
    //
    // The difference matters: the backend refuses a blank `display_name` as a
    // field error and fills one in only when the field is absent entirely.
    //
    const request = buildPersonAssignmentRequest({
      resolveId: 'receipt-1',
      targetKind: 'new',
      selectedPersonId: null,
      displayName: '   ',
      note: '',
      role: 'alt',
    })

    expect(request.target).toEqual({ kind: 'new' })
  })

  it('trims a name that was given', () => {
    const request = buildPersonAssignmentRequest({
      resolveId: 'receipt-1',
      targetKind: 'new',
      selectedPersonId: null,
      displayName: '  张三  ',
      note: '  备注  ',
      role: 'alt',
    })

    expect(request.target).toEqual({
      kind: 'new',
      display_name: '张三',
      note: '备注',
    })
  })

  it('sends an existing person by id alone', () => {
    //
    // No name, no note.  Renaming is its own deliberate operation, and the
    // backend refuses either field here rather than ignoring it.
    //
    const request = buildPersonAssignmentRequest({
      resolveId: 'receipt-1',
      targetKind: 'existing',
      selectedPersonId: 12,
      displayName: '张三',
      note: '备注',
      role: 'matrix',
    })

    expect(request.target).toEqual({ kind: 'existing', person_id: 12 })
  })

  it('carries a move only when it has been confirmed', () => {
    const plain = buildPersonAssignmentRequest({
      resolveId: 'receipt-1',
      targetKind: 'existing',
      selectedPersonId: 12,
      displayName: '',
      note: '',
      role: 'alt',
    })
    expect('allow_move' in plain).toBe(false)

    const confirmed = buildPersonAssignmentRequest({
      resolveId: 'receipt-1',
      targetKind: 'existing',
      selectedPersonId: 12,
      displayName: '',
      note: '',
      role: 'alt',
      allowMove: true,
    })
    expect(confirmed.allow_move).toBe(true)
  })

  it('carries a main replacement only when a demotion was chosen', () => {
    const plain = buildPersonAssignmentRequest({
      resolveId: 'receipt-1',
      targetKind: 'existing',
      selectedPersonId: 12,
      displayName: '',
      note: '',
      role: 'main',
    })
    expect('replace_main' in plain).toBe(false)

    const confirmed = buildPersonAssignmentRequest({
      resolveId: 'receipt-1',
      targetKind: 'existing',
      selectedPersonId: 12,
      displayName: '',
      note: '',
      role: 'main',
      demoteMainTo: 'matrix',
    })
    expect(confirmed.replace_main).toEqual({ demote_to: 'matrix' })
  })
})

describe('readAssignmentConflict', () => {
  it('reads who already holds the account', () => {
    const conflict = readAssignmentConflict(
      refusal(409, 'account_already_attached', {
        current_person: { person_id: 7, display_name: '原来的人' },
      }),
    )

    expect(conflict).toEqual({
      kind: 'account_already_attached',
      current_person: { person_id: 7, display_name: '原来的人' },
    })
  })

  it('reads the main that would have to be replaced', () => {
    const conflict = readAssignmentConflict(
      refusal(409, 'main_account_conflict', {
        current_main: { owner_user_id: 'acc-1', nickname: '主号' },
      }),
    )

    expect(conflict).toEqual({
      kind: 'main_account_conflict',
      current_main: { owner_user_id: 'acc-1', nickname: '主号' },
    })
  })

  it('reads the person a move would strand', () => {
    const conflict = readAssignmentConflict(
      refusal(409, 'last_main_removal_conflict', {
        source_person: { person_id: 7, display_name: '原来的人' },
        current_main: { owner_user_id: 'acc-1', nickname: '主号' },
      }),
    )

    expect(conflict?.kind).toBe('last_main_removal_conflict')
  })

  it('reads a race, which carries nothing', () => {
    const conflict = readAssignmentConflict(refusal(409, 'assignment_raced'))

    expect(conflict).toEqual({ kind: 'assignment_raced' })
  })

  it('refuses to invent details that did not arrive', () => {
    //
    // A malformed 409 must not crash the page and must not produce a
    // confirmation button, because there is nothing to confirm against. The
    // caller falls back to a plain refusal.
    //
    expect(readAssignmentConflict(refusal(409, 'account_already_attached'))).toBeNull()
    expect(
      readAssignmentConflict(
        refusal(409, 'main_account_conflict', { current_main: 'not an object' }),
      ),
    ).toBeNull()
    expect(
      readAssignmentConflict(
        refusal(409, 'account_already_attached', {
          current_person: { display_name: '没有 id' },
        }),
      ),
    ).toBeNull()
  })

  it('is not fooled by a non-conflict failure', () => {
    expect(readAssignmentConflict(refusal(404, 'resolution_not_found'))).toBeNull()
    expect(readAssignmentConflict(refusal(400, 'invalid_assignment'))).toBeNull()
    expect(
      readAssignmentConflict(
        new ApiError({ kind: 'network', status: null, code: null, message: 'x' }),
      ),
    ).toBeNull()
  })

  it('accepts a nickname that is genuinely absent', () => {
    //
    // An account nobody has downloaded has no nickname. That is a real answer,
    // not a malformed one.
    //
    const conflict = readAssignmentConflict(
      refusal(409, 'main_account_conflict', {
        current_main: { owner_user_id: 'acc-1', nickname: null },
      }),
    )

    expect(conflict).toEqual({
      kind: 'main_account_conflict',
      current_main: { owner_user_id: 'acc-1', nickname: null },
    })
  })
})

// >>============================= the flow =============================>>

import { nextTick } from 'vue'

import { usePersonAssignmentFlow } from '../../src/composables/usePersonAssignmentFlow'
import type { PersonAssignmentResult } from '../../src/types/person'
import type { ResolvedResource } from '../../src/types/resolution'

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

function assigned(overrides: Partial<PersonAssignmentResult> = {}): PersonAssignmentResult {
  return {
    person_id: 12,
    owner_user_id: 'acc-9',
    role: 'alt',
    created_person: true,
    display_name: '张三',
    ...overrides,
  }
}

interface Harness {
  resolveCalls: string[]
  assignCalls: PersonAssignmentRequestSpy[]
  //
  // `null` when the re-read was asked for because something changed under the
  // request rather than because it succeeded - a race, not an assignment.
  //
  refreshed: (PersonAssignmentResult | null)[]
}
type PersonAssignmentRequestSpy = ReturnType<typeof buildPersonAssignmentRequest>

function build(options: {
  resolve?: (input: string) => Promise<ResolvedResource>
  assign?: (request: PersonAssignmentRequestSpy) => Promise<PersonAssignmentResult>
  onPeopleChanged?: (result: PersonAssignmentResult | null) => Promise<void>
  fixedPersonId?: number
} = {}) {
  const harness: Harness = { resolveCalls: [], assignCalls: [], refreshed: [] }

  const flow = usePersonAssignmentFlow({
    api: {
      resolveResource: (input: string) => {
        harness.resolveCalls.push(input)
        return options.resolve ? options.resolve(input) : Promise.resolve(ownerResolution())
      },
      assignPersonAccount: (request: PersonAssignmentRequestSpy) => {
        harness.assignCalls.push(request)
        return options.assign ? options.assign(request) : Promise.resolve(assigned())
      },
    },
    onPeopleChanged: async (result: PersonAssignmentResult | null) => {
      harness.refreshed.push(result)
      if (options.onPeopleChanged) {
        await options.onPeopleChanged(result)
      }
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

describe('usePersonAssignmentFlow - resolving', () => {
  it('starts idle with nothing chosen', () => {
    const { flow } = build()

    expect(flow.phase.value).toBe('idle')
    expect(flow.resolution.value).toBeNull()
    //
    // Not defaulted to 'main'. Which account is somebody's main decides where
    // every account of theirs files, so it is a decision, not a default.
    //
    expect(flow.role.value).toBeNull()
  })

  it('sends the paste exactly as typed', async () => {
    const { flow, harness } = build()
    flow.rawInput.value = '4.33 复制打开抖音 https://v.douyin.com/abc/'

    await flow.resolve()

    expect(harness.resolveCalls).toEqual(['4.33 复制打开抖音 https://v.douyin.com/abc/'])
    expect(flow.phase.value).toBe('resolved')
    expect(flow.resolution.value?.resolve_id).toBe('receipt-1')
  })

  it('will not resolve an empty box', async () => {
    const { flow, harness } = build()
    flow.rawInput.value = '   '

    await flow.resolve()

    expect(harness.resolveCalls).toEqual([])
  })

  it('reports a refusal without pretending it resolved', async () => {
    const { flow } = build({
      resolve: () =>
        Promise.reject(
          new ApiError({ kind: 'backend', status: 400, code: 400, message: '没有找到可解析的链接' }),
        ),
    })
    flow.rawInput.value = 'nonsense'

    await flow.resolve()

    expect(flow.phase.value).toBe('idle')
    expect(flow.resolveError.value).toBe('没有找到可解析的链接')
    expect(flow.resolution.value).toBeNull()
  })
})

describe('usePersonAssignmentFlow - the receipt follows the text', () => {
  it('discards the receipt the moment the box is edited', async () => {
    //
    // Without this: paste A, resolve A, edit to B, press confirm - and an
    // account belonging to A is attached while the screen shows B. The server
    // would be right to accept it; the mistake is entirely this screen's, and
    // the user would never see it.
    //
    const { flow } = build()
    flow.rawInput.value = 'https://v.douyin.com/a/'
    await flow.resolve()
    expect(flow.resolution.value).not.toBeNull()

    flow.rawInput.value = 'https://v.douyin.com/b/'
    await nextTick()

    expect(flow.resolution.value).toBeNull()
    expect(flow.phase.value).toBe('idle')
  })

  it('cannot submit once the box has changed', async () => {
    const { flow, harness } = build()
    flow.rawInput.value = 'https://v.douyin.com/a/'
    await flow.resolve()
    flow.role.value = 'alt'
    expect(flow.canSubmit.value).toBe(true)

    flow.rawInput.value = 'https://v.douyin.com/b/'
    await nextTick()
    await flow.submit()

    expect(flow.canSubmit.value).toBe(false)
    expect(harness.assignCalls).toEqual([])
  })

  it('drops a resolve that finished after the text moved on', async () => {
    const first = deferred<ResolvedResource>()
    const answers = [first.promise, Promise.resolve(ownerResolution('receipt-b'))]
    let call = 0
    const { flow } = build({ resolve: () => answers[call++] })

    flow.rawInput.value = 'https://v.douyin.com/a/'
    const pending = flow.resolve()

    flow.rawInput.value = 'https://v.douyin.com/b/'
    await nextTick()
    await flow.resolve()

    first.resolve(ownerResolution('receipt-a'))
    await pending

    expect(flow.resolution.value?.resolve_id).toBe('receipt-b')
  })

  it('drops a stale failure too', async () => {
    const first = deferred<ResolvedResource>()
    const answers: Promise<ResolvedResource>[] = [
      first.promise,
      Promise.resolve(ownerResolution('receipt-b')),
    ]
    let call = 0
    const { flow } = build({ resolve: () => answers[call++] })

    flow.rawInput.value = 'https://v.douyin.com/a/'
    const pending = flow.resolve()
    flow.rawInput.value = 'https://v.douyin.com/b/'
    await nextTick()
    await flow.resolve()

    first.reject(new ApiError({ kind: 'network', status: null, code: null, message: '断了' }))
    await pending

    expect(flow.resolveError.value).toBeNull()
    expect(flow.resolution.value?.resolve_id).toBe('receipt-b')
  })
})

describe('usePersonAssignmentFlow - what may be submitted', () => {
  async function resolved(options: Parameters<typeof build>[0] = {}) {
    const built = build(options)
    built.flow.rawInput.value = 'https://v.douyin.com/a/'
    await built.flow.resolve()
    return built
  }

  it('needs a role to have been chosen', async () => {
    const { flow, harness } = await resolved()

    expect(flow.canSubmit.value).toBe(false)
    await flow.submit()
    expect(harness.assignCalls).toEqual([])

    flow.role.value = 'matrix'
    expect(flow.canSubmit.value).toBe(true)
  })

  it.each(['main', 'alt', 'matrix'] as const)('accepts %s for a new person', async (role) => {
    const { flow, harness } = await resolved()
    flow.role.value = role

    await flow.submit()

    expect(harness.assignCalls[0]).toEqual({
      resolve_id: 'receipt-1',
      target: { kind: 'new' },
      role,
    })
  })

  it('needs no name for a new person', async () => {
    const { flow, harness } = await resolved()
    flow.role.value = 'alt'

    expect(flow.canSubmit.value).toBe(true)
    await flow.submit()

    expect(harness.assignCalls[0].target).toEqual({ kind: 'new' })
  })

  it('needs a person once merging into an existing one', async () => {
    const { flow, harness } = await resolved()
    flow.role.value = 'alt'
    flow.targetKind.value = 'existing'

    expect(flow.canSubmit.value).toBe(false)
    await flow.submit()
    expect(harness.assignCalls).toEqual([])

    flow.selectedPersonId.value = 12
    expect(flow.canSubmit.value).toBe(true)
  })

  it('needs a resolution', async () => {
    const { flow } = build()
    flow.role.value = 'alt'

    expect(flow.canSubmit.value).toBe(false)
  })

  it('refuses a second submission while the first is in flight', async () => {
    const pending = deferred<PersonAssignmentResult>()
    const { flow, harness } = await resolved({ assign: () => pending.promise })
    flow.role.value = 'alt'

    const first = flow.submit()
    await flow.submit()

    expect(harness.assignCalls).toHaveLength(1)
    pending.resolve(assigned())
    await first
  })
})

describe('usePersonAssignmentFlow - switching target', () => {
  async function resolved() {
    const built = build()
    built.flow.rawInput.value = 'https://v.douyin.com/a/'
    await built.flow.resolve()
    built.flow.role.value = 'alt'
    return built
  }

  it('keeps the receipt and the role when switching to an existing person', async () => {
    const { flow } = await resolved()
    flow.displayName.value = '张三'
    flow.note.value = '备注'

    flow.targetKind.value = 'existing'
    await nextTick()

    expect(flow.resolution.value?.resolve_id).toBe('receipt-1')
    expect(flow.role.value).toBe('alt')
    //
    // The name and note belong to a person who is no longer being created.
    //
    expect(flow.displayName.value).toBe('')
    expect(flow.note.value).toBe('')
  })

  it('forgets the chosen person when switching back to a new one', async () => {
    const { flow } = await resolved()
    flow.targetKind.value = 'existing'
    flow.selectedPersonId.value = 12
    await nextTick()

    flow.targetKind.value = 'new'
    await nextTick()

    expect(flow.selectedPersonId.value).toBeNull()
    expect(flow.resolution.value?.resolve_id).toBe('receipt-1')
    expect(flow.role.value).toBe('alt')
  })
})

describe('usePersonAssignmentFlow - success', () => {
  async function submitted(options: Parameters<typeof build>[0] = {}) {
    const built = build(options)
    built.flow.rawInput.value = 'https://v.douyin.com/a/'
    await built.flow.resolve()
    built.flow.role.value = 'alt'
    await built.flow.submit()
    return built
  }

  it('reports what the server decided, not what was typed', async () => {
    const { flow } = await submitted({
      assign: () => Promise.resolve(assigned({ display_name: '自动生成的名字' })),
    })

    expect(flow.phase.value).toBe('success')
    expect(flow.result.value?.display_name).toBe('自动生成的名字')
    expect(flow.result.value?.created_person).toBe(true)
  })

  it('asks the caller to re-read the people it just changed', async () => {
    const { flow, harness } = await submitted()

    expect(harness.refreshed).toHaveLength(1)
    expect(harness.refreshed[0]?.person_id).toBe(12)
    expect(flow.phase.value).toBe('success')
  })

  it('does not call a write a failure because the re-read failed', async () => {
    //
    // The account really was added. Saying "添加失败" would send the user back
    // to do it again, and the second attempt would hit a conflict caused by the
    // first one having worked.
    //
    const { flow } = await submitted({
      onPeopleChanged: () => Promise.reject(new Error('list unavailable')),
    })

    expect(flow.phase.value).toBe('success')
    expect(flow.assignmentError.value).toBeNull()
    expect(flow.refreshWarning.value).not.toBeNull()
  })

  it('clears everything when asked to add another', async () => {
    const { flow } = await submitted()

    flow.reset()

    expect(flow.phase.value).toBe('idle')
    expect(flow.rawInput.value).toBe('')
    expect(flow.resolution.value).toBeNull()
    expect(flow.result.value).toBeNull()
    expect(flow.role.value).toBeNull()
  })
})

describe('usePersonAssignmentFlow - the account belongs to somebody else', () => {
  function refusedOnce(kind: string, details: Record<string, unknown>, status = 409) {
    let called = 0
    return () => {
      called += 1
      return called === 1
        ? Promise.reject(refusal(status, kind, details))
        : Promise.resolve(assigned())
    }
  }

  async function conflicted(assign: () => Promise<PersonAssignmentResult>) {
    const built = build({ assign })
    built.flow.rawInput.value = 'https://v.douyin.com/a/'
    await built.flow.resolve()
    built.flow.role.value = 'alt'
    await built.flow.submit()
    return built
  }

  it('stops and says who holds it, rather than moving it', async () => {
    const { flow, harness } = await conflicted(
      refusedOnce('account_already_attached', {
        current_person: { person_id: 7, display_name: '原来的人' },
      }),
    )

    expect(flow.phase.value).toBe('conflict')
    expect(flow.conflict.value).toEqual({
      kind: 'account_already_attached',
      current_person: { person_id: 7, display_name: '原来的人' },
    })
    //
    // One attempt. Retrying with allow_move on the user's behalf would move an
    // account away from somebody without ever asking them.
    //
    expect(harness.assignCalls).toHaveLength(1)
    expect(harness.assignCalls[0].allow_move).toBeUndefined()
  })

  it('re-sends the same receipt with the move confirmed', async () => {
    const { flow, harness } = await conflicted(
      refusedOnce('account_already_attached', {
        current_person: { person_id: 7, display_name: '原来的人' },
      }),
    )

    await flow.confirmMove()

    expect(harness.assignCalls).toHaveLength(2)
    expect(harness.assignCalls[1].allow_move).toBe(true)
    //
    // The same receipt. Re-resolving would ask the platform again for an answer
    // the server already has, and could name a different resource.
    //
    expect(harness.assignCalls[1].resolve_id).toBe('receipt-1')
    expect(harness.resolveCalls).toHaveLength(1)
    expect(flow.phase.value).toBe('success')
  })

  it('goes back to the resolved state when the conflict is dismissed', async () => {
    const { flow } = await conflicted(
      refusedOnce('account_already_attached', {
        current_person: { person_id: 7, display_name: '原来的人' },
      }),
    )

    flow.cancelConflict()

    expect(flow.phase.value).toBe('resolved')
    expect(flow.conflict.value).toBeNull()
    expect(flow.resolution.value?.resolve_id).toBe('receipt-1')
  })
})

describe('usePersonAssignmentFlow - the person already has a main', () => {
  async function conflicted() {
    let called = 0
    const built = build({
      assign: () => {
        called += 1
        return called === 1
          ? Promise.reject(
              refusal(409, 'main_account_conflict', {
                current_main: { owner_user_id: 'acc-1', nickname: '主号' },
              }),
            )
          : Promise.resolve(assigned({ role: 'main' }))
      },
    })
    built.flow.rawInput.value = 'https://v.douyin.com/a/'
    await built.flow.resolve()
    built.flow.role.value = 'main'
    built.flow.targetKind.value = 'existing'
    built.flow.selectedPersonId.value = 12
    await built.flow.submit()
    return built
  }

  it('names the main that is in the way', async () => {
    const { flow } = await conflicted()

    expect(flow.phase.value).toBe('conflict')
    expect(flow.conflict.value).toEqual({
      kind: 'main_account_conflict',
      current_main: { owner_user_id: 'acc-1', nickname: '主号' },
    })
  })

  it('will not replace until a demotion has been chosen', async () => {
    const { flow, harness } = await conflicted()

    await flow.confirmReplaceMain(null)

    expect(harness.assignCalls).toHaveLength(1)
    expect(flow.phase.value).toBe('conflict')
  })

  it.each(['alt', 'matrix'] as const)('demotes the old main to %s', async (demoteTo) => {
    const { flow, harness } = await conflicted()

    await flow.confirmReplaceMain(demoteTo)

    expect(harness.assignCalls).toHaveLength(2)
    expect(harness.assignCalls[1].replace_main).toEqual({ demote_to: demoteTo })
    expect(harness.assignCalls[1].resolve_id).toBe('receipt-1')
    expect(harness.resolveCalls).toHaveLength(1)
  })
})

describe('usePersonAssignmentFlow - the move would strand a person', () => {
  async function conflicted() {
    const built = build({
      assign: () =>
        Promise.reject(
          refusal(409, 'last_main_removal_conflict', {
            source_person: { person_id: 7, display_name: '原来的人' },
            current_main: { owner_user_id: 'acc-1', nickname: '主号' },
          }),
        ),
    })
    built.flow.rawInput.value = 'https://v.douyin.com/a/'
    await built.flow.resolve()
    built.flow.role.value = 'alt'
    await built.flow.submit()
    return built
  }

  it('offers nothing to confirm, because nothing here is recoverable', async () => {
    const { flow, harness } = await conflicted()

    expect(flow.conflict.value?.kind).toBe('last_main_removal_conflict')
    //
    // No force, no override. The folders those accounts were filed under are
    // not written down anywhere else, so there is no version of this the user
    // could agree to.
    //
    await flow.confirmMove()
    expect(harness.assignCalls).toHaveLength(1)
  })
})

describe('usePersonAssignmentFlow - the account changed hands mid-request', () => {
  async function raced() {
    const built = build({
      assign: () => Promise.reject(refusal(409, 'assignment_raced')),
    })
    built.flow.rawInput.value = 'https://v.douyin.com/a/'
    await built.flow.resolve()
    built.flow.role.value = 'main'
    built.flow.targetKind.value = 'existing'
    built.flow.selectedPersonId.value = 12
    await built.flow.submit()
    return built
  }

  it('returns to the resolved state rather than holding a stale confirmation', async () => {
    const { flow } = await raced()

    expect(flow.phase.value).toBe('resolved')
    expect(flow.conflict.value).toBeNull()
    expect(flow.assignmentError.value).toContain('重新确认')
  })

  it('keeps the receipt, which is still perfectly good', async () => {
    const { flow } = await raced()

    expect(flow.resolution.value?.resolve_id).toBe('receipt-1')
  })

  it('re-reads the people, because what it raced against changed them', async () => {
    const { harness } = await raced()

    expect(harness.refreshed).toHaveLength(1)
  })

  it('does not carry the old confirmations into the next attempt', async () => {
    //
    // The whole point of a race is that the world moved. Re-sending allow_move
    // or replace_main would be confirming something the user agreed to about a
    // state that no longer exists.
    //
    let called = 0
    const built = build({
      assign: () => {
        called += 1
        if (called === 1) {
          return Promise.reject(
            refusal(409, 'account_already_attached', {
              current_person: { person_id: 7, display_name: '原来的人' },
            }),
          )
        }
        if (called === 2) {
          return Promise.reject(refusal(409, 'assignment_raced'))
        }
        return Promise.resolve(assigned())
      },
    })
    built.flow.rawInput.value = 'https://v.douyin.com/a/'
    await built.flow.resolve()
    built.flow.role.value = 'alt'
    await built.flow.submit()
    await built.flow.confirmMove()

    await built.flow.submit()

    expect(built.harness.assignCalls[2].allow_move).toBeUndefined()
    expect(built.harness.assignCalls[2].replace_main).toBeUndefined()
  })
})

describe('usePersonAssignmentFlow - the receipt expired', () => {
  async function expired() {
    const built = build({
      assign: () =>
        Promise.reject(refusal(404, 'resolution_not_found', {})),
    })
    built.flow.rawInput.value = 'https://v.douyin.com/a/'
    await built.flow.resolve()
    built.flow.role.value = 'alt'
    await built.flow.submit()
    return built
  }

  it('throws the receipt away and asks for the link again', async () => {
    const { flow } = await expired()

    expect(flow.resolution.value).toBeNull()
    expect(flow.phase.value).toBe('idle')
    expect(flow.assignmentError.value).toContain('重新解析')
  })

  it('does not silently resolve again on the user behalf', async () => {
    //
    // Re-resolving would mean the server deciding what the user meant, minutes
    // after they asked - which is the one thing the receipt exists to prevent.
    //
    const { harness } = await expired()

    expect(harness.resolveCalls).toHaveLength(1)
  })
})

describe('usePersonAssignmentFlow - a fixed person', () => {
  it('is stuck on that person, and never offers to create one', async () => {
    //
    // The person detail panel's own paste box. Same contract, same conflicts;
    // the only difference is that the target was decided by which panel is open.
    //
    const { flow, harness } = build({ fixedPersonId: 12 })
    flow.rawInput.value = 'https://v.douyin.com/a/'
    await flow.resolve()
    flow.role.value = 'matrix'

    await flow.submit()

    expect(flow.targetKind.value).toBe('existing')
    expect(harness.assignCalls[0].target).toEqual({ kind: 'existing', person_id: 12 })
  })
})

describe('usePersonAssignmentFlow - an answer belongs to the request that asked', () => {
  //
  // The role and person controls stay usable while a submission is in flight -
  // there is no reason to freeze the form, and the submit button is already
  // disabled. But a refusal that comes back describes the request that was
  // *sent*, and if the draft has moved on since, showing it against the new
  // draft attaches one explanation to a different intention.
  //
  // The concrete failure: submit for person 12, change the picker to person 20,
  // the 409 for 12 arrives and is displayed, and pressing "确认移动" sends
  // `allow_move: true` for person 20 - consent given while reading about
  // somebody else. The backend still checks everything, so nothing invalid is
  // written; what is wrong is that the user agreed to a different sentence than
  // the one that was carried out.
  //

  function heldOpen() {
    let settle: (result: PersonAssignmentResult) => void = () => {}
    let refuse: (reason: unknown) => void = () => {}
    const promise = new Promise<PersonAssignmentResult>((res, rej) => {
      settle = res
      refuse = rej
    })
    return { promise, settle, refuse }
  }

  async function submittingFor(personId: number, held: ReturnType<typeof heldOpen>) {
    const built = build({ assign: () => held.promise })
    built.flow.rawInput.value = 'https://v.douyin.com/a/'
    await built.flow.resolve()
    built.flow.role.value = 'alt'
    built.flow.targetKind.value = 'existing'
    built.flow.selectedPersonId.value = personId
    await nextTick()
    return built
  }

  it('drops a refusal raised for a person the user has since changed', async () => {
    const held = heldOpen()
    const { flow } = await submittingFor(12, held)
    const inFlight = flow.submit()

    flow.selectedPersonId.value = 20
    await nextTick()

    held.refuse(
      refusal(409, 'account_already_attached', {
        current_person: { person_id: 7, display_name: '原来的人' },
      }),
    )
    await inFlight

    expect(flow.conflict.value).toBeNull()
    expect(flow.phase.value).toBe('resolved')
  })

  it('drops a refusal raised for a role the user has since changed', async () => {
    const held = heldOpen()
    const { flow } = await submittingFor(12, held)
    const inFlight = flow.submit()

    flow.role.value = 'matrix'
    await nextTick()

    held.refuse(
      refusal(409, 'main_account_conflict', {
        current_main: { owner_user_id: 'acc-1', nickname: '主号' },
      }),
    )
    await inFlight

    expect(flow.conflict.value).toBeNull()
  })

  it('drops a success raised for a draft the user has since changed', async () => {
    //
    // The write did happen, and re-reading the people is still right - but
    // reporting "已将账号添加到 X" beside a form that now says Y would name the
    // wrong person on the one screen the user checks.
    //
    const held = heldOpen()
    const { flow } = await submittingFor(12, held)
    const inFlight = flow.submit()

    flow.selectedPersonId.value = 20
    await nextTick()

    held.settle(assigned({ person_id: 12 }))
    await inFlight

    expect(flow.phase.value).not.toBe('success')
    expect(flow.result.value).toBeNull()
  })

  it('forgets a confirmation the user gave for a superseded draft', async () => {
    const held = heldOpen()
    const { flow, harness } = await submittingFor(12, held)
    const inFlight = flow.submit()

    flow.selectedPersonId.value = 20
    await nextTick()
    held.refuse(
      refusal(409, 'account_already_attached', {
        current_person: { person_id: 7, display_name: '原来的人' },
      }),
    )
    await inFlight

    //
    // There is nothing to confirm: the conflict was dropped with the draft it
    // belonged to, so the button that would have sent `allow_move` does nothing.
    //
    await flow.confirmMove()

    expect(harness.assignCalls).toHaveLength(1)
  })

  it('still answers a conflict raised for the draft that is still on screen', async () => {
    //
    // The guard must not swallow the ordinary case, which is the whole feature.
    //
    let called = 0
    const built = build({
      assign: () => {
        called += 1
        return called === 1
          ? Promise.reject(
              refusal(409, 'account_already_attached', {
                current_person: { person_id: 7, display_name: '原来的人' },
              }),
            )
          : Promise.resolve(assigned())
      },
    })
    built.flow.rawInput.value = 'https://v.douyin.com/a/'
    await built.flow.resolve()
    built.flow.role.value = 'alt'
    built.flow.targetKind.value = 'existing'
    built.flow.selectedPersonId.value = 12
    await nextTick()

    await built.flow.submit()
    expect(built.flow.conflict.value).not.toBeNull()

    await built.flow.confirmMove()

    expect(built.harness.assignCalls).toHaveLength(2)
    expect(built.harness.assignCalls[1]).toMatchObject({
      target: { kind: 'existing', person_id: 12 },
      allow_move: true,
    })
  })
})
