import { defineStore } from 'pinia'
import { ref } from 'vue'

import { ApiError } from '@/api/client'
import { listHistoryOwners } from '@/api/history'
import { listLibraryLives, listLibraryPosts } from '@/api/library'
import { getSystemStatus } from '@/api/system'
import { listTasks } from '@/api/tasks'
import type { LibraryLive, LibraryPost } from '@/types/library'
import type { SystemStatus } from '@/types/system'
import type { Task } from '@/types/task'

/** How many recent tasks the landing page shows. */
const RECENT_TASK_LIMIT = 5

/**
 * The landing page's snapshot of what the other screens already know.
 *
 * A composition of read models that exist rather than a new one. Every number
 * here is a `total` some endpoint already computes, so there is no overview
 * query, no overview table and no second implementation to keep in step.
 *
 * Deliberately its own store rather than a reader of the task, creators,
 * library and system stores. Those hold their screens' filters, selections,
 * paging and refresh lifecycles; borrowing them would mean opening this page
 * could change what the task centre is filtered by, or start the polling that
 * belongs to it. The api adapters are shared; the state is not.
 *
 * Nothing here polls. The task centre watches work in progress and the creators
 * screen owns live probing; this is a snapshot, refreshed when somebody asks.
 */
export const useOverviewStore = defineStore('overview', () => {
  //
  // Each section keeps its own value and its own error, because each is read by
  // its own request and any one of them can fail alone. On a server whose
  // database is down, the system status and the in-process task record still
  // answer perfectly well - and the system card is exactly where somebody would
  // look to find out why the others did not.
  //
  const systemStatus = ref<SystemStatus | null>(null)
  const systemError = ref<string | null>(null)

  const recentTasks = ref<Task[]>([])
  const taskTotal = ref<number | null>(null)
  const tasksError = ref<string | null>(null)

  const creatorTotal = ref<number | null>(null)
  const creatorsError = ref<string | null>(null)

  const libraryPostTotal = ref<number | null>(null)
  const latestPost = ref<LibraryPost | null>(null)
  const postsError = ref<string | null>(null)

  const libraryLiveTotal = ref<number | null>(null)
  const latestLive = ref<LibraryLive | null>(null)
  const livesError = ref<string | null>(null)

  const loading = ref(false)
  const hasLoaded = ref(false)
  const lastUpdatedAt = ref<Date | null>(null)

  //
  // Which batch the store is waiting on. One counter for all five reads: they
  // are refreshed together and abandoned together, and guarding them separately
  // is how half a page ends up describing an older moment than the other half.
  //
  let generation = 0
  let inFlight: AbortController | null = null

  function describe(caught: unknown, fallback: string): string {
    return caught instanceof ApiError ? `${fallback}：${caught.message}` : fallback
  }

  function abandon(): void {
    generation += 1
    if (inFlight !== null) {
      inFlight.abort()
      inFlight = null
    }
    loading.value = false
  }

  /**
   * Run one section's read, and let it fail on its own.
   *
   * The failure of one read is recorded against that section and nowhere else.
   * Whatever that section last showed successfully stays: a refresh that could
   * not reach the server says nothing about whether the previous answer was
   * true, and replacing a count with zero would state "there are none" while
   * meaning "I could not ask".
   */
  async function section(
    mine: number,
    write: () => Promise<void>,
    fail: (message: string) => void,
    fallback: string,
  ): Promise<void> {
    try {
      await write()
    } catch (caught) {
      if (mine !== generation) {
        return
      }
      fail(describe(caught, fallback))
    }
  }

  async function load(): Promise<void> {
    if (loading.value) {
      //
      // One batch at a time. Five reads per click would otherwise multiply with
      // every impatient press.
      //
      return
    }

    const mine = ++generation
    const controller = new AbortController()
    inFlight = controller
    loading.value = true
    const signal = controller.signal

    //
    // Started together and awaited together, but never as one promise that
    // fails as a whole: a single library 503 must not blank the four sections
    // that answered.
    //
    await Promise.all([
      section(
        mine,
        async () => {
          const answer = await getSystemStatus(signal)
          if (mine !== generation) return
          systemStatus.value = answer
          systemError.value = null
        },
        (message) => {
          systemError.value = message
        },
        '暂时无法读取系统状态',
      ),
      section(
        mine,
        async () => {
          const answer = await listTasks({ limit: RECENT_TASK_LIMIT }, signal)
          if (mine !== generation) return
          //
          // In the order the task api produced, and counted by its own total -
          // the list is five rows out of however many the process holds.
          //
          recentTasks.value = answer.items
          taskTotal.value = answer.total
          tasksError.value = null
        },
        (message) => {
          tasksError.value = message
        },
        '暂时无法读取任务记录',
      ),
      section(
        mine,
        async () => {
          const answer = await listHistoryOwners(
            { page: 1, page_size: 1, sort: 'last_checked_at', order: 'desc' },
            signal,
          )
          if (mine !== generation) return
          creatorTotal.value = answer.total
          creatorsError.value = null
        },
        (message) => {
          creatorsError.value = message
        },
        '暂时无法读取账号统计',
      ),
      section(
        mine,
        async () => {
          const answer = await listLibraryPosts(
            { page: 1, page_size: 1, sort: 'downloaded_at', order: 'desc' },
            signal,
          )
          if (mine !== generation) return
          libraryPostTotal.value = answer.total
          latestPost.value = answer.items[0] ?? null
          postsError.value = null
        },
        (message) => {
          postsError.value = message
        },
        '暂时无法读取作品统计',
      ),
      section(
        mine,
        async () => {
          const answer = await listLibraryLives(
            { page: 1, page_size: 1, sort: 'observed_at', order: 'desc' },
            signal,
          )
          if (mine !== generation) return
          libraryLiveTotal.value = answer.total
          latestLive.value = answer.items[0] ?? null
          livesError.value = null
        },
        (message) => {
          livesError.value = message
        },
        '暂时无法读取直播记录统计',
      ),
    ])

    if (mine !== generation) {
      //
      // The page was left, or a newer batch took over, while these were in
      // flight. Nothing above wrote, and nothing here does either.
      //
      return
    }

    hasLoaded.value = true
    lastUpdatedAt.value = new Date()
    loading.value = false
    inFlight = null
  }

  return {
    systemStatus,
    systemError,
    recentTasks,
    taskTotal,
    tasksError,
    creatorTotal,
    creatorsError,
    libraryPostTotal,
    latestPost,
    postsError,
    libraryLiveTotal,
    latestLive,
    livesError,
    loading,
    hasLoaded,
    lastUpdatedAt,
    load,
    abandon,
  }
})
