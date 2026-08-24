import { request } from './client'
import type { AuthUserPayload, LoginRequest } from '@/types/auth'

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
export function login(username: string, password: string): Promise<AuthUserPayload> {
  const body: LoginRequest = { username, password }
  return request<AuthUserPayload>('/auth/login', { method: 'POST', body })
}

/**
 * Who the current cookie belongs to.
 *
 * Throws a 401 when it belongs to nobody - unknown, expired, or revoked - and
 * a 503 when the server cannot answer the question at all. The two mean
 * different things and the store keeps them apart.
 */
export function getCurrentUser(): Promise<AuthUserPayload> {
  return request<AuthUserPayload>('/auth/me')
}

/** End the current session, server-side. Safe to call when there is none. */
export function logout(): Promise<void> {
  return request<void>('/auth/logout', { method: 'POST' })
}
