<script setup lang="ts">
import { storeToRefs } from 'pinia'
import { ref } from 'vue'
import { RouterView, useRouter } from 'vue-router'

import SidebarNav from '@/components/layout/SidebarNav.vue'
import type { NavEntry } from '@/components/layout/SidebarNav.vue'
import { useAppStore } from '@/stores/app'
import { useAuthStore } from '@/stores/auth'

defineProps<{
  title: string
  context?: string
  navigation: readonly NavEntry[]
  navigationLabel: string
}>()

const store = useAppStore()
const { sidebarOpen } = storeToRefs(store)
const auth = useAuthStore()
const router = useRouter()
const signingOut = ref(false)
const logoutError = ref('')

async function signOut(): Promise<void> {
  if (signingOut.value) return
  logoutError.value = ''
  signingOut.value = true
  try {
    await auth.logout()
  } catch {
    logoutError.value = '退出登录失败，请稍后重试'
    return
  } finally {
    signingOut.value = false
  }
  await router.replace({ name: 'login' })
}
</script>

<template>
  <div class="app-shell" :class="{ 'app-shell--nav-open': sidebarOpen }">
    <header class="app-shell__bar">
      <button
        class="app-shell__toggle"
        type="button"
        :aria-expanded="sidebarOpen"
        aria-controls="app-sidebar"
        @click="store.toggleSidebar()"
      >
        <!-- A readable name, not an icon glyph a screen reader would spell out. -->
        {{ sidebarOpen ? '关闭导航' : '打开导航' }}
      </button>
      <span class="app-shell__title">{{ title }}</span>
      <span v-if="context" class="app-shell__context">{{ context }}</span>
      <div v-if="auth.user" class="app-shell__account">
        <span class="app-shell__username">{{ auth.user.username }}</span>
        <span v-if="auth.isAdmin" class="app-shell__role">Admin</span>
        <button
          data-test="logout"
          class="app-shell__logout"
          type="button"
          :disabled="signingOut"
          @click="signOut"
        >
          {{ signingOut ? '正在退出…' : '退出登录' }}
        </button>
        <span
          v-if="logoutError"
          data-test="logout-error"
          class="app-shell__logout-error"
          role="status"
          aria-live="polite"
        >
          {{ logoutError }}
        </span>
      </div>
    </header>

    <div class="app-shell__body">
      <aside id="app-sidebar" class="app-shell__sidebar">
        <SidebarNav
          :entries="navigation"
          :label="navigationLabel"
          @navigate="store.closeSidebar()"
        />
      </aside>

      <main class="app-shell__main">
        <RouterView />
      </main>
    </div>
  </div>
</template>

<style scoped>
.app-shell {
  display: flex;
  flex-direction: column;
  min-height: 100%;
}

.app-shell__bar {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  padding: var(--space-3) var(--space-4);
  background: var(--color-surface);
  border-bottom: 1px solid var(--color-border);
}

.app-shell__title {
  font-size: 0.9375rem;
  font-weight: 600;
}

.app-shell__context {
  padding: var(--space-1) var(--space-2);
  font-size: 0.75rem;
  font-weight: 700;
  color: var(--color-accent);
  background: var(--color-accent-soft);
  border-radius: var(--radius-1);
}

.app-shell__account {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  margin-left: auto;
  font-size: 0.8125rem;
}

.app-shell__username { font-weight: 600; }
.app-shell__role { padding: 2px var(--space-2); color: var(--color-accent); background: var(--color-accent-soft); border-radius: var(--radius-1); font-weight: 700; }
.app-shell__logout { padding: var(--space-1) var(--space-2); font: inherit; color: inherit; background: transparent; border: 1px solid var(--color-border); border-radius: var(--radius-1); cursor: pointer; }
.app-shell__logout:disabled { opacity: 0.6; cursor: wait; }
.app-shell__logout-error { color: #a12a2a; }

.app-shell__toggle {
  display: none;
  padding: var(--space-1) var(--space-3);
  font: inherit;
  color: inherit;
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-1);
  cursor: pointer;
}

.app-shell__body {
  display: flex;
  flex: 1;
  min-height: 0;
}

.app-shell__sidebar {
  flex: 0 0 var(--sidebar-width);
  padding: var(--space-4);
  background: var(--color-surface);
  border-right: 1px solid var(--color-border);
}

.app-shell__main {
  flex: 1;
  min-width: 0;
  padding: var(--space-5);
}

/*
 * Two columns on a desk, one with a disclosed drawer on a phone.  Deliberately
 * not the legacy 20/60/20: the third column there was a recommendation panel
 * that the new information architecture has no place for.
 */
@media (max-width: 720px) {
  .app-shell__toggle {
    display: inline-block;
  }

  .app-shell__sidebar {
    display: none;
  }

  .app-shell--nav-open .app-shell__sidebar {
    display: block;
    flex: 1;
  }

  .app-shell--nav-open .app-shell__main {
    display: none;
  }

  .app-shell__title { display: none; }
  .app-shell__account { gap: var(--space-1); }
}
</style>
