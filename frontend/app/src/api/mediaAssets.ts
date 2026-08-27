import { request } from './client'
import type { ResourceAssetResult } from '@/types/mediaAsset'

//
// Which files are on disk for one resource.
//
// The resource is named by its database identity - never by a path. There is no
// endpoint here that takes a directory, and deliberately so: a browser that
// could name a location would be a browser that could ask for any location.
//
// Read-only metadata. Nothing here transfers a file.
//

/** What is currently on disk for one downloaded post. */
export function listPostAssets(
  platform: string,
  awemeId: string,
  signal?: AbortSignal,
): Promise<ResourceAssetResult> {
  return request<ResourceAssetResult>(
    `/library/posts/${encodeURIComponent(platform)}/${encodeURIComponent(awemeId)}/assets`,
    { ...(signal ? { signal } : {}) },
  )
}

/**
 * What is currently on disk for one recording.
 *
 * Accepts either form the identifier arrives in. `recording_record.recording_id`
 * is a BIGINT, while `LibraryRecording` declares it as a string - a mismatch
 * that predates this endpoint. Both stringify to the same url segment, and the
 * route matches integers only, so a value that is not one is refused there
 * rather than being guessed at here.
 */
export function listRecordingAssets(
  recordingId: number | string,
  signal?: AbortSignal,
): Promise<ResourceAssetResult> {
  return request<ResourceAssetResult>(
    `/library/recordings/${encodeURIComponent(String(recordingId))}/assets`,
    { ...(signal ? { signal } : {}) },
  )
}
