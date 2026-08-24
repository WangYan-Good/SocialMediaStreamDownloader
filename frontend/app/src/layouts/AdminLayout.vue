<script setup lang="ts">
import AppShell from '@/components/layout/AppShell.vue'
import type { NavEntry } from '@/components/layout/SidebarNav.vue'

const navigation: readonly NavEntry[] = [
  { name: 'admin-creators', label: '创作者', hint: 'Creators' },
  { name: 'admin-system', label: '系统', hint: 'System' },
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
