import type { ProbeState } from '@/types/history'

//
// The words this workspace uses, in one place.
//

export const PROBE_STATE_LABELS: Readonly<Record<ProbeState, string>> = {
  pending: '排队中',
  running: '检查中',
  living: '正在直播',
  offline: '未开播',
  //
  // A failed lookup, not a room that is dark. Reporting it as "未开播" would
  // claim nobody is streaming on no evidence - and hide a recording the user
  // could have started.
  //
  error: '查询失败',
}

//
// `room.status == 2` means broadcasting; anything else answered does not.
//
const ROOM_STATUS_LIVING = 2

/**
 * What the database last saw, said in the past tense.
 *
 * Deliberately never "正在直播": this is a cached value from whenever the
 * account was last checked, and an account last seen live an hour ago is not
 * live because of that. Only a probe answers the present tense.
 */
export function lastKnownLiveLabel(status: number | null): string {
  if (status === null) {
    return '上次：未检查'
  }
  return status === ROOM_STATUS_LIVING ? '上次：直播中' : '上次：已结束'
}

/**
 * What one recorded broadcast's status says, on its own terms.
 *
 * Separate from `lastKnownLiveLabel` on purpose. That one describes a cached
 * value and carries a "上次：" to say so; a session row *is* the broadcast it
 * describes, and borrowing that wording would make every row read as though it
 * were about something else.
 */
export function sessionStatusLabel(status: number | null): string {
  if (status === null) {
    return '未知'
  }
  return status === ROOM_STATUS_LIVING ? '直播中' : '已结束'
}

/** Whether a probe result says this account can be recorded right now. */
export function isLivingNow(state: ProbeState | null | undefined): boolean {
  return state === 'living'
}

export function formatCount(value: number | null): string {
  return value === null ? '—' : String(value)
}

/**
 * How much life the configured login has left.
 *
 * The cookie itself never reaches the browser; only this number does.
 *
 * Three tiers, including the healthy one. Saying nothing while the credential
 * is fine would make "plenty of time left" look exactly like "nobody checked" -
 * and the difference matters on the one screen where every read costs a real
 * platform conversation that an expired login turns into a failure.
 */
export function credentialNotice(days: number | null): string | null {
  if (days === null) {
    return null
  }
  if (days < 0) {
    return '抖音登录凭据已过期，请更新配置'
  }
  if (days < 7) {
    //
    // "将在 0 天后过期" is what counting days literally produces on the last
    // day, and it reads as though nothing were wrong. The tier is named
    // instead, with the count in support of it.
    //
    return days === 0
      ? '抖音登录凭据即将过期（不足 1 天）'
      : `抖音登录凭据即将过期（剩余 ${days} 天）`
  }
  return `抖音登录凭据剩余 ${days} 天`
}
