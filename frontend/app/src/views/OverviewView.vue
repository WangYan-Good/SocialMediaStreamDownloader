<script setup lang="ts">
import { storeToRefs } from 'pinia'
import { computed, onBeforeUnmount, onMounted } from 'vue'

import OverviewStatusCard from '@/components/overview/OverviewStatusCard.vue'
import OverviewStats from '@/components/overview/OverviewStats.vue'
import QuickActionsCard from '@/components/overview/QuickActionsCard.vue'
import RecentContentCard from '@/components/overview/RecentContentCard.vue'
import RecentTasksCard from '@/components/overview/RecentTasksCard.vue'
import { useOverviewStore } from '@/stores/overview'
import { formatTimestamp } from '@/utils/time'

//
// The landing page: a composition of what the other screens already know.
//
// It reads five existing read models and writes nothing. Every action lives on
// the screen that owns it, so this page links rather than acts - which is also
// what keeps it free of the filters, selections and pollers those screens hold.
//
const store = useOverviewStore()
const {
  systemStatus,
  systemError,
  recentTasks,
  taskTotal,
  tasksError,
  creatorTotal,
  creatorsError,
  libraryPostTotal,
  latestPost,
  postsError,
  libraryLiveTotal,
  latestLive,
  livesError,
  loading,
  hasLoaded,
  lastUpdatedAt,
} = storeToRefs(store)

onMounted(() => {
  void store.load()
})

//
// Reads still in flight belong to a screen that no longer exists.
//
onBeforeUnmount(() => {
  store.abandon()
})

const updatedLabel = computed(() =>
  lastUpdatedAt.value === null
    ? ''
    : `最近刷新：${formatTimestamp(lastUpdatedAt.value.toISOString())}`,
)
</script>

<template>
  <section class="overview">
    <header class="overview__header">
      <h1 class="overview__title">总览</h1>
      <p class="overview__hint">
        本机已记录内容与当前服务状态的概览。详细操作请前往对应页面。
      </p>
    </header>

    <div class="overview__bar">
      <button
        type="button"
        class="overview__action"
        :disabled="loading"
        @click="store.load()"
      >
        {{ loading ? '正在刷新…' : '刷新总览' }}
      </button>
      <span v-if="updatedLabel" class="overview__muted">{{ updatedLabel }}</span>
    </div>

    <p v-if="!hasLoaded && loading" class="overview__placeholder">正在读取总览…</p>

    <OverviewStats
      :creator-total="creatorTotal"
      :creators-error="creatorsError"
      :post-total="libraryPostTotal"
      :posts-error="postsError"
      :live-total="libraryLiveTotal"
      :lives-error="livesError"
      :task-total="taskTotal"
      :tasks-error="tasksError"
    />

    <div class="overview__grid">
      <OverviewStatusCard :status="systemStatus" :error="systemError" />
      <RecentTasksCard :tasks="recentTasks" :total="taskTotal" :error="tasksError" />
      <RecentContentCard
        :post="latestPost"
        :post-error="postsError"
        :live="latestLive"
        :live-error="livesError"
      />
      <QuickActionsCard />
    </div>
  </section>
</template>

<style scoped>
.overview { display: grid; gap: var(--space-4); }
.overview__header { margin-bottom: var(--space-1); }
.overview__title { margin: 0; font-size: 1.375rem; }
.overview__hint { margin: var(--space-1) 0 0; color: var(--color-muted); font-size: 0.8125rem; }
.overview__bar { display: flex; flex-wrap: wrap; align-items: center; gap: var(--space-3); }
.overview__muted { color: var(--color-muted); font-size: 0.8125rem; }
.overview__action { padding: var(--space-2) var(--space-3); font: inherit; font-size: 0.8125rem; color: inherit; background: var(--color-surface); border: 1px solid var(--color-border); border-radius: var(--radius-1); cursor: pointer; }
.overview__action:disabled { opacity: 0.55; cursor: not-allowed; border-style: dashed; }
.overview__placeholder { margin: 0; padding: var(--space-5); background: var(--color-surface); border: 1px solid var(--color-border); border-radius: var(--radius-2); color: var(--color-muted); text-align: center; }
/* One column on a narrow screen, two when there is room. The same cards stack;
   there is no second set of components for small screens. */
.overview__grid { display: grid; gap: var(--space-4); grid-template-columns: 1fr; }
@media (min-width: 64rem) {
  .overview__grid { grid-template-columns: repeat(2, minmax(0, 1fr)); }
}
</style>
