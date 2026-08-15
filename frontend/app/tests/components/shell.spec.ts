import { createPinia, setActivePinia } from 'pinia'
import { nextTick } from 'vue'
import type { Component } from 'vue'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { createMemoryHistory, createRouter } from 'vue-router'
import type { Router } from 'vue-router'
import { mount } from '@vue/test-utils'

import App from '../../src/App.vue'
import AppShell from '../../src/components/layout/AppShell.vue'
import SidebarNav from '../../src/components/layout/SidebarNav.vue'
import { routes } from '../../src/router'
import { useAppStore } from '../../src/stores/app'

async function mountShell(component: Component = App) {
  const router: Router = createRouter({ history: createMemoryHistory(), routes })
  await router.push('/overview')
  await router.isReady()

  const wrapper = mount(component, {
    global: { plugins: [router] },
  })
  await router.isReady()
  return { wrapper, router }
}

beforeEach(() => {
  setActivePinia(createPinia())
})

describe('AppShell', () => {
  it('renders the routed view', async () => {
    const { wrapper } = await mountShell()

    expect(wrapper.findComponent(AppShell).exists()).toBe(true)
    expect(wrapper.text()).toContain('总览')
  })

  it('renders the navigation', async () => {
    const { wrapper } = await mountShell()

    expect(wrapper.findComponent(SidebarNav).exists()).toBe(true)
  })

  it('changes the rendered view when the route changes', async () => {
    const { wrapper, router } = await mountShell()

    await router.push('/tasks')
    await nextTick()

    expect(wrapper.text()).toContain('任务中心')
    expect(wrapper.text()).not.toContain('总览内容将在后续阶段接入')
  })

  it('gives the navigation toggle a readable name and a wired state', async () => {
    const { wrapper } = await mountShell()

    const toggle = wrapper.find('.app-shell__toggle')
    expect(toggle.exists()).toBe(true)
    expect(toggle.text()).toBeTruthy()
    expect(toggle.attributes('aria-expanded')).toBe('false')
    expect(toggle.attributes('aria-controls')).toBe('app-sidebar')
  })

  it('reflects the drawer state on the toggle', async () => {
    const { wrapper } = await mountShell()

    await wrapper.find('.app-shell__toggle').trigger('click')

    expect(useAppStore().sidebarOpen).toBe(true)
    expect(wrapper.find('.app-shell__toggle').attributes('aria-expanded')).toBe('true')
  })

  it('closes the drawer after navigating', async () => {
    //
    // On a phone the drawer covers the screen.  Leaving it open after a tap
    // would hide the very page the tap asked for.
    //
    const { wrapper } = await mountShell()
    const store = useAppStore()
    store.toggleSidebar()
    await nextTick()

    await wrapper.findAll('.sidebar-nav__link')[1].trigger('click')

    expect(store.sidebarOpen).toBe(false)
  })
})

describe('SidebarNav', () => {
  it('is a landmark with an accessible name', async () => {
    const { wrapper } = await mountShell()

    const nav = wrapper.find('nav')
    expect(nav.exists()).toBe(true)
    expect(nav.attributes('aria-label')).toBeTruthy()
  })

  it('lists the six sections', async () => {
    const { wrapper } = await mountShell()

    const labels = wrapper
      .findAll('.sidebar-nav__list .sidebar-nav__label')
      .map((node) => node.text())

    expect(labels).toEqual(['总览', '新建下载', '创作者', '媒体库', '任务中心', '系统'])
  })

  it('marks the active section with more than colour', async () => {
    const { wrapper } = await mountShell()

    const active = wrapper.findAll('.sidebar-nav__link').filter((link) =>
      link.classes().includes('router-link-active'),
    )

    expect(active).toHaveLength(1)
    expect(active[0].text()).toContain('总览')
  })

  it('moves the active marker when the route changes', async () => {
    const { wrapper, router } = await mountShell()

    await router.push('/library')
    await nextTick()

    const active = wrapper
      .findAll('.sidebar-nav__link')
      .filter((link) => link.classes().includes('router-link-active'))

    expect(active).toHaveLength(1)
    expect(active[0].text()).toContain('媒体库')
  })

  it('offers a way back to the legacy interface', async () => {
    //
    // The most important link in this stage.  Everything the new interface has
    // not built yet still exists at /, and a user who lands on a placeholder
    // needs somewhere to go that is not the back button.
    //
    const { wrapper } = await mountShell()

    const legacy = wrapper.find('.sidebar-nav__link--legacy')
    expect(legacy.exists()).toBe(true)
    expect(legacy.attributes('href')).toBe('/')
  })

  it('leaves the application to reach the legacy interface', async () => {
    //
    // A plain anchor, not a RouterLink: / is served by Flask, not by this
    // router, so a client-side navigation there would resolve to nothing.
    //
    const { wrapper } = await mountShell()

    expect(wrapper.find('a.sidebar-nav__link--legacy').element.tagName).toBe('A')
    expect(wrapper.find('.sidebar-nav__link--legacy').classes()).not.toContain(
      'router-link-active',
    )
  })
})

describe('placeholder views', () => {
  it.each([
    ['/overview', '总览'],
    ['/new', '新建下载'],
    ['/creators', '创作者'],
    ['/library', '媒体库'],
    ['/tasks', '任务中心'],
    ['/system', '系统'],
  ])('%s renders its own title', async (path, title) => {
    const { wrapper, router } = await mountShell()

    await router.push(path)
    await nextTick()

    expect(wrapper.find('h1').text()).toBe(title)
  })

  it('says which stage fills each screen in', async () => {
    const { wrapper, router } = await mountShell()

    await router.push('/new')
    await nextTick()

    expect(wrapper.text()).toContain('P8')
  })
})

describe('the shell asks the backend for nothing', () => {
  it('makes no request while mounting or navigating', async () => {
    //
    // The line between this stage and the next.  Every screen here is a
    // placeholder, and a placeholder that quietly polls would make this stage
    // the beginning of the next one - with none of its tests.
    //
    const fetched = vi.fn()
    vi.stubGlobal('fetch', fetched)

    const { router } = await mountShell()
    for (const path of ['/overview', '/new', '/creators', '/library', '/tasks', '/system']) {
      await router.push(path)
      await nextTick()
    }

    expect(fetched).not.toHaveBeenCalled()
  })
})
