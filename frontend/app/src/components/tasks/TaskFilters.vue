<script setup lang="ts">
import {
  TASK_STATE_LABELS,
  TASK_TYPE_LABELS,
} from '@/components/tasks/taskPresentation'
import { TASK_LIMITS } from '@/stores/tasks'
import type { TaskLimit } from '@/stores/tasks'
import { TASK_STATES, TASK_TYPES } from '@/types/task'
import type { TaskState, TaskType } from '@/types/task'

defineProps<{
  stateFilter: TaskState | null
  typeFilter: TaskType | null
  limit: TaskLimit
  refreshing: boolean
}>()

const emit = defineEmits<{
  'update:stateFilter': [TaskState | null]
  'update:typeFilter': [TaskType | null]
  'update:limit': [TaskLimit]
  refresh: []
}>()

//
// '' is the option element's value for "no filter"; it is turned back into null
// here and never travels to the api, where an empty enum would be rejected.
//
function onState(event: Event) {
  const value = (event.target as HTMLSelectElement).value
  emit('update:stateFilter', value === '' ? null : (value as TaskState))
}

function onType(event: Event) {
  const value = (event.target as HTMLSelectElement).value
  emit('update:typeFilter', value === '' ? null : (value as TaskType))
}

function onLimit(event: Event) {
  emit('update:limit', Number((event.target as HTMLSelectElement).value) as TaskLimit)
}
</script>

<template>
  <div class="filters">
    <label class="filters__field">
      <span class="filters__label">状态</span>
      <select class="filters__select" :value="stateFilter ?? ''" @change="onState">
        <option value="">全部状态</option>
        <option v-for="state in TASK_STATES" :key="state" :value="state">
          {{ TASK_STATE_LABELS[state] }}
        </option>
      </select>
    </label>

    <label class="filters__field">
      <span class="filters__label">类型</span>
      <select class="filters__select" :value="typeFilter ?? ''" @change="onType">
        <option value="">全部类型</option>
        <option v-for="type in TASK_TYPES" :key="type" :value="type">
          {{ TASK_TYPE_LABELS[type] }}
        </option>
      </select>
    </label>

    <label class="filters__field">
      <span class="filters__label">显示条数</span>
      <select class="filters__select" :value="limit" @change="onLimit">
        <option v-for="option in TASK_LIMITS" :key="option" :value="option">
          {{ option }}
        </option>
      </select>
    </label>

    <button
      type="button"
      class="filters__refresh"
      :disabled="refreshing"
      @click="emit('refresh')"
    >
      {{ refreshing ? '正在刷新…' : '刷新' }}
    </button>
  </div>
</template>

<style scoped>
.filters {
  display: flex;
  flex-wrap: wrap;
  align-items: flex-end;
  gap: var(--space-3);
}

.filters__field {
  display: flex;
  flex-direction: column;
  gap: var(--space-1);
}

.filters__label {
  font-size: 0.75rem;
  color: var(--color-muted);
}

.filters__select {
  padding: var(--space-1) var(--space-2);
  font: inherit;
  color: inherit;
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-1);
}

.filters__refresh {
  padding: var(--space-2) var(--space-4);
  font: inherit;
  color: inherit;
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-1);
  cursor: pointer;
}

.filters__refresh:disabled {
  opacity: 0.55;
  cursor: not-allowed;
  border-style: dashed;
}
</style>
