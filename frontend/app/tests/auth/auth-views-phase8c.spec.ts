import { mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { createMemoryHistory, createRouter } from 'vue-router'

import { getCurrentUser, login } from '../../src/api/auth'
import { ApiError } from '../../src/api/client'
import { createAuthorizationGuard } from '../../src/router/authorization'
import { routes } from '../../src/router'
import { useAuthStore } from '../../src/stores/auth'
import AuthUnavailableView from '../../src/views/AuthUnavailableView.vue'
import ForbiddenView from '../../src/views/ForbiddenView.vue'
import LoginView from '../../src/views/LoginView.vue'
import type { AuthUser } from '../../src/types/auth'

vi.mock('../../src/api/auth', () => ({
  getCurrentUser: vi.fn(),
  login: vi.fn(),
  logout: vi.fn(),
}))

const mockedMe = vi.mocked(getCurrentUser)
const mockedLogin = vi.mocked(login)
const USER: AuthUser = { user_id: 1, username: 'alice', role: 'user' }
const ADMIN: AuthUser = { user_id: 2, username: 'operator', role: 'admin' }

function authFailure(status: number) {
  return new ApiError({
    kind: 'backend',
    status,
    code: status,
    message: status === 401 ? '未登录' : '认证服务暂时不可用',
  })
}

async function loginHarness(target: string, loginUser: AuthUser) {
  const pinia = createPinia()
  setActivePinia(pinia)
  const auth = useAuthStore(pinia)
  auth.$patch({ status: 'anonymous', user: null })
  mockedLogin.mockResolvedValue({ user: loginUser })
  const router = createRouter({ history: createMemoryHistory(), routes })
  router.beforeEach(createAuthorizationGuard(router, pinia))
  await router.push(`/login?redirect=${encodeURIComponent(target)}`)
  const wrapper = mount(LoginView, { global: { plugins: [pinia, router] } })
  await wrapper.get('input[name="username"]').setValue(loginUser.username)
  await wrapper.get('input[name="password"]').setValue('correct horse battery')
  await wrapper.get('form').trigger('submit')
  return { wrapper, router, auth }
}

async function unavailableHarness(target = '/tasks') {
  const pinia = createPinia()
  setActivePinia(pinia)
  const auth = useAuthStore(pinia)
  auth.$patch({ status: 'unavailable', user: null })
  const router = createRouter({ history: createMemoryHistory(), routes })
  router.beforeEach(createAuthorizationGuard(router, pinia))
  await router.push(`/auth-unavailable?redirect=${encodeURIComponent(target)}`)
  const wrapper = mount(AuthUnavailableView, {
    global: { plugins: [pinia, router] },
  })
  return { wrapper, router, auth }
}

beforeEach(() => {
  vi.clearAllMocks()
  mockedMe.mockResolvedValue({ user: USER })
  mockedLogin.mockResolvedValue({ user: USER })
})

describe('login return flow', () => {
  it('returns a USER to the original user route with its query', async () => {
    const { router } = await loginHarness('/library?q=x', USER)

    await vi.waitFor(() => expect(router.currentRoute.value.fullPath).toBe('/library?q=x'))
  })

  it('returns an ADMIN to the original Admin route', async () => {
    const { router } = await loginHarness('/admin/system', ADMIN)

    await vi.waitFor(() => expect(router.currentRoute.value.path).toBe('/admin/system'))
  })

  it('does not let a USER bypass the Admin guard through a local return target', async () => {
    const { router } = await loginHarness('/admin/system', USER)

    await vi.waitFor(() => expect(router.currentRoute.value.name).toBe('forbidden'))
  })
})

describe('authentication unavailable retry', () => {
  it('returns an authenticated retry to the original target', async () => {
    mockedMe.mockResolvedValue({ user: USER })
    const { wrapper, router } = await unavailableHarness('/tasks')

    await wrapper.get('button').trigger('click')

    await vi.waitFor(() => expect(router.currentRoute.value.path).toBe('/tasks'))
  })

  it('sends a definitive anonymous retry to login with the original target', async () => {
    mockedMe.mockRejectedValue(authFailure(401))
    const { wrapper, router } = await unavailableHarness('/library?q=x')

    await wrapper.get('button').trigger('click')

    await vi.waitFor(() => expect(router.currentRoute.value.name).toBe('login'))
    expect(router.currentRoute.value.query.redirect).toBe('/library?q=x')
  })

  it('stays on the retry page without exposing backend detail when still unavailable', async () => {
    mockedMe.mockRejectedValue(
      new ApiError({
        kind: 'backend',
        status: 503,
        code: 503,
        message: 'pymysql OperationalError database.internal',
      }),
    )
    const { wrapper, router } = await unavailableHarness()

    await wrapper.get('button').trigger('click')

    await vi.waitFor(() => expect(mockedMe).toHaveBeenCalledTimes(1))
    expect(router.currentRoute.value.name).toBe('auth-unavailable')
    expect(wrapper.text()).toContain('暂时无法确认登录状态，请稍后重试')
    expect(wrapper.text()).not.toContain('pymysql')
    expect(wrapper.text()).not.toContain('database.internal')
  })
})

describe('forbidden presentation', () => {
  it('offers a safe way home without exposing authorization internals', async () => {
    const router = createRouter({ history: createMemoryHistory(), routes })
    await router.push('/forbidden')
    const wrapper = mount(ForbiddenView, { global: { plugins: [router] } })

    expect(wrapper.text()).toContain('无权访问此页面')
    expect(wrapper.text()).toContain('返回首页')
    for (const internal of ['required_role', 'permission matrix', '/api/', 'user_id']) {
      expect(wrapper.text()).not.toContain(internal)
    }
  })
})
