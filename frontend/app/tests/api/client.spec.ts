import { describe, expect, it, vi } from 'vitest'

import { ApiError, apiBaseUrl, request } from '../../src/api/client'

//
// Every test in this file drives a fake `fetch`.  Nothing here may reach a
// network, a Flask process or a file: the client's whole job is turning one
// Response into either data or an ApiError, and that is testable in isolation.
//

function jsonResponse(body: unknown, status = 200): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { 'Content-Type': 'application/json' },
  })
}

function textResponse(body: string, status = 200): Response {
  return new Response(body, {
    status,
    headers: { 'Content-Type': 'text/html' },
  })
}

function stubFetch(response: Response | Error) {
  const fake = vi.fn((_url: string, _init?: RequestInit) =>
    response instanceof Error ? Promise.reject(response) : Promise.resolve(response),
  )
  vi.stubGlobal('fetch', fake)
  return fake
}

//
// Awaiting a rejection and typing it, in one place.  Also asserts the call
// really did fail: a `.catch` alone would quietly pass if it ever succeeded.
//
async function failureOf(promise: Promise<unknown>): Promise<ApiError> {
  try {
    await promise
  } catch (caught) {
    return caught as ApiError
  }
  throw new Error('expected the request to fail, but it resolved')
}

describe('apiBaseUrl', () => {
  it('is a same-origin relative path', () => {
    //
    // Never an absolute hostname.  The app is served by the same process that
    // answers the api, so a relative base is both correct and the only thing
    // that survives being deployed anywhere.
    //
    expect(apiBaseUrl()).toBe('/api')
    expect(apiBaseUrl()).not.toMatch(/^https?:\/\//)
  })
})

describe('request - success', () => {
  it('unwraps the data of a 200 envelope', async () => {
    stubFetch(jsonResponse({ status: 'success', code: 200, data: { total: 3 } }))

    await expect(request<{ total: number }>('/tasks')).resolves.toEqual({ total: 3 })
  })

  it('unwraps the data of a 202 envelope', async () => {
    //
    // Task creation answers 202, and it is a success like any other.  A client
    // that only accepted 200 would reject every accepted task.
    //
    stubFetch(
      jsonResponse({ status: 'success', code: 202, data: { task_id: 'T' } }, 202),
    )

    await expect(request<{ task_id: string }>('/tasks', { method: 'POST' })).resolves.toEqual(
      { task_id: 'T' },
    )
  })

  it('sends json when given a body', async () => {
    const fetched = stubFetch(jsonResponse({ status: 'success', code: 200, data: {} }))

    await request('/resolve', { method: 'POST', body: { input: 'x' } })

    const [url, init] = fetched.mock.calls[0] as [string, RequestInit]
    expect(url).toBe('/api/resolve')
    expect(init.method).toBe('POST')
    expect(init.body).toBe(JSON.stringify({ input: 'x' }))
    expect(new Headers(init.headers).get('Content-Type')).toBe('application/json')
  })

  it('sends no body and no content type for a plain read', async () => {
    const fetched = stubFetch(jsonResponse({ status: 'success', code: 200, data: {} }))

    await request('/tasks')

    const [, init] = fetched.mock.calls[0] as [string, RequestInit]
    expect(init.body).toBeUndefined()
    expect(new Headers(init.headers).get('Content-Type')).toBeNull()
  })

  it('appends query parameters, skipping the ones not given', async () => {
    const fetched = stubFetch(jsonResponse({ status: 'success', code: 200, data: {} }))

    await request('/tasks', { query: { state: 'running', type: undefined, limit: 5 } })

    expect(fetched.mock.calls[0][0]).toBe('/api/tasks?state=running&limit=5')
  })
})

describe('request - what a refusal carries beyond its message', () => {
  //
  // The person endpoints answer 409 with a machine-readable `kind` and the
  // facts the page needs to offer a next step - who already holds an account,
  // what the current main is called.  Both sit at the top level of the
  // envelope, beside `status`, because a failure envelope has no `data`.
  //
  // Before this, the client threw all of it away and kept the Chinese prose.
  // A screen that has to tell "this account belongs to somebody else" from
  // "this person already has a main" - two 409s whose answers are opposite -
  // would have had to match on that prose.
  //

  it('keeps the backend kind separately from the transport kind', async () => {
    stubFetch(
      jsonResponse(
        {
          status: 'error',
          code: 409,
          message: '该人物已经有大号了',
          kind: 'main_account_conflict',
        },
        409,
      ),
    )

    const error = await failureOf(request('/person/assignment', { method: 'POST' }))

    //
    // `kind` still says how the request failed, which is what every existing
    // caller branches on.  What the backend called it is a different question
    // and gets a different field.
    //
    expect(error.kind).toBe('backend')
    expect(error.backendKind).toBe('main_account_conflict')
  })

  it('keeps the extra fields a conflict carries', async () => {
    stubFetch(
      jsonResponse(
        {
          status: 'error',
          code: 409,
          message: '该账号已归属其他人物',
          kind: 'account_already_attached',
          current_person: { person_id: 7, display_name: '原来的人' },
        },
        409,
      ),
    )

    const error = await failureOf(request('/person/assignment', { method: 'POST' }))

    expect(error.details).toEqual({
      current_person: { person_id: 7, display_name: '原来的人' },
    })
  })

  it('leaves the envelope\'s own fields out of the details', async () => {
    //
    // `status`, `code`, `message` and `kind` are already carried as their own
    // properties.  Repeating them inside `details` would invite two readings of
    // the same fact.
    //
    stubFetch(
      jsonResponse(
        {
          status: 'error',
          code: 409,
          message: '冲突',
          kind: 'main_account_conflict',
          current_main: { owner_user_id: 'acc-1', nickname: '主号' },
        },
        409,
      ),
    )

    const error = await failureOf(request('/person/assignment', { method: 'POST' }))

    expect(Object.keys(error.details ?? {}).sort()).toEqual(['current_main'])
  })

  it('says there was no backend kind when the envelope carried none', async () => {
    //
    // Most endpoints answer without one.  `null` rather than `undefined` so a
    // caller can tell "asked and there was none" from "never populated".
    //
    stubFetch(jsonResponse({ status: 'error', code: 400, message: '缺少字段' }, 400))

    const error = await failureOf(request('/person', { method: 'POST' }))

    expect(error.backendKind).toBeNull()
    expect(error.details).toBeNull()
  })

  it('ignores a kind that is not a string', async () => {
    stubFetch(
      jsonResponse({ status: 'error', code: 400, message: 'x', kind: 42 }, 400),
    )

    const error = await failureOf(request('/person', { method: 'POST' }))

    expect(error.backendKind).toBeNull()
  })

  it('carries nothing extra on a network failure', async () => {
    stubFetch(new TypeError('Failed to fetch'))

    const error = await failureOf(request('/person'))

    expect(error.kind).toBe('network')
    expect(error.backendKind).toBeNull()
    expect(error.details).toBeNull()
  })

  it('carries nothing extra on a malformed response', async () => {
    stubFetch(textResponse('<html>502</html>', 502))

    const error = await failureOf(request('/person'))

    expect(error.kind).toBe('malformed')
    expect(error.backendKind).toBeNull()
    expect(error.details).toBeNull()
  })

  it('can still be constructed without them', async () => {
    //
    // Every existing `new ApiError({...})` in this codebase and its tests omits
    // the two new fields.  Making them required would have been a rename
    // wearing the costume of an addition.
    //
    const error = new ApiError({ kind: 'backend', status: 400, code: 400, message: 'x' })

    expect(error.backendKind).toBeNull()
    expect(error.details).toBeNull()
  })
})

describe('request - backend refusals', () => {
  it('turns a 400 envelope into an ApiError', async () => {
    stubFetch(
      jsonResponse({ status: 'error', code: 400, message: '一次只能解析一个链接' }, 400),
    )

    //
    // The trap this exists to avoid: a client that read `data` off an error
    // envelope would hand `undefined` to a component and fail somewhere else
    // entirely, long after the request that actually went wrong.
    //
    await expect(request('/resolve', { method: 'POST' })).rejects.toBeInstanceOf(ApiError)
  })

  it('keeps the status, the code and the message', async () => {
    stubFetch(jsonResponse({ status: 'error', code: 404, message: '任务不存在或已过期' }, 404))

    const error = await failureOf(request('/tasks/nope'))

    expect(error).toBeInstanceOf(ApiError)
    expect(error.kind).toBe('backend')
    expect(error.status).toBe(404)
    expect(error.code).toBe(404)
    expect(error.message).toBe('任务不存在或已过期')
  })

  it.each([400, 404, 409, 500, 502, 503])('rejects on HTTP %i', async (status) => {
    stubFetch(jsonResponse({ status: 'error', code: status, message: 'refused' }, status))

    const error = await failureOf(request('/tasks'))

    expect(error).toBeInstanceOf(ApiError)
    expect(error.status).toBe(status)
  })

  it('rejects a non-2xx even when the envelope claims success', async () => {
    //
    // The two disagreeing means something between here and the app rewrote one
    // of them.  Believing the body over the transport would be the wrong guess.
    //
    stubFetch(jsonResponse({ status: 'success', code: 200, data: {} }, 500))

    await expect(request('/tasks')).rejects.toBeInstanceOf(ApiError)
  })

  it('rejects a 200 whose envelope says error', async () => {
    stubFetch(jsonResponse({ status: 'error', code: 400, message: 'bad' }, 200))

    const error = await failureOf(request('/tasks'))

    expect(error.kind).toBe('backend')
    expect(error.message).toBe('bad')
  })
})

describe('request - transport and shape failures', () => {
  it('turns a network failure into an ApiError', async () => {
    stubFetch(new TypeError('Failed to fetch'))

    const error = await failureOf(request('/tasks'))

    expect(error).toBeInstanceOf(ApiError)
    expect(error.kind).toBe('network')
    expect(error.status).toBeNull()
  })

  it('turns an unparseable body into an ApiError', async () => {
    stubFetch(textResponse('<html>502 Bad Gateway</html>', 502))

    const error = await failureOf(request('/tasks'))

    expect(error).toBeInstanceOf(ApiError)
    expect(error.status).toBe(502)
  })

  it('turns a parseable body that is not an envelope into an ApiError', async () => {
    stubFetch(jsonResponse({ unexpected: true }))

    const error = await failureOf(request('/tasks'))

    expect(error).toBeInstanceOf(ApiError)
    expect(error.kind).toBe('malformed')
  })

  it('rejects an envelope whose status is neither success nor error', async () => {
    stubFetch(jsonResponse({ status: 'partial', code: 200, data: {} }))

    await expect(request('/tasks')).rejects.toBeInstanceOf(ApiError)
  })

  it('never hands back the raw Response', async () => {
    //
    // A Response is single-read and not serialisable; letting one become UI
    // state is how a body gets consumed twice and the second read comes back
    // empty for reasons nothing in the component explains.
    //
    stubFetch(jsonResponse({ status: 'success', code: 200, data: { ok: true } }))

    const value = await request('/tasks')

    expect(value).not.toBeInstanceOf(Response)
    expect(value).toEqual({ ok: true })
  })
})

describe('ApiError', () => {
  it('is a real Error', () => {
    const error = new ApiError({ kind: 'backend', status: 400, code: 400, message: 'x' })

    expect(error).toBeInstanceOf(Error)
    expect(error.name).toBe('ApiError')
    expect(error.message).toBe('x')
  })
})

describe('methods beyond GET and POST', () => {
  it('sends a PATCH with a json body', async () => {
    //
    // The person api really uses these two verbs; adding them here is what
    // keeps every call in this project going through one client rather than a
    // second one growing up beside it.
    //
    const fetched = stubFetch(jsonResponse({ status: 'success', code: 200, data: {} }))

    await request('/person/7', { method: 'PATCH', body: { note: '改过的备注' } })

    const [url, init] = fetched.mock.calls[0] as [string, RequestInit]
    expect(url).toBe('/api/person/7')
    expect(init.method).toBe('PATCH')
    expect(init.body).toBe(JSON.stringify({ note: '改过的备注' }))
    expect(new Headers(init.headers).get('Content-Type')).toBe('application/json')
  })

  it('sends a DELETE with no body at all', async () => {
    //
    // Not an empty string and not "{}": a body on a DELETE is the kind of thing
    // a proxy or a framework is entitled to reject.
    //
    const fetched = stubFetch(jsonResponse({ status: 'success', code: 200, data: {} }))

    await request('/person/7', { method: 'DELETE' })

    const [, init] = fetched.mock.calls[0] as [string, RequestInit]
    expect(init.method).toBe('DELETE')
    expect(init.body).toBeUndefined()
    expect(new Headers(init.headers).get('Content-Type')).toBeNull()
  })

  it('puts a DELETE identifier in the query string', async () => {
    const fetched = stubFetch(jsonResponse({ status: 'success', code: 200, data: {} }))

    await request('/person/account', {
      method: 'DELETE',
      query: { owner_user_id: '58859666123' },
    })

    expect(fetched.mock.calls[0][0]).toBe('/api/person/account?owner_user_id=58859666123')
  })

  it('unwraps and fails the same way whatever the method', async () => {
    stubFetch(jsonResponse({ status: 'error', code: 404, message: '人物不存在' }, 404))

    const error = await failureOf(request('/person/7', { method: 'DELETE' }))

    expect(error).toBeInstanceOf(ApiError)
    expect(error.status).toBe(404)
    expect(error.message).toBe('人物不存在')
  })
})
