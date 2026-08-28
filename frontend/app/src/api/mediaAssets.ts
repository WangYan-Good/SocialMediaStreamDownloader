import { request } from './client'
import type { RecordingId } from '@/types/library'
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
 * Takes the identity in the one form it has. The server sends `recording_id` as
 * decimal text precisely so that it can be put into a url unchanged; converting
 * it here - to a number, or through one - would undo that at the last step.
 *
 * The url segment is the identity verbatim. `encodeURIComponent` still guards
 * it, because a value that is not a decimal identity must not be able to build
 * a path of its own; the route matches integers only, so one that is not is
 * refused there rather than guessed at here.
 */
export function listRecordingAssets(
  recordingId: RecordingId,
  signal?: AbortSignal,
): Promise<ResourceAssetResult> {
  return request<ResourceAssetResult>(
    `/library/recordings/${encodeURIComponent(recordingId)}/assets`,
    { ...(signal ? { signal } : {}) },
  )
}
