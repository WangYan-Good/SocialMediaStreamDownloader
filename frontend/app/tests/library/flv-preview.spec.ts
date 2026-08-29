import { readFileSync } from 'node:fs'
import { dirname, resolve } from 'node:path'
import { fileURLToPath } from 'node:url'

import { mount } from '@vue/test-utils'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { nextTick } from 'vue'

import MediaAssetPreview from '../../src/components/library/MediaAssetPreview.vue'
import type { MediaAsset, MediaPreviewKind } from '../../src/types/mediaAsset'

//
// The transmuxer, replaced. These tests are about what this application asks of
// it - which url, which options, when, and whether it is released again - not
// about whether it can decode FLV.
//
const createPlayer = vi.fn()
const isSupported = vi.fn(() => true)

function fakePlayer() {
  return {
    attachMediaElement: vi.fn(),
    detachMediaElement: vi.fn(),
    load: vi.fn(),
    unload: vi.fn(),
    play: vi.fn(),
    pause: vi.fn(),
    destroy: vi.fn(),
    on: vi.fn(),
    off: vi.fn(),
  }
}

let listeners: Record<string, (...args: unknown[]) => void>

//
// A latch the mocked module awaits before resolving, so a test can hold an
// import open and act while it is still in flight.
//
let importGate: Promise<void> | null = null

vi.mock('mpegts.js', async () => {
  if (importGate) await importGate
  return {
    default: {
      isSupported: () => isSupported(),
      createPlayer: (...args: unknown[]) => createPlayer(...args),
      Events: { ERROR: 'error' },
    },
  }
})

const PREVIEW_URL =
  '/api/library/recordings/9007199254740993/assets/' + 'a'.repeat(64) + '/preview'

function asset(kind: MediaPreviewKind | null, overrides: Partial<MediaAsset> = {}): MediaAsset {
  return {
    asset_id: 'a'.repeat(64),
    kind: 'recording',
    name: 'live.flv',
    size_bytes: 4096,
    media_type: 'video/x-flv',
    image_index: null,
    preview_kind: kind,
    ...overrides,
  }
}

function render(kind: MediaPreviewKind | null, src = PREVIEW_URL) {
  return mount(MediaAssetPreview, { props: { asset: asset(kind), src } })
}

async function settle(times = 10) {
  //
  // The renderer's watcher runs after the DOM is patched (`flush: 'post'`), and
  // the module import that follows resolves as a microtask. Both have to be
  // drained, repeatedly, before the player exists.
  //
  for (let index = 0; index < times; index += 1) {
    await Promise.resolve()
    await nextTick()
  }
}

beforeEach(() => {
  listeners = {}
  importGate = null
  createPlayer.mockReset()
  isSupported.mockReset()
  isSupported.mockReturnValue(true)
  createPlayer.mockImplementation(() => {
    const player = fakePlayer()
    player.on.mockImplementation((event: string, handler: (...a: unknown[]) => void) => {
      listeners[event] = handler
    })
    return player
  })
})

afterEach(() => {
  vi.clearAllMocks()
})

describe('an flv recording preview', () => {
  it('creates a player pointed at the authorized preview url', async () => {
    render('flv')
    await settle()

    expect(createPlayer).toHaveBeenCalledTimes(1)
    const [source] = createPlayer.mock.calls[0]
    expect(source).toMatchObject({
      type: 'flv',
      url: PREVIEW_URL,
      isLive: false,
      cors: false,
      withCredentials: true,
    })
  })

  it('describes a finished recording rather than a live stream', async () => {
    //
    // `isLive` would turn on latency chasing and give up the seeking this
    // depends on. These files stopped being written some time ago.
    //
    render('flv')
    await settle()

    expect(createPlayer.mock.calls[0][0].isLive).toBe(false)
  })

  it('seeks with byte ranges rather than query parameters', async () => {
    render('flv')
    await settle()

    const config = createPlayer.mock.calls[0][1]
    expect(config.seekType).toBe('range')
    //
    // Live-only behaviour must stay off for a file on disk.
    //
    expect(config.liveSync).toBeUndefined()
    expect(config.liveBufferLatencyChasing).toBeUndefined()
    expect(config.enableWorker).toBe(false)
  })

  it('sends no credential of its own in the url', async () => {
    render('flv')
    await settle()

    const url: string = createPlayer.mock.calls[0][0].url
    expect(url).not.toContain('?')
    for (const leak of ['token', 'csrf', 'session', 'user_id', 'role']) {
      expect(url).not.toContain(leak)
    }
    expect(url.startsWith('/api/library/')).toBe(true)
  })

  it('asks for the preview endpoint, never the download', async () => {
    render('flv')
    await settle()

    const url: string = createPlayer.mock.calls[0][0].url
    expect(url.endsWith('/preview')).toBe(true)
    expect(url).not.toContain('/download')
  })

  it('passes no remembered size or invented duration', async () => {
    //
    // The metadata size is from discovery; the endpoint fstats the descriptor
    // and knows better. And nothing here knows the real duration - guessing one
    // from recording timestamps would be a number the player then trusted.
    //
    render('flv')
    await settle()

    const source = createPlayer.mock.calls[0][0]
    expect(source.filesize).toBeUndefined()
    expect(source.duration).toBeUndefined()
  })

  it('attaches to the video element it rendered', async () => {
    const view = render('flv')
    await settle()

    const player = createPlayer.mock.results[0].value
    expect(player.attachMediaElement).toHaveBeenCalledTimes(1)
    expect(player.attachMediaElement.mock.calls[0][0]).toBe(
      view.get('video').element,
    )
  })

  it('loads without playing', async () => {
    const view = render('flv')
    await settle()

    const player = createPlayer.mock.results[0].value
    expect(player.load).toHaveBeenCalledTimes(1)
    expect(player.play).not.toHaveBeenCalled()
    expect(view.get('video').attributes('autoplay')).toBeUndefined()
    expect(view.get('video').attributes('loop')).toBeUndefined()
  })

  it('renders a video element with no src of its own', async () => {
    //
    // The bytes are not a source the browser can read. A `src` alongside the
    // transmuxer would make it try to decode raw FLV and fail.
    //
    const view = render('flv')
    await settle()

    const video = view.get('video')
    expect(video.attributes('src')).toBeUndefined()
    expect(video.attributes('controls')).toBeDefined()
  })
})

