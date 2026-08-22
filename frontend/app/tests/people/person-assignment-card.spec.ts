import { mount } from '@vue/test-utils'
import { describe, expect, it, vi } from 'vitest'
import { nextTick } from 'vue'

import { ApiError } from '../../src/api/client'
import PersonAssignmentCard from '../../src/components/people/PersonAssignmentCard.vue'
import type {
  PersonAssignmentResult,
  PersonIdentityInspection,
  PersonSummaryItem,
} from '../../src/types/person'
import type { ResolvedResource } from '../../src/types/resolution'

const SEC_UID = 'MS4wLjABAAAAGZkW5n1EHZD_TFyQ-QiaISBPemtKFxVVdhLSeoXhh-U'

function ownerResolution(): ResolvedResource {
  return {
    resolve_id: 'receipt-1',
    platform: 'douyin',
    resource_type: 'owner',
    source_url: 'https://v.douyin.com/abc/',
    resolved_url: `https://www.douyin.com/user/${SEC_UID}`,
    identity: { sec_user_id: SEC_UID },
    expires_in_seconds: 600,
  }
}

const PEOPLE: PersonSummaryItem[] = [
  { person_id: 12, display_name: '张三', directory_name: null, note: null, account_count: 2 },
  { person_id: 20, display_name: '李四', directory_name: null, note: null, account_count: 1 },
]

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

//
// The default answer: an account this server has never heard of, which is the
// state the create-a-person half of this card is written for.
//
function unknownAccount(): PersonIdentityInspection {
  return {
    owner: { owner_user_id: 'acc-9', sec_user_id: SEC_UID, nickname: '程儿' },
    known_account: false,
    assignment: null,
  }
}

function build(options: {
  resolve?: () => Promise<ResolvedResource>
  inspect?: () => Promise<PersonIdentityInspection>
  assign?: (request: unknown) => Promise<PersonAssignmentResult>
  fixedPersonId?: number
} = {}) {
  const resolveResource = vi.fn(options.resolve ?? (() => Promise.resolve(ownerResolution())))
  //
  // Stubbed here rather than left to the real api: resolving now inspects on
  // the same click, so a harness without this would reach the network.
  //
  const inspectPersonAssignment = vi.fn(
    options.inspect ?? (() => Promise.resolve(unknownAccount())),
  )
  const assignPersonAccount = vi.fn(options.assign ?? (() => Promise.resolve(assigned())))

  const wrapper = mount(PersonAssignmentCard, {
    props: {
      people: PEOPLE,
      api: { resolveResource, inspectPersonAssignment, assignPersonAccount },
      ...(options.fixedPersonId === undefined ? {} : { fixedPersonId: options.fixedPersonId }),
    },
  })
  return { wrapper, resolveResource, inspectPersonAssignment, assignPersonAccount }
}

async function pasteAndResolve(wrapper: ReturnType<typeof build>['wrapper']) {
  await wrapper.find('[data-test="assignment-input"]').setValue('https://v.douyin.com/abc/')
  await wrapper.find('[data-test="assignment-resolve"]').trigger('click')
  await nextTick()
  await nextTick()
  //
  // One more than before: the click now settles a resolve *and* the inspection
  // it chains into.
  //
  await nextTick()
}

