import { describe, expect, it, vi } from 'vitest'

import { assignPersonAccount, inspectPersonAssignment } from '../../src/api/people'
import { resolveResource } from '../../src/api/resolve'
import { createTask, getTask, listTasks } from '../../src/api/tasks'
import type {
  PersonAssignmentResult,
  PersonIdentityInspection,
} from '../../src/types/person'
import type { ResolvedResource } from '../../src/types/resolution'
import type { CreatedTask, Task, TaskList } from '../../src/types/task'

const SEC_UID = 'MS4wLjABAAAAGZkW5n1EHZD_TFyQ-QiaISBPemtKFxVVdhLSeoXhh-U'
const AWEME_ID = '7657271784144009946'

function stubFetch(data: unknown, status = 200, code = status) {
  const fake = vi.fn((_url: string, _init?: RequestInit) =>
    Promise.resolve(
      new Response(JSON.stringify({ status: 'success', code, data }), {
        status,
        headers: { 'Content-Type': 'application/json' },
      }),
    ),
  )
  vi.stubGlobal('fetch', fake)
  return fake
}

function callOf(fake: ReturnType<typeof stubFetch>) {
  const [url, init] = fake.mock.calls[0]
  const options = init ?? {}
  return { url, init: options, body: options.body ? JSON.parse(String(options.body)) : undefined }
}

describe('resolveResource', () => {
  it('posts the pasted text to /api/resolve', async () => {
    const fake = stubFetch({})

    await resolveResource('4.33 复制打开抖音 https://v.douyin.com/abc/')

    const { url, init, body } = callOf(fake)
    expect(url).toBe('/api/resolve')
    expect(init.method).toBe('POST')
    expect(body).toEqual({ input: '4.33 复制打开抖音 https://v.douyin.com/abc/' })
  })

  it('hands back the resolution', async () => {
    const resolution: ResolvedResource = {
      resolve_id: 'receipt-1',
      platform: 'douyin',
      resource_type: 'post',
      source_url: 'https://v.douyin.com/abc/',
      resolved_url: `https://www.douyin.com/video/${AWEME_ID}`,
      identity: { aweme_id: AWEME_ID },
      expires_in_seconds: 600,
    }
    stubFetch(resolution)

    await expect(resolveResource('https://v.douyin.com/abc/')).resolves.toEqual(resolution)
  })

  it('narrows the identity by resource type', async () => {
    //
    // A type-level assertion as much as a runtime one: reading `sec_user_id`
    // off a post must not compile, which is why the union is discriminated.
    //
    stubFetch({
      resolve_id: 'receipt-2',
      platform: 'douyin',
      resource_type: 'owner',
      source_url: 'https://v.douyin.com/abc/',
      resolved_url: `https://www.douyin.com/user/${SEC_UID}`,
      identity: { sec_user_id: SEC_UID },
      expires_in_seconds: 600,
    })

    const resolution = await resolveResource('https://v.douyin.com/abc/')

    expect(resolution.resource_type).toBe('owner')
    if (resolution.resource_type === 'owner') {
      expect(resolution.identity.sec_user_id).toBe(SEC_UID)
    }
  })
})

describe('createTask', () => {
  const created: CreatedTask = {
    task_id: 'task-1',
    task_type: 'post_download',
    resolve_id: 'receipt-1',
  }

  it('posts a post download without options', async () => {
    const fake = stubFetch(created, 202)

    await createTask({ resolve_id: 'receipt-1', task_type: 'post_download' })

    const { url, init, body } = callOf(fake)
    expect(url).toBe('/api/tasks')
    expect(init.method).toBe('POST')
    expect(body).toEqual({ resolve_id: 'receipt-1', task_type: 'post_download' })
  })

  it('posts a recording without options', async () => {
    const fake = stubFetch({ ...created, task_type: 'live_record' }, 202)

    await createTask({ resolve_id: 'receipt-1', task_type: 'live_record' })

    expect(callOf(fake).body).toEqual({
      resolve_id: 'receipt-1',
      task_type: 'live_record',
    })
  })

  it('posts an owner batch with the mode stated in words', async () => {
    //
    // The backend requires it, and for a reason worth keeping visible here: an
    // owner link on its own does not mean "download the entire back catalogue".
    //
    const fake = stubFetch({ ...created, task_type: 'owner_batch_download' }, 202)

    await createTask({
      resolve_id: 'receipt-1',
      task_type: 'owner_batch_download',
      options: { mode: 'all' },
    })

    expect(callOf(fake).body).toEqual({
      resolve_id: 'receipt-1',
      task_type: 'owner_batch_download',
      options: { mode: 'all' },
    })
  })

  it('accepts the 202 the backend answers', async () => {
    stubFetch(created, 202)

    await expect(
      createTask({ resolve_id: 'receipt-1', task_type: 'post_download' }),
    ).resolves.toEqual(created)
  })

  it('never sends anything describing the resource', async () => {
    //
    // The receipt is the whole claim.  An aweme id or a url in this body would
    // be refused by the backend as an unknown field - and should never be
    // constructible here in the first place.
    //
    const fake = stubFetch(created, 202)

    await createTask({ resolve_id: 'receipt-1', task_type: 'post_download' })

    const sent = Object.keys(callOf(fake).body as object)
    expect(sent.sort()).toEqual(['resolve_id', 'task_type'])
  })
})

