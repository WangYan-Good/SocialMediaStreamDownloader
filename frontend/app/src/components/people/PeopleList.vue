<script setup lang="ts">
import { directoryLabel } from '@/components/people/personPresentation'
import type { PersonSummaryItem } from '@/types/person'

defineProps<{ people: PersonSummaryItem[]; selectedPersonId: number | null }>()

defineEmits<{ select: [number] }>()
</script>

<template>
  <div class="table-scroll">
    <table class="table">
      <thead>
        <tr>
          <th scope="col">人物</th>
          <th scope="col">目录</th>
          <th scope="col">账号数</th>
          <th scope="col">备注</th>
          <th scope="col">操作</th>
        </tr>
      </thead>
      <tbody>
        <tr
          v-for="row in people"
          :key="row.person_id"
          :class="{ 'table__row--selected': row.person_id === selectedPersonId }"
        >
          <td>{{ row.display_name }}</td>
          <td class="table__muted">{{ directoryLabel(row.directory_name) }}</td>
          <td>{{ row.account_count }}</td>
          <td class="table__muted">{{ row.note ?? '—' }}</td>
          <td>
            <button type="button" class="table__view" @click="$emit('select', row.person_id)">
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
.table__muted { color: var(--color-muted); }
.table__view { padding: 2px var(--space-3); font: inherit; font-size: 0.8125rem; color: inherit; background: var(--color-surface); border: 1px solid var(--color-border); border-radius: var(--radius-1); cursor: pointer; }
</style>
