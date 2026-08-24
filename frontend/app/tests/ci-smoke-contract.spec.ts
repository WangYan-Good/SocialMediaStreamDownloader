//
// jsdom, the suite default: importing the router evaluates createWebHistory,
// which needs a window. The workflow file is still read straight off disk -
// node:fs is available either way.
//
import { readFileSync } from 'node:fs'
import { resolve } from 'node:path'
import { describe, expect, it } from 'vitest'

import { routes } from '../src/router'

//
// The deep-link contract, asserted where the rest of the suite can see it.
//
// Every route in this application is a client-side route: Flask has never heard
// of any of them and answers with the shell so the router can resolve them. The
// consequence is that a route can be added, work perfectly in development, and
// 404 on a refresh in production without a single test noticing - because the
// only thing that exercises it is the runtime smoke in CI, and nothing until
// now checked that the smoke had heard of it either.
//
// This is the guard on that gap. It does not run the smoke; it asserts the
// smoke knows which paths exist. Written in the same spirit as build-config,
// which asserts vite's base for the same class of reason.
//

//
// Resolved from the vitest root - frontend/app - rather than from import.meta,
// which under jsdom is an http url and not a path at all.
//
const workflow = readFileSync(
  resolve(process.cwd(), '../../.github/workflows/ci.yml'),
  'utf8',
)

/** Every concrete path the router serves, flattened from the route tree. */
function routerPaths(records = routes, parent = ''): string[] {
  return records.flatMap((record) => {
    const path = record.path.startsWith('/')
      ? record.path
      : `${parent.replace(/\/$/, '')}/${record.path}`
    return [path, ...routerPaths(record.children ?? [], path)]
  })
}

//
// The smoke walks a bare word list - `for path in overview new ...` - so a path
// is covered when its word appears in that loop.
//
function smokeLoopWords(): string[] {
  const loop = workflow.match(/for path in ([^;]+); do/)
  expect(loop, 'the runtime smoke deep-link loop').toBeTruthy()
  return (loop as RegExpMatchArray)[1]
    //
    // The list is wrapped across lines, so the shell's continuation backslashes
    // sit between the words rather than around them.
    //
    .replace(/\\/g, ' ')
    .trim()
    .split(/\s+/)
    .filter((word) => word.length > 0)
}

describe('the runtime smoke covers every user destination', () => {
  it.each(['new', 'library', 'tasks'])('walks /%s', (path) => {
    expect(smokeLoopWords()).toContain(path)
  })

  it('walks the root separately, as the shell itself', () => {
    expect(workflow).toContain('expect / 200')
  })
})

describe('the runtime smoke covers every admin destination', () => {
  //
  // The half that was missing. Phases 3 and 4 added /admin/library and
  // /admin/tasks, and neither reached the smoke - so a Flask-level regression
  // on the admin console would have shipped green.
  //
  it.each([
    'admin',
    'admin/creators',
    'admin/library',
    'admin/tasks',
    'admin/system',
  ])('walks /%s', (path) => {
    expect(smokeLoopWords()).toContain(path)
  })

  it('expects the shell for /admin rather than a server-side redirect', () => {
    //
    // /admin redirects to /admin/creators in the *router*, after the shell has
    // loaded. Flask must answer 200 with the shell; asserting a 302 here would
    // demand the server know about a client-side route.
    //
    expect(workflow).not.toMatch(/expect_redirect\s+\/admin\b/)
  })
})

describe('the runtime smoke covers the legacy paths still promised', () => {
  it.each(['overview', 'creators', 'system'])('walks /%s', (path) => {
    expect(smokeLoopWords()).toContain(path)
  })
})

describe('the smoke and the router cannot drift apart', () => {
  it('walks every concrete path the router defines', () => {
    //
    // The point of this file. A new route added without a line here is a route
    // whose production deep link nothing has ever tried.
    //
    const covered = new Set(smokeLoopWords().map((word) => `/${word}`))
    covered.add('/')

    //
    // The empty child path under /admin renders as '/admin/', which is the same
    // destination as '/admin' - curl and Flask both treat it so.
    //
    const withoutTrailingSlash = (path: string) => path.replace(/(.)\/$/, '$1')

    const missing = routerPaths()
      .filter((path) => !path.includes(':') && path !== '')
      .map(withoutTrailingSlash)
      .filter((path) => !covered.has(path))

    expect(missing).toEqual([])
  })
})
