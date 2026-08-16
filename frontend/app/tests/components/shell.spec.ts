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

//
// `startAt` matters now that the overview reads on arrival: a test about
// screens that ask for nothing has to begin on one of them, or the landing
// page's own reads are what it measures.
//
async function mountShell(component: Component = App, startAt = '/overview') {
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

  it('does not advertise the retired legacy interface', async () => {
    const { wrapper } = await mountShell()

    expect(wrapper.find('.sidebar-nav__legacy').exists()).toBe(false)
    expect(wrapper.find('[href="/legacy/"]').exists()).toBe(false)
    expect(wrapper.text()).not.toContain('Legacy fallback')
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

  //
  // There used to be an assertion here that each unfinished screen announced
  // which stage would fill it in, and it walked from one placeholder to the
  // next as the stages landed. The overview was the last one; with it
  // implemented there is no placeholder route left to observe, so the assertion
  // has been removed rather than pointed at a real screen it would say nothing
  // about. PlaceholderView itself stays - it is a perfectly good component for
  // whatever comes next. Everything else this file guarantees about the shell -
  // navigation, titles, deep links, and which screens read on arrival - is
  // unchanged below.
  //
})

describe('screens with nothing to load ask the backend for nothing', () => {
  it('makes no request while mounting or navigating between them', async () => {
    //
    // The shell owns no data of its own. New Download is the last screen in
    // this list, and stays deliberately: it has a whole workflow, but nothing
    // reaches the network until the user pastes something and presses a button.
    //
    // Every other screen is now out of it - the task centre, the creators
    // workspace, the library, the system page, and with this stage the overview
    // too. Showing what the server is doing, which accounts it knows about,
    // what it has downloaded, how it is configured, and a summary of all four
    // is those screens' entire purpose, so reading on arrival is correct
    // behaviour and is asserted by their own tests rather than forbidden here.
    // The observation point moved each time; the rule never weakened.
    //
    const fetched = vi.fn()
    vi.stubGlobal('fetch', fetched)

    const { router } = await mountShell(App, '/new')
    for (const path of ['/new']) {
      await router.push(path)
      await nextTick()
    }

    expect(fetched).not.toHaveBeenCalled()
  })
})

describe('every screen in the sidebar is now a real one', () => {
  it('leaves no view still standing in for a later stage', async () => {
    //
    // Read from the sources rather than rendered, because what is being
    // asserted is that no screen *is* a placeholder - not that a particular
    // string is missing from a particular render.
    //
    // PlaceholderView itself is deliberately not forbidden: it is a perfectly
    // good component for whatever screen comes next. What must not happen is a
    // route in the sidebar quietly reverting to one.
    //
    const views = import.meta.glob('../../src/views/*View.vue', {
      query: '?raw',
      import: 'default',
      eager: true,
    }) as Record<string, string>

    const routed = [
      'OverviewView.vue',
      'NewDownloadView.vue',
      'CreatorsView.vue',
      'LibraryView.vue',
      'TasksView.vue',
      'SystemView.vue',
    ]

    for (const name of routed) {
      const entry = Object.entries(views).find(([path]) => path.endsWith(name))
      expect(entry, `${name} was not found`).toBeDefined()
      expect(entry?.[1], `${name} still renders a placeholder`).not.toContain(
        'PlaceholderView',
      )
    }
  })
})
