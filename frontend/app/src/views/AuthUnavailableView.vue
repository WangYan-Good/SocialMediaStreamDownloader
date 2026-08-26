<script setup lang="ts">
import { ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import { resolveSafeReturnTarget } from '@/router/returnTarget'
import { useAuthStore } from '@/stores/auth'

const route = useRoute()
const router = useRouter()
const auth = useAuthStore()
const retrying = ref(false)

async function retry(): Promise<void> {
  if (retrying.value) return
  retrying.value = true
  try {
    await auth.refreshCurrentUser()
    const target = resolveSafeReturnTarget(router, route.query.redirect)
    if (auth.status === 'authenticated') {
      await router.replace(target ?? { name: 'user-home' })
    } else if (auth.status === 'anonymous') {
      await router.replace(
        target ? { name: 'login', query: { redirect: target } } : { name: 'login' },
      )
    }
  } finally {
    retrying.value = false
  }
}
</script>

<template>
  <section class="auth-unavailable" aria-labelledby="auth-unavailable-title">
    <h1 id="auth-unavailable-title">暂时无法确认登录状态</h1>
    <p>暂时无法确认登录状态，请稍后重试。</p>
    <button type="button" :disabled="retrying" @click="retry">
      {{ retrying ? '正在重试…' : '重试' }}
    </button>
  </section>
</template>

<style scoped>
.auth-unavailable { max-width: 32rem; margin: var(--space-5) auto; padding: var(--space-5); background: var(--color-surface); border: 1px solid var(--color-border); border-radius: var(--radius-2); }
.auth-unavailable h1 { margin-top: 0; }
.auth-unavailable p { color: var(--color-muted); }
.auth-unavailable button { padding: var(--space-2) var(--space-4); font: inherit; font-weight: 600; color: #fff; background: var(--color-accent); border: 1px solid var(--color-accent); border-radius: var(--radius-1); cursor: pointer; }
.auth-unavailable button:disabled { opacity: 0.6; cursor: wait; }
</style>
