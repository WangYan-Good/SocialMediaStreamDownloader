import { defineStore } from 'pinia'
import { computed, ref } from 'vue'

import { ApiError } from '@/api/client'
import { listTasks } from '@/api/tasks'
import type { Task, TaskState, TaskType } from '@/types/task'

/**
 * How often the task centre re-reads the list while it is open.
 *
 * Slower than the single-task poll in New Download: this is a whole list rather
 * than one record, and nobody is standing over it waiting for one specific
 * thing to finish.
 */
export const TASK_CENTER_POLL_INTERVAL_MS = 3000

/**
 * The page sizes the interface offers.
 *
 * A closed set rather than a free number: the backend applies `limit` after
 * filtering and has no offset, so this is "how much of the newest to show", not
 * a page size someone should be able to type 10000 into.
 */
export const TASK_LIMITS = [25, 50, 100] as const

export type TaskLimit = (typeof TASK_LIMITS)[number]

export const DEFAULT_TASK_LIMIT: TaskLimit = 50

/**
 * The task centre's own state: what is running in this server process.
 *
 * The first domain store in this application, and it earns being one. New
 * Download's state belongs to one visit to one screen and dies with it; this
 * outlives a navigation away and back, is read by several components at once,
 * and owns a polling loop with a lifecycle of its own.
 *
 * It stays out of `useAppStore`, which is shell state - a sidebar toggle has
 * nothing to do with tasks and should not be re-rendered by them.
 */
