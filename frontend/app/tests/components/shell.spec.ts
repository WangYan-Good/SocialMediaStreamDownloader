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

async function mountShell(component: Component = App, startAt = '/new') {
  const router: Router = createRouter({ history: createMemoryHistory(), routes })
  await router.push(startAt)
  await router.isReady()

  const wrapper = mount(component, {
    global: { plugins: [router] },
  })
  await router.isReady()
  return { wrapper, router }
}

beforeEach(() => {
  setActivePinia(createPinia())
  vi.stubGlobal('fetch', vi.fn(() => new Promise<Response>(() => undefined)))
})

afterEach(() => {
  vi.unstubAllGlobals()
})

describe('shared application shell', () => {
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

    expect(labels).toEqual(['首页', '新建下载', '我的资源', '任务'])
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
    expect(labels).toEqual(['创作者', '媒体库', '系统'])
  })

  it('navigates from creators to the admin system route', async () => {
    const { wrapper, router } = await mountShell(App, '/admin/creators')

    await wrapper.findAll('.sidebar-nav__link')[2].trigger('click')
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
