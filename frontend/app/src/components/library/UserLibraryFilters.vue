<script setup lang="ts">
import { COMPLETION_LABELS, TYPE_LABELS } from '@/components/library/libraryPresentation'
import type { LibraryPostFilters } from '@/types/library'

//
// Keyword, type, download status and order.
//
// No person filter - that is a management capability and needs the person
// roster loaded, which this screen deliberately never reads. No source filter
// either: whether a record came from the api or the html fallback is a fact
// about how the downloader worked, not about the download.
//
defineProps<{ filters: LibraryPostFilters; loading: boolean }>()

const emit = defineEmits<{ change: [Partial<LibraryPostFilters>]; refresh: [] }>()

function onKeyword(event: Event) {
  const value = (event.target as HTMLInputElement).value.trim()
  emit('change', { q: value || undefined })
}

function onSelect(field: 'aweme_type' | 'completion' | 'sort' | 'order', event: Event) {
  const value = (event.target as HTMLSelectElement).value
  emit('change', { [field]: value || undefined } as Partial<LibraryPostFilters>)
}
</script>

<template>
  <div class="filters">
    <label class="filters__field filters__field--wide">
      <span class="filters__label">关键词</span>
      <!--
        The server still matches the aweme id and the person name as well - the
        query is unchanged. This only stops advertising two fields a user has
        no reason to search by.
      -->
      <input
        class="filters__input"
        type="search"
        :value="filters.q ?? ''"
        placeholder="搜索文案或创作者"
        @change="onKeyword"
      />
    </label>

    <label class="filters__field">
      <span class="filters__label">类型</span>
      <select class="filters__select" :value="filters.aweme_type ?? ''" @change="onSelect('aweme_type', $event)">
        <option value="">全部</option>
        <option v-for="(label, value) in TYPE_LABELS" :key="value" :value="value">{{ label }}</option>
      </select>
    </label>

    <label class="filters__field">
      <span class="filters__label">下载情况</span>
      <select class="filters__select" :value="filters.completion ?? ''" @change="onSelect('completion', $event)">
        <option value="">全部</option>
        <option v-for="(label, value) in COMPLETION_LABELS" :key="value" :value="value">{{ label }}</option>
      </select>
    </label>

    <label class="filters__field">
      <span class="filters__label">排序</span>
      <select class="filters__select" :value="filters.sort ?? 'downloaded_at'" @change="onSelect('sort', $event)">
        <option value="downloaded_at">下载时间</option>
        <option value="create_time">发布时间</option>
        <option value="nickname">创作者</option>
      </select>
    </label>

    <label class="filters__field">
      <span class="filters__label">方向</span>
      <select class="filters__select" :value="filters.order ?? 'desc'" @change="onSelect('order', $event)">
        <option value="desc">从新到旧</option>
        <option value="asc">从旧到新</option>
      </select>
    </label>

    <button type="button" class="filters__action" :disabled="loading" @click="emit('refresh')">
      {{ loading ? '正在读取…' : '刷新' }}
    </button>
  </div>
</template>

<style scoped>
.filters { display: flex; flex-wrap: wrap; align-items: flex-end; gap: var(--space-3); }
.filters__field { display: flex; flex-direction: column; gap: var(--space-1); }
.filters__field--wide { flex: 1 1 18rem; }
.filters__label { font-size: 0.75rem; color: var(--color-muted); }
.filters__input, .filters__select { width: 100%; padding: var(--space-1) var(--space-2); font: inherit; color: inherit; background: var(--color-surface); border: 1px solid var(--color-border); border-radius: var(--radius-1); }
.filters__action { padding: var(--space-2) var(--space-3); font: inherit; font-size: 0.8125rem; color: inherit; background: var(--color-surface); border: 1px solid var(--color-border); border-radius: var(--radius-1); cursor: pointer; }
.filters__action:disabled { opacity: 0.55; cursor: not-allowed; border-style: dashed; }
</style>
