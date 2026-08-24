<script setup lang="ts">
import AppShell from '@/components/layout/AppShell.vue'
import type { NavEntry } from '@/components/layout/SidebarNav.vue'

//
// The words a user already met elsewhere: the screen calls itself 下载任务,
// and New Download sends them here with 查看所有任务. A sidebar saying 任务
// would be a third name for the same destination.
//
const navigation: readonly NavEntry[] = [
  { name: 'user-home', label: '首页', hint: 'Home' },
  { name: 'new-download', label: '新建下载', hint: 'New Download' },
  { name: 'library', label: '我的资源', hint: 'Library' },
  { name: 'tasks', label: '下载任务', hint: 'Tasks' },
]
</script>

<template>
  <AppShell
    title="Social Media Stream Downloader"
    navigation-label="用户导航"
    :navigation="navigation"
  />
</template>