describe('PersonAssignmentCard - the link comes first', () => {
  it('asks for a link, not for a person name', () => {
    const { wrapper } = build()

    expect(wrapper.find('[data-test="assignment-input"]').exists()).toBe(true)
    //
    // The old two-step flow started by naming an empty person. Nothing here
    // should ask for a name before there is an account to attach.
    //
    expect(wrapper.find('[data-test="assignment-role"]').exists()).toBe(false)
  })

  it('will not resolve an empty box', async () => {
    const { wrapper, resolveResource } = build()

    await wrapper.find('[data-test="assignment-resolve"]').trigger('click')

    expect(resolveResource).not.toHaveBeenCalled()
  })

  it('shows what the link turned out to be', async () => {
    const { wrapper } = build()

    await pasteAndResolve(wrapper)

    const preview = wrapper.find('[data-test="assignment-preview"]')
    expect(preview.exists()).toBe(true)
    expect(preview.text()).toContain('主页')
  })

  it('does not show a made-up account identity', async () => {
    //
    // A resolution names a resource, not an owner. The nickname and the account
    // id are only known once the server has read them, which happens during the
    // assignment - so the preview must not pretend to have them.
    //
    const { wrapper } = build()

    await pasteAndResolve(wrapper)

    expect(wrapper.find('[data-test="assignment-preview"]').text()).not.toContain(SEC_UID)
  })
})

describe('PersonAssignmentCard - choosing who it belongs to', () => {
  it('offers a role only once a link has resolved', async () => {
    const { wrapper } = build()
    expect(wrapper.find('[data-test="assignment-role"]').exists()).toBe(false)

    await pasteAndResolve(wrapper)

    expect(wrapper.find('[data-test="assignment-role"]').exists()).toBe(true)
  })

  it('picks no role by default', async () => {
    const { wrapper } = build()

    await pasteAndResolve(wrapper)

    expect(
      (wrapper.find('[data-test="assignment-role"]').element as HTMLSelectElement).value,
    ).toBe('')
    expect(
      (wrapper.find('[data-test="assignment-submit"]').element as HTMLButtonElement).disabled,
    ).toBe(true)
  })

  it('offers all three roles for a brand new person', async () => {
    const { wrapper } = build()
    await pasteAndResolve(wrapper)

    const options = wrapper
      .find('[data-test="assignment-role"]')
      .findAll('option')
      .map((one) => one.text())

    expect(options).toContain('大号')
    expect(options).toContain('小号')
    expect(options).toContain('矩阵号')
  })

  it.each([
    ['main', '大号'],
    ['alt', '小号'],
    ['matrix', '矩阵号'],
  ])('sends %s for a new person', async (role) => {
    const { wrapper, assignPersonAccount } = build()
    await pasteAndResolve(wrapper)

    await wrapper.find('[data-test="assignment-role"]').setValue(role)
    await wrapper.find('[data-test="assignment-submit"]').trigger('click')
    await nextTick()

    expect(assignPersonAccount).toHaveBeenCalledWith({
      resolve_id: 'receipt-1',
      target: { kind: 'new' },
      role,
    })
  })

  it('lets the name be left empty', async () => {
    const { wrapper } = build()
    await pasteAndResolve(wrapper)

    const name = wrapper.find('[data-test="assignment-name"]')
    expect(name.exists()).toBe(true)
    expect(name.attributes('placeholder')).toContain('自动生成')
  })

  it('hides the name and note once merging into an existing person', async () => {
    const { wrapper } = build()
    await pasteAndResolve(wrapper)

    await wrapper.find('[data-test="assignment-target-existing"]').setValue()
    await nextTick()

    expect(wrapper.find('[data-test="assignment-name"]').exists()).toBe(false)
    expect(wrapper.find('[data-test="assignment-person"]').exists()).toBe(true)
  })

  it('sends the chosen person', async () => {
    const { wrapper, assignPersonAccount } = build()
    await pasteAndResolve(wrapper)

    await wrapper.find('[data-test="assignment-target-existing"]').setValue()
    await nextTick()
    await wrapper.find('[data-test="assignment-person"]').setValue('20')
    await wrapper.find('[data-test="assignment-role"]').setValue('matrix')
    await wrapper.find('[data-test="assignment-submit"]').trigger('click')
    await nextTick()

    expect(assignPersonAccount).toHaveBeenCalledWith({
      resolve_id: 'receipt-1',
      target: { kind: 'existing', person_id: 20 },
      role: 'matrix',
    })
  })
})

