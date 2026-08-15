<script setup lang="ts">
import { formatTimestamp } from '@/utils/time'
import type { PersonSummaryItem, PersonWork } from '@/types/person'

defineProps<{
  people: PersonSummaryItem[]
  selectedPhotographerId: number | null
  works: PersonWork[]
  loading: boolean
  error: string | null
}>()

defineEmits<{ select: [number | null] }>()
</script>

<template>
  <section class="works">
    <!--
      Stated before the list, not after it. The backend records collaboration
      between people rather than against individual posts, so what comes back is
      the whole output of every account belonging to somebody this person has
      worked with. Calling it "TA 拍摄的作品" would turn a association into a
      claim about each row - and there is no data behind that claim.
    -->
    <p class="works__note">
      该列表基于人物级合作关系，展示被记录为该人物拍摄对象的账号所下载内容；并不表示每条作品都已逐条确认由该人物拍摄。
    </p>

    <label class="works__field">
      <span class="works__label">选择摄影师</span>
      <select
        class="works__select"
        :value="selectedPhotographerId ?? ''"
        @change="
          $emit(
            'select',
            ($event.target as HTMLSelectElement).value
              ? Number(($event.target as HTMLSelectElement).value)
              : null,
          )
        "
      >
        <option value="">请选择</option>
        <option v-for="one in people" :key="one.person_id" :value="one.person_id">
          {{ one.display_name }}
        </option>
      </select>
    </label>

    <p v-if="error" class="works__notice" role="alert">{{ error }}</p>
    <p v-else-if="loading" class="works__muted">正在读取关联作品…</p>
    <p v-else-if="selectedPhotographerId === null" class="works__placeholder">
      选择一位人物后，这里会显示与其有拍摄关系的账号已下载的作品。
    </p>
    <p v-else-if="!works.length" class="works__placeholder">
      该人物暂无关联作品记录。
    </p>

    <div v-else class="table-scroll">
      <table class="table">
        <thead>
          <tr>
            <th scope="col">关联对象</th>
            <th scope="col">文案</th>
            <th scope="col">作品 ID</th>
            <th scope="col">下载时间</th>
            <th scope="col">保存目录</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="(row, index) in works" :key="`${row.aweme_id}-${index}`">
            <td>{{ row.owner_display_name ?? '—' }}</td>
            <td class="table__desc">{{ row.desc || '（无文案）' }}</td>
            <td class="table__mono">{{ row.aweme_id ?? '—' }}</td>
            <td class="table__muted">{{ formatTimestamp(row.downloaded_at) }}</td>
            <!-- Text, like every other recorded path on this screen. -->
            <td class="table__path">{{ row.save_dir ?? '—' }}</td>
          </tr>
        </tbody>
      </table>
    </div>
  </section>
</template>

<style scoped>
.works { display: grid; gap: var(--space-3); }
.works__note { margin: 0; padding: var(--space-3); background: var(--color-background); border: 1px solid var(--color-border); border-radius: var(--radius-1); color: var(--color-muted); font-size: 0.8125rem; line-height: 1.6; }
.works__field { display: flex; flex-direction: column; gap: var(--space-1); max-width: 20rem; }
.works__label { font-size: 0.75rem; color: var(--color-muted); }
.works__select { width: 100%; padding: var(--space-1) var(--space-2); font: inherit; color: inherit; background: var(--color-surface); border: 1px solid var(--color-border); border-radius: var(--radius-1); }
.works__notice { margin: 0; padding: var(--space-3); background: var(--color-background); border: 1px solid var(--color-border); border-radius: var(--radius-1); font-size: 0.8125rem; }
.works__muted { margin: 0; color: var(--color-muted); font-size: 0.8125rem; }
.works__placeholder { margin: 0; padding: var(--space-5); background: var(--color-surface); border: 1px solid var(--color-border); border-radius: var(--radius-2); color: var(--color-muted); text-align: center; }
.table-scroll { overflow-x: auto; }
.table { width: 100%; border-collapse: collapse; font-size: 0.875rem; }
.table th, .table td { padding: var(--space-2) var(--space-3); border-bottom: 1px solid var(--color-border); text-align: left; white-space: nowrap; }
.table th { color: var(--color-muted); font-size: 0.75rem; font-weight: 600; }
.table__desc { max-width: 18rem; overflow: hidden; text-overflow: ellipsis; }
.table__mono { font-family: ui-monospace, SFMono-Regular, Menlo, monospace; font-size: 0.8125rem; }
.table__path { max-width: 16rem; overflow: hidden; text-overflow: ellipsis; font-family: ui-monospace, SFMono-Regular, Menlo, monospace; font-size: 0.75rem; }
.table__muted { color: var(--color-muted); }
</style>
