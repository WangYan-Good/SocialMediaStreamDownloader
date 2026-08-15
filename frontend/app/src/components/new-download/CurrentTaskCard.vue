<script setup lang="ts">
import { computed } from 'vue'

import TaskStateBadge from '@/components/new-download/TaskStateBadge.vue'
import type { CreatedTask, Task } from '@/types/task'

const props = defineProps<{
  created: CreatedTask
  task: Task | null
  progressPercent: number | null
  trackError: string | null
  recordMissing: boolean
  canStartOver: boolean
}>()

defineEmits<{ retry: []; startOver: [] }>()

const TYPE_LABELS = {
  post_download: '作品下载',
  live_record: '直播录制',
  owner_batch_download: '主播批量下载',
  live_probe: '直播探测',
} as const

const typeLabel = computed(() => TYPE_LABELS[props.created.task_type])

//
// What a finished task says, in one sentence. The task's own message wins when
// it has one - it is written by whichever runner actually did the work and
// knows more than this screen does.
//
const OUTCOMES = {
  success: '任务已完成',
  partial: '任务部分完成',
  failed: '任务失败',
  cancelled: '任务已停止',
} as const

const outcome = computed(() => {
  const state = props.task?.state
  if (!state || !(state in OUTCOMES)) {
    return null
  }
  return props.task?.message || OUTCOMES[state as keyof typeof OUTCOMES]
})

const progressText = computed(() => {
  const progress = props.task?.progress
  if (!progress) {
    return null
  }
  //
  // A recording has no final count, and that is the honest answer rather than a
  // fabricated total that would render as a bar stuck near zero for hours.
  //
  if (progress.total === null) {
    return `已处理 ${progress.current}`
  }
  return `${progress.current} / ${progress.total}`
})
</script>

<template>
  <section class="card">
    <div class="card__head">
      <h2 class="card__title">当前任务</h2>
      <TaskStateBadge v-if="task" :state="task.state" />
    </div>

    <dl class="facts">
      <div class="facts__row">
        <dt>任务 ID</dt>
        <dd class="facts__mono">{{ created.task_id }}</dd>
      </div>
      <div class="facts__row">
        <dt>类型</dt>
        <dd>{{ typeLabel }}</dd>
      </div>
      <div v-if="task?.title" class="facts__row">
        <dt>标题</dt>
        <dd>{{ task.title }}</dd>
      </div>
      <div v-if="progressText" class="facts__row">
        <dt>进度</dt>
        <dd>
          {{ progressText }}
          <span v-if="progressPercent !== null" class="facts__muted">
            （{{ progressPercent }}%）
          </span>
          <span v-else-if="task?.progress.total === null" class="facts__muted">
            （总量未知）
          </span>
        </dd>
      </div>
      <div v-if="task?.message" class="facts__row">
        <dt>说明</dt>
        <dd>{{ task.message }}</dd>
      </div>
      <div v-if="task?.created_at" class="facts__row">
        <dt>创建时间</dt>
        <dd class="facts__mono">{{ task.created_at }}</dd>
      </div>
      <div v-if="task?.started_at" class="facts__row">
        <dt>开始时间</dt>
        <dd class="facts__mono">{{ task.started_at }}</dd>
      </div>
      <div v-if="task?.finished_at" class="facts__row">
        <dt>结束时间</dt>
        <dd class="facts__mono">{{ task.finished_at }}</dd>
      </div>
    </dl>

    <!--
      Polite, not assertive: this narrates work already under way rather than
      answering something the user is waiting on.
    -->
    <p v-if="outcome" class="card__outcome" aria-live="polite">{{ outcome }}</p>

    <div v-if="trackError" class="card__notice" role="status">
      <p class="card__notice-text">{{ trackError }}</p>
      <!--
        A read failing says nothing about the work. The task is not marked
        failed here, and the only thing offered is another look.
      -->
      <button v-if="!recordMissing" type="button" class="button" @click="$emit('retry')">
        重试获取状态
      </button>
    </div>

    <div v-if="canStartOver" class="card__actions">
      <button type="button" class="button" @click="$emit('startOver')">
        新建另一个下载
      </button>
    </div>
  </section>
</template>

<style scoped>
.card {
  padding: var(--space-4);
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-2);
}

.card__head {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  margin-bottom: var(--space-3);
}

.card__title {
  margin: 0;
  font-size: 1rem;
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

.facts__muted {
  color: var(--color-muted);
}

.card__outcome {
  margin: var(--space-4) 0 0;
  font-size: 0.9375rem;
}

.card__notice {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  flex-wrap: wrap;
  margin-top: var(--space-4);
  padding: var(--space-3);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-1);
  background: var(--color-background);
}

.card__notice-text {
  margin: 0;
  font-size: 0.8125rem;
  color: var(--color-muted);
}

.card__actions {
  margin-top: var(--space-4);
}

.button {
  padding: var(--space-2) var(--space-4);
  font: inherit;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-1);
  background: var(--color-surface);
  color: inherit;
  cursor: pointer;
}
</style>
