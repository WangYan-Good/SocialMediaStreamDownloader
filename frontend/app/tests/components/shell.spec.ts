import { createPinia, setActivePinia } from 'pinia'
import { nextTick } from 'vue'
import type { Component } from 'vue'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { createMemoryHistory, createRouter } from 'vue-router'
import type { Router } from 'vue-router'
import { mount } from '@vue/test-utils'

import App from '../../src/App.vue'
import AppShell from '../../src/components/layout/AppShell.vue'
import SidebarNav from '../../src/components/layout/SidebarNav.vue'
import { routes } from '../../src/router'
import { useAppStore } from '../../src/stores/app'
import { useAuthStore } from '../../src/stores/auth'
import { logout } from '../../src/api/auth'
import { ApiError } from '../../src/api/client'
import type { AuthUser } from '../../src/types/auth'

vi.mock('../../src/api/auth', () => ({
  getCurrentUser: vi.fn(),
  login: vi.fn(),
  logout: vi.fn(),
}))

const mockedLogout = vi.mocked(logout)
const USER: AuthUser = { user_id: 71, username: 'alice', role: 'user' }
const ADMIN: AuthUser = { user_id: 72, username: 'operator', role: 'admin' }

async function mountShell(
  component: Component = App,
  startAt = '/new',
  principal: AuthUser = startAt.startsWith('/admin') ? ADMIN : USER,
) {
  const pinia = createPinia()
  setActivePinia(pinia)
  const auth = useAuthStore(pinia)
  auth.$patch({ status: 'authenticated', user: principal })
  const router: Router = createRouter({ history: createMemoryHistory(), routes })
  await router.push(startAt)
  await router.isReady()

  const wrapper = mount(component, {
    global: { plugins: [pinia, router] },
  })
  await router.isReady()
  return { wrapper, router, auth }
}

beforeEach(() => {
  vi.clearAllMocks()
  mockedLogout.mockResolvedValue(undefined)
  vi.stubGlobal('fetch', vi.fn(() => new Promise<Response>(() => undefined)))
})

afterEach(() => {
  vi.unstubAllGlobals()
})

describe('shared application shell', () => {
  it('shows the username without exposing the numeric user id', async () => {
    const { wrapper } = await mountShell()

    const account = wrapper.get('.app-shell__account').text()
    expect(account).toContain('alice')
    expect(account).not.toContain('71')
  })

  it('logs out locally and replaces the current page with login', async () => {
    const { wrapper, router, auth } = await mountShell()

    await wrapper.get('[data-test="logout"]').trigger('click')

    await vi.waitFor(() => expect(router.currentRoute.value.name).toBe('login'))
    expect(auth.status).toBe('anonymous')
  })

  it.each([
    new ApiError({
      kind: 'backend',
      status: 503,
      code: 503,
      backendKind: 'logout_unavailable',
      message: 'internal backend wording',
    }),
    new ApiError({
      kind: 'network',
      status: null,
      code: null,
      message: 'socket reset',
    }),
  ])('keeps identity and route when the logout request fails', async (failure) => {
    mockedLogout.mockRejectedValueOnce(failure)
    const { wrapper, router, auth } = await mountShell()

    await wrapper.get('[data-test="logout"]').trigger('click')

    await vi.waitFor(() => {
      expect(wrapper.get('[data-test="logout"]').attributes('disabled')).toBeUndefined()
    })
    expect(router.currentRoute.value.path).toBe('/new')
    expect(auth.status).toBe('authenticated')
    expect(auth.user).toEqual(USER)
    expect(wrapper.get('.app-shell__username').text()).toBe('alice')
    const error = wrapper.get('[data-test="logout-error"]')
    expect(error.attributes('role')).toBe('status')
    expect(error.text()).toBe('退出登录失败，请稍后重试')
    expect(error.text()).not.toContain(failure.message)
  })

  it('clears the old error and navigates only after a manual retry succeeds', async () => {
    let finishRetry: () => void = () => {}
    const retry = new Promise<void>((resolve) => {
      finishRetry = resolve
    })
    mockedLogout
      .mockRejectedValueOnce(new TypeError('offline'))
      .mockReturnValueOnce(retry)
    const { wrapper, router, auth } = await mountShell()
    const button = wrapper.get('[data-test="logout"]')

    await button.trigger('click')
    await vi.waitFor(() => {
      expect(wrapper.find('[data-test="logout-error"]').exists()).toBe(true)
    })

    await button.trigger('click')

    expect(wrapper.find('[data-test="logout-error"]').exists()).toBe(false)
    expect(router.currentRoute.value.path).toBe('/new')
    expect(auth.status).toBe('authenticated')
    finishRetry()

    await vi.waitFor(() => expect(router.currentRoute.value.name).toBe('login'))
    expect(auth.status).toBe('anonymous')
    expect(auth.user).toBeNull()
    expect(wrapper.find('[data-test="logout-error"]').exists()).toBe(false)
    expect(mockedLogout).toHaveBeenCalledTimes(2)
  })

  it('renders the routed layout through the shared shell', async () => {
    const { wrapper } = await mountShell()

    expect(wrapper.findComponent(AppShell).exists()).toBe(true)
    expect(wrapper.findComponent(SidebarNav).exists()).toBe(true)
    expect(wrapper.findComponent({ name: 'UserLayout' }).exists()).toBe(true)
    expect(wrapper.findComponent({ name: 'NewDownloadView' }).exists()).toBe(true)
  })

  it('gives the navigation toggle a readable name and a wired state', async () => {
    const { wrapper } = await mountShell()

    const toggle = wrapper.find('.app-shell__toggle')
    expect(toggle.exists()).toBe(true)
    expect(toggle.text()).toBeTruthy()
    expect(toggle.attributes('aria-expanded')).toBe('false')
    expect(toggle.attributes('aria-controls')).toBe('app-sidebar')

    await toggle.trigger('click')

    expect(useAppStore().sidebarOpen).toBe(true)
    expect(toggle.attributes('aria-expanded')).toBe('true')
  })

  it('closes the mobile drawer after navigating', async () => {
    const { wrapper } = await mountShell()
    const store = useAppStore()
    store.toggleSidebar()
    await nextTick()

    await wrapper.findAll('.sidebar-nav__link')[1].trigger('click')

    expect(store.sidebarOpen).toBe(false)
  })
})

