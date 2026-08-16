import { computed, ref, watch } from 'vue'

import { ApiError } from '@/api/client'
import { resolveResources as defaultResolveResources } from '@/api/resolve'
import { createTask as defaultCreateTask } from '@/api/tasks'
import { buildCreateTaskRequest } from '@/composables/useNewDownloadFlow'
import type {
  BatchFailedItem,
  BatchResolveResult,
  BatchResolvedItem,
} from '@/types/resolution'
import type { CreateTaskRequest, CreatedTask } from '@/types/task'

export type BatchDownloadPhase =
  | 'editing'
  | 'resolving'
  | 'review'
  | 'creating'
  | 'complete'

export type BatchCreateState = 'idle' | 'creating' | 'created' | 'failed'

export type BatchReviewFailedItem = BatchFailedItem

export type BatchReviewResolvedItem = BatchResolvedItem & {
  selected: boolean
  ownerConfirmed: boolean
  createState: BatchCreateState
  taskId: string | null
  createError: string | null
}

export type BatchReviewItem = BatchReviewResolvedItem | BatchReviewFailedItem

export interface BatchDownloadApi {
  resolveResources: (input: string) => Promise<BatchResolveResult>
  createTask: (request: CreateTaskRequest) => Promise<CreatedTask>
}

function messageOf(caught: unknown, fallback: string): string {
  return caught instanceof ApiError ? caught.message || fallback : fallback
}

function reviewItem(item: BatchResolveResult['items'][number]): BatchReviewItem {
  if (item.status === 'failed') {
    return item
  }
  return {
    ...item,
    selected: item.resolution.resource_type !== 'owner',
    ownerConfirmed: false,
    createState: 'idle',
    taskId: null,
    createError: null,
  }
}

export function useBatchDownloadFlow(api: Partial<BatchDownloadApi> = {}) {
  const resolveResources = api.resolveResources ?? defaultResolveResources
  const createTask = api.createTask ?? defaultCreateTask

  const input = ref('')
  const phase = ref<BatchDownloadPhase>('editing')
  const items = ref<BatchReviewItem[]>([])
  const resolveError = ref<string | null>(null)
  let resolveGeneration = 0
  let stopped = false

  function discardReview() {
    items.value = []
    resolveError.value = null
  }

  watch(
    input,
    () => {
      if (phase.value === 'creating') {
        return
      }
      if (phase.value === 'resolving') {
        resolveGeneration += 1
      }
      if (phase.value !== 'editing') {
        discardReview()
        phase.value = 'editing'
      }
    },
    { flush: 'sync' },
  )

  const canResolve = computed(
    () =>
      input.value.trim().length > 0 &&
      phase.value !== 'resolving' &&
      phase.value !== 'creating',
  )

  const selectedItems = computed(() =>
    items.value.filter(
      (item): item is BatchReviewResolvedItem =>
        item.status === 'resolved' && item.selected && item.createState !== 'created',
    ),
  )

  const selectedCount = computed(() => selectedItems.value.length)
  const createdCount = computed(
    () =>
      items.value.filter(
        (item) => item.status === 'resolved' && item.createState === 'created',
      ).length,
  )
  const hasUnconfirmedOwner = computed(() =>
    selectedItems.value.some(
      (item) =>
        item.resolution.resource_type === 'owner' && !item.ownerConfirmed,
    ),
  )
  const canCreate = computed(
    () =>
      phase.value === 'review' &&
      selectedCount.value > 0 &&
      !hasUnconfirmedOwner.value,
  )
  const inputLocked = computed(() => phase.value === 'creating')

  async function resolve(): Promise<void> {
    if (!canResolve.value) {
      return
    }
    const submitted = input.value
    const generation = ++resolveGeneration
    stopped = false
    phase.value = 'resolving'
    discardReview()

    try {
      const answer = await resolveResources(submitted)
      if (
        generation !== resolveGeneration ||
        input.value.trim() !== submitted.trim()
      ) {
        return
      }
      items.value = answer.items.map(reviewItem)
      phase.value = 'review'
    } catch (caught) {
      if (generation !== resolveGeneration) {
        return
      }
      resolveError.value = messageOf(caught, '批量解析失败，请稍后重试')
      phase.value = 'editing'
    }
  }

  function setSelected(index: number, selected: boolean) {
    items.value = items.value.map((item) => {
      if (item.status === 'failed' || item.index !== index) {
        return item
      }
      return {
        ...item,
        selected,
        ownerConfirmed: selected ? item.ownerConfirmed : false,
      }
    })
  }

  function setOwnerConfirmed(index: number, confirmed: boolean) {
    items.value = items.value.map((item) =>
      item.status === 'resolved' && item.index === index
        ? { ...item, ownerConfirmed: confirmed }
        : item,
    )
  }

  function replaceResolved(index: number, fields: Partial<BatchReviewResolvedItem>) {
    items.value = items.value.map((item) =>
      item.status === 'resolved' && item.index === index
        ? { ...item, ...fields }
        : item,
    )
  }

  async function createSelected(): Promise<void> {
    if (!canCreate.value) {
      return
    }
    phase.value = 'creating'
    stopped = false
    const queue = [...selectedItems.value].sort((a, b) => a.index - b.index)

    for (const item of queue) {
      if (stopped) {
        break
      }
      replaceResolved(item.index, {
        createState: 'creating',
        createError: null,
      })
      try {
        const answer = await createTask(buildCreateTaskRequest(item.resolution))
        replaceResolved(item.index, {
          createState: 'created',
          taskId: answer.task_id,
          createError: null,
        })
      } catch (caught) {
        const expired = caught instanceof ApiError && caught.status === 404
        replaceResolved(item.index, {
          createState: 'failed',
          createError: expired
            ? '解析结果已过期，请重新批量解析'
            : messageOf(caught, '任务创建失败，请稍后重试'),
        })
      }
    }
    phase.value = 'complete'
  }

  function stop() {
    stopped = true
    // A resolve already on the wire cannot be cancelled by every adapter, but
    // it can be made stale so it never rebuilds a hidden review after a mode or
    // route change.
    resolveGeneration += 1
  }

  return {
    input,
    phase,
    items,
    resolveError,
    canResolve,
    canCreate,
    inputLocked,
    selectedCount,
    createdCount,
    resolve,
    setSelected,
    setOwnerConfirmed,
    createSelected,
    stop,
  }
}
