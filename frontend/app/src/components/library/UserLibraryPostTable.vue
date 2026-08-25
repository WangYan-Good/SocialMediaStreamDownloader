<script setup lang="ts">
import {
  TYPE_LABELS,
  creatorName,
  savedCountLabel,
} from '@/components/library/libraryPresentation'
import { formatTimestamp } from '@/utils/time'
import type { LibraryPost } from '@/types/library'

//
// The USER endpoint already omits operator-only filing fields. This table uses
// only that explicit safe contract; the aweme id remains an undisplayed stable
// row key.
//
defineProps<{
  posts: LibraryPost[]
  selectedKey: string | null
  keyOf: (post: LibraryPost) => string
}>()

defineEmits<{ select: [string] }>()
</script>

<template>
  <div class="table-scroll">
    <table class="table">
      <thead>
        <tr>
          <th scope="col">类型</th>
          <th scope="col">内容</th>
          <th scope="col">创作者</th>
          <th scope="col">下载情况</th>
          <th scope="col">下载时间</th>
          <th scope="col">操作</th>
        </tr>
      </thead>
      <tbody>
        <tr
          v-for="row in posts"
          :key="keyOf(row)"
          :class="{ 'table__row--selected': keyOf(row) === selectedKey }"
        >
          <td>{{ row.aweme_type ? TYPE_LABELS[row.aweme_type] : '—' }}</td>
          <td class="table__desc">{{ row.desc || '（无文案）' }}</td>
          <td>{{ creatorName(row.nickname) }}</td>
          <td>{{ savedCountLabel(row.saved_count, row.media_count) }}</td>
          <td class="table__muted">{{ formatTimestamp(row.downloaded_at) }}</td>
          <td>
            <button type="button" class="table__view" @click="$emit('select', keyOf(row))">
              查看
            </button>
          </td>
        </tr>
      </tbody>
    </table>
  </div>
</template>

<style scoped>
.table-scroll { overflow-x: auto; }
.table { width: 100%; border-collapse: collapse; font-size: 0.875rem; }
.table th, .table td { padding: var(--space-2) var(--space-3); border-bottom: 1px solid var(--color-border); text-align: left; white-space: nowrap; }
.table th { color: var(--color-muted); font-size: 0.75rem; font-weight: 600; }
.table__row--selected { background: var(--color-accent-soft); }
.table__desc { max-width: 22rem; overflow: hidden; text-overflow: ellipsis; }
.table__muted { color: var(--color-muted); }
.table__view { padding: 2px var(--space-3); font: inherit; font-size: 0.8125rem; color: inherit; background: var(--color-surface); border: 1px solid var(--color-border); border-radius: var(--radius-1); cursor: pointer; }
</style>
