import { createPinia, setActivePinia } from 'pinia'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import { getCurrentUser, login } from '../../src/api/auth'
import { useAuthStore } from '../../src/stores/auth'

function response(body: unknown, status = 200): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { 'Content-Type': 'application/json' },
  })
}

beforeEach(() => {
  setActivePinia(createPinia())
})

afterEach(() => {
  vi.unstubAllGlobals()
})

describe('authentication response contracts', () => {
  it.each([
    {},
    { user: null },
    { user: { user_id: 1, username: 'alice', role: 'owner' } },
    { user: { user_id: 1.5, username: 'alice', role: 'user' } },
    { user: { user_id: 1, username: '   ', role: 'user' } },
  ])('rejects a malformed successful principal payload', async (data) => {
    vi.stubGlobal(
      'fetch',
      vi.fn().mockResolvedValue(
        response({ status: 'success', code: 200, data }),
      ),
    )

    await expect(getCurrentUser()).rejects.toMatchObject({
      kind: 'malformed',
    })
  })

  it('maps a malformed successful /auth/me response to unavailable', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn().mockResolvedValue(
        response({ status: 'success', code: 200, data: {} }),
      ),
    )
    const auth = useAuthStore()

    await auth.ensureInitialized()

    expect(auth.status).toBe('unavailable')
    expect(auth.user).toBeNull()
  })

  it('keeps only allowlisted principal fields from a valid response', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn().mockResolvedValue(
        response({
          status: 'success',
          code: 200,
          data: {
            user: {
              user_id: 1,
              username: 'alice',
              role: 'user',
              session_token: 'must-not-enter-the-store',
            },
          },
        }),
      ),
    )

    await expect(getCurrentUser()).resolves.toEqual({
      user: { user_id: 1, username: 'alice', role: 'user' },
    })
  })

  it('rejects the same malformed principal contract after login', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn().mockResolvedValue(
        response({ status: 'success', code: 200, data: { user: null } }),
      ),
    )

    await expect(login('alice', 'password')).rejects.toMatchObject({
      kind: 'malformed',
    })
  })

  it('maps a malformed HTTP 401 response to unavailable rather than anonymous', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn().mockResolvedValue(response({ unexpected: true }, 401)),
    )
    const auth = useAuthStore()

    await auth.ensureInitialized()

    expect(auth.status).toBe('unavailable')
    expect(auth.user).toBeNull()
  })
})
