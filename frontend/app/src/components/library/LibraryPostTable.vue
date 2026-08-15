<script setup lang="ts">
import {
  SOURCE_LABELS,
  TYPE_LABELS,
  savedCountLabel,
} from '@/components/library/libraryPresentation'
import { formatTimestamp } from '@/utils/time'
import type { LibraryPost } from '@/types/library'

defineProps<{ posts: LibraryPost[]; selectedKey: string | null; keyOf: (post: LibraryPost) => string }>()

defineEmits<{ select: [string] }>()
</script>

<template>
  <div class="table-scroll">
    <table class="table">
      <caption class="table__caption">
        本机已下载作品的记录索引。“下载记录”描述的是这条记录，不代表磁盘上的文件当前状态。
      </caption>
      <thead>
        <tr>
          <th scope="col">类型</th>
          <th scope="col">描述</th>
          <th scope="col">创作者</th>
          <th scope="col">人物</th>
          <th scope="col">下载记录</th>
          <th scope="col">下载时间</th>
          <th scope="col">保存目录</th>
          <th scope="col">来源</th>
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
          <td>{{ row.nickname ?? row.owner_user_id ?? '—' }}</td>
          <!--
            Most rows have nobody here. An account that was never attached to a
            person is a perfectly ordinary download, not a gap to apologise for.
          -->
          <td class="table__muted">{{ row.person_display_name ?? '未归并' }}</td>
          <td>{{ savedCountLabel(row.saved_count, row.media_count) }}</td>
          <td class="table__muted">{{ formatTimestamp(row.downloaded_at) }}</td>
          <!--
            Text, and only text. This application does not serve files, so a
            path the browser could act on - a link, an image source, a window
            it could open - would be an affordance with nothing behind it.
          -->
          <td class="table__path">{{ row.save_dir ?? '—' }}</td>
          <td class="table__muted">{{ row.source ? SOURCE_LABELS[row.source] : '—' }}</td>
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
.table__caption { padding-bottom: var(--space-2); color: var(--color-muted); font-size: 0.8125rem; text-align: left; }
.table th, .table td { padding: var(--space-2) var(--space-3); border-bottom: 1px solid var(--color-border); text-align: left; white-space: nowrap; }
.table th { color: var(--color-muted); font-size: 0.75rem; font-weight: 600; }
.table__row--selected { background: var(--color-accent-soft); }
.table__desc { max-width: 18rem; overflow: hidden; text-overflow: ellipsis; }
.table__path { max-width: 16rem; overflow: hidden; text-overflow: ellipsis; font-family: ui-monospace, SFMono-Regular, Menlo, monospace; font-size: 0.75rem; }
.table__muted { color: var(--color-muted); }
.table__view { padding: 2px var(--space-3); font: inherit; font-size: 0.8125rem; color: inherit; background: var(--color-surface); border: 1px solid var(--color-border); border-radius: var(--radius-1); cursor: pointer; }
</style>
