import type { ResourceType } from './resolution'

//
// The unified task vocabulary, matching backend/src/task/model.py exactly.
// Written as const tuples so the union types are derived from one list rather
// than repeated beside it.
//

export const TASK_TYPES = [
  'post_download',
  'live_record',
  'owner_batch_download',
  'live_probe',
] as const

export type TaskType = (typeof TASK_TYPES)[number]

export const TASK_STATES = [
  'pending',
  'running',
  'success',
  'partial',
  'failed',
  'cancelled',
] as const

export type TaskState = (typeof TASK_STATES)[number]

export const TASK_ITEM_STATES = [
  'pending',
  'running',
  'success',
  'failed',
  'skipped',
] as const

export type TaskItemState = (typeof TASK_ITEM_STATES)[number]

//
// A task that has ended.  Anything else may still move.
//
export const TERMINAL_TASK_STATES: readonly TaskState[] = [
  'success',
  'partial',
  'failed',
  'cancelled',
]

export interface TaskProgress {
  current: number
  //
  // Null when there is nothing to divide by - a live recording runs until the
  // broadcast ends, so an honest "unknown" beats a fabricated total.
  //
  total: number | null
}

export interface TaskItem {
  key: string
  state: TaskItemState
  message: string | null
  metadata: Record<string, unknown>
}

export interface Task {
  task_id: string
  task_type: TaskType
  state: TaskState
  title: string | null
  message: string | null
  //
  // ISO 8601, produced by the backend's `to_payload`.
  //
  created_at: string
  started_at: string | null
  finished_at: string | null
  progress: TaskProgress
  //
  // Arbitrary business data - platform, resolve_id, source urls, results.  Kept
  // loose on purpose: the set differs per task type and per stage, and pinning
  // it here would mean editing the frontend every time a runner records one
  // more fact about its own work.
  //
  metadata: Record<string, unknown>
  items: TaskItem[]
}

export interface TaskList {
  items: Task[]
  //
  // How many there are, not how many were returned - the difference is what
  // lets a page say it is showing part of a longer list.
  //
  total: number
}

export interface TaskListFilters {
  state?: TaskState
  type?: TaskType
  limit?: number
}

//
// What `POST /api/tasks` answers.  Deliberately three fields: no future, no
// listener, no legacy job id, no whole snapshot - only the id to watch.
//
export interface CreatedTask {
  task_id: string
  task_type: TaskType
  resolve_id: string
}

//
// What may be asked for, mirroring the backend's compatibility matrix.
//
// A discriminated union rather than `task_type: string` plus `options: any`,
// because the matrix is the whole contract: a post takes no options, a
// recording takes none, and an owner batch has to say `mode: 'all'` in words
// because it is the most expensive thing this api can start.
//
// `selected` is absent on purpose - the backend refuses it, since an owner
// resolution carries only a sec_user_id and not the post payloads that mode
// needs.  The legacy owner page still serves that flow.
//
export type CreateTaskRequest =
  | {
      resolve_id: string
      task_type: 'post_download'
      options?: Record<string, never>
    }
  | {
      resolve_id: string
      task_type: 'live_record'
      options?: Record<string, never>
    }
  | {
      resolve_id: string
      task_type: 'owner_batch_download'
      options: { mode: 'all' }
    }

//
// The one task each kind of resolved resource can currently be turned into.
// Typed as a lookup so a view can offer the right action without restating the
// matrix, and so widening it later is one edit.
//
export const TASK_TYPE_FOR_RESOURCE: Readonly<Record<ResourceType, TaskType>> = {
  post: 'post_download',
  owner: 'owner_batch_download',
  live: 'live_record',
}
