<script setup lang="ts">
import { TASK_STATE_LABELS } from '@/components/tasks/taskPresentation'
import { TASK_STATES } from '@/types/task'
import type { TaskState } from '@/types/task'

//
// State and refresh, and nothing else.
//
// No limit control: how much of the newest list to read is an api parameter,
// and the store's default already covers what a user is looking at. No type
// filter either - with four task types and a list this short, a state filter is
// the one that answers "what is still running".
//
defineProps<{
  stateFilter: TaskState | null
  refreshing: boolean
}>()

const emit = defineEmits<{
  'update:stateFilter': [TaskState | null]
  refresh: []
}>()

function onState(event: Event) {
  const value = (event.target as HTMLSelectElement).value
  emit('update:stateFilter', value === '' ? null : (value as TaskState))
}
</script>

<template>
  <div class="filters">
    <label class="filters__field">
      <span class="filters__label">状态</span>
      <select class="filters__select" :value="stateFilter ?? ''" @change="onState">
        <option value="">全部</option>
        <option v-for="state in TASK_STATES" :key="state" :value="state">
          {{ TASK_STATE_LABELS[state] }}
        </option>
      </select>
    </label>

    <button type="button" class="filters__action" :disabled="refreshing" @click="emit('refresh')">
      {{ refreshing ? '正在读取…' : '刷新' }}
    </button>
  </div>
</template>

<style scoped>
.filters { display: flex; flex-wrap: wrap; align-items: flex-end; gap: var(--space-3); }
.filters__field { display: flex; flex-direction: column; gap: var(--space-1); }
.filters__label { font-size: 0.75rem; color: var(--color-muted); }
.filters__select { padding: var(--space-1) var(--space-2); font: inherit; color: inherit; background: var(--color-surface); border: 1px solid var(--color-border); border-radius: var(--radius-1); }
.filters__action { padding: var(--space-2) var(--space-3); font: inherit; font-size: 0.8125rem; color: inherit; background: var(--color-surface); border: 1px solid var(--color-border); border-radius: var(--radius-1); cursor: pointer; }
.filters__action:disabled { opacity: 0.55; cursor: not-allowed; border-style: dashed; }
</style>
