import { mount } from '@vue/test-utils'
import { describe, expect, it } from 'vitest'
import { nextTick } from 'vue'

import CreatorPreferenceEditor from '../../src/components/creators/CreatorPreferenceEditor.vue'
import type { HistoryOwner } from '../../src/types/history'


function owner(ownerUserId: string, favorite = true, score: number | null = 80): HistoryOwner {
  return {
    owner_user_id: ownerUserId,
    sec_user_id: null,
    nickname: ownerUserId,
    live_share_url: null,
    directory_name: null,
    user_status: null,
    actived_count: 0,
    score,
    favorite,
    last_live_status: null,
    last_checked_at: null,
    last_room_id: null,
  }
}

describe('creator preference editor', () => {
  it('keeps range and number inputs synchronized including score zero', async () => {
    const wrapper = mount(CreatorPreferenceEditor, {
      props: { owner: owner('A'), busy: false, error: null, notice: null },
    })
    const range = wrapper.find('input[type="range"]')
    const number = wrapper.find('input[type="number"]')

    await number.setValue(0)

    expect((range.element as HTMLInputElement).value).toBe('0')
    await wrapper.get('form').trigger('submit')
    expect(wrapper.emitted('save')?.[0]).toEqual([{ favorite: true, score: 0 }])
  })

  it('disables scoring and emits no score when favorite is off', async () => {
    const wrapper = mount(CreatorPreferenceEditor, {
      props: { owner: owner('A'), busy: false, error: null, notice: null },
    })

    await wrapper.find('input[type="checkbox"]').setValue(false)

    expect(wrapper.find('input[type="range"]').attributes('disabled')).toBeDefined()
    await wrapper.get('form').trigger('submit')
    expect(wrapper.emitted('save')?.[0]).toEqual([{ favorite: false }])
  })

  it('resets an unsaved draft when the owner context changes', async () => {
    const wrapper = mount(CreatorPreferenceEditor, {
      props: { owner: owner('A', true, 80), busy: false, error: null, notice: null },
    })
    await wrapper.find('input[type="number"]').setValue(90)

    await wrapper.setProps({ owner: owner('B', true, 20) })
    await nextTick()

    expect((wrapper.find('input[type="number"]').element as HTMLInputElement).value).toBe('20')
  })

  it('prevents a second submit while a save is pending', async () => {
    const wrapper = mount(CreatorPreferenceEditor, {
      props: { owner: owner('A'), busy: true, error: null, notice: null },
    })

    expect(wrapper.find('button[type="submit"]').attributes('disabled')).toBeDefined()
    await wrapper.get('form').trigger('submit')
    expect(wrapper.emitted('save')).toBeUndefined()
  })

  it('states the listener boundary without promising a live reconcile', () => {
    const wrapper = mount(CreatorPreferenceEditor, {
      props: { owner: owner('A'), busy: false, error: null, notice: null },
    })

    expect(wrapper.text()).toContain('持久化')
    expect(wrapper.text()).toContain('不会动态重建')
  })
})
