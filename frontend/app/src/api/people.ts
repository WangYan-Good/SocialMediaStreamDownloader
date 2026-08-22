import { request } from './client'
import type {
  AccountSearchResult,
  AttachAccountByLinkPayload,
  AttachAccountPayload,
  CollaborationPayload,
  CreatePersonPayload,
  PersonAssignmentRequest,
  PersonAssignmentResult,
  PersonDetail,
  PersonIdentityInspection,
  PersonSummaryItem,
  PersonWork,
  UpdatePersonFields,
} from '@/types/person'

//
// The wire shapes of the person endpoints that answer with a named collection.
//
// `request` unwraps the envelope's `data` and stops there; whatever is inside
// it is each adapter's own business. Naming these makes the two layers of
// unwrapping visible - typing the call as `PersonSummaryItem[]` would compile,
// and would hand every caller an object wearing an array's type.
//
interface PersonListData {
  persons: PersonSummaryItem[]
}

interface AccountSearchData {
  accounts: AccountSearchResult[]
}

export async function listPeople(signal?: AbortSignal): Promise<PersonSummaryItem[]> {
  const data = await request<PersonListData>('/person', {
    ...(signal ? { signal } : {}),
  })
  return data.persons
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

export async function searchAccounts(
  keyword: string,
  signal?: AbortSignal,
): Promise<AccountSearchResult[]> {
  const data = await request<AccountSearchData>('/person/accounts', {
    query: { keyword },
    ...(signal ? { signal } : {}),
  })
  return data.accounts
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

/**
 * Create or find a person and attach one resolved account to them, in one call.
 *
 * The link-first way in, and the only one that can create a person and attach
 * an account together - which is what makes "create an empty person first" stop
 * being a step. The account is named by the receipt alone; see
 * `PersonAssignmentRequest` for why nothing here describes it.
 */
export function assignPersonAccount(
  payload: PersonAssignmentRequest,
): Promise<PersonAssignmentResult> {
  return request<PersonAssignmentResult>('/person/assignment', {
    method: 'POST',
    body: payload,
  })
}

/**
 * Ask who a resolved link turns out to be, and whether this server has them.
 *
 * Runs straight after `/api/resolve` and before any form is offered, which is
 * the whole point: the only thing that used to notice a duplicate was the
 * assignment itself, so a user pasting an account they added last month named a
 * person and pressed confirm before being told it was already there.
 *
 * Read-only, and not authority. What it reports is a hint for the interface -
 * the assignment discovers ownership again inside its own transaction and
 * refuses on what it finds there, however long the user spent reading the
 * screen in between.
 *
 * The receipt is the only thing sent, and it survives being read: the resolve
 * store is a TTL store rather than a consume-once one, so the same `resolveId`
 * still assigns afterwards.
 */
export function inspectPersonAssignment(
  resolveId: string,
): Promise<PersonIdentityInspection> {
  return request<PersonIdentityInspection>('/person/inspect', {
    method: 'POST',
    //
    // By receipt alone. This answer decides whether a "create a new person"
    // button appears, so a body able to name the account would let this browser
    // choose which account gets checked - and the backend refuses any such
    // field rather than ignoring it.
    //
    body: { resolve_id: resolveId },
  })
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

/**
 * The posts associated with a photographer through their collaborations.
 *
 * Deliberately absent through the creators phase: it returns content, and
 * content is this phase's business rather than the identity screen's. The
 * endpoint itself is unchanged - it has answered this way since the legacy
 * page, including the part where it returns whole accounts rather than
 * individually attributed shoots.
 *
 * There is no paging to pass: the endpoint takes none and answers with one
 * bounded list.
 */
export async function getPersonWorks(
  personId: number,
  signal?: AbortSignal,
): Promise<PersonWork[]> {
  const data = await request<{ works: PersonWork[] }>(`/person/${personId}/works`, {
    ...(signal ? { signal } : {}),
  })
  return data.works
}