describe('PersonAssignmentCard - refusals', () => {
  async function conflicted(kind: string, details: Record<string, unknown>) {
    const { ApiError } = await import('../../src/api/client')
    let called = 0
    const built = build({
      assign: () => {
        called += 1
        return called === 1
          ? Promise.reject(
              new ApiError({
                kind: 'backend',
                status: 409,
                code: 409,
                message: '拒绝',
                backendKind: kind,
                details,
              }),
            )
          : Promise.resolve(assigned())
      },
    })
    await pasteAndResolve(built.wrapper)
    await built.wrapper.find('[data-test="assignment-role"]').setValue('alt')
    await built.wrapper.find('[data-test="assignment-submit"]').trigger('click')
    await nextTick()
    await nextTick()
    return built
  }

  it('names the person already holding the account', async () => {
    const { wrapper } = await conflicted('account_already_attached', {
      current_person: { person_id: 7, display_name: '原来的人' },
    })

    const conflict = wrapper.find('[data-test="assignment-conflict"]')
    expect(conflict.exists()).toBe(true)
    expect(conflict.text()).toContain('原来的人')
    expect(wrapper.find('[data-test="assignment-confirm-move"]').exists()).toBe(true)
  })

  it('moves only when the move is confirmed', async () => {
    const { wrapper, assignPersonAccount } = await conflicted('account_already_attached', {
      current_person: { person_id: 7, display_name: '原来的人' },
    })

    expect(assignPersonAccount).toHaveBeenCalledTimes(1)

    await wrapper.find('[data-test="assignment-confirm-move"]').trigger('click')
    await nextTick()

    expect(assignPersonAccount).toHaveBeenCalledTimes(2)
    expect(assignPersonAccount.mock.calls[1][0]).toMatchObject({ allow_move: true })
  })

  it('offers to open the person that holds it', async () => {
    const { wrapper } = await conflicted('account_already_attached', {
      current_person: { person_id: 7, display_name: '原来的人' },
    })

    await wrapper.find('[data-test="assignment-open-person"]').trigger('click')

    expect(wrapper.emitted('open-person')?.[0]).toEqual([7])
  })

  it('names the main standing in the way', async () => {
    const { wrapper } = await conflicted('main_account_conflict', {
      current_main: { owner_user_id: 'acc-1', nickname: '主号' },
    })

    expect(wrapper.find('[data-test="assignment-conflict"]').text()).toContain('主号')
  })

  it('will not replace a main until a demotion is chosen', async () => {
    const { wrapper, assignPersonAccount } = await conflicted('main_account_conflict', {
      current_main: { owner_user_id: 'acc-1', nickname: '主号' },
    })

    const confirm = wrapper.find('[data-test="assignment-confirm-replace"]')
    expect((confirm.element as HTMLButtonElement).disabled).toBe(true)

    await wrapper.find('[data-test="assignment-demote-to"]').setValue('matrix')
    await nextTick()
    await wrapper.find('[data-test="assignment-confirm-replace"]').trigger('click')
    await nextTick()

    expect(assignPersonAccount).toHaveBeenCalledTimes(2)
    expect(assignPersonAccount.mock.calls[1][0]).toMatchObject({
      replace_main: { demote_to: 'matrix' },
    })
  })

  it('offers no way through a stranded-main refusal', async () => {
    const { wrapper } = await conflicted('last_main_removal_conflict', {
      source_person: { person_id: 7, display_name: '原来的人' },
      current_main: { owner_user_id: 'acc-1', nickname: '主号' },
    })

    const conflict = wrapper.find('[data-test="assignment-conflict"]')
    expect(conflict.exists()).toBe(true)
    //
    // There is no confirmation, because the folders this protects are not
    // written down anywhere else. The only way forward is to give that person a
    // main of their own first.
    //
    expect(wrapper.find('[data-test="assignment-confirm-move"]').exists()).toBe(false)
    expect(wrapper.find('[data-test="assignment-confirm-replace"]').exists()).toBe(false)
    expect(wrapper.find('[data-test="assignment-open-person"]').exists()).toBe(true)
  })

  it('shows a plain refusal when the conflict details are unreadable', async () => {
    const { wrapper } = await conflicted('main_account_conflict', { current_main: 'nonsense' })

    expect(wrapper.find('[data-test="assignment-confirm-replace"]').exists()).toBe(false)
    expect(wrapper.find('[data-test="assignment-error"]').exists()).toBe(true)
  })
})

