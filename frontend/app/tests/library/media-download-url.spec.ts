import { readFileSync } from 'node:fs'
import { dirname, resolve } from 'node:path'
import { fileURLToPath } from 'node:url'

import { describe, expect, it } from 'vitest'

import {
  postAssetDownloadUrl,
  recordingAssetDownloadUrl,
} from '../../src/api/mediaAssets'
import type { RecordingId } from '../../src/types/library'

const AWEME = '7657271784144009946'
const ASSET = 'a'.repeat(64)

//
// The identity a JavaScript number cannot hold, and what it becomes if one is
// ever allowed to. Asserting the second is absent is what gives these tests
// the ability to fail.
//
const BEYOND_SAFE: RecordingId = '9007199254740993'
const ROUNDED = '9007199254740992'

describe('a download url', () => {
  it('names the post that owns the file, not just the file', () => {
    //
    // The parent identity is in the path because an asset id is not a
    // capability. A url keyed on the id alone would authorize whoever holds it.
    //
    expect(postAssetDownloadUrl('douyin', AWEME, ASSET)).toBe(
      `/api/library/posts/douyin/${AWEME}/assets/${ASSET}/download`,
    )
  })

  it('names the recording that owns the file', () => {
    expect(recordingAssetDownloadUrl('7', ASSET)).toBe(
      `/api/library/recordings/7/assets/${ASSET}/download`,
    )
  })

  it('carries a recording identity beyond the safe range exactly', () => {
    const url = recordingAssetDownloadUrl(BEYOND_SAFE, ASSET)

    expect(url).toBe(
      `/api/library/recordings/9007199254740993/assets/${ASSET}/download`,
    )
    expect(url).not.toContain(ROUNDED)
  })

  it('escapes every segment it is given', () => {
    //
    // None of these should ever occur, which is the reason to encode rather
    // than to trust: a segment that could contain a slash could name a
    // different endpoint entirely.
    //
    const url = postAssetDownloadUrl('dou/yin', 'a b', '../../etc/passwd')

    expect(url).toBe(
      '/api/library/posts/dou%2Fyin/a%20b/assets/..%2F..%2Fetc%2Fpasswd/download',
    )
    expect(url.split('/assets/')[0]).not.toContain('etc')
  })

  it('carries no credential of its own', () => {
    //
    // The session cookie authenticates this, as it does every other request.
    // A token in the url would end up in history, in referrer headers and in
    // any proxy log between here and the server.
    //
    const url = recordingAssetDownloadUrl(BEYOND_SAFE, ASSET)

    expect(url).not.toContain('?')
    for (const leak of ['token', 'csrf', 'session', 'user_id', 'role']) {
      expect(url).not.toContain(leak)
    }
  })
})