describe('listTasks', () => {
  const empty: TaskList = { items: [], total: 0 }

  it('reads /api/tasks with no filters', async () => {
    const fake = stubFetch(empty)

    await listTasks()

    expect(callOf(fake).url).toBe('/api/tasks')
  })

  it('passes the filters it was given', async () => {
    const fake = stubFetch(empty)

    await listTasks({ state: 'running', type: 'post_download', limit: 20 })

    expect(callOf(fake).url).toBe('/api/tasks?state=running&type=post_download&limit=20')
  })

  it('omits the filters it was not given', async () => {
    const fake = stubFetch(empty)

    await listTasks({ state: 'running' })

    expect(callOf(fake).url).toBe('/api/tasks?state=running')
  })

  it('hands back the page and the total separately', async () => {
    stubFetch({ items: [], total: 42 })

    await expect(listTasks({ limit: 1 })).resolves.toEqual({ items: [], total: 42 })
  })
})

describe('getTask', () => {
  const task: Task = {
    task_id: 'task-1',
    task_type: 'post_download',
    state: 'running',
    title: '下载作品',
    message: null,
    created_at: '2026-08-15T09:30:15.250',
    started_at: '2026-08-15T09:30:16.250',
    finished_at: null,
    progress: { current: 0, total: 1 },
    metadata: { platform: 'douyin', source: 'task_api' },
    items: [],
  }

  it('reads one task by id', async () => {
    const fake = stubFetch(task)

    await getTask('task-1')

    expect(callOf(fake).url).toBe('/api/tasks/task-1')
  })

  it('escapes an id that would otherwise change the path', async () => {
    const fake = stubFetch(task)

    await getTask('../secret')

    expect(callOf(fake).url).toBe('/api/tasks/..%2Fsecret')
  })

  it('hands back the task', async () => {
    stubFetch(task)

    await expect(getTask('task-1')).resolves.toEqual(task)
  })

  it('reports an unknown total as null rather than zero', async () => {
    //
    // A recording has no final count.  Zero would render as a progress bar
    // stuck at the start; null is what lets the UI say "unknown" instead.
    //
    stubFetch({ ...task, task_type: 'live_record', progress: { current: 97, total: null } })

    const answered = await getTask('task-1')

    expect(answered.progress.total).toBeNull()
  })
})

describe('listTasks with an abort signal', () => {
  it('passes the signal down to the transport', async () => {
    const fake = stubFetch({ items: [], total: 0 })
    const controller = new AbortController()

    await listTasks({ state: 'running' }, controller.signal)

    const { init } = callOf(fake)
    expect(init.signal).toBe(controller.signal)
  })

  it('sends no signal when none is given', async () => {
    //
    // Backward compatible by omission rather than by passing undefined: every
    // existing caller keeps the request it had.
    //
    const fake = stubFetch({ items: [], total: 0 })

    await listTasks({ state: 'running' })

    expect(callOf(fake).init.signal).toBeUndefined()
  })

  it('still filters the same way with a signal attached', async () => {
    const fake = stubFetch({ items: [], total: 0 })
    const controller = new AbortController()

    await listTasks({ state: 'failed', type: 'live_probe', limit: 25 }, controller.signal)

    expect(callOf(fake).url).toBe('/api/tasks?state=failed&type=live_probe&limit=25')
  })
})