describe('user layout', () => {
  it('shows only user-facing navigation concepts', async () => {
    const { wrapper } = await mountShell()

    const labels = wrapper
      .findAll('.sidebar-nav__list .sidebar-nav__label')
      .map((node) => node.text())

    expect(labels).toEqual(['首页', '新建下载', '我的资源', '下载任务'])
    expect(wrapper.find('nav').attributes('aria-label')).toBe('用户导航')

    const navigation = wrapper.find('nav').text()
    for (const adminConcept of [
      '创作者',
      '账号',
      '人物',
      'main',
      'alt',
      'matrix',
      'Probe',
      'Schema',
      '数据库',
      '系统配置',
    ]) {
      expect(navigation).not.toContain(adminConcept)
    }
  })

  it('adds a management entry only for an ADMIN using the user console', async () => {
    const { wrapper } = await mountShell(App, '/', ADMIN)
    const labels = wrapper
      .findAll('.sidebar-nav__list .sidebar-nav__label')
      .map((node) => node.text())

    expect(labels).toEqual(['首页', '新建下载', '我的资源', '下载任务', '管理后台'])
  })

  it('renders the static user home without starting a resolve flow', async () => {
    const fetched = vi.mocked(fetch)
    const { wrapper } = await mountShell(App, '/')

    expect(wrapper.findComponent({ name: 'UserLayout' }).exists()).toBe(true)
    expect(wrapper.findComponent({ name: 'UserHomeView' }).exists()).toBe(true)
    expect(wrapper.text()).toContain('从分享链接开始下载')
    expect(fetched).not.toHaveBeenCalled()
  })

  it('moves the active marker between user destinations', async () => {
    const { wrapper, router } = await mountShell()

    await router.push('/library')
    await nextTick()

    const active = wrapper
      .findAll('.sidebar-nav__link')
      .filter((link) => link.classes().includes('router-link-active'))

    expect(active).toHaveLength(1)
    expect(active[0].text()).toContain('我的资源')
  })
})

