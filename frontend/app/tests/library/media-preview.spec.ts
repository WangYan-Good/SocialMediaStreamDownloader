import { readFileSync } from 'node:fs'
import { dirname, resolve } from 'node:path'
import { fileURLToPath } from 'node:url'

import { mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import {
  postAssetPreviewUrl,
  recordingAssetPreviewUrl,
} from '../../src/api/mediaAssets'
import MediaAssetSection from '../../src/components/library/MediaAssetSection.vue'
import type { RecordingId } from '../../src/types/library'
import type { MediaAsset, MediaPreviewKind } from '../../src/types/mediaAsset'

const AWEME = '7657271784144009946'
const ASSET = 'a'.repeat(64)
const BEYOND_SAFE: RecordingId = '9007199254740993'
const ROUNDED = '9007199254740992'

function asset(overrides: Partial<MediaAsset> = {}): MediaAsset {
  return {
    asset_id: ASSET,
    kind: 'video',
    name: 'clip.mp4',
    size_bytes: 1024,
    media_type: 'video/mp4',
    image_index: null,
    preview_kind: 'video',
    ...overrides,
  }
}

beforeEach(() => {
  setActivePinia(createPinia())
  vi.clearAllMocks()
})

describe('a preview address', () => {
  it('names the post that owns the file', () => {
    expect(postAssetPreviewUrl('douyin', AWEME, ASSET)).toBe(
      `/api/library/posts/douyin/${AWEME}/assets/${ASSET}/preview`,
    )
  })

  it('names the recording that owns the file', () => {
    expect(recordingAssetPreviewUrl('7', ASSET)).toBe(
      `/api/library/recordings/7/assets/${ASSET}/preview`,
    )
  })

  it('carries a recording identity beyond the safe range exactly', () => {
    const url = recordingAssetPreviewUrl(BEYOND_SAFE, ASSET)

    expect(url).toBe(
      `/api/library/recordings/9007199254740993/assets/${ASSET}/preview`,
    )
    expect(url).not.toContain(ROUNDED)
  })

  it('is a distinct endpoint rather than a flag on the download', () => {
    //
    // Whether a response is rendered or saved is the server's decision. A query
    // parameter would hand it to whoever writes the url.
    //
    const url = postAssetPreviewUrl('douyin', AWEME, ASSET)

    expect(url.endsWith('/preview')).toBe(true)
    expect(url).not.toContain('?')
    expect(url).not.toContain('inline')
    expect(url).not.toContain('download')
  })

  it('carries no credential', () => {
    const url = recordingAssetPreviewUrl(BEYOND_SAFE, ASSET)

    for (const leak of ['token', 'csrf', 'session', 'user_id', 'role']) {
      expect(url).not.toContain(leak)
    }
  })

  it('escapes every segment', () => {
    expect(postAssetPreviewUrl('dou/yin', 'a b', '../x')).toBe(
      '/api/library/posts/dou%2Fyin/a%20b/assets/..%2Fx/preview',
    )
  })
})

function section(assets: MediaAsset[], previewAssetId: string | null = null) {
  return mount(MediaAssetSection, {
    props: {
      storageState: 'available' as const,
      assets,
      loading: false,
      error: null,
      downloadUrlFor: (one: MediaAsset) =>
        `/api/library/posts/douyin/${AWEME}/assets/${one.asset_id}/download`,
      previewAssetId,
    },
  })
}

describe('the preview affordance', () => {
  it.each<MediaPreviewKind>(['image', 'video', 'audio'])(
    'is offered for a %s the server will render',
    (kind) => {
      const view = section([asset({ preview_kind: kind })])

      expect(view.find('.assets__preview').exists()).toBe(true)
      expect(view.get('.assets__preview').text()).toBe('预览')
    },
  )

  it('is offered for an flv recording, which the server now renders', () => {
    //
    // Phase 10E: the live downloader tries FLV first, so most recordings on
    // disk are flv. They are now previewable through the bundled transmuxer -
    // as their own kind, never as native `video`.
    //
    const view = section([
      asset({ name: 'live.flv', media_type: 'video/x-flv', preview_kind: 'flv' }),
    ])

    expect(view.find('.assets__preview').exists()).toBe(true)
    expect(view.find('.assets__download').exists()).toBe(true)
  })

  it('is absent for a file the server will not render', () => {
    //
    // MPEG-TS stayed download-only: seeking within a static .ts file is limited
    // upstream. A disabled button would read as a fault; there simply is no
    // action.
    //
    const view = section([
      asset({ name: 'live.ts', media_type: 'video/mp2t', preview_kind: null }),
    ])

    expect(view.find('.assets__preview').exists()).toBe(false)
    expect(view.find('.assets__download').exists()).toBe(true)
  })

  it('distinguishes an flv recording from a native video', () => {
    //
    // Both are watchable; only one goes through a `<video src>`. Collapsing
    // them would send flv bytes to an element that cannot decode them.
    //
    const flv = section([asset({ preview_kind: 'flv' })])
    const native = section([asset({ preview_kind: 'video' })])

    expect(flv.find('.assets__preview').exists()).toBe(true)
    expect(native.find('.assets__preview').exists()).toBe(true)
  })

  it('leaves the download on every asset, previewable or not', () => {
    const view = section([
      asset({ asset_id: 'a'.repeat(64), preview_kind: 'video' }),
      asset({ asset_id: 'b'.repeat(64), preview_kind: null, name: 'live.flv' }),
    ])

    expect(view.findAll('.assets__download')).toHaveLength(2)
    expect(view.findAll('.assets__preview')).toHaveLength(1)
  })

  it('asks the panel to open a preview when clicked', async () => {
    const view = section([asset()])

    await view.get('.assets__preview').trigger('click')

    expect(view.emitted('preview')?.[0][0]).toMatchObject({ asset_id: ASSET })
  })

  it('offers to close the one already open', async () => {
    const view = section([asset()], ASSET)

    expect(view.get('.assets__preview').text()).toBe('关闭预览')

    await view.get('.assets__preview').trigger('click')

    expect(view.emitted('closePreview')).toHaveLength(1)
    expect(view.emitted('preview')).toBeUndefined()
  })

  it('does not decide previewability from the file name', () => {
    //
    // The server is the authority. An asset the server marked null stays
    // download-only however the file happens to be called.
    //
    const view = section([
      asset({ name: 'looks-like-a.mp4', media_type: 'video/mp4', preview_kind: null }),
    ])

    expect(view.find('.assets__preview').exists()).toBe(false)
  })
})

describe('the preview flow as written', () => {
  const APP_ROOT = resolve(dirname(fileURLToPath(import.meta.url)), '..', '..')

  function sourceOf(relative: string): string {
    return readFileSync(resolve(APP_ROOT, relative), 'utf-8')
  }

  /**
   * The same file with its commentary removed.
   *
   * These modules explain at length why they do *not* autoplay, do *not* set
   * `crossorigin` and do *not* fetch blobs. A grep over the whole text fails on
   * that documentation, which would make the guard punish the explanation
   * rather than the behaviour.
   */
  function codeOf(relative: string): string {
    return sourceOf(relative)
      .replace(/<!--[\s\S]*?-->/g, '')
      .replace(/\/\*[\s\S]*?\*\//g, '')
      .replace(/^\s*\/\/.*$/gm, '')
  }

  it('the comment stripper actually removes commentary', () => {
    //
    // Without this, every guard below could pass by stripping everything.
    //
    const stripped = codeOf('src/components/library/MediaAssetPreview.vue')

    expect(stripped).toMatch(/preload="metadata"/)
    expect(stripped).toMatch(/<video/)
    expect(stripped).not.toMatch(/tens of gigabytes/)
  })

  const FLOW = [
    'src/api/mediaAssets.ts',
    'src/components/library/MediaAssetPreview.vue',
    'src/components/library/MediaAssetSection.vue',
    'src/components/library/UserLibraryDetailPanel.vue',
  ]

  it('never fetches media into the page', () => {
    for (const relative of FLOW) {
      const source = codeOf(relative)
      expect(source).not.toMatch(/createObjectURL/)
      expect(source).not.toMatch(/\.blob\s*\(/)
      expect(source).not.toMatch(/new\s+Blob/)
    }
  })

  it('converts no recording identity to a number', () => {
    for (const relative of FLOW) {
      const source = codeOf(relative)
      expect(source).not.toMatch(/\bNumber\s*\(/)
      expect(source).not.toMatch(/\bparseInt\s*\(/)
      expect(source).not.toMatch(/\bparseFloat\s*\(/)
    }
  })

  it('never turns a same-origin media request into a CORS fetch', () => {
    //
    // These are same-origin resources. `crossorigin` would switch the element
    // to a CORS fetch for no benefit - it does not affect same-origin
    // credentials either way, it is just not applicable.
    //
    expect(codeOf('src/components/library/MediaAssetPreview.vue')).not.toMatch(
      /crossorigin/,
    )
  })

  it('never starts playing on its own', () => {
    const renderer = codeOf('src/components/library/MediaAssetPreview.vue')

    expect(renderer).not.toMatch(/\bautoplay\b/)
    expect(renderer).not.toMatch(/\bloop\b/)
    expect(renderer).toMatch(/preload="metadata"/)
  })

  it('renders no element that could interpret a document', () => {
    const renderer = codeOf('src/components/library/MediaAssetPreview.vue')

    expect(renderer).not.toMatch(/<iframe/)
    expect(renderer).not.toMatch(/<object/)
    expect(renderer).not.toMatch(/<embed/)
    expect(renderer).not.toMatch(/v-html/)
  })

  it('builds preview addresses in one place', () => {
    for (const relative of [
      'src/components/library/MediaAssetPreview.vue',
      'src/components/library/MediaAssetSection.vue',
    ]) {
      expect(codeOf(relative)).not.toMatch(/['"`]\/api\/library/)
    }
  })
})