describe('when flv playback cannot work', () => {
  it('says so plainly when the browser cannot support it', async () => {
    isSupported.mockReturnValue(false)

    const view = render('flv')
    await settle()

    expect(createPlayer).not.toHaveBeenCalled()
    expect(view.text()).toContain('预览失败，可尝试下载文件。')
  })

  it('says so plainly when the player reports an error', async () => {
    const view = render('flv')
    await settle()

    listeners.error?.('NetworkError', { code: -1, msg: 'boom' })
    await settle()

    expect(view.text()).toContain('预览失败，可尝试下载文件。')
    //
    // Nothing about the codec, the network or the demuxer - none of which a
    // viewer can act on differently.
    //
    expect(view.text()).not.toContain('NetworkError')
    expect(view.text()).not.toContain('boom')
  })

  it('releases the player after an error', async () => {
    render('flv')
    await settle()
    const player = createPlayer.mock.results[0].value

    listeners.error?.('MediaError', {})
    await settle()

    expect(player.destroy).toHaveBeenCalled()
  })

  it('survives a player that throws while being created', async () => {
    createPlayer.mockImplementation(() => {
      throw new Error('no MSE here')
    })

    const view = render('flv')
    await settle()

    expect(view.text()).toContain('预览失败，可尝试下载文件。')
  })
})

describe('letting go of an flv player', () => {
  it('releases it when the component unmounts', async () => {
    const view = render('flv')
    await settle()
    const player = createPlayer.mock.results[0].value

    view.unmount()
    await settle()

    expect(player.unload).toHaveBeenCalled()
    expect(player.detachMediaElement).toHaveBeenCalled()
    expect(player.destroy).toHaveBeenCalled()
  })

  it('releases it when the asset changes', async () => {
    const view = render('flv')
    await settle()
    const first = createPlayer.mock.results[0].value

    await view.setProps({
      asset: asset('flv', { asset_id: 'b'.repeat(64), name: 'other.flv' }),
      src: '/api/library/recordings/9007199254740993/assets/bbb/preview',
    })
    await settle()

    expect(first.destroy).toHaveBeenCalled()
    expect(createPlayer).toHaveBeenCalledTimes(2)
  })

  it('releases it when the preview becomes something native', async () => {
    const view = render('flv')
    await settle()
    const player = createPlayer.mock.results[0].value

    await view.setProps({
      asset: asset('video', { name: 'clip.mp4', media_type: 'video/mp4' }),
      src: '/api/library/posts/douyin/1/assets/ccc/preview',
    })
    await settle()

    expect(player.destroy).toHaveBeenCalled()
    //
    // And the native element takes over, with an ordinary src.
    //
    expect(view.get('video').attributes('src')).toBe(
      '/api/library/posts/douyin/1/assets/ccc/preview',
    )
  })

  it('never runs two players at once', async () => {
    const view = render('flv')
    await settle()
    const first = createPlayer.mock.results[0].value

    await view.setProps({
      asset: asset('flv', { asset_id: 'c'.repeat(64) }),
      src: '/api/library/recordings/9007199254740993/assets/ccc/preview',
    })
    await settle()

    expect(first.destroy).toHaveBeenCalled()
    expect(createPlayer).toHaveBeenCalledTimes(2)
  })
})