describe('admin layout', () => {
  it('is visibly administrative and exposes only current admin destinations', async () => {
    const { wrapper } = await mountShell(App, '/admin/creators')

    expect(wrapper.findComponent({ name: 'AdminLayout' }).exists()).toBe(true)
    expect(wrapper.findComponent({ name: 'CreatorsView' }).exists()).toBe(true)
    expect(wrapper.text()).toContain('Admin')
    expect(wrapper.find('nav').attributes('aria-label')).toBe('管理导航')

    const labels = wrapper
      .findAll('.sidebar-nav__list .sidebar-nav__label')
      .map((node) => node.text())
    expect(labels).toEqual(['创作者', '媒体库', '任务', '系统', '返回用户端'])
    expect(wrapper.get('.app-shell__account').text()).toContain('operator')
    expect(wrapper.get('.app-shell__account').text()).toContain('Admin')
  })

  it('navigates from creators to the admin system route', async () => {
    const { wrapper, router } = await mountShell(App, '/admin/creators')

    await wrapper.findAll('.sidebar-nav__link')[3].trigger('click')
    await vi.waitFor(() => {
      expect(router.currentRoute.value.path).toBe('/admin/system')
    })

    expect(router.currentRoute.value.name).toBe('admin-system')
  })

  it('reaches the full management library from the admin navigation', async () => {
    //
    // The user library drops columns; it does not remove them from the
    // application. Everything the single library view could show is still
    // reachable, from here.
    //
    const { wrapper, router } = await mountShell(App, '/admin/creators')

    await wrapper.findAll('.sidebar-nav__link')[1].trigger('click')
    await vi.waitFor(() => {
      expect(router.currentRoute.value.path).toBe('/admin/library')
    })

    expect(router.currentRoute.value.name).toBe('admin-library')
  })
})

describe('screens with nothing to load ask the backend for nothing', () => {
  it('makes no request while mounting new download', async () => {
    const fetched = vi.mocked(fetch)

    await mountShell(App, '/new')

    expect(fetched).not.toHaveBeenCalled()
  })
})

describe('admin task destination', () => {
  it('reaches the full management task view from the admin navigation', async () => {
    //
    // The user task view drops the ids, the raw metadata and the limit control.
    // None of that left the application; this is where it went.
    //
    const { wrapper, router } = await mountShell(App, '/admin/creators')

    await wrapper.findAll('.sidebar-nav__link')[2].trigger('click')
    await vi.waitFor(() => {
      expect(router.currentRoute.value.path).toBe('/admin/tasks')
    })

    expect(router.currentRoute.value.name).toBe('admin-tasks')
  })
})

describe('the boundary between the two consoles', () => {
  //
  // Both layouts render the same AppShell, so the only thing keeping them apart
  // is the navigation each passes in. These assert that separation directly
  // rather than trusting it.
  //
  it('sends every user destination to a user route', async () => {
    const { wrapper } = await mountShell(App, '/')

    const hrefs = wrapper
      .findAll('.sidebar-nav__list .sidebar-nav__link')
      .map((one) => one.attributes('href'))

    expect(hrefs).toEqual(['/', '/new', '/library', '/tasks'])
    for (const href of hrefs) {
      expect(href?.startsWith('/admin')).toBe(false)
    }
  })

  it('sends every admin destination to an admin route', async () => {
    //
    // The trap this guards: an admin entry named 'library' or 'tasks' resolves
    // to the *user* view, which drops exactly the columns an operator opened
    // the admin console for. It would look right in the sidebar and be wrong on
    // arrival.
    //
    const { wrapper } = await mountShell(App, '/admin/creators')

    const hrefs = wrapper
      .findAll('.sidebar-nav__list .sidebar-nav__link')
      .map((one) => one.attributes('href'))

    expect(hrefs).toEqual([
      '/admin/creators',
      '/admin/library',
      '/admin/tasks',
      '/admin/system',
      '/',
    ])
    for (const href of hrefs.slice(0, -1)) {
      expect(href?.startsWith('/admin/')).toBe(true)
    }
  })

  it('keeps the admin console visibly marked as one', async () => {
    const { wrapper: admin } = await mountShell(App, '/admin/creators')
    expect(admin.text()).toContain('Admin')

    const { wrapper: user } = await mountShell(App, '/')
    expect(user.text()).not.toContain('Admin')
  })

  it('offers a user no way into the admin console', async () => {
    //
    // Hiding the entry is navigation UX, never the security boundary; the
    // backend still enforces every Admin endpoint.
    //
    const { wrapper } = await mountShell(App, '/')
    const navigation = wrapper.find('nav').text()

    for (const adminConcept of ['管理', 'Admin', '创作者', '系统', '媒体库']) {
      expect(navigation).not.toContain(adminConcept)
    }
  })
})