describe('assignPersonAccount', () => {
  //
  // The one endpoint that creates a person and attaches an account together.
  // What it must never carry is an identity: the account is named by the
  // receipt, and a request that could describe it itself would let this browser
  // attach an owner the server never resolved.
  //

  it('posts to /api/person/assignment', async () => {
    const fake = stubFetch({})

    await assignPersonAccount({
      resolve_id: 'receipt-1',
      target: { kind: 'new' },
      role: 'alt',
    })

    const { url, init } = callOf(fake)
    expect(url).toBe('/api/person/assignment')
    expect(init.method).toBe('POST')
  })

  it('sends a new-person target exactly as given', async () => {
    const fake = stubFetch({})

    await assignPersonAccount({
      resolve_id: 'receipt-1',
      target: { kind: 'new', display_name: '张三', note: '备注' },
      role: 'matrix',
    })

    expect(callOf(fake).body).toEqual({
      resolve_id: 'receipt-1',
      target: { kind: 'new', display_name: '张三', note: '备注' },
      role: 'matrix',
    })
  })

  it('sends an existing-person target exactly as given', async () => {
    const fake = stubFetch({})

    await assignPersonAccount({
      resolve_id: 'receipt-1',
      target: { kind: 'existing', person_id: 12 },
      role: 'main',
    })

    expect(callOf(fake).body).toEqual({
      resolve_id: 'receipt-1',
      target: { kind: 'existing', person_id: 12 },
      role: 'main',
    })
  })

  it('carries the two confirmations when they are given', async () => {
    const fake = stubFetch({})

    await assignPersonAccount({
      resolve_id: 'receipt-1',
      target: { kind: 'existing', person_id: 12 },
      role: 'main',
      allow_move: true,
      replace_main: { demote_to: 'alt' },
    })

    const { body } = callOf(fake)
    expect(body.allow_move).toBe(true)
    expect(body.replace_main).toEqual({ demote_to: 'alt' })
  })

  it('hands back what the server decided', async () => {
    const result: PersonAssignmentResult = {
      person_id: 12,
      owner_user_id: 'acc-9',
      role: 'alt',
      created_person: true,
      display_name: '张三',
    }
    stubFetch(result)

    await expect(
      assignPersonAccount({
        resolve_id: 'receipt-1',
        target: { kind: 'new' },
        role: 'alt',
      }),
    ).resolves.toEqual(result)
  })
})


describe('inspectPersonAssignment', () => {
  //
  // The question the page asks between resolving a link and offering a form:
  // do we already have this account, and does anybody already hold it?
  //
  // It carries a receipt and nothing else, for the same reason the assignment
  // does - but with a sharper consequence. This answer decides whether the user
  // is shown a "create a new person" button, so a request able to name the
  // account would let a browser choose which account gets checked.
  //

  it('posts to /api/person/inspect', async () => {
    const fake = stubFetch({ owner: { owner_user_id: 'acc-9' }, known_account: false, assignment: null })

    await inspectPersonAssignment('receipt-1')

    const { url, init } = callOf(fake)
    expect(url).toBe('/api/person/inspect')
    expect(init.method).toBe('POST')
  })

  it('sends the receipt and nothing else', async () => {
    const fake = stubFetch({ owner: { owner_user_id: 'acc-9' }, known_account: false, assignment: null })

    await inspectPersonAssignment('receipt-1')

    expect(callOf(fake).body).toEqual({ resolve_id: 'receipt-1' })
  })

  it.each(['owner_user_id', 'sec_user_id', 'nickname', 'person_id', 'role'])(
    'never sends %s',
    async (field) => {
      const fake = stubFetch({ owner: { owner_user_id: 'acc-9' }, known_account: false, assignment: null })

      await inspectPersonAssignment('receipt-1')

      expect(JSON.stringify(callOf(fake).body)).not.toContain(field)
    },
  )

  it('hands back the account and who holds it', async () => {
    const answer: PersonIdentityInspection = {
      owner: { owner_user_id: 'acc-9', sec_user_id: 'MS4wLjABAAAA', nickname: '程儿' },
      known_account: true,
      assignment: { person_id: 12, display_name: '程儿', role: 'main' },
    }
    stubFetch(answer)

    await expect(inspectPersonAssignment('receipt-1')).resolves.toEqual(answer)
  })

  it('hands back a known account nobody has filed', async () => {
    const answer: PersonIdentityInspection = {
      owner: { owner_user_id: 'acc-9', sec_user_id: null, nickname: '程儿' },
      known_account: true,
      assignment: null,
    }
    stubFetch(answer)

    await expect(inspectPersonAssignment('receipt-1')).resolves.toEqual(answer)
  })
})
