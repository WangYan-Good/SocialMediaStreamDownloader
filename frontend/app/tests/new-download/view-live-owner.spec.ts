import { mount } from '@vue/test-utils'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { nextTick } from 'vue'

import NewDownloadView from '../../src/views/NewDownloadView.vue'
import type { CreatedTask, Task, TaskState } from '../../src/types/task'
import { liveResolution, ownerResolution } from './build-request.spec'

const SEC_UID = 'MS4wLjABAAAAGZkW5n1EHZD_TFyQ-QiaISBPemtKFxVVdhLSeoXhh-U'

function taskIn(state: TaskState, overrides: Partial<Task> = {}): Task {
  return {
    task_id: 'task-1',
    task_type: 'post_download',
    state,
    title: null,
    message: null,
    created_at: '2026-08-15T09:30:15.250',
    started_at: null,
    finished_at: null,
    progress: { current: 0, total: 1 },
    metadata: {},
    items: [],
    ...overrides,
  }
}

function mountView(api: Record<string, unknown>) {
  const spies = {
    createTask: vi.fn(async (): Promise<CreatedTask> => ({
      task_id: 'task-1',
      task_type: 'post_download',
      resolve_id: 'receipt-1',
    })),
    getTask: vi.fn(async () => taskIn('pending')),
    ...api,
  }
  const wrapper = mount(NewDownloadView, { props: { api: spies } })
  return { wrapper, spies }
}

async function settle() {
  for (let index = 0; index < 4; index += 1) {
    await Promise.resolve()
  }
  await nextTick()
}

async function resolveWith(api: Record<string, unknown>) {
  const built = mountView(api)
  await built.wrapper.find('textarea').setValue('https://v.douyin.com/abc/')
  await built.wrapper.find('button').trigger('click')
  await settle()
  return built
}

function buttonSaying(wrapper: ReturnType<typeof mount>, text: string) {
  return wrapper.findAll('button').find((button) => button.text().includes(text))
}

beforeEach(() => {
  vi.useFakeTimers()
})

afterEach(() => {
  vi.useRealTimers()
})

describe('a live room, end to end', () => {
  const api = { resolveResource: vi.fn(async () => liveResolution) }

  it('names the resource as a live room', async () => {
    const { wrapper } = await resolveWith({ ...api })

    expect(wrapper.text()).toContain('确认资源')
    expect(wrapper.text()).toContain('直播')
  })

  it('claims nothing about the room the server did not answer', async () => {
    //
    // The resolve endpoint returns an empty identity for a live room on
    // purpose: the number in the url is a web id, not the room id the platform
    // payload uses, and whether anyone is on air changes minute to minute.
    //
    const { wrapper } = await resolveWith({ ...api })
    const text = wrapper.text()

    for (const absent of ['room_id', '房间号', '正在直播', '未开播', '昵称']) {
      expect(text).not.toContain(absent)
    }
  })

  it('offers to record rather than to download', async () => {
    const { wrapper } = await resolveWith({ ...api })

    expect(buttonSaying(wrapper, '开始录制直播')).toBeTruthy()
    expect(buttonSaying(wrapper, '下载该作品')).toBeUndefined()
  })

  it('creates a recording from the receipt alone', async () => {
    const { wrapper, spies } = await resolveWith({ ...api })

    await buttonSaying(wrapper, '开始录制直播')?.trigger('click')
    await settle()

    expect(spies.createTask).toHaveBeenCalledWith({
      resolve_id: 'receipt-1',
      task_type: 'live_record',
    })
  })

  it('renders a recording whose total is unknown', async () => {
    //
    // A recording runs until the broadcast ends. The honest answer is that
    // there is no total - and a template that divided by it anyway would put
    // NaN% on the screen.
    //
    const getTask = vi.fn(async () =>
      taskIn('running', {
        task_type: 'live_record',
        progress: { current: 97, total: null },
      }),
    )
    const { wrapper } = await resolveWith({ ...api, getTask })

    await buttonSaying(wrapper, '开始录制直播')?.trigger('click')
    await settle()

    const text = wrapper.text()
    expect(text).toContain('已处理 97')
    expect(text).toContain('总量未知')
    expect(text).not.toContain('NaN')
    expect(text).not.toContain('Infinity')
  })

  it('asks the platform nothing before creating', async () => {
    const { wrapper, spies } = await resolveWith({ ...api })

    await buttonSaying(wrapper, '开始录制直播')?.trigger('click')
    await settle()

    //
    // No probe. Whether the room is live is the recording's own question, and
    // an answer fetched here would be stale by the time it was acted on.
    //
    expect(vi.mocked(spies.createTask).mock.calls).toHaveLength(1)
  })
})

