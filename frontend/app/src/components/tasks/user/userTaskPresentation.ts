import { TASK_ITEM_STATE_LABELS } from '@/components/tasks/taskPresentation'
import { TASK_ITEM_STATES } from '@/types/task'
import type { TaskItem, TaskItemState } from '@/types/task'

//
// The narrow layer between a task record and a user reading it.
//
// Deliberately small. The runners already write `message` in the user's
// language - "下载失败", "已保存 2 / 3 个媒体文件", "直播录制已停止" - so this
// is not a translation system and must not grow into one. It does two things
// the management panel does not need to do: it withholds text that was never
// written for a person, and it narrows an arbitrary metadata blob to the few
// fields whose meaning a user actually shares.
//
// Nothing here changes a task's state, its progress or how a failure was
// classified. Presentation only.
//

//
// Whether a string was written for a person to read.
//
// The same test the download screen uses, for the same reason: every message a
// runner writes deliberately is in Chinese, and every accident that reaches
// this field - an exception repr, a traceback header, a transport error - is
// not. Cheap, and wrong only in the safe direction.
//
function writtenForAUser(text: string): boolean {
  return /[㐀-鿿]/.test(text)
}

const TASK_TROUBLE = '任务遇到问题，请稍后重试。'

/**
 * What the task itself says, when that is something a user can read.
 *
 * `message` is business text nine times out of ten and is passed straight
 * through: the runner that wrote it knows more about what happened than this
 * layer does. The tenth case is an exception string that reached the field by
 * accident, and it is replaced wholesale rather than shown - a user can act on
 * "任务遇到问题", and cannot act on a `KeyError`.
 */
export function taskNote(message: string | null): string | null {
  const trimmed = (message ?? '').trim()
  if (!trimmed) {
    return null
  }
  return writtenForAUser(trimmed) ? trimmed : TASK_TROUBLE
}

//
// The result fields a user has a use for, and no others.
//
// The management panel's list is longer on purpose - it exists to diagnose a
// run. This one leaves out `save_dir`, `output_path`, `protocol`,
// `owner_user_id`, `nickname`, `room_status`, `live_status` and `test_mode`:
// each describes where the work landed or how it was performed, which is a
// question about the machine rather than about the download.
//
const USER_RESULT_FIELDS: ReadonlyArray<[string, string]> = [
  ['saved_count', '已保存'],
  ['media_count', '媒体总数'],
  ['skipped', '已跳过'],
  ['partial', '部分完成'],
  ['recorded', '已录制'],
  ['reason', '原因'],
]

export interface UserResultField {
  key: string
  label: string
  value: string
}

/**
 * Render a value only when it is a primitive this panel can show.
 *
 * A nested object or an array is skipped rather than stringified: `[object
 * Object]` tells a user nothing, and JSON in a definition list is the raw dump
 * this allow-list exists to prevent.
 */
function readable(value: unknown): string | null {
  if (typeof value === 'string') {
    const trimmed = value.trim()
    if (!trimmed) {
      return null
    }
    //
    // A free-text field the runner filled in. `reason` is the only one, and it
    // carries whatever the downloader recorded - sometimes a sentence, and
    // sometimes an upstream error's repr.
    //
    return writtenForAUser(trimmed) ? trimmed : null
  }
  if (typeof value === 'number' && Number.isFinite(value)) {
    return String(value)
  }
  if (typeof value === 'boolean') {
    return value ? '是' : '否'
  }
  return null
}

/**
 * The user-readable half of a finished task's recorded result.
 *
 * Reads `metadata.result`, which the download and recording runners write once
 * the attempt ends. Anything absent, non-primitive or not on the list above is
 * simply not shown.
 */
export function userResultFields(
  metadata: Record<string, unknown>,
): UserResultField[] {
  const raw = metadata.result
  if (typeof raw !== 'object' || raw === null || Array.isArray(raw)) {
    return []
  }
  const source = raw as Record<string, unknown>

  return USER_RESULT_FIELDS.map(([key, label]) => ({
    key,
    label,
    value: readable(source[key]),
  })).filter((entry): entry is UserResultField => entry.value !== null)
}

export interface ItemStateCount {
  state: TaskItemState
  label: string
  count: number
}

/**
 * How many work items are in each state.
 *
 * Counts rather than a list, because an item's `key` is the aweme id the
 * downloader was working on. That identifies the unit of work to the program
 * and means nothing to the person who asked for it, and there is no
 * human-readable label to put in its place - inventing one would mean guessing
 * a title the task never recorded.
 *
 * Ordered by the item-state vocabulary rather than by count, so a batch does
 * not reorder its own summary as it progresses.
 */
export function itemSummary(items: readonly TaskItem[]): ItemStateCount[] {
  const ORDER: readonly TaskItemState[] = [
    'success',
    'failed',
    'skipped',
    'running',
    'pending',
  ]
  //
  // Guarded against a state the backend adds without this list learning about
  // it: an unknown state is counted nowhere rather than crashing the panel.
  //
  const counts = new Map<TaskItemState, number>()
  for (const item of items) {
    if (!TASK_ITEM_STATES.includes(item.state)) {
      continue
    }
    counts.set(item.state, (counts.get(item.state) ?? 0) + 1)
  }

  return ORDER.filter((state) => (counts.get(state) ?? 0) > 0).map((state) => ({
    state,
    label: TASK_ITEM_STATE_LABELS[state],
    count: counts.get(state) as number,
  }))
}
