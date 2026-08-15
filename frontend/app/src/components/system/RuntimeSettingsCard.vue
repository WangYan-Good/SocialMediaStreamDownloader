<script setup lang="ts">
import { numberLabel, switchLabel } from '@/components/system/systemPresentation'
import type { SystemHistorySettings, SystemServerSettings } from '@/types/system'

defineProps<{ server: SystemServerSettings; history: SystemHistorySettings }>()
</script>

<template>
  <section class="card" aria-labelledby="system-runtime-heading">
    <h2 id="system-runtime-heading" class="card__title">运行设置</h2>

    <dl class="facts">
      <!--
        The bind host and port are not here, and not in the api either: where
        this process listens is infrastructure, and one of the few things worth
        not publishing on a page anybody can open.
      -->
      <div class="facts__row">
        <dt>Debug 模式</dt>
        <dd>{{ switchLabel(server.debug_mode) }}</dd>
      </div>
      <div class="facts__row">
        <dt>历史每页上限</dt>
        <dd>{{ numberLabel(history.page_size_limit) }}</dd>
      </div>
    </dl>

    <!--
      A configuration note, not a debugger. Nothing here prints a traceback or
      turns anything on - it says what the loaded configuration is.
    -->
    <p v-if="server.debug_mode === true" class="card__warning" role="status">
      当前启用了 Debug 模式，不建议用于正式对外环境。
    </p>
  </section>
</template>

<style scoped>
.card { padding: var(--space-4); background: var(--color-surface); border: 1px solid var(--color-border); border-radius: var(--radius-2); }
.card__title { margin: 0 0 var(--space-3); font-size: 1rem; }
.card__warning { margin: var(--space-3) 0 0; padding: var(--space-2) var(--space-3); background: var(--color-background); border: 1px solid #e6a9a9; border-radius: var(--radius-1); color: #a12a2a; font-size: 0.8125rem; line-height: 1.6; }
.facts { margin: 0; display: grid; gap: var(--space-2); }
.facts__row { display: grid; grid-template-columns: 8rem 1fr; gap: var(--space-3); align-items: baseline; }
.facts__row dt { color: var(--color-muted); font-size: 0.8125rem; }
.facts__row dd { margin: 0; font-size: 0.875rem; }
</style>
