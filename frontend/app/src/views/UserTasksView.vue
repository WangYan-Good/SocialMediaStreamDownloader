<script setup lang="ts">
import { storeToRefs } from 'pinia'
import { computed, onBeforeUnmount, onMounted } from 'vue'

import UserTaskDetailPanel from '@/components/tasks/user/UserTaskDetailPanel.vue'
import UserTaskFilters from '@/components/tasks/user/UserTaskFilters.vue'
import UserTaskListTable from '@/components/tasks/user/UserTaskListTable.vue'
import { useTaskStore } from '@/stores/tasks'

//
// The user's view of their own downloads.
//
// The same store, the same api, the same polling loop and the same task model
// as the management screen. What differs is which of it reaches the page: no
// task id, no resolve receipt, no raw metadata, no limit control - and a
// heading about downloads rather than about the service instance holding them.
//
const store = useTaskStore()
const {
  tasks,
  stateFilter,
  selectedTaskId,
  selectedTask,
  refreshing,
  refreshError,
  hasLoaded,
  hasFilters,
} = storeToRefs(store)

//
// The polling loop belongs to this screen, exactly as it belongs to the
// management one - started on arrival and stopped on the way out, so a user
// reading something else is not making a request every three seconds.
//
// The store abandons whatever loop was running when a new one starts, so the
// two views can never leave two schedules alive between them.
//
onMounted(() => {
  void store.startAutoRefresh()
})

onBeforeUnmount(() => {
  store.stopAutoRefresh()
})

//
// A failed read, as a result.
//
// The store keeps its own message - "暂时无法刷新任务列表：<backend message>" -
// and keeps classifying failures exactly as it did. This only decides what
// reaches the screen, because that message can carry a driver or schema detail
// that means nothing to a user.
//
const READ_FAILED = '暂时无法读取任务，请重试。'

//
// Only after a read has actually succeeded. A failed first load knows nothing
// about how many tasks there are, so "还没有下载任务" would be a claim the
// browser is in no position to make.
//
const showEmptyState = computed(
  () => hasLoaded.value && tasks.value.length === 0 && refreshError.value === null,
)
</script>

<template>
  <section class="tasks">
    <header class="tasks__header">
      <h1 class="tasks__title">下载任务</h1>
      <!--
        Accurate about retention without naming it: finished tasks really are
        reclaimed after a while, and a user needs to know an old download may
        not be listed - not what a retention period is.
      -->
      <p class="tasks__hint">
        这里显示正在进行和最近的下载任务，较早的已完成任务可能不再显示。
      </p>
    </header>

    <UserTaskFilters
      :state-filter="stateFilter"
      :refreshing="refreshing"
      @update:state-filter="store.setStateFilter($event)"
      @refresh="store.refresh()"
    />

    <!--
      A failed read says nothing about the tasks themselves, so whatever was
      last seen stays below this banner rather than being replaced by it.
    -->
    <div v-if="refreshError" class="tasks__error" role="alert">
      <span>{{ READ_FAILED }}</span>
      <button type="button" class="tasks__retry" @click="store.retry()">重试</button>
    </div>

    <p v-if="!hasLoaded && !refreshError" class="tasks__placeholder">正在读取任务…</p>

    <p v-else-if="showEmptyState" class="tasks__placeholder">
      {{ hasFilters ? '没有符合条件的任务。' : '还没有下载任务。' }}
    </p>

    <UserTaskListTable
      v-else-if="tasks.length"
      :tasks="tasks"
      :selected-task-id="selectedTaskId"
      @select="store.select($event)"
    />

    <UserTaskDetailPanel
      v-if="selectedTask"
      :task="selectedTask"
      @close="store.clearSelection()"
    />
  </section>
</template>

<style scoped>
.tasks { display: grid; gap: var(--space-4); }
.tasks__header { margin-bottom: var(--space-1); }
.tasks__title { margin: 0; font-size: 1.375rem; }
.tasks__hint { margin: var(--space-1) 0 0; color: var(--color-muted); font-size: 0.8125rem; }
.tasks__error { display: flex; align-items: center; gap: var(--space-3); flex-wrap: wrap; padding: var(--space-3); border: 1px solid var(--color-border); border-radius: var(--radius-1); background: var(--color-background); font-size: 0.8125rem; }
.tasks__retry { padding: 2px var(--space-3); font: inherit; font-size: 0.8125rem; color: inherit; background: var(--color-surface); border: 1px solid var(--color-border); border-radius: var(--radius-1); cursor: pointer; }
.tasks__placeholder { margin: 0; padding: var(--space-5); background: var(--color-surface); border: 1px solid var(--color-border); border-radius: var(--radius-2); color: var(--color-muted); text-align: center; }
</style>
