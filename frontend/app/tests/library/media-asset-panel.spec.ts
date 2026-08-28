import { mount } from '@vue/test-utils'
import type { VueWrapper } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { nextTick } from 'vue'

import { listPostAssets, listRecordingAssets } from '../../src/api/mediaAssets'
import UserLibraryDetailPanel from '../../src/components/library/UserLibraryDetailPanel.vue'
import type { LibraryPost, LibraryRecording } from '../../src/types/library'
import type { MediaAssetStorageState } from '../../src/types/mediaAsset'

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

const VIDEO_ASSET = {
  asset_id: 'a'.repeat(64),
  kind: 'video',
  name: `20260824_${AWEME}.mp4`,
  size_bytes: 1572864,
  media_type: 'video/mp4',
  image_index: null,
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
    expect(wrapper.find('video').exists()).toBe(false)
    expect(wrapper.find('img').exists()).toBe(false)
    expect(wrapper.find('audio').exists()).toBe(false)
    expect(wrapper.find('iframe').exists()).toBe(false)
  })

  it('offers saving, and still nothing else', async () => {
    //
    // Saving arrived in Phase 10B and is the only action added. Opening,
    // playing and previewing remain absent - each would need its own boundary,
    // and an inline media element pointed at the endpoint would be the next
    // phase arriving without one.
    //
    const wrapper = await openPost()

    for (const action of ['打开', '播放', '预览', '复制路径']) {
      expect(buttonSaying(wrapper, action)).toBeUndefined()
    }
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
