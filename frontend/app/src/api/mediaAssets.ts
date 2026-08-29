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

//
// >>------------------------- download addresses -------------------------<<
//
// Addresses only. Nothing here fetches: a download is handed to the browser as
// a same-origin link, so that a recording of any size streams to disk without
// passing through this tab's memory, and so that the browser's own download UI
// does the reporting.
//
// The parent resource is always named in the path. An asset id is a stable name
// for a file, never a capability to read one - the server matches it against a
// fresh discovery of the resource named here, so an id means nothing anywhere
// but where it was issued.
//
// No credential is added. The session cookie already authenticates this request
// like every other; a token placed in a url would survive in browser history,
// in referrer headers, and in any proxy log along the way.
//

/** Where to download one of a post's files. */
export function postAssetDownloadUrl(
  platform: string,
  awemeId: string,
  assetId: string,
): string {
  return (
    `/api/library/posts/${encodeURIComponent(platform)}` +
    `/${encodeURIComponent(awemeId)}` +
    `/assets/${encodeURIComponent(assetId)}/download`
  )
}

/**
 * Where to download the file one recording wrote.
 *
 * The identity is interpolated as the text it already is. It is a BIGINT
 * UNSIGNED whose domain a JavaScript number cannot hold, so converting it -
 * even incidentally, through arithmetic or a parse - would change which
 * recording this url addresses.
 */
export function recordingAssetDownloadUrl(
  recordingId: RecordingId,
  assetId: string,
): string {
  return (
    `/api/library/recordings/${encodeURIComponent(recordingId)}` +
    `/assets/${encodeURIComponent(assetId)}/download`
  )
}

//
// >>------------------------- preview addresses -------------------------<<
//
// The same shape as the download addresses above, and for the same reasons: the
// parent resource is named in the path, nothing carries a credential, and
// nothing here fetches. The browser requests these directly from an `<img>`,
// `<video>` or `<audio>` element, which is what lets a large video stream and
// seek without passing through this tab's memory.
//
// A separate endpoint rather than a flag on the download one. Whether a
// response is rendered or saved is the server's decision, and a query parameter
// would hand that decision to whoever writes the url.
//

/** Where to render one of a post's files in place. */
export function postAssetPreviewUrl(
  platform: string,
  awemeId: string,
  assetId: string,
): string {
  return (
    `/api/library/posts/${encodeURIComponent(platform)}` +
    `/${encodeURIComponent(awemeId)}` +
    `/assets/${encodeURIComponent(assetId)}/preview`
  )
}

/**
 * Where to render the file one recording wrote.
 *
 * The identity is interpolated as the text it already is - see
 * `recordingAssetDownloadUrl` for why converting it would address a different
 * recording.
 */
export function recordingAssetPreviewUrl(
  recordingId: RecordingId,
  assetId: string,
): string {
  return (
    `/api/library/recordings/${encodeURIComponent(recordingId)}` +
    `/assets/${encodeURIComponent(assetId)}/preview`
  )
}
