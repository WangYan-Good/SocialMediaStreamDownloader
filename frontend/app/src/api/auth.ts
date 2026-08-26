import { ApiError, request } from './client'
import type { AuthUser, AuthUserPayload, LoginRequest } from '@/types/auth'

//
// The session travels as a cookie the browser sets and sends by itself, so
// nothing here handles a token. There is no Authorization header to build and
// nothing to persist between calls.
//

/**
 * Exchange a username and password for a session.
 *
 * The session itself arrives as a Set-Cookie header this code never sees. What
 * comes back through here is only who was signed in.
 */
function isAuthUser(value: unknown): value is AuthUser {
  if (typeof value !== 'object' || value === null) return false
  const candidate = value as Partial<Record<keyof AuthUser, unknown>>
  return (
    Number.isInteger(candidate.user_id) &&
    typeof candidate.username === 'string' &&
    candidate.username.trim().length > 0 &&
    (candidate.role === 'user' || candidate.role === 'admin')
  )
}

function requireAuthUserPayload(value: unknown): AuthUserPayload {
  const candidate =
    typeof value === 'object' && value !== null
      ? (value as { user?: unknown }).user
      : undefined
  if (isAuthUser(candidate)) {
    return {
      user: {
        user_id: candidate.user_id,
        username: candidate.username,
        role: candidate.role,
      },
    }
  }
  throw new ApiError({
    kind: 'malformed',
    status: 200,
    code: null,
    message: '服务器返回了预期之外的认证信息',
  })
}

export async function login(
  username: string,
  password: string,
): Promise<AuthUserPayload> {
  const body: LoginRequest = { username, password }
  return requireAuthUserPayload(
    await request<unknown>('/auth/login', { method: 'POST', body }),
  )
}

/**
 * Who the current cookie belongs to.
 *
 * Throws a 401 when it belongs to nobody - unknown, expired, or revoked - and
 * a 503 when the server cannot answer the question at all. The two mean
 * different things and the store keeps them apart.
 */
export async function getCurrentUser(): Promise<AuthUserPayload> {
  return requireAuthUserPayload(await request<unknown>('/auth/me'))
}

/** End the current session, server-side. Safe to call when there is none. */
export function logout(): Promise<void> {
  return request<void>('/auth/logout', { method: 'POST' })
}
