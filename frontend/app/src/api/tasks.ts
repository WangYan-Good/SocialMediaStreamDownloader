import { request } from './client'
import type {
  CreateTaskRequest,
  CreatedTask,
  Task,
  TaskList,
  TaskListFilters,
} from '@/types/task'

/**
 * Start the work a resolution names.  Answers the id to watch, not the result.
 *
 * The request says only which receipt and which kind of work: the server reads
 * the resource back from its own store rather than taking this client's word
 * for what was resolved.
 */
export function createTask(payload: CreateTaskRequest): Promise<CreatedTask> {
  return request<CreatedTask>('/tasks', { method: 'POST', body: payload })
}

/**
 * Every task this process knows about, newest first.
 *
 * `signal` is optional and additive: a caller that watches this list has to be
 * able to abandon a request whose answer it no longer wants - a filter changed,
 * the screen closed - and every existing caller is unaffected by not passing
 * one.
 */
export function listTasks(
  filters: TaskListFilters = {},
  signal?: AbortSignal,
): Promise<TaskList> {
  return request<TaskList>('/tasks', {
    query: {
      state: filters.state,
      type: filters.type,
      limit: filters.limit,
    },
    ...(signal ? { signal } : {}),
  })
}

/** One task, or an ApiError with status 404 once it has expired. */
export function getTask(taskId: string, signal?: AbortSignal): Promise<Task> {
  return request<Task>(`/tasks/${encodeURIComponent(taskId)}`, {
    ...(signal ? { signal } : {}),
  })
}