describe('PersonAssignmentCard - success', () => {
  async function succeeded(result: PersonAssignmentResult) {
    const built = build({ assign: () => Promise.resolve(result) })
    await pasteAndResolve(built.wrapper)
    await built.wrapper.find('[data-test="assignment-role"]').setValue('alt')
    await built.wrapper.find('[data-test="assignment-submit"]').trigger('click')
    await nextTick()
    await nextTick()
    return built
  }

  it('says a person was created, and names them', async () => {
    const { wrapper } = await succeeded(assigned({ created_person: true, display_name: '张三' }))

    const success = wrapper.find('[data-test="assignment-success"]')
    expect(success.text()).toContain('张三')
    expect(success.text()).toContain('已创建')
  })

  it('says an account was merged into an existing person', async () => {
    const { wrapper } = await succeeded(
      assigned({ created_person: false, display_name: '李四', role: 'matrix' }),
    )

    const success = wrapper.find('[data-test="assignment-success"]')
    expect(success.text()).toContain('李四')
    expect(success.text()).toContain('矩阵号')
  })

  it('tells the page which person to open', async () => {
    const { wrapper } = await succeeded(assigned({ person_id: 12 }))

    expect(wrapper.emitted('assigned')?.[0]).toEqual([assigned({ person_id: 12 })])
  })

  it('offers to add another, and clears when asked', async () => {
    const { wrapper } = await succeeded(assigned())

    await wrapper.find('[data-test="assignment-again"]').trigger('click')
    await nextTick()

    expect(wrapper.find('[data-test="assignment-success"]').exists()).toBe(false)
    expect(
      (wrapper.find('[data-test="assignment-input"]').element as HTMLInputElement).value,
    ).toBe('')
  })
})

describe('PersonAssignmentCard - a fixed person', () => {
  it('never offers to create a person', async () => {
    const { wrapper, assignPersonAccount } = build({ fixedPersonId: 12 })

    await pasteAndResolve(wrapper)

    expect(wrapper.find('[data-test="assignment-target-existing"]').exists()).toBe(false)
    expect(wrapper.find('[data-test="assignment-name"]').exists()).toBe(false)

    await wrapper.find('[data-test="assignment-role"]').setValue('matrix')
    await wrapper.find('[data-test="assignment-submit"]').trigger('click')
    await nextTick()

    expect(assignPersonAccount).toHaveBeenCalledWith({
      resolve_id: 'receipt-1',
      target: { kind: 'existing', person_id: 12 },
      role: 'matrix',
    })
  })
})

// >>============================= the detail panel's own box =============================>>

