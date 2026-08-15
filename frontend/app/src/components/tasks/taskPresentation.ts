import type { TaskItemState, TaskState, TaskType } from '@/types/task'

//
// How the task vocabulary reads on screen, in one place.
//
// The wire values are the contract with the backend and never appear to a user;
// these are the words a user sees. Kept apart so a rewording is a change here
// and nowhere else - and so the two screens that show tasks cannot drift into
// calling the same state two different things.
//

export const TASK_TYPE_LABELS: Readonly<Record<TaskType, string>> = {
  post_download: '作品下载',
  live_record: '直播录制',
  owner_batch_download: '主播批量下载',
  live_probe: '直播探测',
}

export const TASK_STATE_LABELS: Readonly<Record<TaskState, string>> = {
  pending: '排队中',
  running: '进行中',
  success: '已完成',
  partial: '部分完成',
  failed: '失败',
  cancelled: '已停止',
}

export const TASK_ITEM_STATE_LABELS: Readonly<Record<TaskItemState, string>> = {
  pending: '排队中',
  running: '进行中',
  success: '已完成',
  failed: '失败',
  //
  // Not a failure. In the owner walk this means the file is already on disk, so
  // the user's goal is met - colouring it like a failure would report a
  // successful outcome as a problem.
  //
  skipped: '已跳过',
}

/**
 * What to call a task in a list.
 *
 * Falls back to the type rather than leaving a blank cell: a recording is named
 * "录制抖音直播" by its runner, but a task created before its title is known
 * would otherwise render as an empty row.
 */
export function taskDisplayTitle(title: string | null, type: TaskType): string {
  const trimmed = (title ?? '').trim()
  return trimmed || TASK_TYPE_LABELS[type]
}

/**
 * A percentage safe to draw a bar with, or null when there is nothing to draw.
 *
 * Null for an unknown total - a recording runs until the broadcast ends - and
 * for a zero total, which would divide. Clamped at both ends because a runner
 * that ever reported more finished units than it declared would otherwise push
 * a bar past the edge of its container.
 */
export function progressPercent(current: number, total: number | null): number | null {
  if (total === null || !Number.isFinite(total) || total <= 0) {
    return null
  }
  if (!Number.isFinite(current)) {
    return null
  }
  return Math.min(100, Math.max(0, Math.round((current / total) * 100)))
}

/**
 * The progress pair as words.
 *
 * "已处理 N" when there is no total, because "N / null" is not a thing and
 * "N / 0" would imply a bound that does not exist.
 */
export function progressText(current: number, total: number | null): string {
  if (total === null) {
    return `已处理 ${current}`
  }
  return `${current} / ${total}`
}

/**
 * A readable local time, or the original string when it cannot be parsed.
 *
 * A malformed timestamp is a bad cell, not a broken page: falling back to the
 * raw value keeps the row rendering and keeps the odd value visible to whoever
 * has to explain it.
 */
export function formatTaskTime(value: string | null): string {
  if (!value) {
    return '—'
  }
  const parsed = new Date(value)
  if (Number.isNaN(parsed.getTime())) {
    return value
  }
  return parsed.toLocaleString()
}

/**
 * Whether a value is safe to put in an `href`.
 *
 * `rel="noopener noreferrer"` does nothing about this: with `javascript:` or
 * `data:` the scheme *is* the payload, and a click runs it. Task metadata is
 * arbitrary business data written by whichever runner did the work, so a url
 * out of it is checked rather than trusted - and a value that fails the check
 * is still shown, as text, because an odd entry in a task record is something
 * somebody needs to be able to read and explain.
 */
export function isLinkableUrl(value: string): boolean {
  try {
    const parsed = new URL(value.trim())
    return parsed.protocol === 'http:' || parsed.protocol === 'https:'
  } catch {
    //
    // Not an absolute url at all. Nothing to link to.
    //
    return false
  }
}
