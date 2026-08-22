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

//
// >>============================= link-first assignment =============================>>
//
//
// One request that resolves to a person holding one more account: create the
// person or merge into an existing one, record who the account is, attach it in
// the role that was chosen - all in one backend transaction.
//
// The account is named by `resolve_id` and by nothing else.  There is
// deliberately no field here for an owner id, a nickname, a sec id or a url:
// the server reads the resource back from its own resolve store, and a request
// that could describe it would let this browser attach an owner the server
// never resolved.
//

/** A person who does not exist yet. */
export interface NewPersonAssignmentTarget {
  kind: 'new'
  //
  // Optional, and omitted rather than sent blank when the user left it empty.
  // The server picks the fallback - the account's recorded folder, then its
  // nickname, then its id - because it is the only side that can see any of
  // them.  A name invented here would be a guess presented as a decision.
  //
  display_name?: string
  note?: string
}

/** A person who already exists.  Renaming is `PATCH /person/<id>`, not this. */
export interface ExistingPersonAssignmentTarget {
  kind: 'existing'
  person_id: number
}

export type PersonAssignmentTarget =
  | NewPersonAssignmentTarget
  | ExistingPersonAssignmentTarget

/** Where the old main goes when it is being replaced.  Never `main`. */
export type DemotedRole = Exclude<PersonRole, 'main'>

export interface PersonAssignmentRequest {
  resolve_id: string
  target: PersonAssignmentTarget
  role: PersonRole
  //
  // Only ever `true`, and only after the user has confirmed it.  Typed as the
  // literal rather than `boolean` so "false" cannot be sent as a way of saying
  // nothing: absent is how this asks for the default, and the backend refuses a
  // move unless the field is present and true.
  //
  allow_move?: true
  //
  // Likewise only sent after an explicit confirmation, and it must say where
  // the outgoing main goes - there is no default, because demoting somebody's
  // main to a role they did not pick is not a detail.
  //
  replace_main?: { demote_to: DemotedRole }
}

export interface PersonAssignmentResult {
  person_id: number
  owner_user_id: string
  role: PersonRole
  /** Whether this request created the person, as opposed to merging into one. */
  created_person: boolean
  //
  // The name the person actually ended up with, which for a new person may be
  // the fallback the server chose rather than anything typed here.
  //
  display_name: string
}

//
// The refusals this endpoint can answer with, as the backend names them.
//
// Two of them are 409 and their remedies are opposite - one needs `allow_move`,
// the other needs `replace_main` - so the page has to be able to tell them
// apart without reading the Chinese message.
//
export const ASSIGNMENT_CONFLICT_KINDS = [
  'account_already_attached',
  'main_account_conflict',
  'last_main_removal_conflict',
  'assignment_raced',
] as const
export type AssignmentConflictKind = (typeof ASSIGNMENT_CONFLICT_KINDS)[number]

/** Who currently holds the account this request tried to attach. */
export interface AccountAlreadyAttachedConflict {
  kind: 'account_already_attached'
  current_person: { person_id: number; display_name: string | null }
}

/** The main this person already has, which a new one would have to replace. */
export interface MainAccountConflict {
  kind: 'main_account_conflict'
  current_main: { owner_user_id: string; nickname: string | null }
}

/**
 * Moving this account would leave its current person without the main their
 * other accounts were filed under.  There is no confirmation for this one: the
 * folders are not recoverable, so the answer is to give that person a new main
 * first.
 */
export interface LastMainRemovalConflict {
  kind: 'last_main_removal_conflict'
  source_person: { person_id: number; display_name: string | null }
  current_main: { owner_user_id: string; nickname: string | null }
}

/** The account changed hands mid-request.  Nothing to confirm; try again. */
export interface AssignmentRacedConflict {
  kind: 'assignment_raced'
}

export type PersonAssignmentConflict =
  | AccountAlreadyAttachedConflict
  | MainAccountConflict
  | LastMainRemovalConflict
  | AssignmentRacedConflict

//
// >>============================= existing identity =============================>>
//
//
// What `POST /api/person/inspect` answers: who a resolved link turns out to
// be, and whether this server already holds them.
//
// Asked between resolving a link and offering a form. Without it the only thing
// that ever noticed a duplicate was the assignment itself, so pasting an
// account added last month meant filling in a form and naming a person before
// being told it had been there all along - and the obvious reading of that
// screen was "I must create this person again".
//
// Named by the receipt alone, like the assignment. There is deliberately no
// field here for an owner id: this answer decides whether a "create a new
// person" button appears, so a request able to name the account would let the
// browser choose which account gets checked.
//

/** The account as the platform describes it right now. */
export interface PersonIdentityOwner {
  //
  // The account's identity, and the only key anything here is matched on. A
  // nickname changes and repeats; a share link differs for the same resource.
  //
  owner_user_id: string
  sec_user_id: string | null
  //
  // Null for an account nobody has downloaded and whose profile said nothing.
  // The id is shown instead.
  //
  nickname: string | null
}

/** Which person holds this account, and as what. */
export interface PersonIdentityAssignment {
  person_id: number
  //
  // The *person's* name, which somebody typed. It is not updated to follow a
  // nickname, so a renamed account legitimately reads "账号：程小程 /
  // 人物：程儿" - and the page shows both rather than reconciling them.
  //
  display_name: string
  role: PersonRole
}

export interface PersonIdentityInspection {
  owner: PersonIdentityOwner
  //
  // Whether this server has ever heard of the account - a `share_url` row,
  // which a download, a live probe or an earlier marking creates.
  //
  // Kept apart from `assignment` because they are different facts and the page
  // shows different things for them. An account downloaded months ago that
  // nobody filed is `known_account: true, assignment: null`: not a duplicate,
  // just an account waiting to be put under somebody. Collapsing the two would
  // lose the commonest case there is.
  //
  known_account: boolean
  //
  // Null when nobody holds the account. Never inferred from a matching
  // display name: two different people may legitimately share one.
  //
  assignment: PersonIdentityAssignment | null
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
