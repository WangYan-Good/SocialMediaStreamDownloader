<script setup lang="ts">
import { storeToRefs } from 'pinia'
import { computed, onBeforeUnmount, onMounted } from 'vue'

import DatabaseStatusCard from '@/components/system/DatabaseStatusCard.vue'
import DownloadSettingsCard from '@/components/system/DownloadSettingsCard.vue'
import LoggingSettingsCard from '@/components/system/LoggingSettingsCard.vue'
import RuntimeSettingsCard from '@/components/system/RuntimeSettingsCard.vue'
import SystemNotice from '@/components/system/SystemNotice.vue'
import { formatTimestamp } from '@/utils/time'
import { useSystemStore } from '@/stores/system'

//
// A read-only view of what this server will say about itself.
//
// Every field is rendered by a named component. Nothing here dumps the response
// as json, deliberately: a dump would publish whatever the backend adds next,
// without anybody deciding it belongs on a page.
//
const store = useSystemStore()
const { status, loading, error, hasLoaded, lastUpdatedAt } = storeToRefs(store)

onMounted(() => {
  void store.load()
})

//
// A read still in flight belongs to a screen that no longer exists. Abandoned
// rather than left to write into a store nobody is showing.
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
  <section class="system">
    <header class="system__header">
      <h1 class="system__title">系统</h1>
      <p class="system__hint">
        服务正在响应。以下为可观察的各项状态与当前进程已加载的安全配置摘要。
      </p>
    </header>

    <div class="system__bar">
      <button
        type="button"
        class="system__action"
        :disabled="loading"
        @click="store.load()"
      >
        {{ loading ? '正在刷新…' : '刷新状态' }}
      </button>
      <span v-if="updatedLabel" class="system__muted">{{ updatedLabel }}</span>
    </div>

    <p v-if="error" class="system__notice" role="alert">{{ error }}</p>

    <!--
      Nothing green before there is evidence for it: a first read that failed
      shows the failure, not a page of reassuring badges.
    -->
    <p v-if="!hasLoaded && !error" class="system__placeholder">正在读取系统状态…</p>
    <p v-else-if="!hasLoaded" class="system__placeholder">
      尚未成功读取系统状态，请稍后重试。
    </p>

    <div v-if="status" class="system__grid">
      <DatabaseStatusCard :database="status.database" />
      <RuntimeSettingsCard
        :server="status.settings.server"
        :history="status.settings.history"
      />
      <LoggingSettingsCard :logging="status.settings.logging" />
      <DownloadSettingsCard
        :download="status.settings.download"
        :douyin="status.settings.douyin"
      />
    </div>

    <SystemNotice />
  </section>
</template>

<style scoped>
.system { display: grid; gap: var(--space-4); }
.system__header { margin-bottom: var(--space-1); }
.system__title { margin: 0; font-size: 1.375rem; }
.system__hint { margin: var(--space-1) 0 0; color: var(--color-muted); font-size: 0.8125rem; }
.system__bar { display: flex; flex-wrap: wrap; align-items: center; gap: var(--space-3); }
.system__muted { color: var(--color-muted); font-size: 0.8125rem; }
.system__notice { margin: 0; padding: var(--space-3); background: var(--color-background); border: 1px solid var(--color-border); border-radius: var(--radius-1); font-size: 0.8125rem; }
.system__action { padding: var(--space-2) var(--space-3); font: inherit; font-size: 0.8125rem; color: inherit; background: var(--color-surface); border: 1px solid var(--color-border); border-radius: var(--radius-1); cursor: pointer; }
.system__action:disabled { opacity: 0.55; cursor: not-allowed; border-style: dashed; }
.system__placeholder { margin: 0; padding: var(--space-5); background: var(--color-surface); border: 1px solid var(--color-border); border-radius: var(--radius-2); color: var(--color-muted); text-align: center; }
/* One column on a narrow screen, two when there is room. No second set of
   components for small screens - the same cards simply stack. */
.system__grid { display: grid; gap: var(--space-4); grid-template-columns: 1fr; }
@media (min-width: 60rem) {
  .system__grid { grid-template-columns: repeat(2, minmax(0, 1fr)); }
}
</style>
