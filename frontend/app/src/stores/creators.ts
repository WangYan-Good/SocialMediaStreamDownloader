import { defineStore } from 'pinia'
import { computed, ref } from 'vue'

import { ApiError } from '@/api/client'
import {
  getLiveProbe,
  listHistoryOwners,
  listOwnerSessions,
  submitLiveProbe,
  updateOwnerPreference,
} from '@/api/history'
import {
  readOwner,
  readOwnerPosts,
  startOwnerAllDownload,
  startOwnerSelectedDownload,
} from '@/api/owners'
import { resolveResource } from '@/api/resolve'
import { createTask } from '@/api/tasks'
import type {
  HistoryFilters,
  HistoryOwner,
  LiveProbeItem,
  LiveSession,
  OwnerPreferenceUpdate,
} from '@/types/history'
import type { OwnerPost, OwnerRead } from '@/types/owner'

/**
 * How often an unfinished probe batch is read again.
 *
 * A probe is two real platform requests per account, so the batch is worth
 * waiting on rather than hurrying.
 */
export const PROBE_POLL_INTERVAL_MS = 2000

/** How many past broadcasts one account's panel shows. */
const SESSION_LIMIT = 20

/**
 * The accounts side of the creators workspace.
 *
 * Kept apart from the people store because the two hold different kinds of
 * fact with different lifetimes: this one mixes what the local database
 * remembers with what the platform says right now, and every part of it is
 * re-read rather than edited. The people store holds a manual identity layer
 * that is written by hand and changes only when somebody changes it.
 */
