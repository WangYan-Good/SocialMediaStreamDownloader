import { mount } from '@vue/test-utils'
import type { VueWrapper } from '@vue/test-utils'
import { createMemoryHistory, createRouter } from 'vue-router'
import { afterEach, describe, expect, it, vi } from 'vitest'
import { nextTick } from 'vue'

import { ApiError } from '../../src/api/client'
import ResourceResolutionCard from '../../src/components/new-download/ResourceResolutionCard.vue'
import { TASK_POLL_INTERVAL_MS } from '../../src/composables/useNewDownloadFlow'
import { routes } from '../../src/router'
import type { BatchResolveResult, ResolvedResource } from '../../src/types/resolution'
import type { CreateTaskRequest, CreatedTask, Task, TaskState } from '../../src/types/task'
import NewDownloadView from '../../src/views/NewDownloadView.vue'
import UserHomeView from '../../src/views/UserHomeView.vue'

afterEach(() => {
  vi.useRealTimers()
})

async function testRouter(path: string) {
  const router = createRouter({ history: createMemoryHistory(), routes })
  await router.push(path)
  await router.isReady()
  return router
}

describe('the home screen as a way in', () => {
  it('says which kinds of share content it accepts', async () => {
    //
    // The one question a first-time user actually has. Answering it here costs
    // nothing and saves a round trip through a failed identification.
    //
    const router = await testRouter('/')
    const wrapper = mount(UserHomeView, { global: { plugins: [router] } })

    for (const supported of ['作品链接', '主播主页', '直播链接', '分享文本']) {
      expect(wrapper.text()).toContain(supported)
    }
  })

  it('leads to the one download screen rather than starting its own', async () => {
    //
    // A second paste box here would be a second implementation of the flow.
    // The home screen links; it does not resolve.
    //
    const router = await testRouter('/')
    const wrapper = mount(UserHomeView, { global: { plugins: [router] } })

    expect(wrapper.find('textarea').exists()).toBe(false)

    const action = wrapper.get('a')
    expect(action.text()).toContain('开始下载')
    expect(action.attributes('href')).toBe('/new')
  })

  it('does not name the machinery behind it', async () => {
    const router = await testRouter('/')
    const wrapper = mount(UserHomeView, { global: { plugins: [router] } })
    const text = wrapper.text()

    for (const internal of ['服务端解析', '解析', '任务', 'resolve', 'Task']) {
      expect(text).not.toContain(internal)
    }
  })
})

//
// ---------------------------------------------------------------------------
// The single-resource flow, which is what "download something" means here.
// ---------------------------------------------------------------------------
//

const postResolution: ResolvedResource = {
  resolve_id: 'receipt-1',
  platform: 'douyin',
  resource_type: 'post',
  source_url: 'https://v.douyin.com/M-kmspLye0o/',
  resolved_url: 'https://www.douyin.com/video/7657271784144009946',
  identity: { aweme_id: '7657271784144009946' },
  expires_in_seconds: 600,
}

const CREATED: CreatedTask = {
  task_id: 'task-1',
  task_type: 'post_download',
  resolve_id: 'receipt-1',
}

function taskIn(state: TaskState, overrides: Partial<Task> = {}): Task {
  return {
    task_id: 'task-1',
    task_type: 'post_download',
    state,
    title: '下载作品',
    message: null,
    created_at: '2026-08-24T10:00:00',
    started_at: '2026-08-24T10:00:01',
    finished_at: null,
    progress: { current: 0, total: 1 },
    metadata: {},
    items: [],
    ...overrides,
  }
}

async function settle() {
  for (let index = 0; index < 6; index += 1) {
    await Promise.resolve()
  }
  await nextTick()
}

async function mountDownload(api: Record<string, unknown> = {}) {
  const spies = {
    resolveResource: vi.fn(async () => postResolution),
    createTask: vi.fn(async () => CREATED),
    getTask: vi.fn(async () => taskIn('running')),
    ...api,
  }
  const router = await testRouter('/new')
  const wrapper = mount(NewDownloadView, {
    props: { api: spies },
    global: { plugins: [router] },
  })
  return { wrapper, spies }
}

function buttonSaying(wrapper: VueWrapper, text: string) {
  return wrapper.findAll('button').find((button) => button.text().includes(text))
}

function linkSaying(wrapper: VueWrapper, text: string) {
  return wrapper.findAll('a').find((link) => link.text().includes(text))
}

