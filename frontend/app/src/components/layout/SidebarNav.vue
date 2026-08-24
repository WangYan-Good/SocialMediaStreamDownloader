<script lang="ts">
export interface NavEntry {
  name: string
  label: string
  hint: string
}
</script>

<script setup lang="ts">
import { RouterLink } from 'vue-router'

defineProps<{
  entries: readonly NavEntry[]
  label: string
}>()

defineEmits<{ navigate: [] }>()
</script>

<template>
  <nav class="sidebar-nav" :aria-label="label">
    <ul class="sidebar-nav__list">
      <li v-for="entry in entries" :key="entry.name">
        <RouterLink
          class="sidebar-nav__link"
          :to="{ name: entry.name }"
          active-class="sidebar-nav__link--related"
          exact-active-class="router-link-active"
          @click="$emit('navigate')"
        >
          <span class="sidebar-nav__label">{{ entry.label }}</span>
          <span class="sidebar-nav__hint">{{ entry.hint }}</span>
        </RouterLink>
      </li>
    </ul>
  </nav>
</template>

<style scoped>
.sidebar-nav {
  display: flex;
  flex-direction: column;
  height: 100%;
  gap: var(--space-4);
}

.sidebar-nav__list {
  list-style: none;
  margin: 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: var(--space-1);
}

.sidebar-nav__link {
  display: flex;
  flex-direction: column;
  gap: 2px;
  padding: var(--space-2) var(--space-3);
  border-radius: var(--radius-2);
  border-left: 3px solid transparent;
  color: var(--color-text);
}

.sidebar-nav__link:hover {
  background: var(--color-accent-soft);
}

/*
 * The active entry is marked three ways - background, a left rule and weight -
 * because colour alone is not a state everyone can see.
 */
.sidebar-nav__link.router-link-active {
  background: var(--color-accent-soft);
  border-left-color: var(--color-accent);
  font-weight: 600;
}

.sidebar-nav__label {
  font-size: 0.9375rem;
}

.sidebar-nav__hint {
  font-size: 0.75rem;
  color: var(--color-muted);
}

</style>
