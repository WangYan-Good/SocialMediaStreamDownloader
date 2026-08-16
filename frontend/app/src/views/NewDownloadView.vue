<script setup lang="ts">
import { computed, onBeforeUnmount, ref, watch } from 'vue'

import BatchResourceInputCard from '@/components/new-download/BatchResourceInputCard.vue'
import BatchResourceReview from '@/components/new-download/BatchResourceReview.vue'
import CurrentTaskCard from '@/components/new-download/CurrentTaskCard.vue'
import ResourceInputCard from '@/components/new-download/ResourceInputCard.vue'
import ResourceResolutionCard from '@/components/new-download/ResourceResolutionCard.vue'
import { useNewDownloadFlow } from '@/composables/useNewDownloadFlow'
import type { NewDownloadApi } from '@/composables/useNewDownloadFlow'
import { useBatchDownloadFlow } from '@/composables/useBatchDownloadFlow'
import type { BatchDownloadApi } from '@/composables/useBatchDownloadFlow'

//
// Injected so a test can drive the whole screen without stubbing globals. In
// the application nothing passes it and the real api modules are used.
//
const props = defineProps<{
  api?: Partial<NewDownloadApi>
  batchApi?: Partial<BatchDownloadApi>
}>()

const flow = useNewDownloadFlow(props.api ?? {})
const batchFlow = useBatchDownloadFlow(props.batchApi ?? {})
const mode = ref<'single' | 'batch'>('single')

//
// Both flows live for as long as this route does, so v-if alone only hides one
// of them. Crossing the mode boundary must also stop its later network/UI
// effects: created tasks keep running in Task Center, but hidden polling and
// not-yet-started batch creation do not.
//
watch(
  mode,
  (next) => {
    if (next === 'single') {
      batchFlow.stop()
    } else {
      flow.stop()
    }
  },
  { flush: 'sync' },
)

const resolving = computed(() => flow.phase.value === 'resolving')
const creating = computed(() => flow.phase.value === 'creating')
const batchResolving = computed(() => batchFlow.phase.value === 'resolving')
const batchCreating = computed(() => batchFlow.phase.value === 'creating')

//
// Leaving the page stops the polling. Nothing here survives the route change:
// carrying a task across screens needs somewhere to put it, and that arrives
// with the task centre.
//
onBeforeUnmount(() => {
  flow.stop()
  batchFlow.stop()
})

function reresolve() {
  //
  // The receipt aged out. Back to the form with the text intact, so the user
  // resolves again deliberately rather than the browser quietly reusing an
  // identity the server has already forgotten.
  //
  flow.resolved.value = null
  flow.createError.value = null
  flow.receiptExpired.value = false
  flow.phase.value = 'editing'
}
</script>

<template>
  <section class="new-download">
    <header class="new-download__header">
      <h1 class="new-download__title">新建下载</h1>
      <p class="new-download__hint">
        粘贴链接 → 服务端解析 → 确认后创建任务 → 跟踪任务状态
      </p>
    </header>

    <nav class="mode" aria-label="资源数量">
      <label
        data-mode="single"
        class="mode__button"
        :class="{ 'mode__button--active': mode === 'single' }"
        @click="mode = 'single'"
      >
        <input v-model="mode" class="mode__radio" type="radio" value="single" />
        单个资源
      </label>
      <label
        data-mode="batch"
        class="mode__button"
        :class="{ 'mode__button--active': mode === 'batch' }"
        @click="mode = 'batch'"
      >
        <input v-model="mode" class="mode__radio" type="radio" value="batch" />
        批量资源
      </label>
    </nav>

    <template v-if="mode === 'single'">
      <ResourceInputCard
        v-model="flow.input.value"
        :can-resolve="flow.canResolve.value"
        :resolving="resolving"
        :locked="flow.inputLocked.value"
        :error="flow.resolveError.value"
        @resolve="flow.resolve()"
      />

      <ResourceResolutionCard
        v-if="flow.resolved.value"
        v-model:owner-confirmed="flow.ownerConfirmed.value"
        :resolved="flow.resolved.value"
        :can-create="flow.canCreate.value"
        :creating="creating"
        :needs-owner-confirmation="flow.needsOwnerConfirmation.value"
        :error="flow.createError.value"
        :receipt-expired="flow.receiptExpired.value"
        @create="flow.create()"
        @reresolve="reresolve()"
      />

      <CurrentTaskCard
        v-if="flow.createdTask.value"
        :created="flow.createdTask.value"
        :task="flow.currentTask.value"
        :progress-percent="flow.progressPercent.value"
        :track-error="flow.trackError.value"
        :record-missing="flow.taskRecordMissing.value"
        :can-start-over="flow.canStartOver.value"
        @retry="flow.retryTracking()"
        @start-over="flow.startOver()"
      />
    </template>

    <template v-else>
      <BatchResourceInputCard
        v-model="batchFlow.input.value"
        :can-resolve="batchFlow.canResolve.value"
        :resolving="batchResolving"
        :locked="batchFlow.inputLocked.value"
        :error="batchFlow.resolveError.value"
        @resolve="batchFlow.resolve()"
      />
      <BatchResourceReview
        v-if="batchFlow.items.value.length"
        :items="batchFlow.items.value"
        :can-create="batchFlow.canCreate.value"
        :creating="batchCreating"
        :selected-count="batchFlow.selectedCount.value"
        :created-count="batchFlow.createdCount.value"
        @select="batchFlow.setSelected"
        @confirm-owner="batchFlow.setOwnerConfirmed"
        @create="batchFlow.createSelected()"
      />
    </template>
  </section>
</template>

<style scoped>
.new-download {
  display: grid;
  gap: var(--space-4);
  max-width: 46rem;
}

.new-download__header {
  margin-bottom: var(--space-1);
}

.new-download__title {
  margin: 0;
  font-size: 1.375rem;
}

.new-download__hint {
  margin: var(--space-1) 0 0;
  color: var(--color-muted);
  font-size: 0.8125rem;
}

.mode { display: flex; gap: var(--space-2); border-bottom: 1px solid var(--color-border); }
.mode__button { padding: var(--space-2) var(--space-4); font: inherit; color: var(--color-muted); background: none; border: 0; border-bottom: 2px solid transparent; cursor: pointer; }
.mode__button--active { color: var(--color-text); border-bottom-color: var(--color-accent); font-weight: 600; }
.mode__radio { position: absolute; inline-size: 1px; block-size: 1px; opacity: 0; pointer-events: none; }
</style>
