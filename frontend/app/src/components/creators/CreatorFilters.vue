<script setup lang="ts">
import {
  HISTORY_ORDERS,
  HISTORY_SORTS,
  LAST_LIVE_WINDOWS,
  USER_STATUSES,
} from '@/types/history'
import type { HistoryFilters } from '@/types/history'

defineProps<{ filters: HistoryFilters; loading: boolean }>()

const emit = defineEmits<{ change: [Partial<HistoryFilters>]; refresh: [] }>()

const SORT_LABELS: Record<string, string> = {
  last_checked_at: '最后检查时间',
  score: '评分',
  actived_count: '开播次数',
  nickname: '昵称',
}

const WINDOW_LABELS: Record<string, string> = {
  '1h': '1 小时内',
  '24h': '24 小时内',
  '7d': '7 天内',
  '30d': '30 天内',
  never: '从未开播',
}

function onText(event: Event) {
  const value = (event.target as HTMLInputElement).value.trim()
  emit('change', { q: value || undefined })
}

function onSelect(field: keyof HistoryFilters, event: Event) {
  const value = (event.target as HTMLSelectElement).value
  emit('change', { [field]: value === '' ? undefined : value } as Partial<HistoryFilters>)
}

function onFavorite(event: Event) {
  const value = (event.target as HTMLSelectElement).value
  //
  // Three states, not two: "all", "only favourites" and "only non-favourites".
  // `false` is a real filter here and must not collapse into "unset".
  //
  emit('change', { favorite: value === '' ? undefined : value === 'true' })
}
</script>

<template>
  <div class="filters">
    <label class="filters__field filters__field--wide">
      <span class="filters__label">搜索</span>
      <input
        class="filters__input"
        type="search"
        :value="filters.q ?? ''"
        placeholder="昵称或目录名"
        @change="onText"
      />
    </label>

    <label class="filters__field">
      <span class="filters__label">收藏</span>
      <select
        class="filters__select"
        :value="filters.favorite === undefined ? '' : String(filters.favorite)"
        @change="onFavorite"
      >
        <option value="">全部</option>
        <option value="true">仅收藏</option>
        <option value="false">未收藏</option>
      </select>
    </label>

    <label class="filters__field">
      <span class="filters__label">最近开播</span>
      <select
        class="filters__select"
        :value="filters.last_live_within ?? ''"
        @change="onSelect('last_live_within', $event)"
      >
        <option value="">不限</option>
        <option v-for="window in LAST_LIVE_WINDOWS" :key="window" :value="window">
          {{ WINDOW_LABELS[window] }}
        </option>
      </select>
    </label>

    <label class="filters__field">
      <span class="filters__label">账号状态</span>
      <select
        class="filters__select"
        :value="filters.user_status ?? ''"
        @change="onSelect('user_status', $event)"
      >
        <option value="">全部</option>
        <option v-for="status in USER_STATUSES" :key="status" :value="status">
          {{ status }}
        </option>
      </select>
    </label>

    <label class="filters__field">
      <span class="filters__label">排序</span>
      <select
        class="filters__select"
        :value="filters.sort ?? 'last_checked_at'"
        @change="onSelect('sort', $event)"
      >
        <option v-for="sort in HISTORY_SORTS" :key="sort" :value="sort">
          {{ SORT_LABELS[sort] }}
        </option>
      </select>
    </label>

    <label class="filters__field">
      <span class="filters__label">方向</span>
      <select
        class="filters__select"
        :value="filters.order ?? 'desc'"
        @change="onSelect('order', $event)"
      >
        <option v-for="order in HISTORY_ORDERS" :key="order" :value="order">
          {{ order === 'desc' ? '降序' : '升序' }}
        </option>
      </select>
    </label>

    <button
      type="button"
      class="filters__refresh"
      :disabled="loading"
      @click="emit('refresh')"
    >
      {{ loading ? '正在读取…' : '刷新' }}
    </button>
  </div>
</template>

<style scoped>
.filters {
  display: flex;
  flex-wrap: wrap;
  align-items: flex-end;
  gap: var(--space-3);
}

.filters__field {
  display: flex;
  flex-direction: column;
  gap: var(--space-1);
}

.filters__field--wide {
  flex: 1 1 12rem;
}

.filters__label {
  font-size: 0.75rem;
  color: var(--color-muted);
}

.filters__input,
.filters__select {
  padding: var(--space-1) var(--space-2);
  font: inherit;
  color: inherit;
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-1);
}

.filters__input {
  width: 100%;
}

.filters__refresh {
  padding: var(--space-2) var(--space-4);
  font: inherit;
  color: inherit;
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-1);
  cursor: pointer;
}

.filters__refresh:disabled {
  opacity: 0.55;
  cursor: not-allowed;
  border-style: dashed;
}
</style>