export const useCreatorsStore = defineStore('creators', () => {
  const owners = ref<HistoryOwner[]>([])
  const ownerTotal = ref(0)
  const page = ref(1)
  const pageSize = ref(20)

  //
  // Defaults that match the backend's own: newest checked first. Stated here so
  // the first request is explicit rather than relying on the server's fallback.
  //
  const filters = ref<HistoryFilters>({
    sort: 'last_checked_at',
    order: 'desc',
  })

  const selectedOwnerUserId = ref<string | null>(null)

  const ownersLoading = ref(false)
  const ownersError = ref<string | null>(null)
  const hasLoadedOwners = ref(false)

  //
  // Which directory request the store is waiting on. Bumped by every filter
  // change and every page move, so an answer for a filter the user has moved on
  // from is dropped rather than written under the new filter's label.
  //
  let ownersGeneration = 0
  let ownersInFlight: AbortController | null = null

  //
  // Posts, and the paging context they belong to.
  //
  // Two entry points produce the first page - a history account is read by id,
  // a profile link arrives with its first page already paid for - but from the
  // second page onwards there is one mechanism, one list and one selection.
  // Sharing the *state* is what keeps them consistent; sharing the first
  // request would mean spending a platform read the owner api already made.
  //
  const posts = ref<OwnerPost[]>([])
  const postsSecUserId = ref<string | null>(null)
  const nextCursor = ref(0)
  const hasMorePosts = ref(false)
  const selectedAwemeIds = ref<string[]>([])
  const postsLoading = ref(false)
  const postsError = ref<string | null>(null)

  let postsGeneration = 0
  let postsInFlight: AbortController | null = null

  const loadedPostCount = computed(() => posts.value.length)

  /**
   * Start a new posts context, whichever entry point is starting it.
   *
   * Both entries funnel through here so their reset behaviour cannot drift:
   * one of them forgetting to clear the selection would leave a download
   * pointed at the previous creator's posts.
   */
  function beginPostsContext(secUserId: string | null) {
    postsGeneration += 1
    if (postsInFlight !== null) {
      postsInFlight.abort()
      postsInFlight = null
    }
    posts.value = []
    postsSecUserId.value = secUserId
    nextCursor.value = 0
    hasMorePosts.value = false
    selectedAwemeIds.value = []
    postsError.value = null
  }

  /**
   * Merge a page in, keeping one row per post in the order first seen.
   *
   * Platform paging repeats rows across boundaries often enough that a list
   * without this shows the same post twice. The cursor and the flag are taken
   * from the response regardless: deduplication is a display decision, paging
   * belongs to the platform, and inferring one from the other would eventually
   * skip a page.
   */
  function absorbPostPage(page: { posts: OwnerPost[]; next_cursor: number; has_more: boolean }) {
    const seen = new Set(posts.value.map((one) => one.aweme_id))
    const added = page.posts.filter((one) => {
      if (seen.has(one.aweme_id)) {
        return false
      }
      seen.add(one.aweme_id)
      return true
    })
    posts.value = [...posts.value, ...added]
    nextCursor.value = page.next_cursor
    hasMorePosts.value = page.has_more
  }

  async function fetchPostPage(secUserId: string, cursor: number): Promise<void> {
    const mine = ++postsGeneration
    const controller = new AbortController()
    postsInFlight = controller
    postsLoading.value = true

    try {
      const page = await readOwnerPosts(secUserId, cursor, controller.signal)
      if (mine !== postsGeneration) {
        return
      }
      absorbPostPage(page)
      postsError.value = null
    } catch (caught) {
      if (mine !== postsGeneration) {
        return
      }
      //
      // Whatever was already loaded stays: a page that could not be read is not
      // evidence that the earlier ones were wrong.
      //
      postsError.value =
        caught instanceof ApiError
          ? `暂时无法读取作品列表：${caught.message}`
          : '暂时无法读取作品列表'
    } finally {
      if (mine === postsGeneration) {
        postsLoading.value = false
        postsInFlight = null
      }
    }
  }

  //
  // Recorded broadcasts of whichever account is open. Read on demand: a page of
  // twenty accounts would otherwise be twenty queries nobody asked for.
  //
  const sessions = ref<LiveSession[]>([])
  const sessionsOwnerUserId = ref<string | null>(null)
  const sessionsLoading = ref(false)
  const sessionsError = ref<string | null>(null)
  let sessionsGeneration = 0

  //
  // One probe batch at a time - the one the user last asked for.
  //
  const probeBatchId = ref<string | null>(null)
  const probeTaskId = ref<string | null>(null)
  const probeItems = ref<Record<string, LiveProbeItem>>({})
  const probePolling = ref(false)
  const probeError = ref<string | null>(null)
  let probeSession = 0
  let probeTimer: ReturnType<typeof setTimeout> | null = null

  function absorbProbeItems(items: LiveProbeItem[]) {
    const next = { ...probeItems.value }
    for (const item of items) {
      next[item.owner_user_id] = item
    }
    probeItems.value = next
  }

  function clearProbeTimer() {
    if (probeTimer !== null) {
      clearTimeout(probeTimer)
      probeTimer = null
    }
  }

  function stopProbePolling() {
    probeSession += 1
    probePolling.value = false
    clearProbeTimer()
  }

  /**
   * Re-read the directory page already on screen, once, after a probe finished.
   *
   * A probe writes `last_live_status` and `last_checked_at` on the server, so
   * without this the row beside the result keeps showing what it said before
   * the check. Not a lie - one column says "上次" and the other "本次检查" - but
   * two numbers disagreeing on screen for no visible reason.
   *
   * An ordinary directory read, which is what makes it safe: the same page and
   * filters rather than a jump back to page one, and the same generation guard,
   * so a refresh that started under the old filters cannot land under new ones.
   * A failure writes `ownersError` and never `probeError`: the probe answered,
   * and the directory failing afterwards is a different fact about a different
   * request.
   *
   * Once. Nothing here starts a timer.
   */
  async function refreshDirectoryAfterProbe(): Promise<void> {
    await loadOwners()
  }

  /**
   * Read the batch again, then decide whether to keep waiting.
   *
   * A recursive timeout, scheduled only after an answer: an interval would put
   * a second read on top of a slow one and the two would land out of order.
   */
  async function pollProbe(session: number): Promise<void> {
    const batchId = probeBatchId.value
    if (session !== probeSession || batchId === null) {
      return
    }

    let answer
    try {
      answer = await getLiveProbe(batchId)
    } catch (caught) {
      if (session !== probeSession) {
        return
      }
      //
      // The browser could not find out. Deliberately *not* recorded as
      // "offline": that would claim nobody is streaming on no evidence, and
      // hide a recording the user could have started.
      //
      probeError.value =
        caught instanceof ApiError
          ? `暂时无法读取直播检查结果：${caught.message}`
          : '暂时无法读取直播检查结果'
      probePolling.value = false
      return
    }

    if (session !== probeSession) {
      return
    }

    absorbProbeItems(answer.items)
    probeError.value = null

    if (answer.done) {
      probePolling.value = false
      await refreshDirectoryAfterProbe()
      return
    }

    clearProbeTimer()
    probeTimer = setTimeout(() => {
      void pollProbe(session)
    }, PROBE_POLL_INTERVAL_MS)
  }

  //
  // A profile opened from a pasted link, and the outcome of whatever action was
  // last started from this screen.
  //
  const openedProfile = ref<OwnerRead | null>(null)
  const profileLoading = ref(false)
  const profileError = ref<string | null>(null)
  let profileGeneration = 0

  //
  // Who the panel is about.
  //
  // Two entry points can put a creator on screen - picking one from the
  // directory, and opening a pasted profile link - and either can still be in
  // flight when the other happens. Whichever the user asked for last owns the
  // panel; an answer for the other arrives about somebody nobody is looking at.
  //
  // One counter rather than one per request, because the thing being owned is
  // the whole panel - profile card, sessions, posts and selection together.
  // Guarding them separately is how one of them ends up describing a different
  // creator from the rest.
  //
  let creatorGeneration = 0

  const preferenceBusy = ref(false)
  const preferenceError = ref<string | null>(null)
  const preferenceNotice = ref<string | null>(null)
  let preferenceGeneration = 0

  const actionBusy = ref(false)
  const actionError = ref<string | null>(null)
  //
  // The task the last action produced. This screen hands the user to the task
  // centre with it and deliberately does not watch it: watching tasks is that
  // screen's job, and a second poller here would be a second opinion.
  //
  const lastStartedTaskId = ref<string | null>(null)
  //
  // Something worth saying that is not a failure - a task started but with no
  // unified record to point at, for instance.
  //
  const actionNotice = ref<string | null>(null)
  //
  // The server's post cache aged out. Retrying the same ids would fail the same
  // way; the list has to be read again first.
  //
  const postPayloadsExpired = ref(false)

  function describeFailure(caught: unknown, fallback: string): string {
    return caught instanceof ApiError ? caught.message || fallback : fallback
  }

  /**
   * Record what a started download can be followed by.
   *
   * The legacy job id is deliberately ignored. It is the old page's
   * compatibility surface, and a new client that read it would end up building
   * a second progress view beside the task centre - and polling it.
   */
  function noteStartedDownload(taskId: string | null) {
    if (taskId === null) {
      actionNotice.value = '下载已提交，但统一任务记录不可用'
      return
    }
    lastStartedTaskId.value = taskId
  }

  const selectedOwner = computed(
    () =>
      owners.value.find((one) => one.owner_user_id === selectedOwnerUserId.value) ?? null,
  )

  const pageCount = computed(() =>
    pageSize.value > 0 ? Math.max(1, Math.ceil(ownerTotal.value / pageSize.value)) : 1,
  )

  const hasPreviousPage = computed(() => page.value > 1)
  const hasNextPage = computed(() => page.value < pageCount.value)

  function abandonOwnersRequest() {
    if (ownersInFlight !== null) {
      ownersInFlight.abort()
      ownersInFlight = null
    }
    ownersGeneration += 1
  }

  /**
   * Hand the panel to a new creator, whichever entry point is doing it.
   */
  function beginCreatorContext(): number {
    creatorGeneration += 1
    preferenceGeneration += 1
    preferenceError.value = null
    preferenceNotice.value = null
    profileGeneration += 1
    openedProfile.value = null
    profileError.value = null
    sessions.value = []
    sessionsOwnerUserId.value = null
    sessionsGeneration += 1
    beginPostsContext(null)
    return creatorGeneration
  }

  function selectOwner(ownerUserId: string) {
    //
    // Takes ownership: a profile still being read, or one already on screen, is
    // no longer what the user is looking at.
    //
    beginCreatorContext()
    selectedOwnerUserId.value = ownerUserId
  }

  function clearOwnerSelection() {
    beginCreatorContext()
    selectedOwnerUserId.value = null
  }

  async function loadOwners(): Promise<void> {
    const mine = ++ownersGeneration
    const controller = new AbortController()
    ownersInFlight = controller
    ownersLoading.value = true

    try {
      const answer = await listHistoryOwners(
        { ...filters.value, page: page.value },
        controller.signal,
      )

      if (mine !== ownersGeneration) {
        return
      }

      //
      // Exactly as the server ordered and counted them.
      //
      owners.value = answer.items
      ownerTotal.value = answer.total
      page.value = answer.page
      pageSize.value = answer.page_size
      hasLoadedOwners.value = true
      ownersError.value = null

      if (
        selectedOwnerUserId.value !== null &&
        !answer.items.some((one) => one.owner_user_id === selectedOwnerUserId.value)
      ) {
        //
        // The selected account is not on this page any more. Leaving the panel
        // open on it would describe something the list beside it does not show.
        //
        selectedOwnerUserId.value = null
      }
    } catch (caught) {
      if (mine !== ownersGeneration) {
        return
      }
      //
      // The directory could not be read. That is not evidence that there are no
      // accounts, so whatever was last seen stays.
      //
      ownersError.value =
        caught instanceof ApiError
          ? `暂时无法读取主播列表：${caught.message}`
          : '暂时无法读取主播列表'
    } finally {
      if (mine === ownersGeneration) {
        ownersLoading.value = false
        ownersInFlight = null
      }
    }
  }

  return {
    owners,
    ownerTotal,
    page,
    pageSize,
    filters,
    selectedOwnerUserId,
    ownersLoading,
    ownersError,
    hasLoadedOwners,
    selectedOwner,
    pageCount,
    hasPreviousPage,
    hasNextPage,
    selectOwner,
    clearOwnerSelection,
    loadOwners,

    preferenceBusy,
    preferenceError,
    preferenceNotice,

    async savePreference(
      ownerUserId: string,
      payload: OwnerPreferenceUpdate,
    ): Promise<void> {
      if (
        preferenceBusy.value ||
        selectedOwnerUserId.value !== ownerUserId
      ) {
        return
      }

      const context = preferenceGeneration
      preferenceBusy.value = true
      preferenceError.value = null
      preferenceNotice.value = null

      try {
        await updateOwnerPreference(ownerUserId, payload)
      } catch (caught) {
        if (
          context === preferenceGeneration &&
          selectedOwnerUserId.value === ownerUserId
        ) {
          preferenceError.value =
            caught instanceof ApiError
              ? `偏好保存失败：${caught.message}`
              : '偏好保存失败，请稍后重试'
        }
        preferenceBusy.value = false
        return
      }

      await loadOwners()
      if (context !== preferenceGeneration) {
        preferenceBusy.value = false
        return
      }
      preferenceNotice.value = ownersError.value
        ? '偏好已保存，但列表暂时无法刷新'
        : '偏好已保存'
      preferenceBusy.value = false
    },

    posts,
    postsSecUserId,
    nextCursor,
    hasMorePosts,
    selectedAwemeIds,
    postsLoading,
    postsError,
    loadedPostCount,

    /** First page for a history account, read by id. */
    async openPostsForOwner(secUserId: string): Promise<void> {
      beginPostsContext(secUserId)
      await fetchPostPage(secUserId, 0)
    },

    /**
     * First page for a profile that has just been read.
     *
     * Deliberately makes no request: `/api/owner` already returned this page,
     * at the cost of a real platform call. Asking again would spend a second
     * one and could answer differently, so the same screen would show a
     * different first page depending on which reply landed last.
     *
     * The paging identity comes from the owner api's own `sec_user_id`, not
     * from whatever the resolve step said earlier: once the owner endpoint has
     * answered, that is the value `/owner/posts` is keyed on.
     */
    adoptPostsFromOwnerRead(read: OwnerRead): void {
      beginPostsContext(read.sec_user_id)
      absorbPostPage({
        posts: read.posts,
        next_cursor: read.next_cursor,
        has_more: read.has_more,
      })
    },

    async loadMorePosts(): Promise<void> {
      const secUserId = postsSecUserId.value
      if (!hasMorePosts.value || secUserId === null || postsLoading.value) {
        return
      }
      await fetchPostPage(secUserId, nextCursor.value)
    },

    sessions,
    sessionsOwnerUserId,
    sessionsLoading,
    sessionsError,

    /** Read one account's recorded broadcasts. */
    async loadSessions(ownerUserId: string): Promise<void> {
      const mine = ++sessionsGeneration
      sessionsOwnerUserId.value = ownerUserId
      sessionsLoading.value = true
      try {
        const answer = await listOwnerSessions(ownerUserId, { limit: SESSION_LIMIT })
        if (mine !== sessionsGeneration) {
          return
        }
        sessions.value = answer.items
        sessionsError.value = null
      } catch (caught) {
        if (mine !== sessionsGeneration) {
          return
        }
        sessionsError.value =
          caught instanceof ApiError
            ? `暂时无法读取直播记录：${caught.message}`
            : '暂时无法读取直播记录'
      } finally {
        if (mine === sessionsGeneration) {
          sessionsLoading.value = false
        }
      }
    },

    probeBatchId,
    probeTaskId,
    probeItems,
    probePolling,
    probeError,
    stopProbePolling,

    probeItemFor(ownerUserId: string): LiveProbeItem | null {
      return probeItems.value[ownerUserId] ?? null
    },

    /**
     * Ask whether these accounts are broadcasting right now.
     *
     * An empty request is refused rather than treated as "check everything":
     * the legacy page read no selection as the whole page, and a probe is one
     * real platform conversation per account.
     */
    async probeOwners(ownerUserIds: string[]): Promise<void> {
      if (ownerUserIds.length === 0) {
        return
      }
      //
      // Whatever batch was being watched is abandoned: only the one the user
      // just asked for is worth polling.
      //
      stopProbePolling()
      const session = ++probeSession
      probeError.value = null

      let answer
      try {
        answer = await submitLiveProbe(ownerUserIds)
      } catch (caught) {
        if (session !== probeSession) {
          return
        }
        probeError.value =
          caught instanceof ApiError
            ? `直播检查失败：${caught.message}`
            : '直播检查失败'
        return
      }

      if (session !== probeSession) {
        return
      }

      probeBatchId.value = answer.batch_id
      probeTaskId.value = answer.task_id ?? null
      absorbProbeItems(answer.items)

      if (answer.done) {
        //
        // Answered entirely from the cache. Nothing to wait for.
        //
        probePolling.value = false
        await refreshDirectoryAfterProbe()
        return
      }

      probePolling.value = true
      clearProbeTimer()
      probeTimer = setTimeout(() => {
        void pollProbe(session)
      }, PROBE_POLL_INTERVAL_MS)
    },

    /** Read the batch again after a failure the user chose to retry. */
    async retryProbe(): Promise<void> {
      if (probeBatchId.value === null) {
        return
      }
      probeError.value = null
      probePolling.value = true
      const session = ++probeSession
      await pollProbe(session)
    },

    openedProfile,
    profileLoading,
    profileError,
    actionBusy,
    actionError,
    lastStartedTaskId,

    /**
     * Record a live room, through the resolve-then-create path.
     *
     * Never the legacy paste endpoint, and never the share url straight to the
     * task api: the receipt is what proves this server resolved the room, and
     * the resolver is what applied the host checks to a short link the user
     * never validated.
     */
    async startRecording(liveShareUrl: string): Promise<void> {
      if (actionBusy.value) {
        return
      }
      actionBusy.value = true
      actionError.value = null
      lastStartedTaskId.value = null

      try {
        const resolution = await resolveResource(liveShareUrl)
        if (resolution.resource_type !== 'live') {
          //
          // The link resolved to something else. Recording it would be starting
          // work the user did not ask for, against a resource that cannot do it.
          //
          actionError.value = '该链接不是直播间，无法开始录制'
          return
        }
        const created = await createTask({
          resolve_id: resolution.resolve_id,
          task_type: 'live_record',
        })
        lastStartedTaskId.value = created.task_id
      } catch (caught) {
        actionError.value = describeFailure(caught, '开始录制失败，请稍后重试')
      } finally {
        actionBusy.value = false
      }
    },

    /**
     * Open a creator's profile from whatever the user pasted.
     *
     * Resolved first, always. `/api/owner` would follow a short link itself,
     * outside the resolver's host allow list and hop limit; handing it an
     * already-resolved url means that following has already happened under
     * those checks.
     */
    async openProfile(rawInput: string): Promise<void> {
      const mine = beginCreatorContext()
      selectedOwnerUserId.value = null
      profileLoading.value = true
      profileError.value = null

      try {
        const resolution = await resolveResource(rawInput)
        if (mine !== creatorGeneration) {
          return
        }
        if (resolution.resource_type !== 'owner') {
          profileError.value = '该链接不是主播主页，请粘贴主页分享链接'
          return
        }

        const read = await readOwner(resolution.resolved_url)
        if (mine !== creatorGeneration) {
          //
          // Somebody else owns the panel now - the user picked an account from
          // the directory while this was in flight. Adopting this profile, or
          // its posts, would put one creator's data under another's name.
          //
          return
        }

        openedProfile.value = read
        //
        // The first page came with the profile, at the cost of a real platform
        // read. Adopting it is what keeps this screen from spending a second.
        //
        beginPostsContext(read.sec_user_id)
        absorbPostPage({
          posts: read.posts,
          next_cursor: read.next_cursor,
          has_more: read.has_more,
        })
        profileError.value = null
      } catch (caught) {
        if (mine !== creatorGeneration) {
          return
        }
        profileError.value = describeFailure(caught, '打开主播主页失败，请稍后重试')
      } finally {
        if (mine === creatorGeneration) {
          profileLoading.value = false
        }
      }
    },

    actionNotice,
    postPayloadsExpired,

    /**
     * Download the ticked posts.
     *
     * Only ids travel: the payloads live in the server's own cache, which is
     * what makes a selection safe to submit at all.
     */
    async downloadSelectedPosts(shareUrl?: string): Promise<void> {
      if (selectedAwemeIds.value.length === 0 || actionBusy.value) {
        return
      }
      actionBusy.value = true
      actionError.value = null
      actionNotice.value = null
      lastStartedTaskId.value = null

      try {
        const started = await startOwnerSelectedDownload(
          [...selectedAwemeIds.value],
          shareUrl,
        )
        noteStartedDownload(started.task_id)
      } catch (caught) {
        if (caught instanceof ApiError && caught.status === 404) {
          //
          // The cached payloads are gone. The ids no longer mean anything to
          // the server, so the selection is cleared rather than left pointing
          // at something that will fail identically on every retry.
          //
          postPayloadsExpired.value = true
          selectedAwemeIds.value = []
          actionError.value = caught.message || '作品数据已过期，请重新读取作品列表'
          return
        }
        actionError.value = describeFailure(caught, '提交下载失败，请稍后重试')
      } finally {
        actionBusy.value = false
      }
    },

    /**
     * Download an entire back catalogue.
     *
     * By owner id, so the server walks the pages. Sending the ids the browser
     * happens to have loaded would download only those - a different thing
     * wearing the same label.
     */
    async downloadAllPosts(shareUrl?: string): Promise<void> {
      const secUserId = postsSecUserId.value
      if (secUserId === null || actionBusy.value) {
        return
      }
      actionBusy.value = true
      actionError.value = null
      actionNotice.value = null
      lastStartedTaskId.value = null

      try {
        const started = await startOwnerAllDownload(secUserId, shareUrl)
        noteStartedDownload(started.task_id)
      } catch (caught) {
        actionError.value = describeFailure(caught, '提交下载失败，请稍后重试')
      } finally {
        actionBusy.value = false
      }
    },

    togglePostSelection(awemeId: string): void {
      selectedAwemeIds.value = selectedAwemeIds.value.includes(awemeId)
        ? selectedAwemeIds.value.filter((one) => one !== awemeId)
        : [...selectedAwemeIds.value, awemeId]
    },

    selectAllLoadedPosts(): void {
      selectedAwemeIds.value = posts.value.map((one) => one.aweme_id)
    },

    clearPostSelection(): void {
      selectedAwemeIds.value = []
    },

    async setFilters(next: Partial<HistoryFilters>): Promise<void> {
      filters.value = { ...filters.value, ...next }
      //
      // Back to the first page: page 3 of one filter has nothing to do with
      // page 3 of another, and landing past the end would read as "no results"
      // for a filter that has plenty.
      //
      page.value = 1
      selectedOwnerUserId.value = null
      abandonOwnersRequest()
      await loadOwners()
    },

    async goToPage(next: number): Promise<void> {
      page.value = Math.max(1, next)
      selectedOwnerUserId.value = null
      abandonOwnersRequest()
      await loadOwners()
    },
  }
})
