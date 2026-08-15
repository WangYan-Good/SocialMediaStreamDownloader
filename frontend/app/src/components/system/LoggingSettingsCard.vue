<script setup lang="ts">
import { enabledLabel, textLabel } from '@/components/system/systemPresentation'
import type { SystemLoggingSettings } from '@/types/system'

defineProps<{ logging: SystemLoggingSettings }>()
</script>

<template>
  <section class="card" aria-labelledby="system-logging-heading">
    <h2 id="system-logging-heading" class="card__title">日志</h2>

    <dl class="facts">
      <div class="facts__row"><dt>日志功能</dt><dd>{{ enabledLabel(logging.enabled) }}</dd></div>
      <div class="facts__row"><dt>级别</dt><dd>{{ textLabel(logging.level) }}</dd></div>
      <div class="facts__row"><dt>持久化</dt><dd>{{ enabledLabel(logging.save_enabled) }}</dd></div>
    </dl>

    <!--
      Stated so nobody goes looking for a viewer that is deliberately absent.
      The log carries urls, creator identities and upstream errors, and this
      project has no redaction contract, no log permission model and no auth
      boundary that would make showing it safe.
    -->
    <p class="card__notice" role="status">
      出于安全边界，本页面不读取或展示日志文件内容，也不显示日志文件位置。
    </p>
  </section>
</template>

<style scoped>
.card { padding: var(--space-4); background: var(--color-surface); border: 1px solid var(--color-border); border-radius: var(--radius-2); }
.card__title { margin: 0 0 var(--space-3); font-size: 1rem; }
.card__notice { margin: var(--space-3) 0 0; padding: var(--space-2) var(--space-3); background: var(--color-background); border: 1px solid var(--color-border); border-radius: var(--radius-1); color: var(--color-muted); font-size: 0.8125rem; line-height: 1.6; }
.facts { margin: 0; display: grid; gap: var(--space-2); }
.facts__row { display: grid; grid-template-columns: 6rem 1fr; gap: var(--space-3); align-items: baseline; }
.facts__row dt { color: var(--color-muted); font-size: 0.8125rem; }
.facts__row dd { margin: 0; font-size: 0.875rem; }
</style>
