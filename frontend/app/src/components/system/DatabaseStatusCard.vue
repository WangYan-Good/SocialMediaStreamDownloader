<script setup lang="ts">
import {
  DATABASE_STATE_LABELS,
  DATABASE_STATE_TONES,
  enabledLabel,
} from '@/components/system/systemPresentation'
import type { SystemDatabaseStatus } from '@/types/system'

defineProps<{ database: SystemDatabaseStatus }>()
</script>

<template>
  <section class="card" aria-labelledby="system-database-heading">
    <h2 id="system-database-heading" class="card__title">数据库</h2>

    <dl class="facts">
      <div class="facts__row">
        <dt>数据库功能</dt>
        <dd>{{ enabledLabel(database.enabled) }}</dd>
      </div>
      <div class="facts__row">
        <dt>Schema 状态</dt>
        <dd>
          <!--
            The word is the signal. Colour is added on top of it, never instead
            of it, so the state survives a monochrome screen or a reader who
            cannot distinguish the tones.
          -->
          <span class="badge" :class="`badge--${DATABASE_STATE_TONES[database.state]}`">
            {{ DATABASE_STATE_LABELS[database.state] }}
          </span>
        </dd>
      </div>
      <div class="facts__row">
        <dt>写入</dt>
        <dd>{{ database.write_ready ? '可用' : '不可用' }}</dd>
      </div>
      <div class="facts__row">
        <dt>说明</dt>
        <dd>{{ database.message }}</dd>
      </div>
    </dl>

    <!--
      Said plainly rather than left for the user to work out: every screen that
      reads history, people or the library goes through this database.
    -->
    <p v-if="database.state !== 'ready'" class="card__notice" role="status">
      数据库当前不是就绪状态，创作者、人物与媒体库等依赖数据库的功能可能受影响。
    </p>
  </section>
</template>

<style scoped>
.card { padding: var(--space-4); background: var(--color-surface); border: 1px solid var(--color-border); border-radius: var(--radius-2); }
.card__title { margin: 0 0 var(--space-3); font-size: 1rem; }
.card__notice { margin: var(--space-3) 0 0; padding: var(--space-2) var(--space-3); background: var(--color-background); border: 1px solid var(--color-border); border-radius: var(--radius-1); color: var(--color-muted); font-size: 0.8125rem; line-height: 1.6; }
.facts { margin: 0; display: grid; gap: var(--space-2); }
.facts__row { display: grid; grid-template-columns: 7rem 1fr; gap: var(--space-3); align-items: baseline; }
.facts__row dt { color: var(--color-muted); font-size: 0.8125rem; }
.facts__row dd { margin: 0; font-size: 0.875rem; overflow-wrap: anywhere; }
.badge { display: inline-block; padding: 1px var(--space-2); border: 1px solid var(--color-border); border-radius: var(--radius-1); font-size: 0.8125rem; }
.badge--ok { border-color: #2f7a4d; color: #2f7a4d; }
.badge--bad { border-color: #a12a2a; color: #a12a2a; }
.badge--muted { color: var(--color-muted); }
</style>
