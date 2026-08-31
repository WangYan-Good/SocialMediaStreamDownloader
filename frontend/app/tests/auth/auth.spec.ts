import { mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { nextTick } from 'vue'
import { createMemoryHistory, createRouter } from 'vue-router'

import { ApiError } from '../../src/api/client'
import { getCurrentUser, login, logout } from '../../src/api/auth'
import { routes } from '../../src/router'
import { createAuthorizationGuard } from '../../src/router/authorization'
import { useAuthStore } from '../../src/stores/auth'
import LoginView from '../../src/views/LoginView.vue'

vi.mock('../../src/api/auth', () => ({
  login: vi.fn(),
  logout: vi.fn(),
  getCurrentUser: vi.fn(),
}))

const mockedLogin = vi.mocked(login)
const mockedLogout = vi.mocked(logout)
const mockedMe = vi.mocked(getCurrentUser)

const ALICE = { user_id: 1, username: 'alice', role: 'user' as const }

async function settle() {
  for (let index = 0; index < 6; index += 1) {
    await Promise.resolve()
  }
  await nextTick()
}

async function openLogin() {
  const router = createRouter({ history: createMemoryHistory(), routes })
  await router.push('/login')
  await router.isReady()
  const wrapper = mount(LoginView, { global: { plugins: [router] } })
  await settle()
  return { wrapper, router }
}

function unauthorized() {
  return new ApiError({ kind: 'backend', status: 401, code: 401, message: '未登录' })
}

beforeEach(() => {
  setActivePinia(createPinia())
  vi.clearAllMocks()
  mockedLogin.mockResolvedValue({ user: ALICE })
  mockedLogout.mockResolvedValue(undefined)
  mockedMe.mockResolvedValue({ user: ALICE })
})

describe('the sign-in screen', () => {
  it('is reachable at its own route', async () => {
    const router = createRouter({ history: createMemoryHistory(), routes })

    await router.push('/login')
    await router.isReady()

    expect(router.currentRoute.value.name).toBe('login')
  })

  it('asks for a username and a password and nothing else', async () => {
    const { wrapper } = await openLogin()

    expect(wrapper.find('input[name="username"]').exists()).toBe(true)
    expect(wrapper.find('input[name="password"]').exists()).toBe(true)
  })

  it('never shows the password as it is typed', async () => {
    const { wrapper } = await openLogin()

    expect(wrapper.get('input[name="password"]').attributes('type')).toBe('password')
  })

  it('offers no way to register an account', async () => {
    //
    // Deliberate. Account lifecycle and Admin bootstrap are operator actions;
    // this phase adds navigation UX, not self-service identity management.
    //
    const { wrapper } = await openLogin()
    const text = wrapper.text()

    for (const absent of ['注册', '创建账户', '忘记密码', '第三方登录']) {
      expect(text).not.toContain(absent)
    }
  })

  it('submits what was typed', async () => {
    const { wrapper } = await openLogin()

    await wrapper.get('input[name="username"]').setValue('alice')
    await wrapper.get('input[name="password"]').setValue('correct horse battery')
    await wrapper.get('form').trigger('submit')
    await settle()

    expect(mockedLogin).toHaveBeenCalledWith('alice', 'correct horse battery')
  })

  it('never puts the password in the address bar', async () => {
    //
    // A GET form would put it in the url, the history and every access log in
    // front of this server.
    //
    const { wrapper, router } = await openLogin()

    await wrapper.get('input[name="username"]').setValue('alice')
    await wrapper.get('input[name="password"]').setValue('correct horse battery')
    await wrapper.get('form').trigger('submit')
    await settle()

    expect(router.currentRoute.value.fullPath).not.toContain('correct horse battery')
    expect(wrapper.get('form').attributes('method')).not.toBe('get')
  })

  it('sends the browser home once it has signed in', async () => {
    const { wrapper, router } = await openLogin()

    await wrapper.get('input[name="username"]').setValue('alice')
    await wrapper.get('input[name="password"]').setValue('correct horse battery')
    await wrapper.get('form').trigger('submit')

    //
    // Waited for rather than counted in ticks: the handler awaits the login
    // request and then the navigation, and how many microtasks that takes is
    // an implementation detail of vue-router rather than something this test
    // should encode.
    //
    await vi.waitFor(() => {
      expect(router.currentRoute.value.name).toBe('user-home')
    })
    expect(router.currentRoute.value.path).toBe('/')
  })

  it('says the pair was wrong without saying which half', async () => {
    mockedLogin.mockRejectedValue(
      new ApiError({
        kind: 'backend',
        status: 401,
        code: 401,
        message: '用户名或密码错误',
      }),
    )
    const { wrapper } = await openLogin()

    await wrapper.get('input[name="username"]').setValue('alice')
    await wrapper.get('input[name="password"]').setValue('wrong')
    await wrapper.get('form').trigger('submit')
    await settle()

    const alert = wrapper.get('[role="alert"]').text()
    expect(alert).toContain('用户名或密码错误')
    expect(alert).not.toContain('不存在')
  })

  it('distinguishes a service that cannot answer from a wrong password', async () => {
    mockedLogin.mockRejectedValue(
      new ApiError({
        kind: 'backend',
        status: 503,
        code: 503,
        message: '认证服务暂时不可用，请稍后重试',
      }),
    )
    const { wrapper } = await openLogin()

    await wrapper.get('input[name="username"]').setValue('alice')
    await wrapper.get('input[name="password"]').setValue('correct horse battery')
    await wrapper.get('form').trigger('submit')
    await settle()

    const alert = wrapper.get('[role="alert"]').text()
    expect(alert).toContain('认证服务暂时不可用')
    expect(alert).not.toContain('密码错误')
  })

  it('shows one fixed safe message when login is rate limited', async () => {
    mockedLogin.mockRejectedValue(
      new ApiError({
        kind: 'backend',
        status: 429,
        code: 429,
        message: 'attacker-controlled limiter detail',
        backendKind: 'rate_limited',
      }),
    )
    const { wrapper } = await openLogin()

    await wrapper.get('input[name="username"]').setValue('alice')
    await wrapper.get('input[name="password"]').setValue('wrong')
    await wrapper.get('form').trigger('submit')
    await settle()

    const alert = wrapper.get('[role="alert"]').text()
    expect(alert).toBe('登录尝试过于频繁，请稍后重试')
    expect(alert).not.toContain('attacker-controlled')
  })

  it('shows nothing of the machinery when something breaks', async () => {
    mockedLogin.mockRejectedValue(
      new ApiError({
        kind: 'backend',
        status: 500,
        code: 500,
        message: 'pymysql OperationalError 2003',
      }),
    )
    const { wrapper } = await openLogin()

    await wrapper.get('input[name="username"]').setValue('alice')
    await wrapper.get('input[name="password"]').setValue('correct horse battery')
    await wrapper.get('form').trigger('submit')
    await settle()

    const text = wrapper.text()
    for (const internal of ['pymysql', 'OperationalError', '2003', 'scrypt']) {
      expect(text).not.toContain(internal)
    }
  })

  it('will not submit an empty form', async () => {
    const { wrapper } = await openLogin()

    await wrapper.get('form').trigger('submit')
    await settle()

    expect(mockedLogin).not.toHaveBeenCalled()
  })
})

describe('the store that remembers who is signed in', () => {
  it('starts out not knowing', async () => {
    //
    // Four states, not two. Assuming "anonymous" before asking would make the
    // interface flicker through a signed-out shape on every page load, and
    // would be wrong for exactly as long as the request takes.
    //
    const store = useAuthStore()

    expect(store.status).toBe('unknown')
    expect(store.user).toBeNull()
  })

  it('becomes authenticated when the server recognises the cookie', async () => {
    const store = useAuthStore()

    await store.loadCurrentUser()

    expect(store.status).toBe('authenticated')
    expect(store.user).toEqual(ALICE)
    expect(store.user?.role).toBe('user')
  })

  it('becomes anonymous when the server does not', async () => {
    mockedMe.mockRejectedValue(unauthorized())
    const store = useAuthStore()

    await store.loadCurrentUser()

    expect(store.status).toBe('anonymous')
    expect(store.user).toBeNull()
  })

  it('does not claim to be signed out when the service is merely unavailable', async () => {
    //
    // A 503 is not a 401. Treating an outage as "signed out" would appear to
    // log everybody out whenever the database hiccuped.
    //
    mockedMe.mockRejectedValue(
      new ApiError({ kind: 'backend', status: 503, code: 503, message: '认证服务暂时不可用' }),
    )
    const store = useAuthStore()

    await store.loadCurrentUser()

    expect(store.status).toBe('unavailable')
  })

  it('remembers who signed in', async () => {
    const store = useAuthStore()

    await store.login('alice', 'correct horse battery')

    expect(store.status).toBe('authenticated')
    expect(store.user).toEqual(ALICE)
  })

  it('forgets them again on the way out', async () => {
    const store = useAuthStore()
    await store.login('alice', 'correct horse battery')

    await store.logout()

    expect(store.status).toBe('anonymous')
    expect(store.user).toBeNull()
    expect(mockedLogout).toHaveBeenCalled()
  })

  it('never holds a session token', async () => {
    //
    // The browser holds the session in a HttpOnly cookie it cannot read, and
    // that is the entire point: anywhere the page can store a token, an XSS on
    // the page can read it.
    //
    const store = useAuthStore()
    await store.login('alice', 'correct horse battery')

    const serialized = JSON.stringify(store.$state)
    for (const forbidden of ['token', 'session', 'password']) {
      expect(serialized.toLowerCase()).not.toContain(forbidden)
    }
  })

  it('keeps nothing in browser storage', async () => {
    const store = useAuthStore()
    await store.login('alice', 'correct horse battery')

    expect(localStorage.length).toBe(0)
    expect(sessionStorage.length).toBe(0)
  })
})

describe('the application route guard', () => {
  it('sends an anonymous protected route to sign-in', async () => {
    mockedMe.mockRejectedValue(unauthorized())
    const pinia = createPinia()
    setActivePinia(pinia)
    const router = createRouter({ history: createMemoryHistory(), routes })
    router.beforeEach(createAuthorizationGuard(router, pinia))

    await router.push('/tasks')

    expect(router.currentRoute.value.name).toBe('login')
    expect(router.currentRoute.value.query.redirect).toBe('/tasks')
  })

  it('sends an anonymous Admin route to sign-in before considering its role', async () => {
    mockedMe.mockRejectedValue(unauthorized())
    const pinia = createPinia()
    setActivePinia(pinia)
    const router = createRouter({ history: createMemoryHistory(), routes })
    router.beforeEach(createAuthorizationGuard(router, pinia))

    await router.push('/admin/system')

    expect(router.currentRoute.value.name).toBe('login')
    expect(router.currentRoute.value.query.redirect).toBe('/admin/system')
  })
})
