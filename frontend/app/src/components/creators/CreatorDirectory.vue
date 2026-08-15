<script setup lang="ts">
import { formatTaskTime } from '@/components/tasks/taskPresentation'
import {
  PROBE_STATE_LABELS,
  formatCount,
  lastKnownLiveLabel,
} from '@/components/creators/creatorPresentation'
import type { HistoryOwner, LiveProbeItem } from '@/types/history'

defineProps<{
  owners: HistoryOwner[]
  selectedOwnerUserId: string | null
  checkedOwnerUserIds: string[]
  probeItems: Record<string, LiveProbeItem>
}>()

defineEmits<{ select: [string]; toggleCheck: [string] }>()
</script>

<template>
  <div class="table-scroll">
    <table class="table">
      <caption class="table__caption">
        本机已知的主播账号。“上次”是数据库缓存的最后已知状态，不代表现在是否开播。
      </caption>
      <thead>
        <tr>
          <th scope="col"><span class="table__sr">选择</span></th>
          <th scope="col">昵称</th>
          <th scope="col">收藏 / 评分</th>
          <th scope="col">开播次数</th>
          <th scope="col">最后已知状态</th>
          <th scope="col">本次检查</th>
          <th scope="col">最后检查</th>
          <th scope="col">账号状态</th>
          <th scope="col">操作</th>
        </tr>
      </thead>
      <tbody>
        <tr
          v-for="row in owners"
          :key="row.owner_user_id"
          :class="{ 'table__row--selected': row.owner_user_id === selectedOwnerUserId }"
        >
          <td>
            <input
              type="checkbox"
              :checked="checkedOwnerUserIds.includes(row.owner_user_id)"
              :aria-label="`选择 ${row.nickname ?? row.owner_user_id}`"
              @change="$emit('toggleCheck', row.owner_user_id)"
            />
          </td>
          <td class="table__name">{{ row.nickname ?? row.owner_user_id }}</td>
          <td>
            <span v-if="row.favorite">★ {{ formatCount(row.score) }}</span>
            <span v-else class="table__muted">—</span>
          </td>
          <td>{{ formatCount(row.actived_count) }}</td>
          <!--
            Past tense on purpose. This is what the database last recorded, and
            saying "正在直播" from it would assert something nobody has checked.
          -->
          <td class="table__muted">{{ lastKnownLiveLabel(row.last_live_status) }}</td>
          <td>
            <span v-if="probeItems[row.owner_user_id]" class="table__probe">
              {{ PROBE_STATE_LABELS[probeItems[row.owner_user_id].state] }}
              <span v-if="probeItems[row.owner_user_id].cached" class="table__muted">
                （缓存）
              </span>
            </span>
            <span v-else class="table__muted">—</span>
          </td>
          <td class="table__muted">{{ formatTaskTime(row.last_checked_at) }}</td>
          <td>{{ row.user_status ?? '—' }}</td>
          <td>
            <button type="button" class="table__view" @click="$emit('select', row.owner_user_id)">
              查看
            </button>
          </td>
        </tr>
      </tbody>
    </table>
  </div>
</template>

<style scoped>
.table-scroll {
  overflow-x: auto;
}

.table {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.875rem;
}

.table__caption {
  padding-bottom: var(--space-2);
  color: var(--color-muted);
  font-size: 0.8125rem;
  text-align: left;
}

.table th,
.table td {
  padding: var(--space-2) var(--space-3);
  border-bottom: 1px solid var(--color-border);
  text-align: left;
  white-space: nowrap;
}

.table th {
  color: var(--color-muted);
  font-size: 0.75rem;
  font-weight: 600;
}

.table__row--selected {
  background: var(--color-accent-soft);
}

.table__name {
  max-width: 14rem;
  overflow: hidden;
  text-overflow: ellipsis;
}

.table__muted {
  color: var(--color-muted);
}

.table__probe {
  font-size: 0.8125rem;
}

.table__sr {
  position: absolute;
  width: 1px;
  height: 1px;
  overflow: hidden;
  clip-path: inset(50%);
}

.table__view {
  padding: 2px var(--space-3);
  font: inherit;
  font-size: 0.8125rem;
  color: inherit;
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-1);
  cursor: pointer;
}
</style>