describe('nothing but flv reaches the transmuxer', () => {
  it.each<[MediaPreviewKind, string]>([
    ['image', 'img'],
    ['video', 'video'],
    ['audio', 'audio'],
  ])('a %s preview stays native', async (kind, tag) => {
    const view = mount(MediaAssetPreview, {
      props: {
        asset: asset(kind, {
          name: kind === 'image' ? 'a.jpg' : kind === 'video' ? 'a.mp4' : 'a.mp3',
          media_type:
            kind === 'image' ? 'image/jpeg' : kind === 'video' ? 'video/mp4' : 'audio/mpeg',
        }),
        src: PREVIEW_URL,
      },
    })
    await settle()

    expect(createPlayer).not.toHaveBeenCalled()
    expect(view.get(tag).attributes('src')).toBe(PREVIEW_URL)
  })

  it('an unrenderable asset draws nothing at all', async () => {
    const view = render(null)
    await settle()

    expect(createPlayer).not.toHaveBeenCalled()
    expect(view.find('video').exists()).toBe(false)
    expect(view.find('img').exists()).toBe(false)
  })
})

describe('the source as written', () => {
  const APP_ROOT = resolve(dirname(fileURLToPath(import.meta.url)), '..', '..')

  function codeOf(relative: string): string {
    return readFileSync(resolve(APP_ROOT, relative), 'utf-8')
      .replace(/<!--[\s\S]*?-->/g, '')
      .replace(/\/\*[\s\S]*?\*\//g, '')
      .replace(/^\s*\/\/.*$/gm, '')
  }

  it('imports the transmuxer lazily, never at module scope', () => {
    //
    // A static import would put a demuxer in the entry chunk for every visitor,
    // including the ones who only ever look at photographs.
    //
    const source = codeOf('src/components/library/MediaAssetPreview.vue')

    expect(source).toMatch(/await import\(['"]mpegts\.js['"]\)/)
    expect(source).not.toMatch(/^import .*from ['"]mpegts\.js['"]/m)
  })

  it('loads it from the bundle rather than the network', () => {
    const source = codeOf('src/components/library/MediaAssetPreview.vue')

    expect(source).not.toMatch(/<script src=/)
    expect(source).not.toMatch(/cdn|unpkg|jsdelivr/i)
  })

  it('never fetches media itself', () => {
    //
    // The transmuxer uses MediaSource and object urls internally, which is its
    // business. This application must not.
    //
    const source = codeOf('src/components/library/MediaAssetPreview.vue')

    expect(source).not.toMatch(/createObjectURL/)
    expect(source).not.toMatch(/\.blob\s*\(/)
    expect(source).not.toMatch(/fetch\s*\(/)
  })

  it('never calls play', () => {
    expect(codeOf('src/components/library/MediaAssetPreview.vue')).not.toMatch(
      /\.play\s*\(/,
    )
  })
})

describe('a module that arrives too late', () => {
  //
  // The race this protection exists for. Loading the transmuxer is
  // asynchronous, and a viewer can close the preview or open something else
  // while the import is still in flight.
  //
  // Without a generation check the import resolves into a player for an asset
  // nobody is looking at: attached to an element that has been removed, reading
  // a file that is no longer open, and never released because nothing knows it
  // exists.
  //
  it('does not create a player for a preview that was closed', async () => {
    let release!: () => void
    importGate = new Promise<void>((resolve) => {
      release = resolve
    })

    const view = render('flv')
    await settle(3)

    //
    // Still loading - nothing has been created yet.
    //
    expect(createPlayer).not.toHaveBeenCalled()

    view.unmount()
    await settle(3)

    release()
    await settle()

    expect(createPlayer).not.toHaveBeenCalled()
  })

  it('does not create a player for an asset that was replaced', async () => {
    let release!: () => void
    importGate = new Promise<void>((resolve) => {
      release = resolve
    })

    const view = render('flv')
    await settle(3)
    expect(createPlayer).not.toHaveBeenCalled()

    //
    // The viewer opened something native while the module was loading.
    //
    importGate = null
    await view.setProps({
      asset: asset('image', { name: 'a.jpg', media_type: 'image/jpeg' }),
      src: '/api/library/posts/douyin/1/assets/ddd/preview',
    })
    await settle()

    release()
    await settle()

    //
    // The stale import must not build anything, and the native element is what
    // remains.
    //
    expect(createPlayer).not.toHaveBeenCalled()
    expect(view.find('img').exists()).toBe(true)
  })

  it('builds only the current player when two flv previews race', async () => {
    let releaseFirst!: () => void
    importGate = new Promise<void>((resolve) => {
      releaseFirst = resolve
    })

    const view = render('flv')
    await settle(3)

    importGate = null
    await view.setProps({
      asset: asset('flv', { asset_id: 'z'.repeat(64), name: 'second.flv' }),
      src: '/api/library/recordings/9007199254740993/assets/zzz/preview',
    })
    await settle()

    releaseFirst()
    await settle()

    //
    // Exactly one, and it is the one still open.
    //
    expect(createPlayer).toHaveBeenCalledTimes(1)
    expect(createPlayer.mock.calls[0][0].url).toContain('/zzz/preview')
  })
})
