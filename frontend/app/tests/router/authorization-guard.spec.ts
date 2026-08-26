import { createPinia, setActivePinia } from 'pinia'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { createMemoryHistory, createRouter } from 'vue-router'

import { getCurrentUser } from '../../src/api/auth'
import { ApiError } from '../../src/api/client'
import { createAuthorizationGuard } from '../../src/router/authorization'
import { routes } from '../../src/router'
import { resolveSafeReturnTarget } from '../../src/router/returnTarget'
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

function unauthorized() {
  return new ApiError({ kind: 'backend', status: 401, code: 401, message: '未登录' })
}

function unavailable() {
  return new ApiError({
    kind: 'backend',
    status: 503,
    code: 503,
    message: '认证服务暂时不可用',
  })
}

function guardedRouter() {
  const pinia = createPinia()
  setActivePinia(pinia)
  const router = createRouter({ history: createMemoryHistory(), routes })
  router.beforeEach(createAuthorizationGuard(router, pinia))
  return { router, auth: useAuthStore(pinia) }
}

beforeEach(() => {
  vi.clearAllMocks()
  mockedMe.mockResolvedValue({ user: USER })
})

describe('safe local return targets', () => {
  it('preserves a real local route with its query and fragment', () => {
    const { router } = guardedRouter()

    expect(resolveSafeReturnTarget(router, '/library?page=2#saved')).toBe(
      '/library?page=2#saved',
    )
  })

  it.each([
    'https://evil.example',
    '//evil.example',
    'javascript:alert(1)',
    '/not-a-real-screen',
    '/login',
    '/forbidden',
    '/auth-unavailable',
  ])('rejects unsafe or non-business target %s', (target) => {
    const { router } = guardedRouter()

    expect(resolveSafeReturnTarget(router, target)).toBeNull()
  })
})

describe('central route authorization', () => {
  it.each(['/', '/new', '/library?q=x', '/tasks', '/admin/creators'])(
    'sends anonymous navigation to login while preserving a safe target: %s',
    async (target) => {
      mockedMe.mockRejectedValue(unauthorized())
      const { router } = guardedRouter()

      await router.push(target)

      expect(router.currentRoute.value.name).toBe('login')
      expect(router.currentRoute.value.query.redirect).toBe(target)
    },
  )

  it.each(['/', '/new', '/library', '/tasks'])(
    'allows a USER to use user route %s',
    async (target) => {
      const { router } = guardedRouter()

      await router.push(target)

      expect(router.currentRoute.value.fullPath).toBe(target)
    },
  )

  it.each(['/admin', '/admin/system', '/creators'])(
    'sends a USER admin target through forbidden UX: %s',
    async (target) => {
      const { router } = guardedRouter()

      await router.push(target)

      expect(router.currentRoute.value.name).toBe('forbidden')
    },
  )

  it.each(['/', '/tasks', '/admin/creators', '/admin/system'])(
    'allows an ADMIN to use both consoles: %s',
    async (target) => {
      mockedMe.mockResolvedValue({ user: ADMIN })
      const { router } = guardedRouter()

      await router.push(target)

      expect(router.currentRoute.value.fullPath).toBe(target)
    },
  )

  it('sends unavailable protected navigation to the retry page, not login', async () => {
    mockedMe.mockRejectedValue(unavailable())
    const { router } = guardedRouter()

    await router.push('/tasks')

    expect(router.currentRoute.value.name).toBe('auth-unavailable')
    expect(router.currentRoute.value.query.redirect).toBe('/tasks')
    expect(mockedMe).toHaveBeenCalledTimes(1)
  })

  it('does not retry authentication on later navigation while unavailable', async () => {
    mockedMe.mockRejectedValue(unavailable())
    const { router } = guardedRouter()
    await router.push('/tasks')

    await router.push('/library')

    expect(router.currentRoute.value.name).toBe('auth-unavailable')
    expect(mockedMe).toHaveBeenCalledTimes(1)
  })

  it('sends an anonymous direct visit to forbidden through login without a loop target', async () => {
    mockedMe.mockRejectedValue(unauthorized())
    const { router } = guardedRouter()

    await router.push('/forbidden')

    expect(router.currentRoute.value.name).toBe('login')
    expect(router.currentRoute.value.query.redirect).toBeUndefined()
  })

  it('redirects an authenticated login visit through the guard of its preserved target', async () => {
    const { router } = guardedRouter()

    await router.push('/login?redirect=/admin/system')

    expect(router.currentRoute.value.name).toBe('forbidden')
  })
})
