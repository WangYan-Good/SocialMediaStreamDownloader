import { createPinia } from 'pinia'
import { createApp, defineComponent, h } from 'vue'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { createMemoryHistory, createRouter, RouterView } from 'vue-router'

import { getCurrentUser } from '../../src/api/auth'
import { ApiError } from '../../src/api/client'
import { bootstrapApplication } from '../../src/bootstrap'

vi.mock('../../src/api/auth', () => ({
  getCurrentUser: vi.fn(),
  login: vi.fn(),
  logout: vi.fn(),
}))

const mockedMe = vi.mocked(getCurrentUser)

function deferred<T>() {
  let resolve: (value: T) => void = () => {}
  let reject: (reason: unknown) => void = () => {}
  const promise = new Promise<T>((settle, fail) => {
    resolve = settle
    reject = fail
  })
  return { promise, resolve, reject }
}

beforeEach(() => {
  document.body.innerHTML = '<div id="app"></div>'
  vi.clearAllMocks()
})

describe('application authentication bootstrap', () => {
  it('does not mount a protected view before the initial identity decision', async () => {
    const setupProtected = vi.fn()
    const Protected = defineComponent({
      name: 'Protected',
      setup() {
        setupProtected()
        return () => h('p', 'protected')
      },
    })
    const Login = defineComponent({ name: 'Login', setup: () => () => h('p', 'login') })
    const Unavailable = defineComponent({
      name: 'Unavailable',
      setup: () => () => h('p', 'unavailable'),
    })
    const pending = deferred<{ user: { user_id: number; username: string; role: 'user' } }>()
    mockedMe.mockReturnValue(pending.promise)
    const router = createRouter({
      history: createMemoryHistory(),
      routes: [
        { path: '/', component: Protected, meta: { requiresAuth: true } },
        { path: '/login', name: 'login', component: Login },
        { path: '/auth-unavailable', name: 'auth-unavailable', component: Unavailable },
        { path: '/forbidden', name: 'forbidden', component: Login, meta: { requiresAuth: true } },
      ],
    })
    const app = createApp({ setup: () => () => h(RouterView) })

    const started = bootstrapApplication(app, createPinia(), router, '#app')
    await Promise.resolve()

    expect(setupProtected).not.toHaveBeenCalled()
    expect(document.querySelector('#app')?.textContent).toBe('')

    pending.reject(
      new ApiError({ kind: 'backend', status: 401, code: 401, message: '未登录' }),
    )
    await started

    expect(router.currentRoute.value.name).toBe('login')
    expect(setupProtected).not.toHaveBeenCalled()
    expect(document.querySelector('#app')?.textContent).toContain('login')
    app.unmount()
  })
})
