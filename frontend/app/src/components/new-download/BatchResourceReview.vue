<script setup lang="ts">
import { RouterLink } from 'vue-router'

import type { BatchReviewItem } from '@/composables/useBatchDownloadFlow'

defineProps<{
  items: BatchReviewItem[]
  canCreate: boolean
  creating: boolean
  selectedCount: number
  createdCount: number
}>()

const emit = defineEmits<{
  select: [number, boolean]
  confirmOwner: [number, boolean]
  create: []
}>()

const LABELS = { post: '作品', live: '直播', owner: '主播全部作品' } as const

function checked(event: Event): boolean {
  return (event.target as HTMLInputElement).checked
}
</script>

<template>
  <section class="batch-review card">
    <div class="card__head">
      <div>
        <h2 class="card__title">检查并选择</h2>
        <p class="card__hint">每个成功项都有独立解析凭证，并会创建独立普通任务。</p>
      </div>
      <span class="card__count">{{ items.length }} 项</span>
    </div>

    <ol class="batch-review__list">
      <li v-for="item in items" :key="item.index" class="batch-review__item">
        <template v-if="item.status === 'failed'">
          <div>
            <strong>第 {{ item.index + 1 }} 个链接解析失败</strong>
            <p class="batch-review__muted">{{ item.error.message }}</p>
          </div>
        </template>
        <template v-else>
          <label class="batch-review__choice">
            <input
              type="checkbox"
              :checked="item.selected"
              :disabled="creating || item.createState === 'created'"
              @change="emit('select', item.index, checked($event))"
            />
            <span>
              第 {{ item.index + 1 }} 项 · {{ item.resolution.platform }} ·
              {{ LABELS[item.resolution.resource_type] }}
            </span>
          </label>
          <p class="batch-review__identity">
            <template v-if="item.resolution.resource_type === 'post'">
              作品 ID {{ item.resolution.identity.aweme_id }}
            </template>
            <template v-else-if="item.resolution.resource_type === 'owner'">
              主播 ID {{ item.resolution.identity.sec_user_id }}
            </template>
            <template v-else>直播资源</template>
          </p>
          <label
            v-if="item.selected && item.resolution.resource_type === 'owner'"
            class="batch-review__confirm"
          >
            <input
              type="checkbox"
              :checked="item.ownerConfirmed"
              :disabled="creating"
              @change="emit('confirmOwner', item.index, checked($event))"
            />
            <span>我确认下载该账号的全部作品</span>
          </label>
          <p v-if="item.createState === 'created'" class="batch-review__result">
            已创建任务 {{ item.taskId }}
          </p>
          <p v-else-if="item.createState === 'failed'" class="batch-review__error" role="alert">
            {{ item.createError }}
          </p>
          <p v-else-if="item.createState === 'creating'" class="batch-review__muted">
            正在创建该项…
          </p>
        </template>
      </li>
    </ol>

    <div class="batch-review__actions">
      <button
        type="button"
        class="batch-review__create button button--primary"
        :disabled="!canCreate || creating"
        @click="emit('create')"
      >
        {{ creating ? '正在逐项创建…' : `创建选中任务（${selectedCount}）` }}
      </button>
      <span v-if="createdCount" class="batch-review__result">已创建 {{ createdCount }} 个任务</span>
      <RouterLink v-if="createdCount" class="batch-review__task-link" :to="{ name: 'tasks' }">
        前往任务中心
      </RouterLink>
    </div>
  </section>
</template>

<style scoped>
.card { padding: var(--space-4); background: var(--color-surface); border: 1px solid var(--color-border); border-radius: var(--radius-2); }
.card__head { display: flex; justify-content: space-between; gap: var(--space-3); }
.card__title { margin: 0; font-size: 1rem; }
.card__hint, .card__count, .batch-review__muted, .batch-review__identity { color: var(--color-muted); font-size: 0.8125rem; }
.card__hint { margin: var(--space-1) 0 0; }
.batch-review__list { display: grid; gap: var(--space-2); margin: var(--space-4) 0; padding: 0; list-style: none; }
.batch-review__item { padding: var(--space-3); background: var(--color-background); border: 1px solid var(--color-border); border-radius: var(--radius-1); }
.batch-review__choice, .batch-review__confirm { display: flex; align-items: flex-start; gap: var(--space-2); font-size: 0.875rem; }
.batch-review__identity, .batch-review__muted, .batch-review__result, .batch-review__error { margin: var(--space-1) 0 0 calc(13px + var(--space-2)); }
.batch-review__confirm { margin: var(--space-2) 0 0 calc(13px + var(--space-2)); }
.batch-review__result, .batch-review__error { font-size: 0.8125rem; }
.batch-review__error { color: #a12a2a; }
.batch-review__actions { display: flex; align-items: center; flex-wrap: wrap; gap: var(--space-3); }
.button { padding: var(--space-2) var(--space-4); font: inherit; border: 1px solid var(--color-border); border-radius: var(--radius-1); cursor: pointer; }
.button--primary { color: #fff; background: var(--color-accent); border-color: var(--color-accent); }
.button:disabled { opacity: 0.55; cursor: not-allowed; }
.batch-review__task-link { color: var(--color-accent); font-size: 0.8125rem; text-decoration: underline; }
</style>
