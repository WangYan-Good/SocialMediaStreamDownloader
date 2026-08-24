import type { Component } from 'vue'
import { describe, expect, it } from 'vitest'
import { createMemoryHistory, createRouter } from 'vue-router'
import type { RouteLocationMatched, RouteRecordRaw } from 'vue-router'

import { routes } from '../../src/router'

function testRouter() {
  return createRouter({ history: createMemoryHistory(), routes })
}

function matchedComponentName(record: RouteLocationMatched) {
  const component = record.components?.default as (Component & { __name?: string }) | undefined
  return component?.__name
}

function routerPaths(records: readonly RouteRecordRaw[], parentPath = ''): string[] {
  return records.flatMap((record) => {
    const path = record.path.startsWith('/')
      ? record.path
      : `${parentPath.replace(/\/$/, '')}/${record.path}`
    return [path, ...routerPaths(record.children ?? [], path)]
  })
}

describe('user and admin route boundaries', () => {
  it.each([
    ['/', 'user-home', ['UserLayout', 'UserHomeView']],
    ['/new', 'new-download', ['UserLayout', 'NewDownloadView']],
    ['/library', 'library', ['UserLayout', 'LibraryView']],
    ['/tasks', 'tasks', ['UserLayout', 'TasksView']],
    ['/admin/creators', 'admin-creators', ['AdminLayout', 'CreatorsView']],
    ['/admin/system', 'admin-system', ['AdminLayout', 'SystemView']],
  ])('loads %s through its expected layout and view', async (path, name, components) => {
    const router = testRouter()

    await router.push(path)
    await router.isReady()

    expect(router.currentRoute.value.name).toBe(name)
    expect(router.currentRoute.value.matched.map(matchedComponentName)).toEqual(components)
  })

  it('sends the admin root to creators', async () => {
    const router = testRouter()

    await router.push('/admin')
    await router.isReady()

    expect(router.currentRoute.value.path).toBe('/admin/creators')
    expect(router.currentRoute.value.name).toBe('admin-creators')
  })

  it.each([
    ['/overview', '/', 'user-home'],
    ['/creators', '/admin/creators', 'admin-creators'],
    ['/system', '/admin/system', 'admin-system'],
  ])('redirects the legacy URL %s to %s', async (legacyPath, currentPath, name) => {
    const router = testRouter()

    await router.push(legacyPath)
    await router.isReady()

    expect(router.currentRoute.value.path).toBe(currentPath)
    expect(router.currentRoute.value.name).toBe(name)
  })

  it('sends an unknown path to the user home', async () => {
    const router = testRouter()

    await router.push('/no-such-page')
    await router.isReady()

    expect(router.currentRoute.value.path).toBe('/')
    expect(router.currentRoute.value.name).toBe('user-home')
  })

  it('keeps every current screen reachable by name', () => {
    const router = testRouter()

    for (const name of [
      'user-home',
      'new-download',
      'library',
      'tasks',
      'admin-creators',
      'admin-system',
    ]) {
      expect(router.hasRoute(name)).toBe(true)
    }
  })

  it('does not restore retired legacy sections', () => {
    const paths = routerPaths(routes)

    for (const legacy of ['/history', '/posts', '/person', '/log', '/settings']) {
      expect(paths).not.toContain(legacy)
    }
  })
})

describe('router base', () => {
  it('is taken from the build rather than written out again', async () => {
    const { router } = await import('../../src/router')

    const expected = import.meta.env.BASE_URL.replace(/\/$/, '')
    expect(router.options.history.base).toBe(expected)
  })
})
