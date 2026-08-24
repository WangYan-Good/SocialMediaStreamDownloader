<script setup lang="ts">
import TaskProgress from '@/components/tasks/TaskProgress.vue'
import TaskStateBadge from '@/components/tasks/TaskStateBadge.vue'
import {
  TASK_TYPE_LABELS,
  formatTaskTime,
  taskDisplayTitle,
} from '@/components/tasks/taskPresentation'
import { taskNote } from '@/components/tasks/user/userTaskPresentation'
import type { Task } from '@/types/task'

//
// The same rows the management table renders, without the task id column and
// without a caption about service instances. State, progress and the task's
// own note are reused unchanged - they are already the user-facing half.
//
defineProps<{
  tasks: Task[]
  selectedTaskId: string | null
}>()

defineEmits<{ select: [string] }>()
</script>

<template>
  <div class="table-scroll">
    <table class="table">
      <thead>
        <tr>
          <th scope="col">状态</th>
          <th scope="col">内容</th>
          <th scope="col">类型</th>
          <th scope="col">进度</th>
          <th scope="col">说明</th>
          <th scope="col">开始时间</th>
          <th scope="col">操作</th>
        </tr>
      </thead>
      <tbody>
        <tr
          v-for="task in tasks"
          :key="task.task_id"
          :class="{ 'table__row--selected': task.task_id === selectedTaskId }"
        >
          <td><TaskStateBadge :state="task.state" /></td>
          <td class="table__title">{{ taskDisplayTitle(task.title, task.task_type) }}</td>
          <td>{{ TASK_TYPE_LABELS[task.task_type] }}</td>
          <td><TaskProgress :progress="task.progress" /></td>
          <td class="table__message">{{ taskNote(task.message) ?? '—' }}</td>
          <td class="table__time">{{ formatTaskTime(task.started_at ?? task.created_at) }}</td>
          <td>
            <button type="button" class="table__view" @click="$emit('select', task.task_id)">
              查看
            </button>
          </td>
        </tr>
      </tbody>
    </table>
  </div>
</template>

<style scoped>
.table-scroll { overflow-x: auto; }
.table { width: 100%; border-collapse: collapse; font-size: 0.875rem; }
.table th, .table td { padding: var(--space-2) var(--space-3); border-bottom: 1px solid var(--color-border); text-align: left; white-space: nowrap; }
.table th { color: var(--color-muted); font-size: 0.75rem; font-weight: 600; }
.table__row--selected { background: var(--color-accent-soft); }
.table__title { max-width: 18rem; overflow: hidden; text-overflow: ellipsis; }
.table__message { max-width: 16rem; overflow: hidden; text-overflow: ellipsis; color: var(--color-muted); }
.table__time { color: var(--color-muted); font-size: 0.8125rem; }
.table__view { padding: 2px var(--space-3); font: inherit; font-size: 0.8125rem; color: inherit; background: var(--color-surface); border: 1px solid var(--color-border); border-radius: var(--radius-1); cursor: pointer; }
</style>
