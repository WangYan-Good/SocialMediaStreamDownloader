<script setup lang="ts">
import { RouterLink } from 'vue-router'

import {
  DATABASE_STATE_LABELS,
  DATABASE_STATE_TONES,
} from '@/components/system/systemPresentation'
import type { SystemStatus } from '@/types/system'

defineProps<{ status: SystemStatus | null; error: string | null }>()
</script>

<template>
  <section class="card" aria-labelledby="overview-status-heading">
    <h2 id="overview-status-heading" class="card__title">服务状态</h2>

    <!--
      That this page rendered at all is the evidence the http application is
      answering. Deliberately not "all systems healthy": nothing here checked
      the platform, the filesystem or any worker, and a green summary built on
      one successful request would be claiming more than was measured.
    -->
    <p class="card__line">服务正在响应。</p>

    <p v-if="error" class="card__notice" role="status">{{ error }}</p>

    <dl v-else-if="status" class="facts">
      <div class="facts__row">
        <dt>数据库</dt>
        <dd>
          <span class="badge" :class="`badge--${DATABASE_STATE_TONES[status.database.state]}`">
            {{ DATABASE_STATE_LABELS[status.database.state] }}
          </span>
        </dd>
      </div>
      <div class="facts__row"><dt>说明</dt><dd>{{ status.database.message }}</dd></div>
    </dl>

    <p v-if="status?.settings.server.debug_mode === true" class="card__warning" role="status">
      当前启用了 Debug 模式，不建议用于正式对外环境。
    </p>
    <p v-if="status?.settings.download.test_mode === true" class="card__warning" role="status">
      当前为测试模式，下载行为可能与正常模式不同。
    </p>

    <!--
      The full configuration summary lives on the system page. Copying it here
      would be two places to keep in step for no gain.
    -->
    <RouterLink class="card__link" :to="{ name: 'system' }">查看系统详情</RouterLink>
  </section>
</template>

<style scoped>
.card { padding: var(--space-4); background: var(--color-surface); border: 1px solid var(--color-border); border-radius: var(--radius-2); }
.card__title { margin: 0 0 var(--space-2); font-size: 1rem; }
.card__line { margin: 0 0 var(--space-3); font-size: 0.875rem; }
.card__notice { margin: 0 0 var(--space-3); padding: var(--space-2) var(--space-3); background: var(--color-background); border: 1px solid var(--color-border); border-radius: var(--radius-1); font-size: 0.8125rem; }
.card__warning { margin: var(--space-2) 0 0; padding: var(--space-2) var(--space-3); background: var(--color-background); border: 1px solid #e6a9a9; border-radius: var(--radius-1); color: #a12a2a; font-size: 0.8125rem; }
.card__link { display: inline-block; margin-top: var(--space-3); color: var(--color-accent); text-decoration: underline; font-size: 0.8125rem; }
.facts { margin: 0; display: grid; gap: var(--space-2); }
.facts__row { display: grid; grid-template-columns: 5rem 1fr; gap: var(--space-3); align-items: baseline; }
.facts__row dt { color: var(--color-muted); font-size: 0.8125rem; }
.facts__row dd { margin: 0; font-size: 0.875rem; }
.badge { display: inline-block; padding: 1px var(--space-2); border: 1px solid var(--color-border); border-radius: var(--radius-1); font-size: 0.8125rem; }
.badge--ok { border-color: #2f7a4d; color: #2f7a4d; }
.badge--bad { border-color: #a12a2a; color: #a12a2a; }
.badge--muted { color: var(--color-muted); }
</style>
