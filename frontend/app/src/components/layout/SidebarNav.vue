<script setup lang="ts">
import { RouterLink } from 'vue-router'

interface NavEntry {
  name: string
  label: string
  hint: string
}

//
// One list, rendered once.  The router owns the paths; this owns the words.
//
const entries: NavEntry[] = [
  { name: 'overview', label: '总览', hint: 'Overview' },
  { name: 'new-download', label: '新建下载', hint: 'New Download' },
  { name: 'creators', label: '创作者', hint: 'Creators' },
  { name: 'library', label: '媒体库', hint: 'Library' },
  { name: 'tasks', label: '任务中心', hint: 'Tasks' },
  { name: 'system', label: '系统', hint: 'System' },
]

defineEmits<{ navigate: [] }>()
</script>

<template>
  <nav class="sidebar-nav" aria-label="主导航">
    <ul class="sidebar-nav__list">
      <li v-for="entry in entries" :key="entry.name">
        <RouterLink
          class="sidebar-nav__link"
          :to="{ name: entry.name }"
          @click="$emit('navigate')"
        >
          <span class="sidebar-nav__label">{{ entry.label }}</span>
          <span class="sidebar-nav__hint">{{ entry.hint }}</span>
        </RouterLink>
      </li>
    </ul>

    <div class="sidebar-nav__legacy">
      <!--
        The explicit rollback surface after cutover.  A plain anchor, not a
        RouterLink: /legacy/ belongs to Flask and leaves the SPA entirely.
      -->
      <a class="sidebar-nav__link sidebar-nav__link--legacy" href="/legacy/">
        <span class="sidebar-nav__label">旧版界面</span>
        <span class="sidebar-nav__hint">Legacy fallback</span>
      </a>
    </div>
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

.sidebar-nav__legacy {
  margin-top: auto;
  padding-top: var(--space-4);
  border-top: 1px solid var(--color-border);
}
</style>
