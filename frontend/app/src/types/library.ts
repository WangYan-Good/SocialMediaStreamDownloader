//
// The library is an index of what this server already downloaded.
//
// Everything here comes from the project's own database rows, never from a
// platform and never from the filesystem. That shapes the types more than it
// might look: there is no cover url because `aweme_record` does not keep one,
// and there is no output path for a live record because `live_record` has no
// such column. Adding either as an optional field would invite the interface to
// fill it in with a guess.
//

/** Which of the two record kinds a row is. */
export type LibraryKind = 'post' | 'live' | 'recording'

/** What the downloader writes into `aweme_record.aweme_type`. */
export type LibraryAwemeType = 'video' | 'image'

/** Which route answered when the post was fetched. */
export type LibrarySource = 'api' | 'html'

/**
 * Whether the recorded run saved everything it set out to.
 *
 * A statement about the download record and nothing else. Nothing in this
 * phase checks whether those files are still on disk, so "complete" means the
 * record is complete - not that the media exists.
 */
export type LibraryCompletion = 'complete' | 'partial'

export interface LibraryPost {
  platform: string
  aweme_id: string
  // Management-only filing fields are absent from USER responses.
  owner_user_id?: string | null
  sec_user_id?: string | null
  nickname: string | null
  directory_name?: string | null
  //
  // Null for the majority of rows: most downloaded accounts have never been
  // attached to a person, and they belong in the library all the same.
  //
  person_id?: number | null
  person_display_name?: string | null
  aweme_type: LibraryAwemeType | null
  desc: string | null
  create_time: string | null
  downloaded_at: string | null
  media_count: number | null
  saved_count: number | null
  //
  // The directory the downloader recorded at the time, as text. Never a link,
  // never an image source: this application does not serve files, and a path
  // the browser could act on would be exactly that.
  //
  save_dir?: string | null
  source?: LibrarySource | null
}

export interface LibraryPostPage {
  total: number
  page: number
  page_size: number
  items: LibraryPost[]
}

export interface LibraryPostFilters {
  q?: string
  owner_user_id?: string
  person_id?: number
  aweme_type?: LibraryAwemeType
  completion?: LibraryCompletion
  source?: LibrarySource
  sort?: 'downloaded_at' | 'create_time' | 'nickname' | 'aweme_id'
  order?: 'asc' | 'desc'
  page?: number
  page_size?: number
}

export interface LibraryLive {
  observed_at: string | null
  platform: string
  room_id: string | null
  owner_user_id: string | null
  nickname: string | null
  directory_name: string | null
  person_id: number | null
  person_display_name: string | null
  title: string | null
  //
  // The status recorded at the moment of observation - 2 was broadcasting, 4
  // had finished. Historical either way: whether the room is live *now* is only
  // answerable by a probe, which belongs to the creators workspace.
  //
  room_status: number | null
  start_time: string | null
  finish_time: string | null
  status_code: number | null
}

export interface LibraryLivePage {
  total: number
  page: number
  page_size: number
  items: LibraryLive[]
}

export interface LibraryLiveFilters {
  q?: string
  owner_user_id?: string
  person_id?: number
  sort?: 'observed_at' | 'start_time' | 'finish_time' | 'nickname'
  order?: 'asc' | 'desc'
  page?: number
  page_size?: number
}

/** One completed or persisted recording resource owned by an app user. */
export interface LibraryRecording {
  recording_id: string
  platform: string
  room_id: string
  title: string | null
  nickname: string | null
  started_at: string | null
  finished_at: string | null
  created_at: string
}

export interface LibraryRecordingPage {
  total: number
  page: number
  page_size: number
  items: LibraryRecording[]
}

export interface LibraryRecordingFilters {
  q?: string
  owner_user_id?: string
  protocol?: 'flv' | 'hls'
  sort?: 'finished_at' | 'started_at' | 'created_at' | 'title' | 'nickname'
  order?: 'asc' | 'desc'
  page?: number
  page_size?: number
}
