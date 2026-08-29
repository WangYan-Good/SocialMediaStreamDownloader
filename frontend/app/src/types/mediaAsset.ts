//
// What is on disk right now for one library resource.
//
// Deliberately a separate contract from `types/library.ts`. A library row says
// what a downloader once recorded; these types say what survived. The two are
// different facts and are allowed to disagree - a post whose record says
// "3 / 3 saved" can perfectly well have an empty directory today, and both
// statements stay true.
//
// There is no path here, and there must never be one. The server knows where
// these files are; a browser learning it would learn the shape of the host's
// filesystem, and would be one step from asking for a file by location.
//

import type { RecordingId } from './library'

export type MediaAssetKind = 'video' | 'image' | 'music' | 'cover' | 'recording'

/**
 * Which element could render an asset in place, when the server permits it.
 *
 * The server is the authority. It serves inline only for a closed list of media
 * types - anything a browser renders is also something it may interpret - and
 * this is how it says which of them an asset is.
 */
export type MediaPreviewKind = 'image' | 'video' | 'audio'

/**
 * What could be said about a resource's files.
 *
 * `missing` is not an error and not a 404: the resource exists, its files do
 * not. `unavailable` means the server could not safely determine the answer -
 * the reason is a fact about its own filesystem and is deliberately not sent.
 */
export type MediaAssetStorageState = 'available' | 'missing' | 'empty' | 'unavailable'

export interface MediaAsset {
  //
  // Derived from the resource and the file name, never stored. It identifies a
  // file without disclosing where it is - and it is not a capability: a later
  // phase that serves bytes must still authenticate, authorize the parent
  // resource and rediscover its assets before honouring one.
  //
  asset_id: string
  kind: MediaAssetKind
  name: string
  size_bytes: number
  media_type: string
  //
  // The position an image records in its own name, so pictures stay in order.
  // Null for everything that is not one of a numbered set.
  //
  image_index: number | null
  //
  // Which element could render this file in place, or `null` for download-only.
  //
  // The server decides and this field reports it. FLV and TS recordings are the
  // ordinary `null` case: no browser decodes either without a JavaScript
  // demuxer. Recomputing this from the extension here would be a second opinion
  // that can disagree with the one actually gating the bytes.
  //
  preview_kind: MediaPreviewKind | null
}

export interface PostAssetResource {
  kind: 'post'
  platform: string
  aweme_id: string
}

export interface RecordingAssetResource {
  kind: 'recording'
  //
  // The same type the library row carries. These files belong to that
  // recording, so the two must name it identically - a resource the browser
  // could not match back to the row it came from would be no identity at all.
  //
  recording_id: RecordingId
}

export type AssetResource = PostAssetResource | RecordingAssetResource

export interface ResourceAssetResult {
  resource: AssetResource
  storage_state: MediaAssetStorageState
  assets: MediaAsset[]
}
