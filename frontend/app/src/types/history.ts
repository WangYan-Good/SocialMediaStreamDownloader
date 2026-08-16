//
// What the history api knows: local facts about accounts this server has seen
// before. Distinct from the owner api, which asks the platform what is true
// right now - see types/owner.ts.
//

/** One account as the local database remembers it. */
export interface HistoryOwner {
  owner_user_id: string
  sec_user_id: string | null
  nickname: string | null
  live_share_url: string | null
  directory_name: string | null
  user_status: string | null
  actived_count: number | null
  score: number | null
  favorite: boolean
  //
  // The *last known* room status, cached in the database. Not evidence about
  // now: an account last seen broadcasting an hour ago is not broadcasting
  // because of that. Only a live probe answers the present tense.
  //
  last_live_status: number | null
  last_checked_at: string | null
  last_room_id: string | null
}

export interface HistoryOwnerPage {
  total: number
  page: number
  page_size: number
  items: HistoryOwner[]
}

export type OwnerPreferenceUpdate =
  | { favorite: true; score: number }
  | { favorite: false }

export interface OwnerPreferenceResult {
  owner_user_id: string
  favorite: boolean
  score: number | null
}

export const LAST_LIVE_WINDOWS = ['1h', '24h', '7d', '30d', 'never'] as const
export type LastLiveWindow = (typeof LAST_LIVE_WINDOWS)[number]

export const HISTORY_SORTS = [
  'last_checked_at',
  'score',
  'actived_count',
  'nickname',
] as const
export type HistorySort = (typeof HISTORY_SORTS)[number]

export const HISTORY_ORDERS = ['asc', 'desc'] as const
export type HistoryOrder = (typeof HISTORY_ORDERS)[number]

//
// The two values the database stores, in the database's own words.
//
export const USER_STATUSES = ['正常', '已注销'] as const
export type UserStatus = (typeof USER_STATUSES)[number]

export interface HistoryFilters {
  q?: string
  favorite?: boolean
  score_min?: number
  score_max?: number
  last_live_within?: LastLiveWindow
  user_status?: UserStatus
  sort?: HistorySort
  order?: HistoryOrder
  page?: number
  page_size?: number
}

/** One recorded broadcast. */
export interface LiveSession {
  observed_at: string | null
  room_id: string | null
  title: string | null
  room_status: number | null
  start_time: string | null
  finish_time: string | null
  status_code: number | null
}

//
// A probe's own vocabulary, deliberately separate from TaskState. `living` and
// `offline` are answers about a room, not lifecycle states of a job - folding
// them into the task states would mean a probe that finished successfully and
// found nobody streaming looked like a different kind of outcome from one that
// found somebody.
//
export const PROBE_STATES = ['pending', 'running', 'living', 'offline', 'error'] as const
export type ProbeState = (typeof PROBE_STATES)[number]

export interface LiveProbeItem {
  owner_user_id: string
  state: ProbeState
  nickname?: string | null
  live_share_url?: string | null
  room_id?: string | null
  title?: string | null
  checked_at?: string | null
  //
  // Answered from the recent-status cache rather than by asking the platform.
  // Worth showing: it is still a real answer, just not a fresh request.
  //
  cached?: boolean
  message?: string | null
}

export interface LiveProbeBatch {
  batch_id: string
  done: boolean
  items: LiveProbeItem[]
  //
  // Present on submission only, and null when nothing is mirroring onto the
  // unified task service.
  //
  task_id?: string | null
}
