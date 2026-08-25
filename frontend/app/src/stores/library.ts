import { defineStore } from 'pinia'
import { computed, ref } from 'vue'

import { ApiError } from '@/api/client'
import {
  listLibraryLives,
  listLibraryPosts,
  listLibraryRecordings,
} from '@/api/library'
import { getPersonWorks, listPeople } from '@/api/people'
import type {
  LibraryLive,
  LibraryLiveFilters,
  LibraryPost,
  LibraryPostFilters,
  LibraryRecording,
  LibraryRecordingFilters,
} from '@/types/library'
import type { PersonSummaryItem, PersonWork } from '@/types/person'

/**
 * The library: an index of what this server already downloaded.
 *
 * One store rather than three, because the three sections share a lifetime -
 * they are opened, filtered and abandoned together as one screen - but their
 * state is kept apart inside it, because they are not the same schema. A
 * downloaded post, a recorded broadcast and a collaboration association have
 * different columns and different meanings, and flattening them into one
 * `LibraryItem` with thirty optional fields would lose exactly the distinctions
 * this page exists to show.
 *
 * Nothing here polls. The task centre already reports work in progress; this is
 * a record index, and a record index that re-queries the database every few
 * seconds is asking a question whose answer only changes when a download ends.
 */
export const useLibraryStore = defineStore('library', () => {
  //
  // Downloaded posts.
  //
  const posts = ref<LibraryPost[]>([])
  const postTotal = ref(0)
  const postPage = ref(1)
  const postPageSize = ref(25)
  const postFilters = ref<LibraryPostFilters>({
    sort: 'downloaded_at',
    order: 'desc',
  })
  const postLoading = ref(false)
  const postError = ref<string | null>(null)
  const hasLoadedPosts = ref(false)
  const selectedPostKey = ref<string | null>(null)

  let postGeneration = 0
  let postInFlight: AbortController | null = null

  //
  // Recorded live observations.
  //
  const lives = ref<LibraryLive[]>([])
  const liveTotal = ref(0)
  const livePage = ref(1)
  const livePageSize = ref(25)
  const liveFilters = ref<LibraryLiveFilters>({
    sort: 'observed_at',
    order: 'desc',
  })
  const liveLoading = ref(false)
  const liveError = ref<string | null>(null)
  const hasLoadedLives = ref(false)
  const selectedLiveKey = ref<string | null>(null)

  let liveGeneration = 0
  let liveInFlight: AbortController | null = null

  // Persistent recordings are user resources. They never share the Admin
  // live-observation state above because the rows have different meanings.
  const recordings = ref<LibraryRecording[]>([])
  const recordingTotal = ref(0)
  const recordingPage = ref(1)
  const recordingPageSize = ref(25)
  const recordingFilters = ref<LibraryRecordingFilters>({
    sort: 'finished_at',
    order: 'desc',
  })
  const recordingLoading = ref(false)
  const recordingError = ref<string | null>(null)
  const hasLoadedRecordings = ref(false)
  const selectedRecordingId = ref<string | null>(null)

  let recordingGeneration = 0
  let recordingInFlight: AbortController | null = null

  //
  // The person list, used only to populate a filter and a photographer picker.
  //
  // Read through the api rather than through the creators store on purpose: the
  // two screens must not share a selection, or opening a filter here would
  // change what the identity screen is showing.
  //
  const peopleOptions = ref<PersonSummaryItem[]>([])
  const peopleOptionsError = ref<string | null>(null)
  const hasLoadedPeopleOptions = ref(false)

  //
  // Posts associated with a photographer through a collaboration.
  //
  const selectedPhotographerId = ref<number | null>(null)
  const personWorks = ref<PersonWork[]>([])
  const personWorksLoading = ref(false)
  const personWorksError = ref<string | null>(null)

  let worksGeneration = 0
  let worksInFlight: AbortController | null = null

  function describe(caught: unknown, fallback: string): string {
    return caught instanceof ApiError ? `${fallback}：${caught.message}` : fallback
  }

  const postPageCount = computed(() =>
    postPageSize.value > 0
      ? Math.max(1, Math.ceil(postTotal.value / postPageSize.value))
      : 1,
  )
  const livePageCount = computed(() =>
    livePageSize.value > 0
      ? Math.max(1, Math.ceil(liveTotal.value / livePageSize.value))
      : 1,
  )
  const recordingPageCount = computed(() =>
    recordingPageSize.value > 0
      ? Math.max(1, Math.ceil(recordingTotal.value / recordingPageSize.value))
      : 1,
  )

  /** The database's own key for a post: one platform, one id. */
  function postKey(item: LibraryPost): string {
    return `${item.platform}:${item.aweme_id}`
  }

  /** Every part of live_record's key, so two observations never collide. */
  function liveKey(item: LibraryLive): string {
    return `${item.observed_at}:${item.platform}:${item.owner_user_id}:${item.room_id}`
  }

  const selectedPost = computed(
    () => posts.value.find((one) => postKey(one) === selectedPostKey.value) ?? null,
  )
  const selectedLive = computed(
    () => lives.value.find((one) => liveKey(one) === selectedLiveKey.value) ?? null,
  )
  const selectedRecording = computed(
    () =>
      recordings.value.find((one) => one.recording_id === selectedRecordingId.value) ??
      null,
  )

  async function loadPosts(): Promise<void> {
    const mine = ++postGeneration
    if (postInFlight !== null) {
      postInFlight.abort()
    }
    const controller = new AbortController()
    postInFlight = controller
    postLoading.value = true

    try {
      const answer = await listLibraryPosts(
        { ...postFilters.value, page: postPage.value },
        controller.signal,
      )
      if (mine !== postGeneration) {
        return
      }
      //
      // Exactly as the server ordered and counted them. Sorting again here
      // would contradict the total beside it.
      //
      posts.value = answer.items
      postTotal.value = answer.total
      postPage.value = answer.page
      postPageSize.value = answer.page_size
      hasLoadedPosts.value = true
      postError.value = null

      if (
        selectedPostKey.value !== null &&
        !answer.items.some((one) => postKey(one) === selectedPostKey.value)
      ) {
        selectedPostKey.value = null
      }
    } catch (caught) {
      if (mine !== postGeneration) {
        return
      }
      //
      // Whatever was last read stays on screen. A failed read is not evidence
      // that nothing was downloaded, and showing an empty table would say so.
      //
      postError.value = describe(caught, '媒体库暂时无法读取')
    } finally {
      if (mine === postGeneration) {
        postLoading.value = false
        postInFlight = null
      }
    }
  }

  async function loadLives(): Promise<void> {
    const mine = ++liveGeneration
    if (liveInFlight !== null) {
      liveInFlight.abort()
    }
    const controller = new AbortController()
    liveInFlight = controller
    liveLoading.value = true

    try {
      const answer = await listLibraryLives(
        { ...liveFilters.value, page: livePage.value },
        controller.signal,
      )
      if (mine !== liveGeneration) {
        return
      }
      lives.value = answer.items
      liveTotal.value = answer.total
      livePage.value = answer.page
      livePageSize.value = answer.page_size
      hasLoadedLives.value = true
      liveError.value = null

      if (
        selectedLiveKey.value !== null &&
        !answer.items.some((one) => liveKey(one) === selectedLiveKey.value)
      ) {
        selectedLiveKey.value = null
      }
    } catch (caught) {
      if (mine !== liveGeneration) {
        return
      }
      liveError.value = describe(caught, '直播记录暂时无法读取')
    } finally {
      if (mine === liveGeneration) {
        liveLoading.value = false
        liveInFlight = null
      }
    }
  }

  async function loadRecordings(): Promise<void> {
    const mine = ++recordingGeneration
    recordingInFlight?.abort()
    const controller = new AbortController()
    recordingInFlight = controller
    recordingLoading.value = true

    try {
      const answer = await listLibraryRecordings(
        { ...recordingFilters.value, page: recordingPage.value },
        controller.signal,
      )
      if (mine !== recordingGeneration) return
      recordings.value = answer.items
      recordingTotal.value = answer.total
      recordingPage.value = answer.page
      recordingPageSize.value = answer.page_size
      hasLoadedRecordings.value = true
      recordingError.value = null
      if (
        selectedRecordingId.value !== null &&
        !answer.items.some((one) => one.recording_id === selectedRecordingId.value)
      ) {
        selectedRecordingId.value = null
      }
    } catch (caught) {
      if (mine !== recordingGeneration) return
      recordingError.value = describe(caught, '直播记录暂时无法读取')
    } finally {
      if (mine === recordingGeneration) {
        recordingLoading.value = false
        recordingInFlight = null
      }
    }
  }

  return {
    posts,
    postTotal,
    postPage,
    postPageSize,
    postFilters,
    postLoading,
    postError,
    hasLoadedPosts,
    selectedPostKey,
    selectedPost,
    postPageCount,
    postKey,
    loadPosts,

    async setPostFilters(next: Partial<LibraryPostFilters>): Promise<void> {
      postFilters.value = { ...postFilters.value, ...next }
      //
      // Back to the first page: page four of one filter has nothing to do with
      // page four of another, and landing past the end reads as "no results"
      // for a filter that has plenty.
      //
      postPage.value = 1
      selectedPostKey.value = null
      await loadPosts()
    },

    async goToPostPage(next: number): Promise<void> {
      postPage.value = Math.max(1, next)
      selectedPostKey.value = null
      await loadPosts()
    },

    selectPost(key: string | null): void {
      //
      // From the page already on screen. Re-reading one row by id would be a
      // request per click for data the list is already holding.
      //
      selectedPostKey.value = key
    },

    lives,
    liveTotal,
    livePage,
    livePageSize,
    liveFilters,
    liveLoading,
    liveError,
    hasLoadedLives,
    selectedLiveKey,
    selectedLive,
    livePageCount,
    liveKey,
    loadLives,

    async setLiveFilters(next: Partial<LibraryLiveFilters>): Promise<void> {
      liveFilters.value = { ...liveFilters.value, ...next }
      livePage.value = 1
      selectedLiveKey.value = null
      await loadLives()
    },

    async goToLivePage(next: number): Promise<void> {
      livePage.value = Math.max(1, next)
      selectedLiveKey.value = null
      await loadLives()
    },

    selectLive(key: string | null): void {
      selectedLiveKey.value = key
    },

    recordings,
    recordingTotal,
    recordingPage,
    recordingPageSize,
    recordingFilters,
    recordingLoading,
    recordingError,
    hasLoadedRecordings,
    selectedRecordingId,
    selectedRecording,
    recordingPageCount,
    loadRecordings,

    async setRecordingFilters(next: Partial<LibraryRecordingFilters>): Promise<void> {
      recordingFilters.value = { ...recordingFilters.value, ...next }
      recordingPage.value = 1
      selectedRecordingId.value = null
      await loadRecordings()
    },

    async goToRecordingPage(next: number): Promise<void> {
      recordingPage.value = Math.max(1, next)
      selectedRecordingId.value = null
      await loadRecordings()
    },

    selectRecording(recordingId: string | null): void {
      selectedRecordingId.value = recordingId
    },

    peopleOptions,
    peopleOptionsError,
    hasLoadedPeopleOptions,

    /**
     * Fill the person filter.
     *
     * A convenience, and treated as one: a failure here is recorded and shown
     * beside the filter, and never propagated to the index itself. The library
     * works without knowing anybody's name.
     */
    async loadPeopleOptions(): Promise<void> {
      try {
        peopleOptions.value = await listPeople()
        hasLoadedPeopleOptions.value = true
        peopleOptionsError.value = null
      } catch (caught) {
        peopleOptionsError.value = describe(caught, '人物选项暂不可用')
      }
    },

    selectedPhotographerId,
    personWorks,
    personWorksLoading,
    personWorksError,

    /**
     * Read what one photographer is associated with.
     *
     * Association rather than attribution - see the api adapter. Nothing is
     * read until somebody is picked: this endpoint returns whole accounts'
     * output, and running it for everybody on arrival would be the most
     * expensive thing the page does, for a list nobody asked to see.
     */
    async selectPhotographer(personId: number | null): Promise<void> {
      const mine = ++worksGeneration
      if (worksInFlight !== null) {
        worksInFlight.abort()
      }
      selectedPhotographerId.value = personId
      personWorks.value = []
      personWorksError.value = null

      if (personId === null) {
        worksInFlight = null
        return
      }

      const controller = new AbortController()
      worksInFlight = controller
      personWorksLoading.value = true

      try {
        const answer = await getPersonWorks(personId, controller.signal)
        if (mine !== worksGeneration) {
          //
          // A later photographer owns the panel. Writing this answer would put
          // one person's associations under another's name.
          //
          return
        }
        personWorks.value = answer
        personWorksError.value = null
      } catch (caught) {
        if (mine !== worksGeneration) {
          return
        }
        personWorksError.value = describe(caught, '拍摄关系关联作品暂时无法读取')
      } finally {
        if (mine === worksGeneration) {
          personWorksLoading.value = false
          worksInFlight = null
        }
      }
    },
  }
})
