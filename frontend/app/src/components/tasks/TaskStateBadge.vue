<script setup lang="ts">
import { computed } from 'vue'

import { TASK_STATE_LABELS } from '@/components/tasks/taskPresentation'
import type { TaskState } from '@/types/task'

const props = defineProps<{ state: TaskState }>()

//
// The word beside the colour. A badge that distinguished success from failure
// by hue alone would be unreadable to a good number of people, and invisible in
// a screenshot pasted into a bug report.
//
const label = computed(() => TASK_STATE_LABELS[props.state])
</script>

<template>
  <span class="badge" :class="`badge--${state}`">{{ label }}</span>
</template>

<style scoped>
.badge {
  display: inline-block;
  padding: 2px var(--space-2);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-1);
  font-size: 0.75rem;
  line-height: 1.6;
  white-space: nowrap;
}

.badge--pending {
  color: var(--color-muted);
}

.badge--running {
  color: var(--color-accent);
  border-color: var(--color-accent);
  background: var(--color-accent-soft);
}

.badge--success {
  color: #147a3d;
  border-color: #9dd7b4;
  background: #eaf7ef;
}

.badge--partial {
  color: #8a5a00;
  border-color: #e3c489;
  background: #fdf3e2;
}

.badge--failed {
  color: #a12a2a;
  border-color: #e6a9a9;
  background: #fdecec;
}

.badge--cancelled {
  color: var(--color-muted);
  background: var(--color-background);
}

@media (prefers-color-scheme: dark) {
  .badge--success {
    color: #7fd3a1;
    border-color: #2f6244;
    background: #17301f;
  }

  .badge--partial {
    color: #e8bd76;
    border-color: #6b5326;
    background: #2e2413;
  }

  .badge--failed {
    color: #f0a2a2;
    border-color: #6f3030;
    background: #2f1717;
  }
}
</style>