export const useTaskStore = defineStore('tasks', () => {
  const tasks = ref<Task[]>([])
  const total = ref(0)

  const stateFilter = ref<TaskState | null>(null)
  const typeFilter = ref<TaskType | null>(null)
  const limit = ref<TaskLimit>(DEFAULT_TASK_LIMIT)

  const selectedTaskId = ref<string | null>(null)

  const initialLoading = ref(false)
  const refreshing = ref(false)
  const refreshError = ref<string | null>(null)
  const lastUpdatedAt = ref<Date | null>(null)
  const pollingActive = ref(false)

  //
  // Whether a read has ever succeeded. Distinct from "the list is empty": a
  // failed first load must not be reported as "there are no tasks", because
  // nothing has been learned about how many there are.
  //
  const hasLoaded = ref(false)

  //
  // Which question the store is waiting on an answer to.
  //
  // Bumped by every filter change, every stop, and every start. An answer whose
  // generation is stale is dropped - otherwise a slow request for the previous
  // filter, arriving after a fast one for the new filter, would put the old
  // list back under the new filter's label.
  //
  let generation = 0
  //
  // Which polling loop owns the screen. Bumped by every start and every stop,
  // so a loop whose session is stale schedules nothing and writes nothing.
  //
  let pollSession = 0
  let timer: ReturnType<typeof setTimeout> | null = null
  let inFlight: AbortController | null = null

  const selectedTask = computed(
    () => tasks.value.find((one) => one.task_id === selectedTaskId.value) ?? null,
  )

  //
  // More match the filters than fitted inside the limit.
  //
  const isTruncated = computed(() => total.value > tasks.value.length)

  const hasFilters = computed(
    () => stateFilter.value !== null || typeFilter.value !== null,
  )

  function clearTimer() {
    if (timer !== null) {
      clearTimeout(timer)
      timer = null
    }
  }

  function abandonInFlight() {
    //
    // Abort what is on the wire, and bump the generation so that an answer
    // which was already past the point of being abortable is ignored too. The
    // abort alone is not enough: a response can be fully received and queued
    // before the signal lands.
    //
    if (inFlight !== null) {
      inFlight.abort()
      inFlight = null
    }
    generation += 1
  }

  function select(taskId: string) {
    selectedTaskId.value = taskId
  }

  function clearSelection() {
    selectedTaskId.value = null
  }

  async function load(): Promise<void> {
    const mine = ++generation
    const controller = new AbortController()
    inFlight = controller

    refreshing.value = true
    if (!hasLoaded.value) {
      initialLoading.value = true
    }

    try {
      const page = await listTasks(
        {
          //
          // Undefined, never an empty string: the backend validates these
          // against its own vocabulary and '' is not part of it.
          //
          ...(stateFilter.value !== null ? { state: stateFilter.value } : {}),
          ...(typeFilter.value !== null ? { type: typeFilter.value } : {}),
          limit: limit.value,
        },
        controller.signal,
      )

      if (mine !== generation) {
        return
      }

      //
      // Kept exactly as the server ordered them. It sorts newest-first and its
      // total is bound to that ordering; re-sorting here would disagree with it
      // about which task is the newest.
      //
      tasks.value = page.items
      total.value = page.total
      hasLoaded.value = true
      lastUpdatedAt.value = new Date()
      refreshError.value = null

      if (
        selectedTaskId.value !== null &&
        !page.items.some((one) => one.task_id === selectedTaskId.value)
      ) {
        //
        // The selected task is no longer in the list - reclaimed after its
        // retention, or filtered out. Keeping the panel open on it would show a
        // detail with nothing beside it in the list.
        //
        selectedTaskId.value = null
      }
    } catch (caught) {
      if (mine !== generation) {
        return
      }
      //
      // The list could not be read. That says nothing about the tasks
      // themselves, so whatever was last seen stays on screen and no task's
      // state is touched.
      //
      refreshError.value =
        caught instanceof ApiError
          ? `暂时无法刷新任务列表：${caught.message}`
          : '暂时无法刷新任务列表'
    } finally {
      if (mine === generation) {
        refreshing.value = false
        initialLoading.value = false
        inFlight = null
      }
    }
  }

  /**
   * Read the list, then schedule the next read - if this loop still owns the
   * screen.
   *
   * A recursive timeout rather than an interval, scheduled only once an answer
   * has arrived. An interval would launch a second read on top of a slow first
   * one and the two answers would land out of order.
   *
   * Unlike the single-task poll in New Download, this does not stop when
   * everything on screen has finished: the next task routinely arrives from
   * somewhere else - New Download, Creators, another browser, or a probe - and
   * a loop that stopped would never see it.
   */
  async function poll(session: number): Promise<void> {
    if (session !== pollSession) {
      return
    }

    await load()

    if (session !== pollSession) {
      //
      // The screen was closed, or the filters changed, while the read was in
      // flight. Scheduling now would leave a loop running behind whatever
      // replaced this one.
      //
      return
    }

    if (refreshError.value !== null) {
      //
      // Paused rather than retried on a timer: a backend that is not answering
      // does not need to be asked again every three seconds, and the user has
      // an explicit retry.
      //
      pollingActive.value = false
      return
    }

    clearTimer()
    timer = setTimeout(() => {
      void poll(session)
    }, TASK_CENTER_POLL_INTERVAL_MS)
  }

  async function startAutoRefresh(): Promise<void> {
    //
    // Whatever loop was running is abandoned first, so starting twice - a
    // remount racing an unmount - cannot leave two schedules alive.
    //
    stopAutoRefresh()
    const session = ++pollSession
    pollingActive.value = true
    await poll(session)
  }

  function stopAutoRefresh(): void {
    pollSession += 1
    pollingActive.value = false
    clearTimer()
    abandonInFlight()
  }

  return {
    tasks,
    total,
    stateFilter,
    typeFilter,
    limit,
    selectedTaskId,
    initialLoading,
    refreshing,
    refreshError,
    lastUpdatedAt,
    pollingActive,
    hasLoaded,
    selectedTask,
    isTruncated,
    hasFilters,
    select,
    clearSelection,

    /** Read the list again with the current filters. */
    startAutoRefresh,
    stopAutoRefresh,

    /** Read the list again with the current filters, without starting a loop. */
    async refresh(): Promise<void> {
      abandonInFlight()
      await load()
    },

    /**
     * Try again after a failure the user has chosen to retry, and resume the
     * loop that the failure paused.
     */
    async retry(): Promise<void> {
      refreshError.value = null
      await startAutoRefresh()
    },

    async setStateFilter(next: TaskState | null): Promise<void> {
      stateFilter.value = next
      selectedTaskId.value = null
      //
      // Restarted rather than merely re-read: the previous schedule would
      // otherwise fire on its own clock and race the new filter's reads.
      //
      if (pollingActive.value) {
        await startAutoRefresh()
      } else {
        abandonInFlight()
        await load()
      }
    },

    async setTypeFilter(next: TaskType | null): Promise<void> {
      typeFilter.value = next
      selectedTaskId.value = null
      //
      // Restarted rather than merely re-read: the previous schedule would
      // otherwise fire on its own clock and race the new filter's reads.
      //
      if (pollingActive.value) {
        await startAutoRefresh()
      } else {
        abandonInFlight()
        await load()
      }
    },

    async setLimit(next: TaskLimit): Promise<void> {
      limit.value = next
      selectedTaskId.value = null
      //
      // Restarted rather than merely re-read: the previous schedule would
      // otherwise fire on its own clock and race the new filter's reads.
      //
      if (pollingActive.value) {
        await startAutoRefresh()
      } else {
        abandonInFlight()
        await load()
      }
    },

  }
})