describe('PersonDetailPanel - adding by link', () => {
  //
  // The panel used to resolve a link and then call `/person/account/by-link`,
  // which is a second link workflow with its own rules. It now hands the same
  // receipt to the same assignment endpoint the main card does, so there is one
  // set of rules about mains, moves and folders rather than two.
  //

  it('uses the assignment card rather than a second link form', async () => {
    const PersonDetailPanel = (
      await import('../../src/components/people/PersonDetailPanel.vue')
    ).default
    const { detail, person } = await import('./fixtures')

    const wrapper = mount(PersonDetailPanel, {
      props: {
        person: person(),
        detail: detail(),
        detailLoading: false,
        detailError: null,
        searchResults: [],
        searching: false,
        candidates: [],
        mutating: false,
        movesFrom: () => null,
        people: PEOPLE,
      },
    })

    expect(wrapper.find('[data-test="assignment-input"]').exists()).toBe(true)
    //
    // The old form's own button, gone with the workflow behind it.
    //
    expect(
      wrapper.findAll('button').some((one) => one.text().trim() === '按链接添加'),
    ).toBe(false)
  })

  it('keeps searching known accounts, which is a different question', async () => {
    const PersonDetailPanel = (
      await import('../../src/components/people/PersonDetailPanel.vue')
    ).default
    const { detail, person } = await import('./fixtures')

    const wrapper = mount(PersonDetailPanel, {
      props: {
        person: person(),
        detail: detail(),
        detailLoading: false,
        detailError: null,
        searchResults: [],
        searching: false,
        candidates: [],
        mutating: false,
        movesFrom: () => null,
        people: PEOPLE,
      },
    })

    expect(wrapper.text()).toContain('搜索')
  })
})

// >>============================= what the check found =============================>>

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
  overrides: Partial<NonNullable<PersonIdentityInspection['assignment']>> = {},
): PersonIdentityInspection {
  return {
    owner: { owner_user_id: 'acc-9', sec_user_id: SEC_UID, nickname: '程儿' },
    known_account: true,
    assignment: { person_id: 12, display_name: '张三', role: 'main', ...overrides },
  }
}

