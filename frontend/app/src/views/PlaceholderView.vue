<script setup lang="ts">
//
// Every screen in this stage is the same shape: a title and one sentence saying
// which stage fills it in.  Written once so the six views cannot drift into six
// slightly different empty states, and so replacing any one of them with the
// real thing is a self-contained change.
//
defineProps<{
  title: string
  hint: string
  note: string
}>()
</script>

<template>
  <section class="placeholder">
    <header class="placeholder__header">
      <h1 class="placeholder__title">{{ title }}</h1>
      <p class="placeholder__hint">{{ hint }}</p>
    </header>
    <p class="placeholder__note">{{ note }}</p>
  </section>
</template>

<style scoped>
.placeholder {
  max-width: 46rem;
}

.placeholder__header {
  margin-bottom: var(--space-4);
}

.placeholder__title {
  margin: 0;
  font-size: 1.375rem;
}

.placeholder__hint {
  margin: var(--space-1) 0 0;
  color: var(--color-muted);
  font-size: 0.8125rem;
}

.placeholder__note {
  margin: 0;
  padding: var(--space-4);
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-2);
  color: var(--color-muted);
  line-height: 1.7;
}
</style>
