//
// The manual identity layer: which platform accounts belong to the same real
// person, and who filmed whom.
//
// Nothing here is derived. A nickname is not evidence - the same name appears on
// unrelated accounts and one person renames themselves freely - so every
// attachment in this file exists because somebody said so.
//

/**
 * What one account is to the person who owns it.
 *
 * `main` also decides the folder downloads are filed under, which is why a
 * person has no directory of its own until an account is marked main.
 */
export const PERSON_ROLES = ['main', 'alt', 'matrix'] as const
export type PersonRole = (typeof PERSON_ROLES)[number]

export interface PersonSummaryItem {
  person_id: number
  display_name: string
  directory_name: string | null
  note: string | null
  account_count: number
}

export interface PersonAccount {
  owner_user_id: string
  nickname: string | null
  role: PersonRole
}

export interface PersonAggregateSummary {
  aweme_count: number
  live_count: number
}

/** The other end of a collaboration, in whichever direction it was recorded. */
export interface PersonRelation {
  person_id: number
  display_name: string
  note: string | null
}

export interface PersonDetail {
  accounts: PersonAccount[]
  summary: PersonAggregateSummary
  //
  // Directed, and both directions are kept apart on purpose: "filmed" and "was
  // filmed by" are different facts, and somebody who does both would otherwise
  // collapse into one undifferentiated list of people they have worked with.
  //
  subjects: PersonRelation[]
  photographers: PersonRelation[]
}

export interface AccountSearchResult {
  owner_user_id: string
  nickname: string | null
  directory_name: string | null
  //
  // Null when the account belongs to nobody yet. When it is set, attaching the
  // account elsewhere *moves* it - the backend upserts - which is why the
  // interface has to say so before doing it.
  //
  person_id: number | null
  role: PersonRole | null
}

export interface CreatePersonPayload {
  display_name: string
  note?: string
}

export interface UpdatePersonFields {
  display_name?: string
  note?: string
}

export interface AttachAccountPayload {
  owner_user_id: string
  person_id: number
  role: PersonRole
}

export interface AttachAccountByLinkPayload {
  //
  // Always a url the resolver has already validated, never a user's raw paste.
  // The short-link following and host checks belong to /api/resolve.
  //
  url: string
  person_id: number
  role: PersonRole
}

export interface CollaborationPayload {
  photographer_id: number
  subject_id: number
  note?: string
}

/**
 * One downloaded post associated with a photographer through a collaboration.
 *
 * Association, not attribution. The backend records collaboration between
 * *people*, so this returns the whole output of every account belonging to
 * somebody the photographer has worked with - it is not evidence that any
 * particular post here was shot by them. The interface has to say so.
 */
export interface PersonWork {
  aweme_id: string | null
  desc: string | null
  //
  // Text only, like every other recorded path in this application.
  //
  save_dir: string | null
  downloaded_at: string | null
  /** The subject this post's account belongs to. */
  owner_display_name: string | null
}