describe('PersonAssignmentCard - an account somebody already holds', () => {
  //
  // The screen this whole step exists to produce. Before it, pasting an account
  // added last month showed "创建新人物 / 归并到已有人物 / 选择角色 / 确认添加"
  // and only said the account was taken after the confirm - which reads as
  // "I must create this person again".
  //

  it('says the account is already there, rather than offering a form', async () => {
    const { wrapper } = build({ inspect: () => Promise.resolve(knownFiled()) })

    await pasteAndResolve(wrapper)

    expect(wrapper.find('[data-test="assignment-existing"]').exists()).toBe(true)
    expect(wrapper.text()).toContain('该账号已经存在，无需重复添加')
  })

  it('hides every way of creating a person by default', async () => {
    //
    // The duplicate is created by a form being on screen when it should not be,
    // so the assertion is about absence.
    //
    const { wrapper } = build({ inspect: () => Promise.resolve(knownFiled()) })

    await pasteAndResolve(wrapper)

    expect(wrapper.find('[data-test="assignment-target-new"]').exists()).toBe(false)
    expect(wrapper.find('[data-test="assignment-name"]').exists()).toBe(false)
    expect(wrapper.find('[data-test="assignment-role"]').exists()).toBe(false)
    expect(wrapper.find('[data-test="assignment-submit"]').exists()).toBe(false)
  })

  it('names the person holding it', async () => {
    const { wrapper } = build({ inspect: () => Promise.resolve(knownFiled()) })

    await pasteAndResolve(wrapper)

    expect(wrapper.find('[data-test="assignment-existing"]').text()).toContain('张三')
  })

  it('says what kind of account it is', async () => {
    const { wrapper } = build({ inspect: () => Promise.resolve(knownFiled()) })

    await pasteAndResolve(wrapper)

    expect(wrapper.find('[data-test="assignment-existing"]').text()).toContain('大号')
  })

  it('shows the account under its own current nickname and id', async () => {
    const { wrapper } = build({
      inspect: () =>
        Promise.resolve({
          owner: { owner_user_id: 'acc-9', sec_user_id: SEC_UID, nickname: '程小程' },
          known_account: true,
          assignment: { person_id: 12, display_name: '张三', role: 'main' as const },
        }),
    })

    await pasteAndResolve(wrapper)

    const shown = wrapper.find('[data-test="assignment-existing"]').text()
    //
    // Both names, unreconciled. The account renamed itself; the person is still
    // called what somebody typed, and pretending otherwise would quietly rename
    // a person to follow a handle.
    //
    expect(shown).toContain('程小程')
    expect(shown).toContain('张三')
    expect(shown).toContain('acc-9')
  })

  it('is not dressed up as a successful addition', async () => {
    const { wrapper } = build({ inspect: () => Promise.resolve(knownFiled()) })

    await pasteAndResolve(wrapper)

    expect(wrapper.find('[data-test="assignment-success"]').exists()).toBe(false)
    expect(wrapper.text()).not.toContain('已创建人物')
  })

  it('offers to open the person who holds it', async () => {
    const { wrapper } = build({ inspect: () => Promise.resolve(knownFiled()) })
    await pasteAndResolve(wrapper)

    await wrapper.find('[data-test="assignment-open-existing"]').trigger('click')

    expect(wrapper.emitted('open-person')).toEqual([[12]])
  })

  it('opens the person it actually found, not one matched by name', async () => {
    const { wrapper } = build({
      inspect: () => Promise.resolve(knownFiled({ person_id: 20, display_name: '张三' })),
    })
    await pasteAndResolve(wrapper)

    await wrapper.find('[data-test="assignment-open-existing"]').trigger('click')

    expect(wrapper.emitted('open-person')).toEqual([[20]])
  })

  it('reaches the form only when the user asks to change the assignment', async () => {
    const { wrapper } = build({ inspect: () => Promise.resolve(knownFiled()) })
    await pasteAndResolve(wrapper)

    await wrapper.find('[data-test="assignment-adjust"]').trigger('click')

    expect(wrapper.find('[data-test="assignment-role"]').exists()).toBe(true)
    expect(wrapper.find('[data-test="assignment-submit"]').exists()).toBe(true)
  })

  it('will not resubmit the assignment it is already showing', async () => {
    const { wrapper, assignPersonAccount } = build({
      inspect: () => Promise.resolve(knownFiled()),
    })
    await pasteAndResolve(wrapper)
    await wrapper.find('[data-test="assignment-adjust"]').trigger('click')

    await wrapper.find('[data-test="assignment-submit"]').trigger('click')

    expect(assignPersonAccount).not.toHaveBeenCalled()
  })

  it('submits once the role is actually changed', async () => {
    const { wrapper, assignPersonAccount } = build({
      inspect: () => Promise.resolve(knownFiled()),
    })
    await pasteAndResolve(wrapper)
    await wrapper.find('[data-test="assignment-adjust"]').trigger('click')

    await wrapper.find('[data-test="assignment-role"]').setValue('alt')
    await wrapper.find('[data-test="assignment-submit"]').trigger('click')

    expect(assignPersonAccount).toHaveBeenCalledTimes(1)
    expect(assignPersonAccount.mock.calls[0][0]).toEqual({
      resolve_id: 'receipt-1',
      target: { kind: 'existing', person_id: 12 },
      role: 'alt',
    })
  })
})

describe('PersonAssignmentCard - an account seen but never filed', () => {
  it('says the account is known and still needs a person', async () => {
    const { wrapper } = build({ inspect: () => Promise.resolve(knownUnfiled()) })

    await pasteAndResolve(wrapper)

    expect(wrapper.text()).toContain('该账号已经存在，但尚未归入人物')
  })

  it('still offers the whole assignment form', async () => {
    //
    // A `share_url` row means a download happened, not that anybody was
    // created. Hiding the form here would leave the account unfilable.
    //
    const { wrapper } = build({ inspect: () => Promise.resolve(knownUnfiled()) })

    await pasteAndResolve(wrapper)

    expect(wrapper.find('[data-test="assignment-target-new"]').exists()).toBe(true)
    expect(wrapper.find('[data-test="assignment-role"]').exists()).toBe(true)
    expect(wrapper.find('[data-test="assignment-existing"]').exists()).toBe(false)
  })
})

