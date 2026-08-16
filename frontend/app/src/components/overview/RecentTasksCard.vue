<script setup lang="ts">
import { RouterLink } from 'vue-router'

import TaskStateBadge from '@/components/tasks/TaskStateBadge.vue'
import {
  TASK_TYPE_LABELS,
  progressText,
  taskDisplayTitle,
} from '@/components/tasks/taskPresentation'
import { formatTimestamp } from '@/utils/time'
import type { Task } from '@/types/task'

//
// A snapshot of the newest few, read once. Watching a task as it runs is the
// task centre's job and costs a poller; duplicating it here would mean two
// screens polling the same record with two different ideas of what it says.
//
defineProps<{ tasks: Task[]; total: number | null; error: string | null }>()
</script>

<template>
  <section class="card" aria-labelledby="overview-tasks-heading">
    <div class="card__head">
      <h2 id="overview-tasks-heading" class="card__title">最近任务</h2>
      <RouterLink class="card__link" :to="{ name: 'tasks' }">前往任务中心</RouterLink>
    </div>

    <p v-if="error" class="card__notice" role="status">{{ error }}</p>
    <p v-else-if="!tasks.length" class="card__muted">当前进程还没有任务记录。</p>

    <ul v-else class="rows">
      <li v-for="one in tasks" :key="one.task_id" class="rows__row">
        <span class="rows__title">{{ taskDisplayTitle(one.title, one.task_type) }}</span>
        <span class="rows__muted">{{ TASK_TYPE_LABELS[one.task_type] }}</span>
        <TaskStateBadge :state="one.state" />
        <span class="rows__muted">{{ progressText(one.progress.current, one.progress.total) }}</span>
        <span class="rows__muted">{{ formatTimestamp(one.created_at) }}</span>
      </li>
    </ul>

    <p v-if="total !== null && !error" class="card__muted">
      当前进程共 {{ total }} 条任务记录。
    </p>
  </section>
</template>

<style scoped>
.card { padding: var(--space-4); background: var(--color-surface); border: 1px solid var(--color-border); border-radius: var(--radius-2); }
.card__head { display: flex; flex-wrap: wrap; align-items: baseline; gap: var(--space-3); margin-bottom: var(--space-3); }
.card__title { margin: 0; font-size: 1rem; }
.card__link { margin-left: auto; color: var(--color-accent); text-decoration: underline; font-size: 0.8125rem; }
.card__notice { margin: 0; padding: var(--space-2) var(--space-3); background: var(--color-background); border: 1px solid var(--color-border); border-radius: var(--radius-1); font-size: 0.8125rem; }
.card__muted { margin: var(--space-2) 0 0; color: var(--color-muted); font-size: 0.8125rem; }
.rows { list-style: none; margin: 0; padding: 0; display: grid; gap: var(--space-1); }
.rows__row { display: flex; flex-wrap: wrap; align-items: center; gap: var(--space-3); padding: var(--space-1) 0; border-bottom: 1px solid var(--color-border); font-size: 0.8125rem; }
.rows__title { max-width: 16rem; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.rows__muted { color: var(--color-muted); }
</style>
