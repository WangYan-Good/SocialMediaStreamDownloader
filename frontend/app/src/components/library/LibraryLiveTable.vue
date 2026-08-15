<script setup lang="ts">
import { recordedLiveStatusLabel } from '@/components/library/libraryPresentation'
import { formatTimestamp } from '@/utils/time'
import type { LibraryLive } from '@/types/library'

defineProps<{ lives: LibraryLive[]; selectedKey: string | null; keyOf: (live: LibraryLive) => string }>()

defineEmits<{ select: [string] }>()
</script>

<template>
  <div class="table-scroll">
    <table class="table">
      <caption class="table__caption">
        数据库中的直播记录。每行是当时观察到的状态，不代表现在是否开播。
      </caption>
      <thead>
        <tr>
          <th scope="col">创作者</th>
          <th scope="col">人物</th>
          <th scope="col">标题</th>
          <th scope="col">房间号</th>
          <th scope="col">记录状态</th>
          <th scope="col">开始</th>
          <th scope="col">结束</th>
          <th scope="col">观察时间</th>
          <th scope="col">操作</th>
        </tr>
      </thead>
      <tbody>
        <!--
          No play button and no file link: live_record has no output path at
          all, so anything offered here would be a path this page guessed.
        -->
        <tr
          v-for="row in lives"
          :key="keyOf(row)"
          :class="{ 'table__row--selected': keyOf(row) === selectedKey }"
        >
          <td>{{ row.nickname ?? row.owner_user_id ?? '—' }}</td>
          <td class="table__muted">{{ row.person_display_name ?? '未归并' }}</td>
          <td class="table__title">{{ row.title ?? '—' }}</td>
          <td class="table__mono">{{ row.room_id ?? '—' }}</td>
          <td>{{ recordedLiveStatusLabel(row.room_status) }}</td>
          <td class="table__muted">{{ formatTimestamp(row.start_time) }}</td>
          <td class="table__muted">{{ formatTimestamp(row.finish_time) }}</td>
          <td class="table__muted">{{ formatTimestamp(row.observed_at) }}</td>
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
.table__title { max-width: 18rem; overflow: hidden; text-overflow: ellipsis; }
.table__mono { font-family: ui-monospace, SFMono-Regular, Menlo, monospace; font-size: 0.8125rem; }
.table__muted { color: var(--color-muted); }
.table__view { padding: 2px var(--space-3); font: inherit; font-size: 0.8125rem; color: inherit; background: var(--color-surface); border: 1px solid var(--color-border); border-radius: var(--radius-1); cursor: pointer; }
</style>
