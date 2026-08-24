import type { ApiEnvelope, ApiErrorKind, ApiFailure } from '@/types/api'

//
// The one place that talks to the backend.
//
// Components never call `fetch` directly, for two reasons that both showed up
// in the legacy interface: the envelope has to be unwrapped identically
// everywhere, and a failure has to arrive as one throwable shape rather than as
// three - a rejected promise, a non-2xx Response, and a 200 whose body says
// "error" - each handled differently at each call site.
//

const DEFAULT_BASE_URL = '/api'
const CSRF_COOKIE_NAME = 'smsd_csrf'
const CSRF_HEADER_NAME = 'X-CSRF-Token'
const MUTATION_METHODS = new Set<RequestMethod>(['POST', 'PATCH', 'DELETE'])

export interface ApiErrorFields {
  kind: ApiErrorKind
  //
  // The HTTP status, or null when the request never got one.
  //
  status: number | null
  //
  // The code inside the envelope, when there was one.
  //
  code: number | null
  message: string
  //
  // Both optional, because only `backend` failures can have them and because
  // every existing construction of this class predates them.  Making them
  // required would have been a rename wearing the costume of an addition.
  //
  backendKind?: string | null
  details?: Record<string, unknown> | null
}

//
// The envelope's own fields, which are already carried as named properties.
// Repeating them inside `details` would leave two readings of the same fact,
// and the one nobody expected would eventually be the one somebody read.
//
const ENVELOPE_FIELDS = new Set(['status', 'code', 'message', 'kind', 'data'])

export class ApiError extends Error {
  //
  // How the request failed: it never arrived, it arrived somewhere that is not
  // this api, or this api refused it.  Unchanged, and deliberately so - every
  // existing caller branches on this, and none of them should have to learn a
  // new vocabulary because the person endpoints grew a richer one.
  //
  readonly kind: ApiErrorKind
  readonly status: number | null
  readonly code: number | null
  //
  // What the *backend* called the refusal, when it said.  A different question
  // from `kind` and therefore a different field: `kind` is about the transport,
  // this is about the decision.
  //
  readonly backendKind: string | null
  //
  // The rest of what the refusal carried, unread and untyped here.  Whoever
  // knows which refusal this is knows what shape to expect; this layer's job is
  // only to stop throwing it away.
  //
  readonly details: Record<string, unknown> | null

  constructor(fields: ApiErrorFields) {
    super(fields.message)
    this.name = 'ApiError'
    this.kind = fields.kind
    this.status = fields.status
    this.code = fields.code
    this.backendKind = fields.backendKind ?? null
    this.details = fields.details ?? null
  }
}

/**
 * Read the machine-readable half of a failure envelope.
 *
 * Both halves are validated rather than believed. A `kind` that is not a string
 * is not a kind, and an envelope carrying nothing beyond its own fields gets
 * `null` rather than an empty object - so "this refusal said nothing extra" and
 * "this refusal said something I have not read yet" stay distinguishable.
 */
function refusalExtras(payload: ApiFailure): {
  backendKind: string | null
  details: Record<string, unknown> | null
} {
  const raw = (payload as Record<string, unknown>).kind
  const backendKind = typeof raw === 'string' && raw.trim() ? raw : null

  const details: Record<string, unknown> = {}
  for (const [key, value] of Object.entries(payload)) {
    if (!ENVELOPE_FIELDS.has(key)) {
      details[key] = value
    }
  }
  return {
    backendKind,
    details: Object.keys(details).length ? details : null,
  }
}

/**
 * Where the json api lives, relative to wherever this app is served from.
 *
 * Relative on purpose.  The bundle is served by the same Flask process that
 * answers `/api`, so an absolute hostname would be both redundant and the one
 * thing that breaks the moment the app is reached by any other name - a LAN
 * address, a tunnel, a reverse proxy.
 */
export function apiBaseUrl(): string {
  const configured = import.meta.env?.VITE_API_BASE_URL
  if (typeof configured === 'string' && configured.trim()) {
    return configured.trim().replace(/\/+$/, '')
  }
  return DEFAULT_BASE_URL
}

export type QueryValue = string | number | boolean | undefined | null

//
// The verbs this backend actually uses. PATCH and DELETE arrived with the
// person api, which edits and removes records; adding them here is what keeps
// every call in this project going through one client rather than a second one
// growing up beside it for two endpoints.
//
export type RequestMethod = 'GET' | 'POST' | 'PATCH' | 'DELETE'

