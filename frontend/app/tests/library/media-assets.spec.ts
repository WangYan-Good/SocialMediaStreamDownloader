import { createPinia, setActivePinia } from 'pinia'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import { ApiError } from '../../src/api/client'
import { listPostAssets, listRecordingAssets } from '../../src/api/mediaAssets'
import { useLibraryAssetsStore } from '../../src/stores/libraryAssets'
import type { ResourceAssetResult } from '../../src/types/mediaAsset'

vi.mock('../../src/api/mediaAssets', () => ({
  listPostAssets: vi.fn(),
  listRecordingAssets: vi.fn(),
}))

const mockedPost = vi.mocked(listPostAssets)
const mockedRecording = vi.mocked(listRecordingAssets)

const AWEME = '7657271784144009946'

function available(name = `20260824_${AWEME}.mp4`): ResourceAssetResult {
  return {
    resource: { kind: 'post', platform: 'douyin', aweme_id: AWEME },
    storage_state: 'available',
    assets: [
      {
        asset_id: 'a'.repeat(64),
        kind: 'video',
        name,
        size_bytes: 1048576,
        media_type: 'video/mp4',
        image_index: null,
        preview_kind: 'video',
      },
    ],
  }
}

function deferred<T>() {
  let settle: (value: T) => void = () => {}
  const promise = new Promise<T>((resolve) => {
    settle = resolve
  })
  return { promise, settle }
}

beforeEach(() => {
  setActivePinia(createPinia())
  vi.clearAllMocks()
  mockedPost.mockResolvedValue(available())
  mockedRecording.mockResolvedValue({
    resource: { kind: 'recording', recording_id: '7' },
    storage_state: 'available',
    assets: [],
  })
})

describe('the asset store as a short-lived view of one resource', () => {
  it('knows nothing until something is selected', () => {
    const store = useLibraryAssetsStore()

    expect(store.assets).toEqual([])
    expect(store.storageState).toBeNull()
    expect(store.loading).toBe(false)
    expect(mockedPost).not.toHaveBeenCalled()
  })

  it('reads one post when one post is opened', async () => {
    const store = useLibraryAssetsStore()

    await store.loadPostAssets('douyin', AWEME)

    expect(mockedPost).toHaveBeenCalledTimes(1)
    expect(mockedPost.mock.calls[0][0]).toBe('douyin')
    expect(mockedPost.mock.calls[0][1]).toBe(AWEME)
    expect(store.storageState).toBe('available')
    expect(store.assets).toHaveLength(1)
  })

  it('reads one recording when one recording is opened', async () => {
    const store = useLibraryAssetsStore()

    await store.loadRecordingAssets('7')

    expect(mockedRecording).toHaveBeenCalledTimes(1)
    expect(mockedRecording.mock.calls[0][0]).toBe('7')
    expect(store.storageState).toBe('available')
  })

  it('forgets the previous resource when told to clear', async () => {
    const store = useLibraryAssetsStore()
    await store.loadPostAssets('douyin', AWEME)

    store.clear()

    expect(store.assets).toEqual([])
    expect(store.storageState).toBeNull()
    expect(store.error).toBeNull()
  })

  it('reads again on refresh, for the same resource', async () => {
    //
    // The point of a refresh button: somebody deleted the files by hand and
    // wants the page to say so.
    //
    const store = useLibraryAssetsStore()
    await store.loadPostAssets('douyin', AWEME)
    mockedPost.mockResolvedValue({ ...available(), storage_state: 'missing', assets: [] })

    await store.refresh()

    expect(mockedPost).toHaveBeenCalledTimes(2)
    expect(store.storageState).toBe('missing')
  })

  it('has nothing to refresh before a resource is chosen', async () => {
    const store = useLibraryAssetsStore()

    await store.refresh()

    expect(mockedPost).not.toHaveBeenCalled()
    expect(mockedRecording).not.toHaveBeenCalled()
  })
})

describe('a slow answer never lands on the wrong resource', () => {
  it('drops a late post result once another post is opened', async () => {
    //
    // Click post A, click post B before A answers. A's files must not be
    // reported as B's - the panel would name B and list somebody else's media.
    //
    const slow = deferred<ResourceAssetResult>()
    mockedPost.mockReturnValueOnce(slow.promise)
    const store = useLibraryAssetsStore()

    const first = store.loadPostAssets('douyin', 'AAA')
    mockedPost.mockResolvedValue(available('b.mp4'))
    await store.loadPostAssets('douyin', 'BBB')

    slow.settle({ ...available('a.mp4'), storage_state: 'empty', assets: [] })
    await first

    expect(store.storageState).toBe('available')
    expect(store.assets[0].name).toBe('b.mp4')
  })

  it('drops a late post result once a recording is opened', async () => {
    const slow = deferred<ResourceAssetResult>()
    mockedPost.mockReturnValueOnce(slow.promise)
    const store = useLibraryAssetsStore()

    const first = store.loadPostAssets('douyin', AWEME)
    await store.loadRecordingAssets('7')

    slow.settle(available())
    await first

    expect(store.assets).toEqual([])
    expect(store.storageState).toBe('available')
  })

  it('drops a late failure too', async () => {
    //
    // An error from an abandoned request would otherwise put a red banner over
    // a resource that loaded perfectly well.
    //
    let reject: (reason: unknown) => void = () => {}
    mockedPost.mockReturnValueOnce(
      new Promise((_resolve, rejectFn) => {
        reject = rejectFn
      }),
    )
    const store = useLibraryAssetsStore()

    const first = store.loadPostAssets('douyin', 'AAA')
    mockedPost.mockResolvedValue(available())
    await store.loadPostAssets('douyin', 'BBB')

    reject(new ApiError({ kind: 'network', status: null, code: null, message: 'gone' }))
    await first

    expect(store.error).toBeNull()
    expect(store.storageState).toBe('available')
  })
})

describe('when the server will not answer', () => {
  it('reports a refusal without repeating the server wording', async () => {
    mockedPost.mockRejectedValue(
      new ApiError({ kind: 'backend', status: 500, code: 500, message: 'PermissionError /app/downloads' }),
    )
    const store = useLibraryAssetsStore()

    await store.loadPostAssets('douyin', AWEME)

    expect(store.error).toBeTruthy()
    expect(store.error).not.toContain('/app/downloads')
    expect(store.error).not.toContain('PermissionError')
    expect(store.assets).toEqual([])
  })

  it('treats a resource that is not there as an empty result rather than a crash', async () => {
    mockedPost.mockRejectedValue(
      new ApiError({ kind: 'backend', status: 404, code: 404, message: '资源不存在' }),
    )
    const store = useLibraryAssetsStore()

    await store.loadPostAssets('douyin', AWEME)

    expect(store.assets).toEqual([])
    expect(store.error).toBeTruthy()
  })

  it('stops loading whether the read succeeded or failed', async () => {
    mockedPost.mockRejectedValue(
      new ApiError({ kind: 'network', status: null, code: null, message: 'x' }),
    )
    const store = useLibraryAssetsStore()

    await store.loadPostAssets('douyin', AWEME)

    expect(store.loading).toBe(false)
  })
})

describe('the store never holds a location', () => {
  it('keeps no path for any resource it has read', async () => {
    const store = useLibraryAssetsStore()
    await store.loadPostAssets('douyin', AWEME)

    const serialized = JSON.stringify(store.$state).toLowerCase()

    for (const forbidden of ['save_dir', 'output_path', '/downloads', 'absolute_path']) {
      expect(serialized).not.toContain(forbidden)
    }
  })
})
