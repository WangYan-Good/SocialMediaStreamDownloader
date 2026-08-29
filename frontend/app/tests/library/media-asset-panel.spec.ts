import { mount } from '@vue/test-utils'
import type { VueWrapper } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { nextTick } from 'vue'

import { listPostAssets, listRecordingAssets } from '../../src/api/mediaAssets'
import UserLibraryDetailPanel from '../../src/components/library/UserLibraryDetailPanel.vue'
import type { LibraryPost, LibraryRecording } from '../../src/types/library'
import type { MediaAsset, MediaAssetStorageState } from '../../src/types/mediaAsset'

vi.mock('../../src/api/mediaAssets', () => ({
  listPostAssets: vi.fn(),
  listRecordingAssets: vi.fn(),
  //
  // Real implementations rather than stubs: these are pure functions over a
  // resource identity, and a test that faked them would stop noticing if the
  // url the panel builds ever drifted from the route that serves it.
  //
  postAssetDownloadUrl: (platform: string, awemeId: string, assetId: string) =>
    `/api/library/posts/${encodeURIComponent(platform)}/${encodeURIComponent(awemeId)}` +
    `/assets/${encodeURIComponent(assetId)}/download`,
  recordingAssetDownloadUrl: (recordingId: string, assetId: string) =>
    `/api/library/recordings/${encodeURIComponent(recordingId)}` +
    `/assets/${encodeURIComponent(assetId)}/download`,
  postAssetPreviewUrl: (platform: string, awemeId: string, assetId: string) =>
    `/api/library/posts/${encodeURIComponent(platform)}/${encodeURIComponent(awemeId)}` +
    `/assets/${encodeURIComponent(assetId)}/preview`,
  recordingAssetPreviewUrl: (recordingId: string, assetId: string) =>
    `/api/library/recordings/${encodeURIComponent(recordingId)}` +
    `/assets/${encodeURIComponent(assetId)}/preview`,
}))

const mockedPost = vi.mocked(listPostAssets)
const mockedRecording = vi.mocked(listRecordingAssets)

const AWEME = '7657271784144009946'

function post(): LibraryPost {
  return {
    platform: 'douyin',
    aweme_id: AWEME,
    nickname: '某位主播',
    aweme_type: 'video',
    desc: '一条作品',
    create_time: null,
    downloaded_at: '2026-08-24T09:30:15.250',
    media_count: 3,
    saved_count: 3,
  } as unknown as LibraryPost
}

function recording(): LibraryRecording {
  return {
    recording_id: 7,
    platform: 'douyin',
    nickname: '某位主播',
    title: '晚间直播',
    protocol: 'flv',
    started_at: null,
    finished_at: null,
    created_at: '2026-08-24T09:30:15.250',
  } as unknown as LibraryRecording
}

function result(state: MediaAssetStorageState, assets: unknown[] = []) {
  return {
    resource: { kind: 'post', platform: 'douyin', aweme_id: AWEME },
    storage_state: state,
    assets,
  }
}

const VIDEO_ASSET: MediaAsset = {
  asset_id: 'a'.repeat(64),
  kind: 'video',
  name: `20260824_${AWEME}.mp4`,
  size_bytes: 1572864,
  media_type: 'video/mp4',
  image_index: null,
  preview_kind: 'video',
}

const TS_ASSET: MediaAsset = {
  asset_id: 'f'.repeat(64),
  kind: 'recording',
  name: 'live.ts',
  size_bytes: 4096,
  media_type: 'video/mp2t',
  image_index: null,
  //
  // Still download-only: seeking within a static .ts file is limited upstream.
  //
  preview_kind: null,
}

async function settle() {
  for (let index = 0; index < 8; index += 1) {
    await Promise.resolve()
  }
  await nextTick()
}

async function openPost(state: MediaAssetStorageState = 'available', assets = [VIDEO_ASSET]) {
  mockedPost.mockResolvedValue(result(state, assets) as never)
  const wrapper = mount(UserLibraryDetailPanel, {
    props: { post: post(), recording: null },
  })
  await settle()
  return wrapper
}

function buttonSaying(wrapper: VueWrapper, text: string) {
  return wrapper.findAll('button').find((one) => one.text().includes(text))
}