async function identify(wrapper: VueWrapper, input = '4.33 复制打开抖音 https://v.douyin.com/abc/') {
  await wrapper.get('textarea').setValue(input)
  await buttonSaying(wrapper, '识别内容')?.trigger('click')
  await settle()
}

describe('identifying what was pasted', () => {
  it('opens on the single-resource flow', async () => {
    //
    // Batch stays reachable, but one link is what most people arrive with, so
    // it is what the screen is already showing.
    //
    const { wrapper } = await mountDownload()

    expect(wrapper.get('[data-mode="single"]').classes()).toContain('mode__button--active')
    expect(wrapper.find('.batch-input').exists()).toBe(false)
    expect(wrapper.get('textarea').element.value).toBe('')
  })

  it('cannot identify an empty box', async () => {
    const { wrapper, spies } = await mountDownload()

    const identifyButton = buttonSaying(wrapper, '识别内容')
    expect(identifyButton?.attributes('disabled')).toBeDefined()

    await identifyButton?.trigger('click')
    await settle()

    expect(spies.resolveResource).not.toHaveBeenCalled()
  })

  it('sends the pasted text exactly as typed', async () => {
    //
    // Pulling the link out of a share sentence stays the server's job. A regex
    // here would be a second opinion that eventually disagrees with it.
    //
    const { wrapper, spies } = await mountDownload()
    const pasted = '4.33 复制打开抖音，看看【某某的作品】 https://v.douyin.com/abc/'

    await identify(wrapper, pasted)

    expect(spies.resolveResource).toHaveBeenCalledWith(pasted)
  })

  it('describes what came back in words rather than identifiers', async () => {
    const { wrapper } = await mountDownload()
    await identify(wrapper)

    const card = wrapper.getComponent(ResourceResolutionCard)
    expect(card.text()).toContain('识别结果')
    expect(card.text()).toContain('作品')
    expect(card.text()).toContain('抖音')
    expect(card.get('a').attributes('href')).toBe(postResolution.source_url)
  })

  it('keeps the receipt and the resource identity off the screen', async () => {
    //
    // The receipt still does all the work - it is the only thing the create
    // request carries - it simply is not the user's business.
    //
    const { wrapper } = await mountDownload()
    await identify(wrapper)
    const text = wrapper.text()

    for (const internal of [
      postResolution.resolve_id,
      postResolution.identity.aweme_id,
      postResolution.resolved_url,
      '作品 ID',
      '解析后链接',
      '凭证',
      'receipt',
      'resolve_id',
    ]) {
      expect(text).not.toContain(internal)
    }
  })
})

describe('starting the download', () => {
  it('creates the task through the existing flow, on the receipt alone', async () => {
    const { wrapper, spies } = await mountDownload()
    await identify(wrapper)

    const start = buttonSaying(wrapper, '开始下载')
    expect(start).toBeTruthy()
    await start?.trigger('click')
    await settle()

    expect(spies.createTask).toHaveBeenCalledWith({
      resolve_id: 'receipt-1',
      task_type: 'post_download',
    })
  })

  it('says the download has started and offers the way to all of them', async () => {
    const { wrapper } = await mountDownload()
    await identify(wrapper)
    await buttonSaying(wrapper, '开始下载')?.trigger('click')
    await settle()

    expect(wrapper.text()).toContain('下载已开始')
    expect(linkSaying(wrapper, '查看所有任务')?.attributes('href')).toBe('/tasks')
    expect(wrapper.text()).not.toContain(CREATED.task_id)
    expect(wrapper.text()).not.toContain('任务 ID')
  })

  it('shows the state and the progress of the running download', async () => {
    const { wrapper } = await mountDownload({
      getTask: vi.fn(async () => taskIn('running', { progress: { current: 1, total: 4 } })),
    })
    await identify(wrapper)
    await buttonSaying(wrapper, '开始下载')?.trigger('click')
    await settle()

    expect(wrapper.text()).toContain('进行中')
    expect(wrapper.text()).toContain('1 / 4')
  })

  it('reports a failure as a reason rather than a state name', async () => {
    const { wrapper } = await mountDownload({
      getTask: vi.fn(async () => taskIn('failed', { message: '作品已被删除' })),
    })
    await identify(wrapper)
    await buttonSaying(wrapper, '开始下载')?.trigger('click')
    await settle()

    expect(wrapper.text()).toContain('作品已被删除')
  })
})