describe('an owner, end to end', () => {
  const api = { resolveResource: vi.fn(async () => ownerResolution) }

  it('names the resource and its id', async () => {
    const { wrapper } = await resolveWith({ ...api })

    expect(wrapper.text()).toContain('主播')
    expect(wrapper.text()).toContain(SEC_UID)
  })

  it('says plainly that this downloads everything', async () => {
    //
    // "下载" alone would read the same for one post as for a back catalogue of
    // several hundred.
    //
    const { wrapper } = await resolveWith({ ...api })

    expect(buttonSaying(wrapper, '下载全部作品')).toBeTruthy()
  })

  it('will not create until the box is ticked', async () => {
    const { wrapper, spies } = await resolveWith({ ...api })

    const create = buttonSaying(wrapper, '下载全部作品')
    expect(create?.attributes('disabled')).toBeDefined()

    await create?.trigger('click')
    await settle()

    expect(spies.createTask).not.toHaveBeenCalled()
  })

  it('offers the confirmation with a readable label', async () => {
    const { wrapper } = await resolveWith({ ...api })

    const checkbox = wrapper.find('input[type="checkbox"]')
    expect(checkbox.exists()).toBe(true)
    expect(wrapper.find('.confirm__label').text()).toContain('全部作品')
  })

  it('creates the whole-feed download once ticked', async () => {
    const { wrapper, spies } = await resolveWith({ ...api })

    await wrapper.find('input[type="checkbox"]').setValue(true)
    await nextTick()

    const create = buttonSaying(wrapper, '下载全部作品')
    expect(create?.attributes('disabled')).toBeUndefined()
    await create?.trigger('click')
    await settle()

    expect(spies.createTask).toHaveBeenCalledWith({
      resolve_id: 'receipt-1',
      task_type: 'owner_batch_download',
      options: { mode: 'all' },
    })
  })

  it('never offers picking individual posts', async () => {
    //
    // The backend refuses `selected`, because an owner receipt carries only a
    // sec_user_id and not the payloads that mode needs. The legacy owner page
    // still serves that flow.
    //
    const { wrapper } = await resolveWith({ ...api })
    const text = wrapper.text()

    expect(text).not.toContain('选择作品')
    expect(text).not.toContain('aweme_ids')
    expect(wrapper.findAll('input[type="checkbox"]')).toHaveLength(1)
  })

  it('forgets the tick if the text is edited', async () => {
    const { wrapper, spies } = await resolveWith({ ...api })
    await wrapper.find('input[type="checkbox"]').setValue(true)
    await nextTick()

    await wrapper.find('textarea').setValue('https://v.douyin.com/completely-other/')
    await nextTick()

    expect(wrapper.text()).not.toContain('确认资源')
    expect(spies.createTask).not.toHaveBeenCalled()
  })
})

describe('editing the box after resolving', () => {
  it('withdraws the resolution and the ability to create', async () => {
    //
    // The invariant the whole screen is built around: a task must never be
    // created for the link that used to be in the box.
    //
    const { wrapper, spies } = await resolveWith({
      resolveResource: vi.fn(async () => liveResolution),
    })
    expect(wrapper.text()).toContain('确认资源')

    await wrapper.find('textarea').setValue('https://v.douyin.com/different/')
    await nextTick()

    expect(wrapper.text()).not.toContain('确认资源')
    expect(buttonSaying(wrapper, '开始录制直播')).toBeUndefined()
    expect(spies.createTask).not.toHaveBeenCalled()
  })

  it('leaves a resolution alone when only spacing changed', async () => {
    const { wrapper } = await resolveWith({
      resolveResource: vi.fn(async () => liveResolution),
    })

    await wrapper.find('textarea').setValue('  https://v.douyin.com/abc/  ')
    await nextTick()

    expect(wrapper.text()).toContain('确认资源')
  })
})