beforeEach(() => {
  setActivePinia(createPinia())
  vi.clearAllMocks()
  mockedPost.mockResolvedValue(result('available', [VIDEO_ASSET]) as never)
  mockedRecording.mockResolvedValue(result('available', []) as never)
})

describe('file status appears only when a resource is opened', () => {
  it('asks about the post that was opened', async () => {
    await openPost()

    expect(mockedPost).toHaveBeenCalledTimes(1)
    expect(mockedPost.mock.calls[0][0]).toBe('douyin')
    expect(mockedPost.mock.calls[0][1]).toBe(AWEME)
  })

  it('asks about the recording that was opened', async () => {
    mount(UserLibraryDetailPanel, { props: { post: null, recording: recording() } })
    await settle()

    expect(mockedRecording).toHaveBeenCalledTimes(1)
    expect(mockedRecording.mock.calls[0][0]).toBe(7)
    expect(mockedPost).not.toHaveBeenCalled()
  })
})

describe('what the panel says about each storage state', () => {
  it('lists the files that are there', async () => {
    const wrapper = await openPost()
    const text = wrapper.text()

    expect(text).toContain('文件状态')
    expect(text).toContain(`20260824_${AWEME}.mp4`)
    expect(text).toContain('视频')
    //
    // A size somebody can read, not a byte count.
    //
    expect(text).toContain('1.5 MB')
  })

  it('says the files are gone without calling the record wrong', async () => {
    //
    // The database still says 3 / 3 were saved. That remains true - it is what
    // the download recorded. Both facts are shown.
    //
    const wrapper = await openPost('missing', [])

    expect(wrapper.text()).toContain('文件已不在当前下载目录中')
    expect(wrapper.text()).toContain('3 / 3')
  })

  it('says the directory is there but holds nothing recognisable', async () => {
    const wrapper = await openPost('empty', [])

    expect(wrapper.text()).toContain('没有发现可识别的媒体文件')
  })

  it('says it cannot safely tell, and says nothing more', async () => {
    const wrapper = await openPost('unavailable', [])
    const text = wrapper.text()

    expect(text).toContain('暂时无法安全确认文件状态')
    for (const internal of ['/app/downloads', '/tmp', 'symlink', 'PermissionError', '权限']) {
      expect(text).not.toContain(internal)
    }
  })
})

describe('the panel never discloses where a file lives', () => {
  it('shows a name and a size and no location', async () => {
    const wrapper = await openPost()
    const text = wrapper.text()

    for (const forbidden of ['/downloads', '/app', 'save_dir', 'output_path', '..']) {
      expect(text).not.toContain(forbidden)
    }
  })

  it('renders no media element, and no link but the download', async () => {
    //
    // Phase 10A had no route behind an anchor, so it allowed none. Phase 10B
    // serves attachments, so exactly one link is expected per asset - and it
    // must go to the download endpoint rather than anywhere else.
    //
    // Media elements stay forbidden. The server sends every asset as an
    // attachment, images included, so nothing stored here is rendered by this
    // page; a `<video>` or an `<img src>` pointed at the endpoint would be
    // inline delivery arriving without the design it needs.
    //
    const wrapper = await openPost()

    for (const link of wrapper.findAll('a')) {
      expect(link.attributes('href')).toMatch(/^\/api\/library\/.+\/download$/)
    }
    //
    // Nothing is rendered until somebody asks. Phase 10D added a preview, and
    // it appears on a click - never on opening the panel. See the on-demand
    // tests below.
    //
    expect(wrapper.find('video').exists()).toBe(false)
    expect(wrapper.find('img').exists()).toBe(false)
    expect(wrapper.find('audio').exists()).toBe(false)
    expect(wrapper.find('iframe').exists()).toBe(false)
  })

  it('offers saving and previewing, and still nothing else', async () => {
    //
    // Saving arrived in Phase 10B, previewing in Phase 10D. Opening a file with
    // something else, playing it automatically and copying its path remain
    // absent - the last permanently, since no path exists here to copy.
    //
    const wrapper = await openPost()

    for (const action of ['打开', '播放', '复制路径']) {
      expect(buttonSaying(wrapper, action)).toBeUndefined()
    }
    //
    // Present, because the server said this mp4 is renderable - and still inert
    // until it is clicked.
    //
    expect(buttonSaying(wrapper, '预览')).toBeTruthy()
    expect(wrapper.find('video').exists()).toBe(false)
    expect(buttonSaying(wrapper, '刷新')).toBeTruthy()

    //
    // A link the browser follows, not a button that fetches. And still no path
    // anywhere in it - the href names the resource and the asset id, which is
    // exactly what the server needs and nothing about where the file lives.
    //
    const download = wrapper.get('.assets__download')
    expect(download.element.tagName).toBe('A')
    expect(download.attributes('href')).toBe(
      `/api/library/posts/douyin/${AWEME}/assets/${'a'.repeat(64)}/download`,
    )
  })

  it('re-reads on refresh and reflects what changed', async () => {
    const wrapper = await openPost()
    expect(wrapper.text()).toContain(`20260824_${AWEME}.mp4`)

    mockedPost.mockResolvedValue(result('missing', []) as never)
    await buttonSaying(wrapper, '刷新')?.trigger('click')
    await settle()

    expect(mockedPost).toHaveBeenCalledTimes(2)
    expect(wrapper.text()).toContain('文件已不在当前下载目录中')
  })
})