describe('failures the user can act on', () => {
  it('asks for a fresh identification when the receipt aged out', async () => {
    const gone = new ApiError({
      kind: 'backend',
      status: 404,
      code: 404,
      message: '解析结果不存在或已过期，请重新解析',
    })
    const { wrapper, spies } = await mountDownload({
      createTask: vi.fn(async () => Promise.reject(gone)),
    })
    await identify(wrapper)
    await buttonSaying(wrapper, '开始下载')?.trigger('click')
    await settle()

    expect(wrapper.text()).toContain('链接识别结果已过期，请重新识别。')
    expect(buttonSaying(wrapper, '重新识别')).toBeTruthy()
    //
    // Nothing was created, so nothing is tracked. Showing a download here would
    // invent a record the server never made.
    //
    expect(wrapper.text()).not.toContain('下载已开始')
    expect(spies.getTask).not.toHaveBeenCalled()
  })

  it('returns to the box with the text intact rather than re-identifying itself', async () => {
    const gone = new ApiError({
      kind: 'backend',
      status: 404,
      code: 404,
      message: '解析结果不存在或已过期，请重新解析',
    })
    const { wrapper, spies } = await mountDownload({
      createTask: vi.fn(async () => Promise.reject(gone)),
    })
    await identify(wrapper, 'https://v.douyin.com/abc/')
    await buttonSaying(wrapper, '开始下载')?.trigger('click')
    await settle()

    await buttonSaying(wrapper, '重新识别')?.trigger('click')
    await nextTick()

    expect(wrapper.text()).not.toContain('识别结果')
    expect(wrapper.get('textarea').element.value).toBe('https://v.douyin.com/abc/')
    expect(spies.resolveResource).toHaveBeenCalledTimes(1)
  })

  it('does not put a browser transport failure on the screen', async () => {
    const offline = new ApiError({
      kind: 'network',
      status: null,
      code: null,
      message: 'Failed to fetch',
    })
    const { wrapper } = await mountDownload({
      resolveResource: vi.fn(async () => Promise.reject(offline)),
    })
    await identify(wrapper)

    const alert = wrapper.get('[role="alert"]')
    expect(alert.text()).toContain('网络连接失败')
    expect(alert.text()).not.toContain('Failed to fetch')
  })
})

describe('protections the simpler wording must not have removed', () => {
  it('drops a late identification for text the user has moved on from', async () => {
    //
    // Paste A, identify A, edit to B. The answer about A must not land under
    // text that says B - with a download button beneath it that would start A.
    //
    let settleFirst: (value: ResolvedResource) => void = () => {}
    const slow = new Promise<ResolvedResource>((resolve) => {
      settleFirst = resolve
    })
    const { wrapper, spies } = await mountDownload({
      resolveResource: vi.fn(() => slow),
    })
    await wrapper.get('textarea').setValue('https://v.douyin.com/AAA/')
    await buttonSaying(wrapper, '识别内容')?.trigger('click')

    await wrapper.get('textarea').setValue('https://v.douyin.com/BBB/')
    settleFirst(postResolution)
    await settle()

    expect(wrapper.text()).not.toContain('识别结果')
    expect(buttonSaying(wrapper, '开始下载')).toBeUndefined()
    expect(spies.createTask).not.toHaveBeenCalled()
  })

  it('withdraws an identification once the text is edited', async () => {
    const { wrapper, spies } = await mountDownload()
    await identify(wrapper)
    expect(wrapper.text()).toContain('识别结果')

    await wrapper.get('textarea').setValue('https://v.douyin.com/something-else/')
    await nextTick()

    expect(wrapper.text()).not.toContain('识别结果')
    expect(spies.createTask).not.toHaveBeenCalled()
  })

  it('stops reading the status once the screen is gone', async () => {
    vi.useFakeTimers()
    const getTask = vi.fn(async () => taskIn('running'))
    const { wrapper } = await mountDownload({ getTask })
    await identify(wrapper)
    await buttonSaying(wrapper, '开始下载')?.trigger('click')
    await settle()
    const before = getTask.mock.calls.length

    wrapper.unmount()
    await vi.advanceTimersByTimeAsync(TASK_POLL_INTERVAL_MS * 5)

    expect(getTask).toHaveBeenCalledTimes(before)
  })

  it('still refuses to start a whole back catalogue without a tick', async () => {
    const ownerResolution: ResolvedResource = {
      ...postResolution,
      resource_type: 'owner',
      identity: { sec_user_id: 'MS4wLjABAAAA-owner' },
    }
    const { wrapper, spies } = await mountDownload({
      resolveResource: vi.fn(async () => ownerResolution),
    })
    await identify(wrapper)

    const start = buttonSaying(wrapper, '开始下载全部作品')
    expect(start?.attributes('disabled')).toBeDefined()
    await start?.trigger('click')
    await settle()
    expect(spies.createTask).not.toHaveBeenCalled()

    await wrapper.get('input[type="checkbox"]').setValue(true)
    await nextTick()
    await buttonSaying(wrapper, '开始下载全部作品')?.trigger('click')
    await settle()

    expect(spies.createTask).toHaveBeenCalledWith({
      resolve_id: 'receipt-1',
      task_type: 'owner_batch_download',
      options: { mode: 'all' },
    })
  })
})

