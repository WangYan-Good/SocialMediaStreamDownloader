import { request } from './client'
import type {
  LibraryLiveFilters,
  LibraryLivePage,
  LibraryPostFilters,
  LibraryPostPage,
  LibraryRecordingFilters,
  LibraryRecordingPage,
} from '@/types/library'

/**
 * One page of downloaded posts, filtered and counted by the server.
 *
 * Every filter is applied where the data is. The total that comes back counts
 * everything matching rather than everything returned, and the two would drift
 * apart the moment the browser started filtering as well - the pager would
 * then be built on one number while the rows came from another.
 */
export function listLibraryPosts(
  filters: LibraryPostFilters = {},
  signal?: AbortSignal,
): Promise<LibraryPostPage> {
  return request<LibraryPostPage>('/library/posts', {
    query: {
      q: filters.q,
      owner_user_id: filters.owner_user_id,
      person_id: filters.person_id,
      aweme_type: filters.aweme_type,
      completion: filters.completion,
      source: filters.source,
      sort: filters.sort,
      order: filters.order,
      page: filters.page,
      page_size: filters.page_size,
    },
    ...(signal ? { signal } : {}),
  })
}

/**
 * One page of recorded live observations.
 *
 * There is deliberately no "live now" filter to pass: every row is something
 * observed in the past, and the present tense belongs to the probe.
 */
export function listLibraryLives(
  filters: LibraryLiveFilters = {},
  signal?: AbortSignal,
): Promise<LibraryLivePage> {
  return request<LibraryLivePage>('/library/lives', {
    query: {
      q: filters.q,
      owner_user_id: filters.owner_user_id,
      person_id: filters.person_id,
      sort: filters.sort,
      order: filters.order,
      page: filters.page,
      page_size: filters.page_size,
    },
    ...(signal ? { signal } : {}),
  })
}

/** One page of persistent recording resources, scoped by the server role. */
export function listLibraryRecordings(
  filters: LibraryRecordingFilters = {},
  signal?: AbortSignal,
): Promise<LibraryRecordingPage> {
  return request<LibraryRecordingPage>('/library/recordings', {
    query: {
      q: filters.q,
      owner_user_id: filters.owner_user_id,
      protocol: filters.protocol,
      sort: filters.sort,
      order: filters.order,
      page: filters.page,
      page_size: filters.page_size,
    },
    ...(signal ? { signal } : {}),
  })
}
