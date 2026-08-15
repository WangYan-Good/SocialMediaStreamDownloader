<script setup lang="ts">
import { computed } from 'vue'

import TaskProgress from '@/components/tasks/TaskProgress.vue'
import TaskStateBadge from '@/components/tasks/TaskStateBadge.vue'
import {
  TASK_ITEM_STATE_LABELS,
  TASK_TYPE_LABELS,
  formatTaskTime,
  isLinkableUrl,
  taskDisplayTitle,
} from '@/components/tasks/taskPresentation'
import type { Task } from '@/types/task'

const props = defineProps<{ task: Task }>()

defineEmits<{ close: [] }>()

//
// An allow list, not a dump.
//
// `metadata` is arbitrary business data written by whichever runner did the
// work. Rendering all of it would put whatever a future runner happens to
// record - a signed url, an internal path, a cookie someone stored by mistake -
// straight onto the screen. Every field here is one this project already knows
// the meaning of.
//
const IDENTITY_FIELDS: ReadonlyArray<[string, string]> = [
  ['platform', '平台'],
  ['source', '来源'],
  ['resolve_id', '解析凭证'],
  ['aweme_id', '作品 ID'],
  ['sec_user_id', '主播 ID'],
  ['mode', '模式'],
  ['legacy_job_id', '兼容任务 ID'],
]

const URL_FIELDS: ReadonlyArray<[string, string]> = [
  ['source_url', '原始链接'],
  ['resolved_url', '解析后链接'],
]

const RESULT_FIELDS: ReadonlyArray<[string, string]> = [
  ['saved_count', '已保存'],
  ['media_count', '媒体数'],
  ['save_dir', '保存目录'],
  ['output_path', '输出文件'],
  ['protocol', '协议'],
  ['live_status', '直播状态'],
  ['room_status', '房间状态'],
  ['owner_user_id', '主播用户 ID'],
  ['nickname', '昵称'],
  ['recorded', '已录制'],
  ['skipped', '已跳过'],
  ['partial', '部分完成'],
  ['test_mode', '测试模式'],
  ['reason', '原因'],
]

/** Render a metadata value only when it is a primitive this panel can show. */
function readable(value: unknown): string | null {
  if (typeof value === 'string') {
    return value.trim() || null
  }
  if (typeof value === 'number' && Number.isFinite(value)) {
    return String(value)
  }
  if (typeof value === 'boolean') {
    return value ? '是' : '否'
  }
  return null
}

function pick(source: Record<string, unknown>, fields: ReadonlyArray<[string, string]>) {
  return fields
    .map(([key, label]) => ({ key, label, value: readable(source[key]) }))
    .filter((entry): entry is { key: string; label: string; value: string } =>
      entry.value !== null,
    )
}

const identity = computed(() => pick(props.task.metadata, IDENTITY_FIELDS))
const urls = computed(() => pick(props.task.metadata, URL_FIELDS))

const result = computed(() => {
  const raw = props.task.metadata.result
  if (typeof raw !== 'object' || raw === null) {
    return []
  }
  return pick(raw as Record<string, unknown>, RESULT_FIELDS)
})
</script>

