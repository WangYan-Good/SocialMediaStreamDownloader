<script setup lang="ts">
import { COMPLETION_LABELS, SOURCE_LABELS, TYPE_LABELS } from '@/components/library/libraryPresentation'
import type { LibraryPostFilters } from '@/types/library'
import type { PersonSummaryItem } from '@/types/person'

defineProps<{
  filters: LibraryPostFilters
  people: PersonSummaryItem[]
  peopleError: string | null
  loading: boolean
}>()

const emit = defineEmits<{ change: [Partial<LibraryPostFilters>]; refresh: [] }>()

function onKeyword(event: Event) {
  const value = (event.target as HTMLInputElement).value.trim()
  emit('change', { q: value || undefined })
}

function onPerson(event: Event) {
  const value = (event.target as HTMLSelectElement).value
  emit('change', { person_id: value ? Number(value) : undefined })
}

function onSelect(field: 'aweme_type' | 'completion' | 'source' | 'sort' | 'order', event: Event) {
  const value = (event.target as HTMLSelectElement).value
  emit('change', { [field]: value || undefined } as Partial<LibraryPostFilters>)
}

function onPageSize(event: Event) {
  const value = Number((event.target as HTMLSelectElement).value)
  emit('change', { page_size: value })
}
</script>

<template>
  <div class="filters">
    <label class="filters__field filters__field--wide">
      <span class="filters__label">关键词</span>
      <input
        class="filters__input"
        type="search"
        :value="filters.q ?? ''"
        placeholder="作品 ID、文案、创作者或人物"
        @change="onKeyword"
      />
    </label>

    <label class="filters__field">
      <span class="filters__label">人物</span>
      <select class="filters__select" :value="filters.person_id ?? ''" @change="onPerson">
        <option value="">全部</option>
        <option v-for="one in people" :key="one.person_id" :value="one.person_id">
          {{ one.display_name }}
        </option>
      </select>
      <!--
        A convenience that failed. The index itself is unaffected, and saying so
        here is better than an empty dropdown that looks like "no people exist".
      -->
      <span v-if="peopleError" class="filters__hint">{{ peopleError }}</span>
    </label>

    <label class="filters__field">
      <span class="filters__label">类型</span>
      <select class="filters__select" :value="filters.aweme_type ?? ''" @change="onSelect('aweme_type', $event)">
        <option value="">全部</option>
        <option v-for="(label, value) in TYPE_LABELS" :key="value" :value="value">{{ label }}</option>
      </select>
    </label>

    <label class="filters__field">
      <span class="filters__label">下载记录</span>
      <select class="filters__select" :value="filters.completion ?? ''" @change="onSelect('completion', $event)">
        <option value="">全部</option>
        <option v-for="(label, value) in COMPLETION_LABELS" :key="value" :value="value">{{ label }}</option>
      </select>
    </label>

    <label class="filters__field">
      <span class="filters__label">来源</span>
      <select class="filters__select" :value="filters.source ?? ''" @change="onSelect('source', $event)">
        <option value="">全部</option>
        <option v-for="(label, value) in SOURCE_LABELS" :key="value" :value="value">{{ label }}</option>
      </select>
    </label>

    <label class="filters__field">
      <span class="filters__label">排序</span>
      <select class="filters__select" :value="filters.sort ?? 'downloaded_at'" @change="onSelect('sort', $event)">
        <option value="downloaded_at">下载时间</option>
        <option value="create_time">发布时间</option>
        <option value="nickname">创作者</option>
        <option value="aweme_id">作品 ID</option>
      </select>
    </label>

    <label class="filters__field">
      <span class="filters__label">方向</span>
      <select class="filters__select" :value="filters.order ?? 'desc'" @change="onSelect('order', $event)">
        <option value="desc">降序</option>
        <option value="asc">升序</option>
      </select>
    </label>

    <label class="filters__field">
      <span class="filters__label">每页</span>
      <select class="filters__select" :value="String(filters.page_size ?? 25)" @change="onPageSize">
        <option value="25">25</option>
        <option value="50">50</option>
        <option value="100">100</option>
      </select>
    </label>

    <button type="button" class="filters__action" :disabled="loading" @click="emit('refresh')">
      {{ loading ? '正在读取…' : '刷新' }}
    </button>
  </div>
</template>

<style scoped>
.filters { display: flex; flex-wrap: wrap; align-items: flex-end; gap: var(--space-3); padding: var(--space-3); background: var(--color-surface); border: 1px solid var(--color-border); border-radius: var(--radius-2); }
.filters__field { display: flex; flex-direction: column; gap: var(--space-1); }
.filters__field--wide { flex: 1 1 16rem; }
.filters__label { font-size: 0.75rem; color: var(--color-muted); }
.filters__hint { font-size: 0.6875rem; color: var(--color-muted); }
.filters__input, .filters__select { width: 100%; padding: var(--space-1) var(--space-2); font: inherit; color: inherit; background: var(--color-background); border: 1px solid var(--color-border); border-radius: var(--radius-1); }
.filters__action { padding: var(--space-2) var(--space-3); font: inherit; font-size: 0.8125rem; color: inherit; background: var(--color-surface); border: 1px solid var(--color-border); border-radius: var(--radius-1); cursor: pointer; }
.filters__action:disabled { opacity: 0.55; cursor: not-allowed; border-style: dashed; }
</style>