describe('the download url flow as written', () => {
  const APP_ROOT = resolve(dirname(fileURLToPath(import.meta.url)), '..', '..')

  function sourceOf(relative: string): string {
    return readFileSync(resolve(APP_ROOT, relative), 'utf-8')
  }

  const FLOW = [
    'src/api/mediaAssets.ts',
    'src/components/library/MediaAssetSection.vue',
    'src/components/library/UserLibraryDetailPanel.vue',
  ]

  it.each(FLOW)('%s converts no identity to a number', (relative) => {
    const source = sourceOf(relative)

    for (const lossy of [/\bNumber\s*\(/, /\bparseInt\s*\(/, /\bparseFloat\s*\(/]) {
      expect(source).not.toMatch(lossy)
    }
  })

  it('never fetches media into the page', () => {
    //
    // A recording can be tens of gigabytes. `fetch(...).blob()` would put all
    // of it in the tab's memory before anything was saved, and would also
    // discard the browser's own download UI. A plain same-origin anchor lets
    // the browser stream it to disk.
    //
    for (const relative of FLOW) {
      const source = sourceOf(relative)
      expect(source).not.toMatch(/createObjectURL/)
      expect(source).not.toMatch(/\.blob\s*\(/)
      expect(source).not.toMatch(/new\s+Blob/)
      expect(source).not.toMatch(/responseType\s*:\s*['"]blob/)
    }
  })

  it('adds no preview, player or inline media element', () => {
    //
    // This phase delivers attachments. A `<video>`, an `<img src>` pointing at
    // the endpoint, or an inline disposition would all be the next phase
    // arriving early and without its own design.
    //
    const section = sourceOf('src/components/library/MediaAssetSection.vue')

    for (const element of [/<video/, /<audio/, /<img\b/, /<iframe/]) {
      expect(section).not.toMatch(element)
    }
  })

  it('builds the url in one place rather than at each call site', () => {
    //
    // A url assembled by string concatenation in a component is a url that
    // drifts from the route it is meant to address.
    //
    const section = sourceOf('src/components/library/MediaAssetSection.vue')

    expect(section).not.toMatch(/['"`]\/api\/library/)
  })
})

import { mount } from '@vue/test-utils'

import MediaAssetSection from '../../src/components/library/MediaAssetSection.vue'
import type { MediaAsset, MediaAssetStorageState } from '../../src/types/mediaAsset'

function asset(overrides: Partial<MediaAsset> = {}): MediaAsset {
  return {
    asset_id: ASSET,
    kind: 'video',
    name: '20260824_video.mp4',
    size_bytes: 1024,
    media_type: 'video/mp4',
    image_index: null,
    //
    // Phase 10D: the server says whether it will render a file. These download
    // tests do not exercise previewing, but the shape has to be honest.
    //
    preview_kind: 'video',
    ...overrides,
  }
}

function section(
  storageState: MediaAssetStorageState | null,
  assets: MediaAsset[] = [],
  withUrl = true,
) {
  return mount(MediaAssetSection, {
    props: {
      storageState,
      assets,
      loading: false,
      error: null,
      downloadUrlFor: withUrl
        ? (one: MediaAsset) => recordingAssetDownloadUrl(BEYOND_SAFE, one.asset_id)
        : null,
      previewAssetId: null,
    },
  })
}

describe('the download affordance', () => {
  it('appears for a file the server just said is there', () => {
    const view = section('available', [asset()])

    const link = view.get('.assets__download')
    expect(link.attributes('href')).toBe(
      `/api/library/recordings/9007199254740993/assets/${ASSET}/download`,
    )
    expect(link.text()).toBe('下载')
  })

  it('carries the recording identity into the href without rounding it', () => {
    const view = section('available', [asset()])

    const href = view.get('.assets__download').attributes('href') ?? ''
    expect(href).toContain('9007199254740993')
    expect(href).not.toContain(ROUNDED)
  })

  it.each<MediaAssetStorageState>(['missing', 'empty', 'unavailable'])(
    'offers nothing when the server reports %s',
    (state) => {
      //
      // These states are rendered as a note instead of a list, so there is no
      // row to attach a download to - and there must not be, because the server
      // has just said it cannot see the files.
      //
      const view = section(state, [asset()])

      expect(view.find('.assets__download').exists()).toBe(false)
    },
  )

  it('offers nothing while the read failed', () => {
    const view = mount(MediaAssetSection, {
      props: {
        storageState: null,
        assets: [asset()],
        loading: false,
        error: '暂时无法读取文件状态，请重试。',
        downloadUrlFor: () => '/api/library/posts/douyin/x/assets/y/download',
        previewAssetId: null,
      },
    })

    expect(view.find('.assets__download').exists()).toBe(false)
  })

  it('offers nothing when no resource is open to address', () => {
    const view = section('available', [asset()], false)

    expect(view.find('.assets__download').exists()).toBe(false)
    //
    // The file is still listed - only the way to save it is absent.
    //
    expect(view.find('.assets__name').exists()).toBe(true)
  })

  it('renders a link the browser follows, not a script-driven button', () => {
    const view = section('available', [asset()])
    const link = view.get('.assets__download')

    expect(link.element.tagName).toBe('A')
    //
    // No click handler intercepting it, and no `download` attribute either -
    // the server's Content-Disposition decides the filename, and it is the
    // side that knows the file's real name.
    //
    expect(link.attributes('download')).toBeUndefined()
    expect(link.attributes('target')).toBeUndefined()
  })

  it('shows one download per file', () => {
    const view = section('available', [
      asset(),
      asset({ asset_id: 'b'.repeat(64), name: 'second.mp4' }),
    ])

    expect(view.findAll('.assets__download')).toHaveLength(2)
  })
})
