import { mount } from '@vue/test-utils'
import { describe, expect, it, vi } from 'vitest'
import { nextTick } from 'vue'

import PersonAssignmentCard from '../../src/components/people/PersonAssignmentCard.vue'
import type { PersonAssignmentResult, PersonSummaryItem } from '../../src/types/person'
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

function build(options: {
  resolve?: () => Promise<ResolvedResource>
  assign?: (request: unknown) => Promise<PersonAssignmentResult>
  fixedPersonId?: number
} = {}) {
  const resolveResource = vi.fn(options.resolve ?? (() => Promise.resolve(ownerResolution())))
  const assignPersonAccount = vi.fn(options.assign ?? (() => Promise.resolve(assigned())))

  const wrapper = mount(PersonAssignmentCard, {
    props: {
      people: PEOPLE,
      api: { resolveResource, assignPersonAccount },
      ...(options.fixedPersonId === undefined ? {} : { fixedPersonId: options.fixedPersonId }),
    },
  })
  return { wrapper, resolveResource, assignPersonAccount }
}

async function pasteAndResolve(wrapper: ReturnType<typeof build>['wrapper']) {
  await wrapper.find('[data-test="assignment-input"]').setValue('https://v.douyin.com/abc/')
  await wrapper.find('[data-test="assignment-resolve"]').trigger('click')
  await nextTick()
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
