//
// What the platform says about an account right now. Every field here costs a
// request and a valid login to obtain - which is why the history api does not
// carry any of it, and why nothing in this file may be invented from a history
// row.
//

export interface OwnerProfile {
  sec_user_id: string | null
  uid: string | null
  nickname: string | null
  unique_id: string | null
  signature: string | null
  avatar_url: string | null
  follower_count: number | null
  following_count: number | null
  aweme_count: number | null
  total_favorited: number | null
}

export interface OwnerPost {
  aweme_id: string
  desc: string
  create_time: number | null
  cover_url: string
  duration: number | null
  aweme_type: 'video' | 'image'
  digg_count: number | null
  comment_count: number | null
  //
  // Whether this server already has it. `false` means "not downloaded", never
  // "the download failed" - nothing here has been attempted.
  //
  downloaded: boolean
  saved_count: number | null
  media_count: number | null
}

export interface OwnerPostPage {
  posts: OwnerPost[]
  next_cursor: number
  has_more: boolean
}

export interface OwnerCredential {
  //
  // How long the configured login has left. Negative means it has already
  // expired. The cookie itself never leaves the server.
  //
  expires_in_days: number | null
}

export interface OwnerRead extends OwnerPostPage {
  sec_user_id: string
  //
  // Null when the profile could not be read - an expired session, most often -
  // while the post list still arrived. The two requests are independent on the
  // backend on purpose, so one failing must not hide the other.
  //
  owner: OwnerProfile | null
  owner_message: string | null
  credential: OwnerCredential
}

export interface OwnerDownloadStarted {
  //
  // The legacy job record. Kept in the response for the old page; the new
  // interface reads `task_id` and hands the user to the task centre.
  //
  job_id: string
  task_id: string | null
}
