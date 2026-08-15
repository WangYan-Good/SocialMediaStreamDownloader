import { request } from './client'
import type {
  AccountSearchResult,
  AttachAccountByLinkPayload,
  AttachAccountPayload,
  CollaborationPayload,
  CreatePersonPayload,
  PersonDetail,
  PersonSummaryItem,
  UpdatePersonFields,
} from '@/types/person'

export function listPeople(signal?: AbortSignal): Promise<PersonSummaryItem[]> {
  return request<PersonSummaryItem[]>('/person', {
    ...(signal ? { signal } : {}),
  })
}

export function createPerson(payload: CreatePersonPayload): Promise<{ person_id: number }> {
  return request<{ person_id: number }>('/person', {
    method: 'POST',
    body: payload,
  })
}

/** Change only the fields that were actually edited. */
export function updatePerson(
  personId: number,
  fields: UpdatePersonFields,
): Promise<{ person_id: number }> {
  return request<{ person_id: number }>(`/person/${personId}`, {
    method: 'PATCH',
    body: fields,
  })
}

export function deletePerson(personId: number): Promise<{ person_id: number }> {
  return request<{ person_id: number }>(`/person/${personId}`, {
    method: 'DELETE',
  })
}

/** Accounts, counts, and both directions of the collaboration relation. */
export function getPersonDetail(
  personId: number,
  signal?: AbortSignal,
): Promise<PersonDetail> {
  return request<PersonDetail>(`/person/${personId}/detail`, {
    ...(signal ? { signal } : {}),
  })
}

export function searchAccounts(
  keyword: string,
  signal?: AbortSignal,
): Promise<AccountSearchResult[]> {
  return request<AccountSearchResult[]>('/person/accounts', {
    query: { keyword },
    ...(signal ? { signal } : {}),
  })
}

/**
 * Put one account under one person.
 *
 * An upsert on the backend, which means attaching an account that already
 * belongs to somebody else *moves* it. The interface has to say so before
 * calling this; the api itself will not ask.
 */
export function attachAccount(
  payload: AttachAccountPayload,
): Promise<{ owner_user_id: string; person_id: number }> {
  return request<{ owner_user_id: string; person_id: number }>('/person/account', {
    method: 'POST',
    body: payload,
  })
}

/**
 * Attach whichever account a link belongs to.
 *
 * The url must already be resolved - see `/api/resolve`. The endpoint works
 * from a profile, a post or a live room, so no particular resource type is
 * required here; what is required is that the following and host checks have
 * already happened.
 */
export function attachAccountByLink(
  payload: AttachAccountByLinkPayload,
): Promise<{ owner_user_id: string; person_id: number }> {
  return request<{ owner_user_id: string; person_id: number }>(
    '/person/account/by-link',
    { method: 'POST', body: payload },
  )
}

export function detachAccount(ownerUserId: string): Promise<{ owner_user_id: string }> {
  return request<{ owner_user_id: string }>('/person/account', {
    method: 'DELETE',
    query: { owner_user_id: ownerUserId },
  })
}

export function addCollaboration(
  payload: CollaborationPayload,
): Promise<{ photographer_id: number; subject_id: number }> {
  return request<{ photographer_id: number; subject_id: number }>(
    '/person/collaboration',
    { method: 'POST', body: payload },
  )
}

/**
 * Remove one directed relation.
 *
 * Both ids are required and their order is the relation: swapping them removes
 * a different fact, or nothing at all.
 */
export function removeCollaboration(
  photographerId: number,
  subjectId: number,
): Promise<{ photographer_id: number; subject_id: number }> {
  return request<{ photographer_id: number; subject_id: number }>(
    '/person/collaboration',
    {
      method: 'DELETE',
      query: { photographer_id: photographerId, subject_id: subjectId },
    },
  )
}