export interface RequestOptions {
  method?: RequestMethod
  body?: unknown
  query?: Record<string, QueryValue>
  signal?: AbortSignal
}

function buildUrl(path: string, query?: Record<string, QueryValue>): string {
  const url = `${apiBaseUrl()}${path.startsWith('/') ? path : `/${path}`}`
  if (!query) {
    return url
  }
  const search = new URLSearchParams()
  for (const [key, value] of Object.entries(query)) {
    //
    // Skipped rather than sent empty: a UI that always holds its filter fields
    // sends blank ones when nothing is chosen, and that means "do not narrow",
    // not "match the empty string".
    //
    if (value === undefined || value === null || value === '') {
      continue
    }
    search.set(key, String(value))
  }
  const encoded = search.toString()
  return encoded ? `${url}?${encoded}` : url
}

function isEnvelope(payload: unknown): payload is ApiEnvelope<unknown> {
  if (typeof payload !== 'object' || payload === null) {
    return false
  }
  const status = (payload as { status?: unknown }).status
  return status === 'success' || status === 'error'
}

function readableCookie(name: string): string | null {
  if (typeof document === 'undefined') {
    return null
  }
  const prefix = `${encodeURIComponent(name)}=`
  for (const part of document.cookie.split(';')) {
    const cookie = part.trim()
    if (!cookie.startsWith(prefix)) {
      continue
    }
    const value = cookie.slice(prefix.length)
    try {
      return decodeURIComponent(value)
    } catch {
      return value
    }
  }
  return null
}

/**
 * Call one backend endpoint and hand back its `data`, or throw an `ApiError`.
 *
 * Both halves of the answer are checked.  The transport status decides first -
 * a 500 is a failure whatever the body claims - and the envelope decides
 * second, because this backend also answers `status: "error"` with a 200 in
 * places.  Anything that is neither is reported as malformed rather than
 * guessed at.
 */
export async function request<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const { method = 'GET', body, query, signal } = options

  const init: RequestInit = {
    method,
    //
    // Stated rather than inherited.  This is already fetch's default, and the
    // session cookie is HttpOnly and same-origin, so nothing changes by saying
    // it - but authentication now depends on that cookie being attached, and a
    // dependency that rests on a default nobody wrote down is one a future
    // edit can remove without noticing.
    //
    credentials: 'same-origin',
  }
  const headers: Record<string, string> = {}
  if (body !== undefined) {
    headers['Content-Type'] = 'application/json'
    init.body = JSON.stringify(body)
  }
  if (MUTATION_METHODS.has(method)) {
    const csrfToken = readableCookie(CSRF_COOKIE_NAME)
    if (csrfToken) {
      headers[CSRF_HEADER_NAME] = csrfToken
    }
  }
  if (Object.keys(headers).length) {
    init.headers = headers
  }
  if (signal) {
    init.signal = signal
  }

  let response: Response
  try {
    response = await fetch(buildUrl(path, query), init)
  } catch (caught) {
    //
    // Offline, DNS, connection reset, an aborted request.  There is no status
    // and no envelope, so the caller is told exactly that rather than being
    // handed a fabricated 0.
    //
    throw new ApiError({
      kind: 'network',
      status: null,
      code: null,
      message: caught instanceof Error ? caught.message : '网络请求失败',
    })
  }

  let payload: unknown
  try {
    payload = await response.json()
  } catch {
    //
    // Something answered, but not this api - a proxy's HTML error page, a
    // truncated body.  Reported with the status it came with, because that is
    // the only reliable fact available about it.
    //
    throw new ApiError({
      kind: 'malformed',
      status: response.status,
      code: null,
      message: `服务器返回了无法解析的响应（HTTP ${response.status}）`,
    })
  }

  if (!isEnvelope(payload)) {
    throw new ApiError({
      kind: 'malformed',
      status: response.status,
      code: null,
      message: '服务器返回了预期之外的响应格式',
    })
  }

  if (payload.status === 'error') {
    throw new ApiError({
      kind: 'backend',
      status: response.status,
      code: payload.code,
      message: payload.message,
      ...refusalExtras(payload),
    })
  }

  if (!response.ok) {
    //
    // The body says success and the transport says otherwise.  Something
    // between here and the application rewrote one of them, and believing the
    // body over the transport would be the wrong guess to make.
    //
    throw new ApiError({
      kind: 'malformed',
      status: response.status,
      code: payload.code,
      message: `服务器返回了 HTTP ${response.status}`,
    })
  }

  return payload.data as T
}
