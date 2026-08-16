import { describe, expect, it } from 'vitest'
import { createMemoryHistory, createRouter } from 'vue-router'

import { routes } from '../../src/router'

function testRouter() {
  return createRouter({ history: createMemoryHistory(), routes })
}

describe('route map', () => {
  it('declares the six sections of the new information architecture', () => {
    const names = routes.map((route) => route.name).filter(Boolean)

    expect(names).toEqual([
      'overview',
      'new-download',
      'creators',
      'library',
      'tasks',
      'system',
    ])
  })

  it.each([
    ['/overview', 'overview'],
    ['/new', 'new-download'],
    ['/creators', 'creators'],
    ['/library', 'library'],
    ['/tasks', 'tasks'],
    ['/system', 'system'],
  ])('resolves %s to %s', async (path, name) => {
    const router = testRouter()

    await router.push(path)

    expect(router.currentRoute.value.name).toBe(name)
  })

  it('sends the bare root to the overview', async () => {
    const router = testRouter()

    await router.push('/')
    await router.isReady()

    expect(router.currentRoute.value.name).toBe('overview')
  })

  it('sends an unknown path to the overview rather than nowhere', async () => {
    //
    // The server hands the shell back for every path under the prefix, so an
    // unknown one does reach the router.  Landing on the first real screen is
    // the honest answer while most of the application is still to come.
    //
    const router = testRouter()

    await router.push('/no-such-page')

    expect(router.currentRoute.value.name).toBe('overview')
  })

  it('keeps every section reachable by name', async () => {
    const router = testRouter()

    for (const name of ['overview', 'new-download', 'creators', 'library', 'tasks', 'system']) {
      await router.push({ name })
      expect(router.currentRoute.value.name).toBe(name)
    }
  })

  it('carries no legacy section into the new map', () => {
    //
    // History, Posts, Person, Log and Settings were grouped by which page
    // happened to exist.  Copying them across would have locked the old shape
    // into the new interface before a single screen was written.
    //
    const paths = routes.map((route) => route.path)

    for (const legacy of ['/history', '/posts', '/person', '/log', '/settings']) {
      expect(paths).not.toContain(legacy)
    }
  })
})

describe('router base', () => {
  it('is taken from the build rather than written out again', async () => {
    //
    // Vite owns the deployment base, and the router has to read it back
    // rather than repeat the literal: two copies drift apart the first time
    // either one moves, and the symptom would be every deep link 404ing in
    // production only - where nothing that runs here would have caught it.
    //
    // Asserted against whatever base this build carries rather than copying it.
    // Under test and production P15 that is '/'.
    //
    const { router } = await import('../../src/router')

    const expected = import.meta.env.BASE_URL.replace(/\/$/, '')
    expect(router.options.history.base).toBe(expected)
  })
})
