<script setup lang="ts">
import { RouterLink } from 'vue-router'

//
// Links, all of them. The overview is a landing surface: it starts no download,
// probes no room and writes nothing. Anything that acts belongs on the screen
// that owns the action, where its state and its failures live.
//
const ACTIONS = [
  { name: 'new-download', label: '新建下载', hint: '粘贴链接开始一次下载' },
  { name: 'creators', label: '创作者', hint: '账号目录、直播与作品' },
  { name: 'library', label: '媒体库', hint: '已下载内容索引' },
  { name: 'tasks', label: '任务中心', hint: '进行中的工作' },
  { name: 'system', label: '系统', hint: '运行状态与配置摘要' },
] as const
</script>

<template>
  <section class="card" aria-labelledby="overview-actions-heading">
    <h2 id="overview-actions-heading" class="card__title">快速入口</h2>
    <ul class="actions">
      <li v-for="action in ACTIONS" :key="action.name" class="actions__item">
        <RouterLink class="actions__link" :to="{ name: action.name }">
          {{ action.label }}
        </RouterLink>
        <span class="actions__hint">{{ action.hint }}</span>
      </li>
    </ul>
  </section>
</template>

<style scoped>
.card { padding: var(--space-4); background: var(--color-surface); border: 1px solid var(--color-border); border-radius: var(--radius-2); }
.card__title { margin: 0 0 var(--space-3); font-size: 1rem; }
.actions { list-style: none; margin: 0; padding: 0; display: grid; gap: var(--space-2); }
.actions__item { display: flex; flex-wrap: wrap; align-items: baseline; gap: var(--space-3); padding-bottom: var(--space-2); border-bottom: 1px solid var(--color-border); }
.actions__link { color: var(--color-accent); text-decoration: underline; font-size: 0.875rem; }
.actions__hint { color: var(--color-muted); font-size: 0.8125rem; }
</style>