describe('several links at once, as a secondary way in', () => {
  const ownerResolution: ResolvedResource = {
    ...postResolution,
    resolve_id: 'receipt-2',
    resource_type: 'owner',
    source_url: 'https://www.douyin.com/user/2',
    resolved_url: 'https://www.douyin.com/user/2',
    identity: { sec_user_id: 'MS4wLjABAAAA-owner' },
  }

  const batch: BatchResolveResult = {
    total: 3,
    resolved_count: 2,
    failed_count: 1,
    items: [
      { index: 0, status: 'resolved', resolution: postResolution },
      {
        index: 1,
        status: 'failed',
        error: { kind: 'unsupported_platform', message: '暂不支持该平台的链接' },
      },
      { index: 2, status: 'resolved', resolution: ownerResolution },
    ],
  }

  async function mountBatch() {
    const router = await testRouter('/new')
    const batchCreateTask = vi.fn(
      async (request: CreateTaskRequest): Promise<CreatedTask> => ({
        task_id: `T-${request.resolve_id}`,
        task_type: request.task_type,
        resolve_id: request.resolve_id,
      }),
    )
    const wrapper = mount(NewDownloadView, {
      props: {
        api: { resolveResource: vi.fn() },
        batchApi: {
          resolveResources: vi.fn(async () => batch),
          createTask: batchCreateTask,
        },
      },
      global: { plugins: [router] },
    })
    await wrapper.get('[data-mode="batch"]').trigger('click')
    await wrapper.get('.batch-input textarea').setValue('three links')
    await wrapper.get('.batch-input button').trigger('click')
    await settle()
    return { wrapper, batchCreateTask }
  }

  it('reviews the links in download language, without identifiers', async () => {
    const { wrapper } = await mountBatch()
    const review = wrapper.get('.batch-review')

    expect(review.text()).toContain('暂不支持该平台的链接')
    expect(review.text()).toContain('开始下载')
    for (const internal of [
      '作品 ID',
      '主播 ID',
      postResolution.identity.aweme_id,
      ownerResolution.identity.sec_user_id,
      '凭证',
      '创建任务',
    ]) {
      expect(review.text()).not.toContain(internal)
    }
  })

  it('keeps every guard the batch flow already had', async () => {
    const { wrapper, batchCreateTask } = await mountBatch()
    const rows = wrapper.findAll('.batch-review__item')

    //
    // Unchanged from before this phase: a failed row is not selectable, an
    // owner row starts unselected, and its whole-catalogue tick is required.
    //
    expect(rows[1].find('input[type="checkbox"]').exists()).toBe(false)
    expect((rows[0].find('input[type="checkbox"]').element as HTMLInputElement).checked).toBe(true)
    expect((rows[2].find('input[type="checkbox"]').element as HTMLInputElement).checked).toBe(false)

    await rows[2].get('input[type="checkbox"]').setValue(true)
    expect(wrapper.get('.batch-review__create').attributes('disabled')).toBeDefined()

    await rows[2].get('.batch-review__confirm input').setValue(true)
    await wrapper.get('.batch-review__create').trigger('click')
    await settle()

    expect(batchCreateTask).toHaveBeenCalledTimes(2)
    expect(wrapper.get('.batch-review__task-link').attributes('href')).toContain('/tasks')
  })
})