describe('PersonAssignmentCard - an account nobody has seen', () => {
  it('names the account it identified', async () => {
    const { wrapper } = build()

    await pasteAndResolve(wrapper)

    expect(wrapper.text()).toContain('已识别账号')
    expect(wrapper.find('[data-test="assignment-preview"]').text()).toContain('程儿')
  })

  it('leaves the ordinary flow exactly as it was', async () => {
    const { wrapper } = build()

    await pasteAndResolve(wrapper)

    expect(wrapper.find('[data-test="assignment-target-new"]').exists()).toBe(true)
    expect(wrapper.find('[data-test="assignment-target-existing"]').exists()).toBe(true)
    expect(wrapper.find('[data-test="assignment-existing"]').exists()).toBe(false)
  })
})

describe('PersonAssignmentCard - the check could not be made', () => {
  it('says so, and offers no form to file the account with', async () => {
    //
    // Whether this account is already filed is unknown, and a form offering
    // 创建新人物 would turn that unknown into an invitation - during a person
    // lookup outage, every pasted link would read as a fresh account. The
    // 解析 button stays, so re-running the check is one click.
    //
    const { wrapper } = build({
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

    await pasteAndResolve(wrapper)

    expect(wrapper.find('[data-test="assignment-inspect-error"]').text()).toContain(
      '暂时无法确认该账号的归属',
    )
    expect(wrapper.find('[data-test="assignment-role"]').exists()).toBe(false)
    expect(wrapper.find('[data-test="assignment-submit"]').exists()).toBe(false)
    expect(wrapper.find('[data-test="assignment-target-new"]').exists()).toBe(false)
    //
    // Still retryable without re-pasting the link.
    //
    expect(wrapper.find('[data-test="assignment-resolve"]').exists()).toBe(true)
  })
})

describe('PersonAssignmentCard - inside a person detail panel', () => {
  it('says the account is already under this very person', async () => {
    const { wrapper } = build({
      inspect: () => Promise.resolve(knownFiled()),
      fixedPersonId: 12,
    })

    await pasteAndResolve(wrapper)

    expect(wrapper.text()).toContain('该账号已经在这个人物下')
    expect(wrapper.find('[data-test="assignment-submit"]').exists()).toBe(false)
  })

  it('says who else holds it, without moving anything', async () => {
    const { wrapper, assignPersonAccount } = build({
      inspect: () => Promise.resolve(knownFiled({ person_id: 20, display_name: '李四' })),
      fixedPersonId: 12,
    })

    await pasteAndResolve(wrapper)

    expect(wrapper.find('[data-test="assignment-existing"]').text()).toContain('李四')
    expect(assignPersonAccount).not.toHaveBeenCalled()
  })
})

// >>============================= two people, one name =============================>>

describe('PersonAssignmentCard - people who share a display name', () => {
  //
  // Two different humans may legitimately be called 小明. Nothing here may
  // collapse them, and nothing here may use a name as an identity - which is
  // why the picker keys on `person_id` and the inspection reports one.
  //

  const NAMESAKES: PersonSummaryItem[] = [
    { person_id: 1, display_name: '小明', directory_name: null, note: null, account_count: 1 },
    { person_id: 2, display_name: '小明', directory_name: null, note: null, account_count: 3 },
  ]

  function buildWithNamesakes() {
    return mount(PersonAssignmentCard, {
      props: {
        people: NAMESAKES,
        api: {
          resolveResource: vi.fn(() => Promise.resolve(ownerResolution())),
          inspectPersonAssignment: vi.fn(() => Promise.resolve(unknownAccount())),
          assignPersonAccount: vi.fn(() => Promise.resolve(assigned())),
        },
      },
    })
  }

  it('offers both of them, separately', async () => {
    //
    // A `Set` over display names would silently drop one, and the dropped
    // person would be unreachable from this screen forever.
    //
    const wrapper = buildWithNamesakes()
    await pasteAndResolve(wrapper)
    await wrapper.find('[data-test="assignment-target-existing"]').setValue()
    await nextTick()

    const options = wrapper
      .find('[data-test="assignment-person"]')
      .findAll('option')
      .filter((one) => one.attributes('value') !== '')

    expect(options).toHaveLength(2)
    expect(options.map((one) => one.attributes('value'))).toEqual(['1', '2'])
  })

  it('sends the id that was picked, not the name', async () => {
    const wrapper = buildWithNamesakes()
    const assignSpy = vi.fn(() => Promise.resolve(assigned()))
    await pasteAndResolve(wrapper)
    await wrapper.setProps({
      api: {
        resolveResource: vi.fn(() => Promise.resolve(ownerResolution())),
        inspectPersonAssignment: vi.fn(() => Promise.resolve(unknownAccount())),
        assignPersonAccount: assignSpy,
      },
    })

    await wrapper.find('[data-test="assignment-target-existing"]').setValue()
    await nextTick()
    await wrapper.find('[data-test="assignment-person"]').setValue('2')
    await wrapper.find('[data-test="assignment-role"]').setValue('alt')

    expect(
      (wrapper.find('[data-test="assignment-person"]').element as HTMLSelectElement).value,
    ).toBe('2')
  })

  it('reports the namesake that actually holds the account', async () => {
    const wrapper = mount(PersonAssignmentCard, {
      props: {
        people: NAMESAKES,
        api: {
          resolveResource: vi.fn(() => Promise.resolve(ownerResolution())),
          inspectPersonAssignment: vi.fn(() =>
            Promise.resolve({
              owner: { owner_user_id: 'acc-9', sec_user_id: SEC_UID, nickname: '小明' },
              known_account: true,
              assignment: { person_id: 2, display_name: '小明', role: 'alt' as const },
            }),
          ),
          assignPersonAccount: vi.fn(() => Promise.resolve(assigned())),
        },
      },
    })

    await pasteAndResolve(wrapper)
    await wrapper.find('[data-test="assignment-open-existing"]').trigger('click')

    //
    // Person 2, never person 1. A name match would have picked whichever came
    // back first and merged two strangers.
    //
    expect(wrapper.emitted('open-person')).toEqual([[2]])
  })
})

describe('PersonDetailPanel - one row per account', () => {
  //
  // The list is keyed on the account, which is what `person_account` is keyed
  // on. Two accounts sharing a nickname are two accounts - the same streamer
  // name appears on unrelated accounts and one person renames themselves
  // freely - so a nickname key would silently render one of them and leave the
  // other unreachable from this panel.
  //
  // The grain itself is settled in the query; see the backend's ListingGrainTest.
  //

  async function mountPanel(accounts: Array<Record<string, unknown>>) {
    const PersonDetailPanel = (
      await import('../../src/components/people/PersonDetailPanel.vue')
    ).default
    const { detail, person } = await import('./fixtures')

    return mount(PersonDetailPanel, {
      props: {
        person: person(),
        detail: detail({ accounts: accounts as never }),
        detailLoading: false,
        detailError: null,
        searchResults: [],
        searching: false,
        candidates: [],
        mutating: false,
        movesFrom: () => null,
        people: PEOPLE,
      },
    })
  }

  it('shows two accounts that happen to share a nickname', async () => {
    const wrapper = await mountPanel([
      { owner_user_id: 'acc-1', nickname: '程儿', role: 'main' },
      { owner_user_id: 'acc-2', nickname: '程儿', role: 'alt' },
    ])

    const shown = wrapper.text()
    expect(shown).toContain('acc-1')
    expect(shown).toContain('acc-2')
  })

  it('shows each account exactly once', async () => {
    const wrapper = await mountPanel([
      { owner_user_id: 'acc-1', nickname: '程儿', role: 'main' },
      { owner_user_id: 'acc-2', nickname: '程小程', role: 'alt' },
    ])

    const shown = wrapper.text()
    expect(shown.match(/acc-1/g) ?? []).toHaveLength(1)
    expect(shown.match(/acc-2/g) ?? []).toHaveLength(1)
  })
})
