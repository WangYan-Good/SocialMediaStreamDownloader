import type { ApiEnvelope, ApiErrorKind } from '@/types/api'

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
}

export class ApiError extends Error {
  readonly kind: ApiErrorKind
  readonly status: number | null
  readonly code: number | null

  constructor(fields: ApiErrorFields) {
    super(fields.message)
    this.name = 'ApiError'
    this.kind = fields.kind
    this.status = fields.status
    this.code = fields.code
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

export interface RequestOptions {
  method?: 'GET' | 'POST'
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

  const init: RequestInit = { method }
  if (body !== undefined) {
    init.headers = { 'Content-Type': 'application/json' }
    init.body = JSON.stringify(body)
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