<template>
  <aside class="detail" aria-labelledby="task-detail-heading">
    <div class="detail__head">
      <h2 id="task-detail-heading" class="detail__title">
        {{ taskDisplayTitle(task.title, task.task_type) }}
      </h2>
      <TaskStateBadge :state="task.state" />
      <button type="button" class="detail__close" @click="$emit('close')">关闭详情</button>
    </div>

    <dl class="facts">
      <div class="facts__row">
        <dt>任务 ID</dt>
        <dd class="facts__mono">{{ task.task_id }}</dd>
      </div>
      <div class="facts__row">
        <dt>类型</dt>
        <dd>{{ TASK_TYPE_LABELS[task.task_type] }}</dd>
      </div>
      <div class="facts__row">
        <dt>进度</dt>
        <dd><TaskProgress :progress="task.progress" /></dd>
      </div>
      <div v-if="task.message" class="facts__row">
        <dt>说明</dt>
        <dd>{{ task.message }}</dd>
      </div>
      <div class="facts__row">
        <dt>创建时间</dt>
        <dd class="facts__time">{{ formatTaskTime(task.created_at) }}</dd>
      </div>
      <div class="facts__row">
        <dt>开始时间</dt>
        <dd class="facts__time">{{ formatTaskTime(task.started_at) }}</dd>
      </div>
      <div class="facts__row">
        <dt>结束时间</dt>
        <dd class="facts__time">{{ formatTaskTime(task.finished_at) }}</dd>
      </div>
      <div v-for="entry in identity" :key="entry.key" class="facts__row">
        <dt>{{ entry.label }}</dt>
        <dd class="facts__mono">{{ entry.value }}</dd>
      </div>
      <div v-for="entry in urls" :key="entry.key" class="facts__row">
        <dt>{{ entry.label }}</dt>
        <dd>
          <a
            v-if="isLinkableUrl(entry.value)"
            :href="entry.value"
            target="_blank"
            rel="noopener noreferrer"
          >{{ entry.value }}</a>
          <!--
            Anything that is not plainly http(s) is shown as text. The value
            stays visible; only the click is withheld.
          -->
          <span v-else>{{ entry.value }}</span>
        </dd>
      </div>
    </dl>

    <section v-if="result.length" class="detail__section">
      <h3 class="detail__subtitle">结果</h3>
      <dl class="facts">
        <div v-for="entry in result" :key="entry.key" class="facts__row">
          <dt>{{ entry.label }}</dt>
          <dd>{{ entry.value }}</dd>
        </div>
      </dl>
    </section>

    <section v-if="task.items.length" class="detail__section">
      <h3 class="detail__subtitle">工作项（{{ task.items.length }}）</h3>
      <ul class="items">
        <li v-for="item in task.items" :key="item.key" class="items__row">
          <span class="items__key">{{ item.key }}</span>
          <span class="items__state">{{ TASK_ITEM_STATE_LABELS[item.state] }}</span>
          <span v-if="item.message" class="items__message">{{ item.message }}</span>
        </li>
      </ul>
    </section>
  </aside>
</template>

<style scoped>
.detail {
  padding: var(--space-4);
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-2);
}

.detail__head {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  flex-wrap: wrap;
  margin-bottom: var(--space-3);
}

.detail__title {
  margin: 0;
  font-size: 1rem;
}

.detail__close {
  margin-left: auto;
  padding: 2px var(--space-3);
  font: inherit;
  font-size: 0.8125rem;
  color: inherit;
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-1);
  cursor: pointer;
}

.detail__section {
  margin-top: var(--space-4);
}

.detail__subtitle {
  margin: 0 0 var(--space-2);
  font-size: 0.875rem;
}

.facts {
  margin: 0;
  display: grid;
  gap: var(--space-2);
}

.facts__row {
  display: grid;
  grid-template-columns: 7rem 1fr;
  gap: var(--space-3);
  align-items: baseline;
}

.facts__row dt {
  color: var(--color-muted);
  font-size: 0.8125rem;
}

.facts__row dd {
  margin: 0;
  font-size: 0.875rem;
  overflow-wrap: anywhere;
}

.facts__mono {
  font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
  font-size: 0.8125rem;
}

.facts__time {
  font-size: 0.8125rem;
}

.items {
  list-style: none;
  margin: 0;
  padding: 0;
  display: grid;
  gap: var(--space-1);
  max-height: 18rem;
  overflow-y: auto;
}

.items__row {
  display: flex;
  gap: var(--space-3);
  align-items: baseline;
  padding: var(--space-1) 0;
  border-bottom: 1px solid var(--color-border);
  font-size: 0.8125rem;
}

.items__key {
  font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
  overflow-wrap: anywhere;
}

.items__state {
  color: var(--color-muted);
  white-space: nowrap;
}

.items__message {
  color: var(--color-muted);
  overflow-wrap: anywhere;
}
</style>
