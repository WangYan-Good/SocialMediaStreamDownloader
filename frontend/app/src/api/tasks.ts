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

/** Every task this process knows about, newest first. */
export function listTasks(filters: TaskListFilters = {}): Promise<TaskList> {
  return request<TaskList>('/tasks', {
    query: {
      state: filters.state,
      type: filters.type,
      limit: filters.limit,
    },
  })
}

/** One task, or an ApiError with status 404 once it has expired. */
export function getTask(taskId: string): Promise<Task> {
  return request<Task>(`/tasks/${encodeURIComponent(taskId)}`)
}
