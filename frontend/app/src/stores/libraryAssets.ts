import { defineStore } from 'pinia'
import { ref } from 'vue'

import { ApiError } from '@/api/client'
import { listPostAssets, listRecordingAssets } from '@/api/mediaAssets'
import type { RecordingId } from '@/types/library'
import type { MediaAsset, MediaAssetStorageState } from '@/types/mediaAsset'

/**
 * What is on disk for the one resource currently open.
 *
 * A store of its own rather than more state inside `useLibraryStore`. That one
 * holds paging, filters, three kinds of row and a person picker, all of which
 * live for as long as the screen does. This is the opposite: a single selected
 * resource, discarded the moment the panel closes.
 *
 * Nothing here is loaded on arrival, and nothing polls. Reading it means the
 * server touches its filesystem, so it happens exactly when somebody opens one
 * resource and asks.
 */
export const useLibraryAssetsStore = defineStore('libraryAssets', () => {
  const assets = ref<MediaAsset[]>([])
  const storageState = ref<MediaAssetStorageState | null>(null)
  const loading = ref(false)
  const error = ref<string | null>(null)

  //
  // Which resource the state below describes, so a refresh knows what to ask
  // for again.
  //
  const currentResourceKey = ref<string | null>(null)
  let currentRequest: (() => Promise<void>) | null = null

  //
  // Which question is being waited on.
  //
  // Bumped by every load. An answer whose generation is stale is dropped:
  // opening post A and then post B before A replies would otherwise list A's
  // files under B's name, which is the same class of mistake as a stale
  // resolution in New Download.
  //
  let generation = 0
  let inFlight: AbortController | null = null

  //
  // The server's own message is not shown. A failure here can carry a
  // filesystem path or a driver string, and neither belongs on a page.
  //
  const READ_FAILED = '暂时无法读取文件状态，请重试。'

  function reset(): void {
    assets.value = []
    storageState.value = null
    error.value = null
  }

  async function run(
    key: string,
    read: (signal: AbortSignal) => Promise<{
      storage_state: MediaAssetStorageState
      assets: MediaAsset[]
    }>,
  ): Promise<void> {
    const mine = ++generation
    inFlight?.abort()
    const controller = new AbortController()
    inFlight = controller

    currentResourceKey.value = key
    loading.value = true
    reset()

    try {
      const answer = await read(controller.signal)
      if (mine !== generation) return
      storageState.value = answer.storage_state
      assets.value = answer.assets ?? []
    } catch (caught) {
      if (mine !== generation) return
      //
      // Including a 404. The resource is gone or was never this user's, and
      // either way there is nothing to list - said in the interface's own
      // words rather than the server's.
      //
      error.value = caught instanceof ApiError ? READ_FAILED : READ_FAILED
    } finally {
      if (mine === generation) {
        loading.value = false
        inFlight = null
      }
    }
  }

  return {
    assets,
    storageState,
    loading,
    error,
    currentResourceKey,

    async loadPostAssets(platform: string, awemeId: string): Promise<void> {
      currentRequest = () => this.loadPostAssets(platform, awemeId)
      await run(`post:${platform}:${awemeId}`, (signal) =>
        listPostAssets(platform, awemeId, signal),
      )
    },

    async loadRecordingAssets(recordingId: RecordingId): Promise<void> {
      currentRequest = () => this.loadRecordingAssets(recordingId)
      //
      // Interpolated as it arrived. The key exists to tell one open resource
      // from another, so an identity narrowed on its way into it would make two
      // different recordings share a key.
      //
      await run(`recording:${recordingId}`, (signal) =>
        listRecordingAssets(recordingId, signal),
      )
    },

    /** Ask again about the resource already open. A read, nothing more. */
    async refresh(): Promise<void> {
      if (currentRequest === null) return
      await currentRequest()
    },

    /** Forget the open resource - the panel closed, or another row was picked. */
    clear(): void {
      generation += 1
      inFlight?.abort()
      inFlight = null
      currentRequest = null
      currentResourceKey.value = null
      loading.value = false
      reset()
    },
  }
})
