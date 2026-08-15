//
// What `POST /api/resolve` answers: which resource a pasted link names.
//
// Identity-level only.  The backend deliberately does not read a nickname, a
// cover or a live status here - each costs a platform request and two of them
// need a valid cookie - so nothing of that kind appears in these types either.
//

export const RESOURCE_TYPES = ['post', 'owner', 'live'] as const

export type ResourceType = (typeof RESOURCE_TYPES)[number]

export interface ResolvedResourceBase {
  //
  // The opaque receipt.  It is the only thing a later task-creation request may
  // say about the resource: the server reads the rest back from its own store
  // rather than trusting a browser's account of what was resolved.
  //
  resolve_id: string
  platform: string
  //
  // The link lifted out of whatever was pasted.
  //
  source_url: string
  //
  // The link the verdict was actually read from.  Equal to `source_url` unless
  // a short link had to be followed.
  //
  resolved_url: string
  expires_in_seconds: number
}

//
// Discriminated on `resource_type`, so reading `identity.aweme_id` off an owner
// is a compile error rather than `undefined` at runtime.
//
export type ResolvedResource =
  | (ResolvedResourceBase & {
      resource_type: 'post'
      identity: { aweme_id: string }
    })
  | (ResolvedResourceBase & {
      resource_type: 'owner'
      identity: { sec_user_id: string }
    })
  | (ResolvedResourceBase & {
      resource_type: 'live'
      //
      // Deliberately empty.  The number in a live url is a web id, not the room
      // id the platform payload uses, and guessing one would mint an identifier
      // that looks server-verified and is not.
      //
      identity: Record<string, never>
    })

export interface ResolveRequest {
  //
  // Whatever the user pasted: a bare link, or the whole share sentence the app
  // puts on the clipboard.  Extracting the link is the server's job.
  //
  input: string
}
