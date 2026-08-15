<script setup lang="ts">
import TaskProgress from '@/components/tasks/TaskProgress.vue'
import TaskStateBadge from '@/components/tasks/TaskStateBadge.vue'
import {
  TASK_TYPE_LABELS,
  formatTaskTime,
  taskDisplayTitle,
} from '@/components/tasks/taskPresentation'
import type { Task } from '@/types/task'

defineProps<{
  tasks: Task[]
  selectedTaskId: string | null
}>()

defineEmits<{ select: [string] }>()
</script>

<template>
  <div class="table-scroll">
    <table class="table">
      <caption class="table__caption">
        当前服务实例中的任务，按创建时间从新到旧排列
      </caption>
      <thead>
        <tr>
          <th scope="col">状态</th>
          <th scope="col">类型</th>
          <th scope="col">标题</th>
          <th scope="col">进度</th>
          <th scope="col">说明</th>
          <th scope="col">创建时间</th>
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
          <td>{{ TASK_TYPE_LABELS[task.task_type] }}</td>
          <td class="table__title">{{ taskDisplayTitle(task.title, task.task_type) }}</td>
          <td><TaskProgress :progress="task.progress" /></td>
          <td class="table__message">{{ task.message ?? '—' }}</td>
          <td class="table__time">{{ formatTaskTime(task.created_at) }}</td>
          <td>
            <!--
              A real button rather than a click handler on the row: a row is not
              focusable, cannot be reached by keyboard, and gives a screen
              reader nothing to announce as an action.
            -->
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
/* Narrow screens scroll the table rather than getting a second implementation. */
.table-scroll {
  overflow-x: auto;
}

.table {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.875rem;
}

.table__caption {
  padding-bottom: var(--space-2);
  color: var(--color-muted);
  font-size: 0.8125rem;
  text-align: left;
}

.table th,
.table td {
  padding: var(--space-2) var(--space-3);
  border-bottom: 1px solid var(--color-border);
  text-align: left;
  vertical-align: middle;
  white-space: nowrap;
}

.table th {
  color: var(--color-muted);
  font-size: 0.75rem;
  font-weight: 600;
}

.table__row--selected {
  background: var(--color-accent-soft);
}

.table__title,
.table__message {
  max-width: 18rem;
  overflow: hidden;
  text-overflow: ellipsis;
}

.table__time {
  color: var(--color-muted);
  font-size: 0.8125rem;
}

.table__view {
  padding: 2px var(--space-3);
  font: inherit;
  font-size: 0.8125rem;
  color: inherit;
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-1);
  cursor: pointer;
}
</style>
