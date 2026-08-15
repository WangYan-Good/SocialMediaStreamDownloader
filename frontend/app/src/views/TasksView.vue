<script setup lang="ts">
import { storeToRefs } from 'pinia'
import { computed, onBeforeUnmount, onMounted } from 'vue'

import TaskDetailPanel from '@/components/tasks/TaskDetailPanel.vue'
import TaskFilters from '@/components/tasks/TaskFilters.vue'
import TaskListTable from '@/components/tasks/TaskListTable.vue'
import { formatTaskTime } from '@/components/tasks/taskPresentation'
import { useTaskStore } from '@/stores/tasks'

const store = useTaskStore()
const {
  tasks,
  total,
  stateFilter,
  typeFilter,
  limit,
  selectedTaskId,
  selectedTask,
  refreshing,
  refreshError,
  lastUpdatedAt,
  hasLoaded,
  hasFilters,
  isTruncated,
} = storeToRefs(store)

//
// The polling loop belongs to this screen, not to the application.
//
// Started here and stopped here so a user sitting on Creators is not making a
// request every three seconds for a list nothing is showing. A sidebar badge or
// an overview widget would change that, and each would need its own decision
// about the cost.
//
onMounted(() => {
  void store.startAutoRefresh()
})

onBeforeUnmount(() => {
  store.stopAutoRefresh()
})

const countLabel = computed(() => {
  if (!hasLoaded.value) {
    return ''
  }
  //
  // No page numbers: the api takes a limit and has no offset, so "page 1 of 2"
  // would be a control that cannot go anywhere.
  //
  return isTruncated.value
    ? `显示最新 ${tasks.value.length} 条，共 ${total.value} 条`
    : `共 ${total.value} 条`
})

const showEmptyState = computed(
  //
  // Only after a read has actually succeeded. A failed first load knows nothing
  // about how many tasks there are, and saying "no tasks" would be a claim the
  // browser is in no position to make.
  () => hasLoaded.value && tasks.value.length === 0 && refreshError.value === null,
)
</script>

<template>
  <section class="tasks">
    <header class="tasks__header">
      <h1 class="tasks__title">任务中心</h1>
      <p class="tasks__hint">
        显示当前服务实例中的任务；已结束的任务会在保留期后自动移除。
      </p>
    </header>

    <TaskFilters
      :state-filter="stateFilter"
      :type-filter="typeFilter"
      :limit="limit"
      :refreshing="refreshing"
      @update:state-filter="store.setStateFilter($event)"
      @update:type-filter="store.setTypeFilter($event)"
      @update:limit="store.setLimit($event)"
      @refresh="store.refresh()"
    />

    <p class="tasks__status" role="status">
      <span v-if="countLabel">{{ countLabel }}</span>
      <span v-if="lastUpdatedAt" class="tasks__updated">
        最后更新 {{ formatTaskTime(lastUpdatedAt.toISOString()) }}
      </span>
    </p>

    <!--
      A failed read says nothing about the tasks themselves, so whatever was
      last seen stays below this banner rather than being replaced by it.
    -->
    <div v-if="refreshError" class="tasks__error" role="alert">
      <span>{{ refreshError }}</span>
      <button type="button" class="tasks__retry" @click="store.retry()">重试</button>
    </div>

    <p v-if="!hasLoaded && !refreshError" class="tasks__placeholder">正在读取任务…</p>

    <p v-else-if="showEmptyState" class="tasks__placeholder">
      {{ hasFilters ? '当前没有符合条件的任务，可以调整筛选条件。' : '当前没有任务。' }}
    </p>

    <TaskListTable
      v-else-if="tasks.length"
      :tasks="tasks"
      :selected-task-id="selectedTaskId"
      @select="store.select($event)"
    />

    <TaskDetailPanel
      v-if="selectedTask"
      :task="selectedTask"
      @close="store.clearSelection()"
    />
  </section>
</template>

<style scoped>
.tasks {
  display: grid;
  gap: var(--space-4);
}

.tasks__header {
  margin-bottom: var(--space-1);
}

.tasks__title {
  margin: 0;
  font-size: 1.375rem;
}

.tasks__hint {
  margin: var(--space-1) 0 0;
  color: var(--color-muted);
  font-size: 0.8125rem;
}

.tasks__status {
  display: flex;
  gap: var(--space-4);
  margin: 0;
  color: var(--color-muted);
  font-size: 0.8125rem;
}

.tasks__updated {
  color: var(--color-muted);
}

.tasks__error {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  flex-wrap: wrap;
  padding: var(--space-3);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-1);
  background: var(--color-background);
  font-size: 0.8125rem;
}

.tasks__retry {
  padding: 2px var(--space-3);
  font: inherit;
  font-size: 0.8125rem;
  color: inherit;
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-1);
  cursor: pointer;
}

.tasks__placeholder {
  margin: 0;
  padding: var(--space-5);
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-2);
  color: var(--color-muted);
  text-align: center;
}
</style>
