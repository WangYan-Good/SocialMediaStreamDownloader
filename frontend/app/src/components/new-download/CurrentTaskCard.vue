<script setup lang="ts">
import { computed } from 'vue'
import { RouterLink } from 'vue-router'

import { trackingFailureMessage } from '@/components/new-download/downloadPresentation'
import TaskStateBadge from '@/components/tasks/TaskStateBadge.vue'
import {
  TASK_TYPE_LABELS,
  progressText,
} from '@/components/tasks/taskPresentation'
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

const typeLabel = computed(() => TASK_TYPE_LABELS[props.created.task_type])

//
// What a finished download says, in one sentence. The task's own message wins
// when it has one - it is written by whichever runner actually did the work and
// knows more than this screen does.
//
const OUTCOMES = {
  success: '下载已完成',
  partial: '部分内容已下载',
  failed: '下载失败',
  cancelled: '下载已停止',
} as const

const outcome = computed(() => {
  const state = props.task?.state
  if (!state || !(state in OUTCOMES)) {
    return null
  }
  return props.task?.message || OUTCOMES[state as keyof typeof OUTCOMES]
})

const progressLabel = computed(() => {
  const progress = props.task?.progress
  if (!progress) {
    return null
  }
  //
  // A recording has no final count, and that is the honest answer rather than a
  // fabricated total that would render as a bar stuck near zero for hours.
  //
  return progressText(progress.current, progress.total)
})

//
// The status read failed, said as a result. Mapped here rather than in the flow
// so the composable keeps classifying failures exactly as it did - this decides
// only which of its words reach the screen.
//
const notice = computed(() =>
  trackingFailureMessage(props.trackError, props.recordMissing),
)
</script>

<template>
  <section class="card">
    <div class="card__head">
      <!--
        The heading a user is waiting for. It stays true afterwards: the
        download did start, and how it ended is said just below.
      -->
      <h2 class="card__title">下载已开始</h2>
      <TaskStateBadge v-if="task" :state="task.state" />
    </div>

    <!--
      The task id, and the three timestamps that used to sit here, are not shown.
      They identify the record rather than describe the download, and the task
      list is where a record is looked up.
    -->
    <dl class="facts">
      <div class="facts__row">
        <dt>内容</dt>
        <dd>{{ typeLabel }}</dd>
      </div>
      <div v-if="task?.title" class="facts__row">
        <dt>标题</dt>
        <dd>{{ task.title }}</dd>
      </div>
      <div v-if="progressLabel" class="facts__row">
        <dt>进度</dt>
        <dd>
          {{ progressLabel }}
          <span v-if="progressPercent !== null" class="facts__muted">
            （{{ progressPercent }}%）
          </span>
          <span v-else-if="task?.progress.total === null" class="facts__muted">
            （总量未知）
          </span>
        </dd>
      </div>
    </dl>

    <!--
      Polite, not assertive: this narrates work already under way rather than
      answering something the user is waiting on.
    -->
    <p v-if="outcome" class="card__outcome" aria-live="polite">{{ outcome }}</p>

    <div v-if="notice" class="card__notice" role="status">
      <p class="card__notice-text">{{ notice }}</p>
      <!--
        A read failing says nothing about the work. The task is not marked
        failed here, and the only thing offered is another look.
      -->
      <button v-if="!recordMissing" type="button" class="button" @click="$emit('retry')">
        重试获取状态
      </button>
    </div>

    <div class="card__actions">
      <!--
        The way out of this screen. One download is shown here; everything the
        user has ever started lives in the task list, and this is the only link
        to it from the flow.
      -->
      <RouterLink class="card__link" :to="{ name: 'tasks' }">查看所有任务</RouterLink>
      <button
        v-if="canStartOver"
        type="button"
        class="button"
        @click="$emit('startOver')"
      >
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
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: var(--space-3);
  margin-top: var(--space-4);
}

.card__link {
  color: var(--color-accent);
  font-size: 0.875rem;
  text-decoration: underline;
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