describe('when the status cannot be read at all', () => {
  it('says so in the interface own words', async () => {
    const { ApiError } = await import('../../src/api/client')
    mockedPost.mockRejectedValue(
      new ApiError({
        kind: 'backend',
        status: 500,
        code: 500,
        message: 'PermissionError /app/downloads/creator',
      }),
    )
    const wrapper = mount(UserLibraryDetailPanel, {
      props: { post: post(), recording: null },
    })
    await settle()

    const text = wrapper.text()
    expect(text).toContain('暂时无法读取文件状态')
    expect(text).not.toContain('/app/downloads')
    expect(text).not.toContain('PermissionError')
  })
})

//
// >>========================= preview, on demand only =========================<<
//
const IMAGE_ASSET: MediaAsset = {
  asset_id: 'c'.repeat(64),
  kind: 'image',
  name: `20260824_${AWEME}_01.jpg`,
  size_bytes: 2048,
  media_type: 'image/jpeg',
  image_index: 1,
  preview_kind: 'image',
}

const AUDIO_ASSET: MediaAsset = {
  asset_id: 'd'.repeat(64),
  kind: 'music',
  name: `20260824_${AWEME}_music.mp3`,
  size_bytes: 4096,
  media_type: 'audio/mpeg',
  image_index: null,
  preview_kind: 'audio',
}

function previewButtons(wrapper: VueWrapper) {
  return wrapper.findAll('button').filter((one) => one.text().includes('预览'))
}

