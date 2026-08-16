import { request } from './client'
import type {
  HistoryFilters,
  HistoryOwnerPage,
  LiveProbeBatch,
  LiveSession,
  OwnerPreferenceResult,
  OwnerPreferenceUpdate,
} from '@/types/history'

/**
 * The accounts this server has seen before, filtered and paged by the server.
 *
 * Every filter is applied where the data is; the total that comes back counts
 * everything matching, not everything returned, and the two would drift apart
 * the moment the browser started filtering as well.
 */
export function listHistoryOwners(
  filters: HistoryFilters = {},
  signal?: AbortSignal,
): Promise<HistoryOwnerPage> {
  return request<HistoryOwnerPage>('/history/owners', {
    query: {
      q: filters.q,
      //
      // Sent even when false: "not favourited" is a choice, and the query
      // builder drops undefined rather than falsy.
      //
      favorite: filters.favorite,
      score_min: filters.score_min,
      score_max: filters.score_max,
      last_live_within: filters.last_live_within,
      user_status: filters.user_status,
      sort: filters.sort,
      order: filters.order,
      page: filters.page,
      page_size: filters.page_size,
    },
    ...(signal ? { signal } : {}),
  })
}

/** The recorded broadcasts of one account, newest first. */
export function listOwnerSessions(
  ownerUserId: string,
  options: { limit?: number } = {},
  signal?: AbortSignal,
): Promise<{ items: LiveSession[] }> {
  return request<{ items: LiveSession[] }>(
    `/history/owners/${encodeURIComponent(ownerUserId)}/sessions`,
    {
      query: { limit: options.limit },
      ...(signal ? { signal } : {}),
    },
  )
}

export function updateOwnerPreference(
  ownerUserId: string,
  payload: OwnerPreferenceUpdate,
): Promise<OwnerPreferenceResult> {
  return request<OwnerPreferenceResult>(
    `/history/owners/${encodeURIComponent(ownerUserId)}/preference`,
    { method: 'PATCH', body: payload },
  )
}

/**
 * Ask whether these accounts are broadcasting right now.
 *
 * Answers 202 with whatever is already known - a batch answered entirely from
 * the recent-status cache comes back `done` immediately - and the rest arrives
 * by reading the batch again.
 */
export function submitLiveProbe(ownerUserIds: string[]): Promise<LiveProbeBatch> {
  return request<LiveProbeBatch>('/live/probe', {
    method: 'POST',
    body: { owner_user_ids: ownerUserIds },
  })
}

export function getLiveProbe(
  batchId: string,
  signal?: AbortSignal,
): Promise<LiveProbeBatch> {
  return request<LiveProbeBatch>(`/live/probe/${encodeURIComponent(batchId)}`, {
    ...(signal ? { signal } : {}),
  })
}
