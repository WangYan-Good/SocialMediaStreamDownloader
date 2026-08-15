<script setup lang="ts">
import { computed } from 'vue'

import { progressPercent, progressText } from '@/components/tasks/taskPresentation'
import type { TaskProgress } from '@/types/task'

const props = defineProps<{ progress: TaskProgress }>()

const percent = computed(() =>
  progressPercent(props.progress.current, props.progress.total),
)

const label = computed(() => progressText(props.progress.current, props.progress.total))
</script>

<template>
  <div class="progress">
    <span class="progress__label">{{ label }}</span>
    <!--
      "进度", never "成功进度". `current` counts units dealt with, whatever the
      outcome was: a post that failed still advances it. Calling this a success
      rate would misreport a batch where every item failed as 100% good.
    -->
    <template v-if="percent !== null">
      <span class="progress__percent">{{ percent }}%</span>
      <span class="progress__track" aria-hidden="true">
        <span class="progress__fill" :style="{ width: `${percent}%` }"></span>
      </span>
    </template>
    <span v-else-if="progress.total === null" class="progress__muted">总量未知</span>
  </div>
</template>

<style scoped>
.progress {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  font-size: 0.8125rem;
  white-space: nowrap;
}

.progress__percent {
  color: var(--color-muted);
}

.progress__muted {
  color: var(--color-muted);
}

.progress__track {
  display: inline-block;
  width: 4rem;
  height: 6px;
  border-radius: 999px;
  background: var(--color-border);
  overflow: hidden;
}

.progress__fill {
  display: block;
  height: 100%;
  background: var(--color-accent);
}
</style>
