import { request } from './client'
import type { OwnerDownloadStarted, OwnerPostPage, OwnerRead } from '@/types/owner'

/**
 * Read one account's profile and first page of posts from the platform.
 *
 * The url handed over must already have been through `/api/resolve`: that is
 * where a short link is followed under host checks and a hop limit. Passing a
 * user's raw paste here would ask this endpoint to do that following itself,
 * outside those checks.
 */
export function readOwner(resolvedUrl: string, signal?: AbortSignal): Promise<OwnerRead> {
  return request<OwnerRead>('/owner', {
    query: { url: resolvedUrl },
    ...(signal ? { signal } : {}),
  })
}

/** One more page of posts, by the cursor the previous page answered with. */
export function readOwnerPosts(
  secUserId: string,
  cursor: number,
  signal?: AbortSignal,
): Promise<OwnerPostPage> {
  return request<OwnerPostPage>('/owner/posts', {
    query: { sec_user_id: secUserId, cursor },
    ...(signal ? { signal } : {}),
  })
}

/**
 * Download the posts the user ticked.
 *
 * Only ids travel. The post payloads live in the server's own cache, which is
 * what makes this safe: the browser says *which* posts, and never what they
 * are.
 */
export function startOwnerSelectedDownload(
  awemeIds: string[],
  shareUrl?: string,
): Promise<OwnerDownloadStarted> {
  return request<OwnerDownloadStarted>('/owner/download', {
    method: 'POST',
    body: {
      aweme_ids: awemeIds,
      ...(shareUrl ? { share_url: shareUrl } : {}),
    },
  })
}

/** Download an entire back catalogue, by owner rather than by listing ids. */
export function startOwnerAllDownload(
  secUserId: string,
  shareUrl?: string,
): Promise<OwnerDownloadStarted> {
  return request<OwnerDownloadStarted>('/owner/download', {
    method: 'POST',
    body: {
      all: true,
      sec_user_id: secUserId,
      ...(shareUrl ? { share_url: shareUrl } : {}),
    },
  })
}