describe('opening a preview', () => {
  it('renders nothing and requests no media until asked', async () => {
    //
    // The whole point of on-demand. Opening a detail panel for a post with a
    // 300 MB video must cost one metadata call, not the video.
    //
    const wrapper = await openPost('available', [VIDEO_ASSET, IMAGE_ASSET])

    expect(wrapper.find('video').exists()).toBe(false)
    expect(wrapper.find('img').exists()).toBe(false)
    expect(wrapper.find('audio').exists()).toBe(false)
    expect(mockedPost).toHaveBeenCalledTimes(1)
  })

  it('renders an image where the server said it would', async () => {
    const wrapper = await openPost('available', [IMAGE_ASSET])

    await previewButtons(wrapper)[0].trigger('click')
    await settle()

    const image = wrapper.get('img')
    expect(image.attributes('src')).toBe(
      `/api/library/posts/douyin/${AWEME}/assets/${IMAGE_ASSET.asset_id}/preview`,
    )
    expect(image.attributes('alt')).toBe(IMAGE_ASSET.name)
    expect(image.attributes('loading')).toBe('lazy')
  })

  it('renders a video with controls and no autoplay', async () => {
    const wrapper = await openPost('available', [VIDEO_ASSET])

    await previewButtons(wrapper)[0].trigger('click')
    await settle()

    const video = wrapper.get('video')
    expect(video.attributes('src')).toBe(
      `/api/library/posts/douyin/${AWEME}/assets/${VIDEO_ASSET.asset_id}/preview`,
    )
    expect(video.attributes('controls')).toBeDefined()
    expect(video.attributes('preload')).toBe('metadata')
    expect(video.attributes('autoplay')).toBeUndefined()
    expect(video.attributes('loop')).toBeUndefined()
    //
    // Same-origin, so there is no CORS request to configure and the attribute
    // has no place here.
    //
    expect(video.attributes('crossorigin')).toBeUndefined()
  })

  it('renders audio with controls and no autoplay', async () => {
    const wrapper = await openPost('available', [AUDIO_ASSET])

    await previewButtons(wrapper)[0].trigger('click')
    await settle()

    const audio = wrapper.get('audio')
    expect(audio.attributes('controls')).toBeDefined()
    expect(audio.attributes('preload')).toBe('metadata')
    expect(audio.attributes('autoplay')).toBeUndefined()
  })

  it('shows one asset at a time', async () => {
    //
    // An image set can hold thirty files. Thirty elements would be thirty
    // requests for media nobody asked to see.
    //
    const wrapper = await openPost('available', [IMAGE_ASSET, VIDEO_ASSET])

    await previewButtons(wrapper)[0].trigger('click')
    await settle()
    expect(wrapper.findAll('img')).toHaveLength(1)

    await previewButtons(wrapper)[1].trigger('click')
    await settle()

    expect(wrapper.findAll('video')).toHaveLength(1)
    expect(wrapper.find('img').exists()).toBe(false)
  })

  it('closes when the same asset is asked for again', async () => {
    const wrapper = await openPost('available', [VIDEO_ASSET])

    await previewButtons(wrapper)[0].trigger('click')
    await settle()
    expect(wrapper.find('video').exists()).toBe(true)

    await previewButtons(wrapper)[0].trigger('click')
    await settle()

    expect(wrapper.find('video').exists()).toBe(false)
  })

  it('closes from the preview own control', async () => {
    const wrapper = await openPost('available', [VIDEO_ASSET])
    await previewButtons(wrapper)[0].trigger('click')
    await settle()

    await wrapper.get('.preview__close').trigger('click')
    await settle()

    expect(wrapper.find('video').exists()).toBe(false)
  })

  it('offers no preview for a file the server will not render', async () => {
    const wrapper = await openPost('available', [TS_ASSET])

    expect(previewButtons(wrapper)).toHaveLength(0)
    //
    // And it is still downloadable - refusing to render is not refusing to
    // deliver.
    //
    expect(wrapper.find('.assets__download').exists()).toBe(true)
  })
})

describe('a preview that must not outlive what it shows', () => {
  it('closes when the panel switches to another resource', async () => {
    const wrapper = await openPost('available', [VIDEO_ASSET])
    await previewButtons(wrapper)[0].trigger('click')
    await settle()
    expect(wrapper.find('video').exists()).toBe(true)

    mockedPost.mockResolvedValue(result('available', [IMAGE_ASSET]) as never)
    await wrapper.setProps({
      post: { ...post(), aweme_id: '1111111111111111111' },
      recording: null,
    })
    await settle()

    //
    // Showing one post's details above another post's media would be a lie the
    // interface tells while still streaming it.
    //
    expect(wrapper.find('video').exists()).toBe(false)
  })

  it('closes when the file list is re-read', async () => {
    //
    // Refreshing exists because the disk may have changed. The same asset id
    // can name different bytes afterwards, so an element still pointed at the
    // old representation is showing something that may no longer exist.
    //
    const wrapper = await openPost('available', [VIDEO_ASSET])
    await previewButtons(wrapper)[0].trigger('click')
    await settle()
    expect(wrapper.find('video').exists()).toBe(true)

    await buttonSaying(wrapper, '刷新')?.trigger('click')
    await settle()

    expect(wrapper.find('video').exists()).toBe(false)
    expect(mockedPost).toHaveBeenCalledTimes(2)
  })

  it('closes when the asset it was showing has gone', async () => {
    const wrapper = await openPost('available', [VIDEO_ASSET])
    await previewButtons(wrapper)[0].trigger('click')
    await settle()

    mockedPost.mockResolvedValue(result('missing', []) as never)
    await buttonSaying(wrapper, '刷新')?.trigger('click')
    await settle()

    expect(wrapper.find('video').exists()).toBe(false)
    expect(wrapper.text()).toContain('文件已不在当前下载目录中')
  })

  it('reports a failure in the interface own words', async () => {
    const wrapper = await openPost('available', [IMAGE_ASSET])
    await previewButtons(wrapper)[0].trigger('click')
    await settle()

    await wrapper.get('img').trigger('error')
    await settle()

    expect(wrapper.text()).toContain('预览失败，可尝试下载文件。')
    //
    // Nothing about the status, the path or the codec - none of which a viewer
    // could act on differently.
    //
    expect(wrapper.text()).not.toContain('404')
    expect(wrapper.text()).not.toContain('/downloads')
    //
    // And the useful next step is still there.
    //
    expect(wrapper.find('.assets__download').exists()).toBe(true)
  })
})

