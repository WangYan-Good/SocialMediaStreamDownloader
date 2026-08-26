<script setup lang="ts">
import AppShell from '@/components/layout/AppShell.vue'
import type { NavEntry } from '@/components/layout/SidebarNav.vue'

const navigation: readonly NavEntry[] = [
  { name: 'admin-creators', label: '创作者', hint: 'Creators' },
  { name: 'admin-library', label: '媒体库', hint: 'Library' },
  { name: 'admin-tasks', label: '任务', hint: 'Tasks' },
  { name: 'admin-system', label: '系统', hint: 'System' },
  { name: 'user-home', label: '返回用户端', hint: 'User Console' },
]
</script>

<template>
  <AppShell
    title="Social Media Stream Downloader"
    context="Admin"
    navigation-label="管理导航"
    :navigation="navigation"
  />
</template>
