import { mount } from '@vue/test-utils'
import { describe, expect, it, vi } from 'vitest'
import { nextTick } from 'vue'
import { createMemoryHistory, createRouter } from 'vue-router'

import { routes } from '../../src/router'
import NewDownloadView from '../../src/views/NewDownloadView.vue'
import type { BatchResolveResult, ResolvedResource } from '../../src/types/resolution'


const post: ResolvedResource = {
  resolve_id: 'R-post',
  platform: 'douyin',
  resource_type: 'post',
  source_url: 'https://www.douyin.com/video/1',
  resolved_url: 'https://www.douyin.com/video/1',
  identity: { aweme_id: '1' },
  expires_in_seconds: 600,
}

const owner: ResolvedResource = {
  resolve_id: 'R-owner',
  platform: 'douyin',
  resource_type: 'owner',
  source_url: 'https://www.douyin.com/user/2',
  resolved_url: 'https://www.douyin.com/user/2',
  identity: { sec_user_id: '2' },
  expires_in_seconds: 600,
}

const result: BatchResolveResult = {
  total: 3,
  resolved_count: 2,
  failed_count: 1,
  items: [
    { index: 0, status: 'resolved', resolution: post },
    {
      index: 1,
      status: 'failed',
      error: { kind: 'unsupported_platform', message: '暂不支持该平台的链接' },
    },
    { index: 2, status: 'resolved', resolution: owner },
  ],
}

async function settle() {
  for (let index = 0; index < 5; index += 1) await Promise.resolve()
  await nextTick()
}

async function mountView() {
  const router = createRouter({ history: createMemoryHistory(), routes })
  await router.push('/new')
  await router.isReady()
  const singleResolve = vi.fn()
  const batchResolve = vi.fn(async () => result)
  const createTask = vi.fn(async (request) => ({
    task_id: `T-${request.resolve_id}`,
    task_type: request.task_type,
    resolve_id: request.resolve_id,
  }))
  const wrapper = mount(NewDownloadView, {
    props: {
      api: { resolveResource: singleResolve },
      batchApi: { resolveResources: batchResolve, createTask },
    },
    global: { plugins: [router] },
  })
  return { wrapper, singleResolve, batchResolve, createTask }
}

describe('explicit batch mode', () => {
  it('opens in single mode and never infers batch from text', async () => {
    const { wrapper } = await mountView()

    expect(wrapper.find('[data-mode="single"]').classes()).toContain('mode__button--active')
    expect(wrapper.find('.batch-input').exists()).toBe(false)
  })

  it('sends exact raw input only through the batch adapter', async () => {
    const { wrapper, singleResolve, batchResolve } = await mountView()
    await wrapper.get('[data-mode="batch"]').trigger('click')
    const input = 'A https://v.douyin.com/A/\nB https://v.douyin.com/B/'
    await wrapper.get('.batch-input textarea').setValue(input)
    await wrapper.get('.batch-input button').trigger('click')
    await settle()

    expect(batchResolve).toHaveBeenCalledWith(input)
    expect(singleResolve).not.toHaveBeenCalled()
  })

  it('shows safe review rows and leaves failed/owner items unselected', async () => {
    const { wrapper } = await mountView()
    await wrapper.get('[data-mode="batch"]').trigger('click')
    await wrapper.get('.batch-input textarea').setValue('three')
    await wrapper.get('.batch-input button').trigger('click')
    await settle()

    const rows = wrapper.findAll('.batch-review__item')
    expect(rows).toHaveLength(3)
    expect(rows[1].text()).toContain('第 2 个链接无法识别')
    expect(rows[1].text()).not.toContain('http')
    expect(rows[1].find('input[type="checkbox"]').exists()).toBe(false)
    expect((rows[0].find('input[type="checkbox"]').element as HTMLInputElement).checked).toBe(true)
    expect((rows[2].find('input[type="checkbox"]').element as HTMLInputElement).checked).toBe(false)
  })

  it('requires the owner row confirmation and links completed work to Task Center', async () => {
    const { wrapper, createTask } = await mountView()
    await wrapper.get('[data-mode="batch"]').trigger('click')
    await wrapper.get('.batch-input textarea').setValue('three')
    await wrapper.get('.batch-input button').trigger('click')
    await settle()
    const ownerRow = wrapper.findAll('.batch-review__item')[2]
    await ownerRow.get('input[type="checkbox"]').setValue(true)

    expect(wrapper.get('.batch-review__create').attributes('disabled')).toBeDefined()
    await ownerRow.get('.batch-review__confirm input').setValue(true)
    await wrapper.get('.batch-review__create').trigger('click')
    await settle()

    expect(createTask).toHaveBeenCalledTimes(2)
    expect(wrapper.text()).toContain('已开始 2 个下载')
    expect(wrapper.find('.batch-review__task-link').attributes('href')).toContain('/tasks')
  })
})