describe('a recording preview', () => {
  it('carries an identity beyond the safe range exactly', async () => {
    const RECORDING_MP4 = {
      ...VIDEO_ASSET,
      asset_id: 'e'.repeat(64),
      kind: 'recording',
      name: 'live.mp4',
    }
    mockedRecording.mockResolvedValue({
      resource: { kind: 'recording', recording_id: '9007199254740993' },
      storage_state: 'available',
      assets: [RECORDING_MP4],
    } as never)

    const wrapper = mount(UserLibraryDetailPanel, {
      props: {
        post: null,
        recording: { ...recording(), recording_id: '9007199254740993' },
      },
    })
    await settle()

    await previewButtons(wrapper)[0].trigger('click')
    await settle()

    const src = wrapper.get('video').attributes('src') ?? ''
    expect(src).toBe(
      `/api/library/recordings/9007199254740993/assets/${RECORDING_MP4.asset_id}/preview`,
    )
    expect(src).not.toContain('9007199254740992')
  })
})

//
// >>===================== flv recordings through the panel =====================<<
//
const FLV_RECORDING: MediaAsset = {
  asset_id: 'g'.repeat(64),
  kind: 'recording',
  name: 'live.flv',
  size_bytes: 8192,
  media_type: 'video/x-flv',
  image_index: null,
  preview_kind: 'flv',
}

describe('previewing an flv recording', () => {
  it('addresses it with an identity beyond the safe range, intact', async () => {
    mockedRecording.mockResolvedValue({
      resource: { kind: 'recording', recording_id: '9007199254740993' },
      storage_state: 'available',
      assets: [FLV_RECORDING],
    } as never)

    const wrapper = mount(UserLibraryDetailPanel, {
      props: {
        post: null,
        recording: { ...recording(), recording_id: '9007199254740993' },
      },
    })
    await settle()

    await previewButtons(wrapper)[0].trigger('click')
    await settle()

    //
    // The element exists; what feeds it is the transmuxer, which is mocked away
    // in this file. What matters here is the address the panel built.
    //
    const video = wrapper.find('video')
    expect(video.exists()).toBe(true)
    //
    // No src of its own - the bytes are supplied through Media Source
    // Extensions, not read from the attribute.
    //
    expect(video.attributes('src')).toBeUndefined()
  })

  it('still costs nothing until it is asked for', async () => {
    mockedRecording.mockResolvedValue({
      resource: { kind: 'recording', recording_id: '9007199254740993' },
      storage_state: 'available',
      assets: [FLV_RECORDING],
    } as never)

    const wrapper = mount(UserLibraryDetailPanel, {
      props: {
        post: null,
        recording: { ...recording(), recording_id: '9007199254740993' },
      },
    })
    await settle()

    expect(wrapper.find('video').exists()).toBe(false)
    expect(previewButtons(wrapper)).toHaveLength(1)
  })

  it('is closed by the same controls as any other preview', async () => {
    mockedRecording.mockResolvedValue({
      resource: { kind: 'recording', recording_id: '9007199254740993' },
      storage_state: 'available',
      assets: [FLV_RECORDING],
    } as never)

    const wrapper = mount(UserLibraryDetailPanel, {
      props: {
        post: null,
        recording: { ...recording(), recording_id: '9007199254740993' },
      },
    })
    await settle()

    await previewButtons(wrapper)[0].trigger('click')
    await settle()
    expect(wrapper.find('video').exists()).toBe(true)

    await wrapper.get('.preview__close').trigger('click')
    await settle()

    expect(wrapper.find('video').exists()).toBe(false)
  })
})
