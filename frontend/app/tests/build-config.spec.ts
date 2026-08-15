// @vitest-environment node
//
// Node, not jsdom: this file imports the real vite config, which resolves paths
// through import.meta.url - a file:// URL only outside a browser environment.
//
import { describe, expect, it } from 'vitest'
import type { UserConfig } from 'vite'

import viteConfig from '../vite.config'

//
// The build's own contract, asserted here because nothing else in this suite
// can see it: the router reads `import.meta.env.BASE_URL`, which under test is
// always '/', so a wrong or missing `base` would pass every other test in the
// project and only break in production - as every asset 404ing.
//

async function resolvedConfig(mode = 'production'): Promise<UserConfig> {
  const factory = viteConfig as unknown as (env: {
    command: 'build' | 'serve'
    mode: string
  }) => UserConfig | Promise<UserConfig>
  return await factory({ command: 'build', mode })
}

describe('vite base', () => {
  it('is the prefix Flask serves the application from', async () => {
    const config = await resolvedConfig()

    expect(config.base).toBe('/app/')
  })

  it('keeps the trailing slash', async () => {
    //
    // Vite joins asset paths onto this string directly.  Without the slash the
    // emitted urls become '/appassets/...', which is a 404 that reads like a
    // typo nobody made.
    //
    const config = await resolvedConfig()

    expect(config.base).toMatch(/\/$/)
  })
})

describe('dev proxy', () => {
  it('forwards the api to a backend during development', async () => {
    const config = await resolvedConfig('development')
    const proxy = config.server?.proxy as Record<string, { target?: string }> | undefined

    expect(proxy).toBeDefined()
    expect(proxy?.['/api']).toBeDefined()
    expect(proxy?.['/api']?.target).toMatch(/^http:\/\//)
  })

  it('defaults to the port this project server actually listens on', async () => {
    const config = await resolvedConfig('development')
    const proxy = config.server?.proxy as Record<string, { target?: string }>

    expect(proxy['/api'].target).toContain('5001')
  })
})

describe('the production bundle carries no backend hostname', () => {
  it('states no absolute api base', async () => {
    //
    // The application is served by the same process that answers /api, so the
    // api base is a relative path.  An absolute hostname here would work on one
    // machine and break the moment the app is reached by any other name.
    //
    const config = await resolvedConfig()
    const defined = JSON.stringify(config.define ?? {})

    expect(defined).not.toMatch(/https?:\/\//)
  })
})
