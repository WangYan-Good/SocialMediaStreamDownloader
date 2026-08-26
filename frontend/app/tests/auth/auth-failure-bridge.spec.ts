import { createPinia, setActivePinia } from 'pinia'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { createMemoryHistory, createRouter } from 'vue-router'

import { getCurrentUser } from '../../src/api/auth'
import { request, setAuthorizationFailureHandler } from '../../src/api/client'
import { installAuthFailureBridge } from '../../src/auth/failureBridge'
import { createAuthorizationGuard } from '../../src/router/authorization'
import { routes } from '../../src/router'
import { useAuthStore } from '../../src/stores/auth'
import type { AuthUser } from '../../src/types/auth'

vi.mock('../../src/api/auth', () => ({
  getCurrentUser: vi.fn(),
  login: vi.fn(),
  logout: vi.fn(),
}))

const mockedMe = vi.mocked(getCurrentUser)
const USER: AuthUser = { user_id: 1, username: 'alice', role: 'user' }
const ADMIN: AuthUser = { user_id: 2, username: 'operator', role: 'admin' }

function refusal(status: number, backendKind?: string) {
  return new Response(
    JSON.stringify({
      status: 'error',
      code: status,
      message: status === 401 ? '未登录' : '没有权限执行此操作',
      ...(backendKind ? { kind: backendKind } : {}),
    }),
    { status, headers: { 'Content-Type': 'application/json' } },
  )
}

async function rejectRequest(path: string, response: Response) {
  vi.stubGlobal('fetch', vi.fn().mockResolvedValue(response))
  await expect(request(path)).rejects.toThrow()
}

async function harness(user: AuthUser = USER) {
  mockedMe.mockResolvedValue({ user })
  const pinia = createPinia()
  setActivePinia(pinia)
  const router = createRouter({ history: createMemoryHistory(), routes })
  router.beforeEach(createAuthorizationGuard(router, pinia))
  const stop = installAuthFailureBridge(router, pinia)
  return { pinia, router, auth: useAuthStore(pinia), stop }
}

beforeEach(() => {
  vi.clearAllMocks()
  mockedMe.mockResolvedValue({ user: USER })
})

afterEach(() => {
  setAuthorizationFailureHandler(null)
  vi.unstubAllGlobals()
})

describe('business authentication failures', () => {
  it('turns a business 401 into anonymous login with the current return target', async () => {
    const { router, auth, stop } = await harness()
    await router.push('/tasks')

    await rejectRequest('/tasks', refusal(401))

    await vi.waitFor(() => expect(router.currentRoute.value.name).toBe('login'))
    expect(router.currentRoute.value.query.redirect).toBe('/tasks')
    expect(auth.status).toBe('anonymous')
    stop()
  })

  it.each(['/auth/login', '/auth/me', '/auth/logout'])(
    'does not turn %s 401 into a global session-expiry redirect',
    async (path) => {
      const { router, auth, stop } = await harness()
      await router.push('/tasks')

      await rejectRequest(path, refusal(401))

      await Promise.resolve()
      expect(router.currentRoute.value.path).toBe('/tasks')
      expect(auth.status).toBe('authenticated')
      stop()
    },
  )
})

describe('business authorization failures', () => {
  it('refreshes a stale Admin role and leaves the now-forbidden route', async () => {
    const { router, auth, stop } = await harness(ADMIN)
    await router.push('/admin/system')
    mockedMe.mockResolvedValue({ user: USER })

    await rejectRequest('/system/status', refusal(403, 'forbidden'))

    await vi.waitFor(() => expect(router.currentRoute.value.name).toBe('forbidden'))
    expect(auth.user).toEqual(USER)
    expect(auth.isAdmin).toBe(false)
    stop()
  })

  it('does not refresh identity or navigate on csrf_invalid', async () => {
    const { router, auth, stop } = await harness(ADMIN)
    await router.push('/admin/system')
    const meCalls = mockedMe.mock.calls.length

    await rejectRequest('/mutation', refusal(403, 'csrf_invalid'))

    await Promise.resolve()
    expect(router.currentRoute.value.path).toBe('/admin/system')
    expect(auth.isAdmin).toBe(true)
    expect(mockedMe).toHaveBeenCalledTimes(meCalls)
    stop()
  })
})
