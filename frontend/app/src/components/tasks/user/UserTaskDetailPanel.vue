<script setup lang="ts">
import { computed } from 'vue'

import TaskProgress from '@/components/tasks/TaskProgress.vue'
import TaskStateBadge from '@/components/tasks/TaskStateBadge.vue'
import {
  TASK_TYPE_LABELS,
  formatTaskTime,
  isLinkableUrl,
  taskDisplayTitle,
} from '@/components/tasks/taskPresentation'
import {
  itemSummary,
  taskNote,
  userResultFields,
} from '@/components/tasks/user/userTaskPresentation'
import type { Task } from '@/types/task'

//
// What happened, for the person who asked for it.
//
// Built from the row already on screen, exactly as the management panel is.
// The difference is what it refuses to render: no task id, no resolve receipt,
// no aweme or sec_user id, no legacy job id, no resolved url, no save
// directory, no protocol, no test-mode flag. Each answers a question about how
// the program did the work rather than about the download.
//
const props = defineProps<{ task: Task }>()

defineEmits<{ close: [] }>()

const note = computed(() => taskNote(props.task.message))
const results = computed(() => userResultFields(props.task.metadata))
const items = computed(() => itemSummary(props.task.items))

//
// The link the user pasted in the first place - the one url here they have any
// relationship with. `resolved_url` is the short link followed to its
// destination, which is the program showing its working.
//
// Guarded by the existing isLinkableUrl rule rather than a second opinion about
// it: metadata is arbitrary, and anything not plainly http(s) stays text.
//
const sourceUrl = computed(() => {
  const raw = props.task.metadata.source_url
  return typeof raw === 'string' && raw.trim() ? raw.trim() : null
})
</script>

<template>
  <aside class="detail" aria-labelledby="user-task-detail-heading">
    <div class="detail__head">
      <h2 id="user-task-detail-heading" class="detail__title">
        {{ taskDisplayTitle(task.title, task.task_type) }}
      </h2>
      <TaskStateBadge :state="task.state" />
      <button type="button" class="detail__close" @click="$emit('close')">关闭</button>
    </div>

    <dl class="facts">
      <div class="facts__row">
        <dt>类型</dt>
        <dd>{{ TASK_TYPE_LABELS[task.task_type] }}</dd>
      </div>
      <div class="facts__row">
        <dt>进度</dt>
        <dd><TaskProgress :progress="task.progress" /></dd>
      </div>
      <div v-if="note" class="facts__row">
        <dt>说明</dt>
        <dd>{{ note }}</dd>
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
        <dt>完成时间</dt>
        <dd class="facts__time">{{ formatTaskTime(task.finished_at) }}</dd>
      </div>
      <div v-if="sourceUrl" class="facts__row">
        <dt>原始分享链接</dt>
        <dd>
          <a
            v-if="isLinkableUrl(sourceUrl)"
            :href="sourceUrl"
            target="_blank"
            rel="noopener noreferrer"
          >{{ sourceUrl }}</a>
          <span v-else>{{ sourceUrl }}</span>
        </dd>
      </div>
    </dl>

    <section v-if="results.length" class="detail__section">
      <h3 class="detail__subtitle">下载结果</h3>
      <dl class="facts">
        <div v-for="entry in results" :key="entry.key" class="facts__row">
          <dt>{{ entry.label }}</dt>
          <dd>{{ entry.value }}</dd>
        </div>
      </dl>
    </section>

    <!--
      Counts, not keys. An item's key is the aweme id the downloader was working
      on; there is no human-readable label recorded beside it, and inventing one
      would mean guessing a title the task never had.
    -->
    <section v-if="items.length" class="detail__section">
      <h3 class="detail__subtitle">处理情况</h3>
      <ul class="counts">
        <li v-for="entry in items" :key="entry.state" class="counts__row">
          <span class="counts__label">{{ entry.label }}</span>
          <span class="counts__value">{{ entry.count }}</span>
        </li>
      </ul>
    </section>
  </aside>
</template>

<style scoped>
.detail { padding: var(--space-4); background: var(--color-surface); border: 1px solid var(--color-border); border-radius: var(--radius-2); }
.detail__head { display: flex; align-items: center; gap: var(--space-3); flex-wrap: wrap; margin-bottom: var(--space-3); }
.detail__title { margin: 0; font-size: 1rem; }
.detail__close { margin-left: auto; padding: 2px var(--space-3); font: inherit; font-size: 0.8125rem; color: inherit; background: var(--color-surface); border: 1px solid var(--color-border); border-radius: var(--radius-1); cursor: pointer; }
.detail__section { margin-top: var(--space-4); }
.detail__subtitle { margin: 0 0 var(--space-2); font-size: 0.875rem; }
.facts { margin: 0; display: grid; gap: var(--space-2); }
.facts__row { display: grid; grid-template-columns: 7rem 1fr; gap: var(--space-3); align-items: baseline; }
.facts__row dt { color: var(--color-muted); font-size: 0.8125rem; }
.facts__row dd { margin: 0; font-size: 0.875rem; overflow-wrap: anywhere; }
.facts__time { font-size: 0.8125rem; }
.counts { list-style: none; margin: 0; padding: 0; display: flex; flex-wrap: wrap; gap: var(--space-3); }
.counts__row { display: flex; align-items: baseline; gap: var(--space-2); padding: var(--space-1) var(--space-3); background: var(--color-background); border: 1px solid var(--color-border); border-radius: var(--radius-1); }
.counts__label { color: var(--color-muted); font-size: 0.8125rem; }
.counts__value { font-size: 0.9375rem; font-weight: 600; }
</style>
