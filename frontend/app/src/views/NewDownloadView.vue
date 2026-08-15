<script setup lang="ts">
import { computed, onBeforeUnmount } from 'vue'

import CurrentTaskCard from '@/components/new-download/CurrentTaskCard.vue'
import ResourceInputCard from '@/components/new-download/ResourceInputCard.vue'
import ResourceResolutionCard from '@/components/new-download/ResourceResolutionCard.vue'
import { useNewDownloadFlow } from '@/composables/useNewDownloadFlow'
import type { NewDownloadApi } from '@/composables/useNewDownloadFlow'

//
// Injected so a test can drive the whole screen without stubbing globals. In
// the application nothing passes it and the real api modules are used.
//
const props = defineProps<{ api?: Partial<NewDownloadApi> }>()

const flow = useNewDownloadFlow(props.api ?? {})

const resolving = computed(() => flow.phase.value === 'resolving')
const creating = computed(() => flow.phase.value === 'creating')

//
// Leaving the page stops the polling. Nothing here survives the route change:
// carrying a task across screens needs somewhere to put it, and that arrives
// with the task centre.
//
onBeforeUnmount(() => {
  flow.stop()
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
</style>
