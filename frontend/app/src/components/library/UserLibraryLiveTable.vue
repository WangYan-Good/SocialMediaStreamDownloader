<script setup lang="ts">
import {
  creatorName,
  recordedLiveStatusLabel,
} from '@/components/library/libraryPresentation'
import { formatTimestamp } from '@/utils/time'
import type { LibraryLive } from '@/types/library'

//
// No room id column. It is the platform's own identifier for a room, nothing
// on this screen does anything with it, and a user recognises a broadcast by
// who was on and what it was called.
//
// No play control and no file link either: live_record has no output path at
// all, so anything offered here would be a path this page invented.
//
defineProps<{
  lives: LibraryLive[]
  selectedKey: string | null
  keyOf: (live: LibraryLive) => string
}>()

defineEmits<{ select: [string] }>()
</script>

<template>
  <div class="table-scroll">
    <table class="table">
      <thead>
        <tr>
          <th scope="col">主播</th>
          <th scope="col">标题</th>
          <th scope="col">记录状态</th>
          <th scope="col">开始</th>
          <th scope="col">结束</th>
          <th scope="col">记录时间</th>
          <th scope="col">操作</th>
        </tr>
      </thead>
      <tbody>
        <tr
          v-for="row in lives"
          :key="keyOf(row)"
          :class="{ 'table__row--selected': keyOf(row) === selectedKey }"
        >
          <td>{{ creatorName(row.nickname) }}</td>
          <td class="table__title">{{ row.title ?? '—' }}</td>
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
.table th, .table td { padding: var(--space-2) var(--space-3); border-bottom: 1px solid var(--color-border); text-align: left; white-space: nowrap; }
.table th { color: var(--color-muted); font-size: 0.75rem; font-weight: 600; }
.table__row--selected { background: var(--color-accent-soft); }
.table__title { max-width: 22rem; overflow: hidden; text-overflow: ellipsis; }
.table__muted { color: var(--color-muted); }
.table__view { padding: 2px var(--space-3); font: inherit; font-size: 0.8125rem; color: inherit; background: var(--color-surface); border: 1px solid var(--color-border); border-radius: var(--radius-1); cursor: pointer; }
</style>
