<script setup lang="ts">
import { computed, ref } from 'vue'
import { useRouter } from 'vue-router'

import { ApiError } from '@/api/client'
import { useAuthStore } from '@/stores/auth'

//
// The whole sign-in surface: a name, a password, and a button.
//
// No registration, no password reset, no third-party provider. Nothing is
// owned by anybody yet and no endpoint checks permissions, so a self-service
// account would be an account that can already see everything in the
// deployment. Accounts are created deliberately, through the CLI, by whoever
// runs it.
//
const router = useRouter()
const auth = useAuthStore()

const username = ref('')
const password = ref('')
const submitting = ref(false)
const failure = ref<string | null>(null)

const canSubmit = computed(
  () => username.value.trim().length > 0 && password.value.length > 0,
)

//
// What to say when the server refused.
//
// 401 is answered with the server's own wording, which is deliberately one
// message for no-such-account, wrong-password and disabled alike - repeating
// it here keeps that property rather than reconstructing it.
//
// 503 is a different fact and gets a different sentence: being told the
// password is wrong when the service is merely down sends somebody off to
// reset a password that was fine.
//
const UNAVAILABLE = '认证服务暂时不可用，请稍后重试'
const UNEXPECTED = '暂时无法登录，请稍后重试'

function describe(caught: unknown): string {
  if (!(caught instanceof ApiError)) {
    return UNEXPECTED
  }
  if (caught.status === 401) {
    return caught.message || '用户名或密码错误'
  }
  if (caught.status === 503) {
    return UNAVAILABLE
  }
  //
  // Anything else is replaced wholesale rather than shown. A 500 carries
  // whatever the server happened to say, which can be a driver string.
  //
  return UNEXPECTED
}

async function submit() {
  if (!canSubmit.value || submitting.value) {
    return
  }
  submitting.value = true
  failure.value = null
  try {
    await auth.login(username.value.trim(), password.value)
    //
    // Cleared on the way out rather than left in a ref that outlives the
    // navigation.
    //
    password.value = ''
    await router.push({ name: 'user-home' })
  } catch (caught) {
    failure.value = describe(caught)
  } finally {
    submitting.value = false
  }
}
</script>

<template>
  <section class="login" aria-labelledby="login-title">
    <h1 id="login-title" class="login__title">登录</h1>
    <p class="login__hint">请输入管理员为你创建的账户。</p>

    <!--
      A real form with a submit handler, and never method="get": a GET form
      would put the password in the url, the browser history and every access
      log between here and the server.
    -->
    <form class="login__form" method="post" @submit.prevent="submit">
      <label class="login__field">
        <span class="login__label">用户名</span>
        <input
          v-model="username"
          class="login__input"
          name="username"
          type="text"
          autocomplete="username"
          :disabled="submitting"
        />
      </label>

      <label class="login__field">
        <span class="login__label">密码</span>
        <input
          v-model="password"
          class="login__input"
          name="password"
          type="password"
          autocomplete="current-password"
          :disabled="submitting"
        />
      </label>

      <p v-if="failure" class="login__error" role="alert">{{ failure }}</p>

      <button
        type="submit"
        class="login__submit"
        :disabled="!canSubmit || submitting"
      >
        {{ submitting ? '正在登录…' : '登录' }}
      </button>
    </form>
  </section>
</template>

<style scoped>
.login { max-width: 22rem; margin: 0 auto; padding: var(--space-5); background: var(--color-surface); border: 1px solid var(--color-border); border-radius: var(--radius-2); }
.login__title { margin: 0; font-size: 1.375rem; }
.login__hint { margin: var(--space-2) 0 var(--space-4); color: var(--color-muted); font-size: 0.8125rem; }
.login__form { display: grid; gap: var(--space-3); }
.login__field { display: grid; gap: var(--space-1); }
.login__label { font-size: 0.75rem; color: var(--color-muted); }
.login__input { width: 100%; padding: var(--space-2); font: inherit; color: inherit; background: var(--color-background); border: 1px solid var(--color-border); border-radius: var(--radius-1); }
.login__input:disabled { opacity: 0.6; cursor: not-allowed; }
.login__error { margin: 0; color: #a12a2a; font-size: 0.8125rem; }
.login__submit { padding: var(--space-2) var(--space-4); font: inherit; font-weight: 600; color: #fff; background: var(--color-accent); border: 1px solid var(--color-accent); border-radius: var(--radius-1); cursor: pointer; }
.login__submit:disabled { opacity: 0.55; cursor: not-allowed; border-style: dashed; }

@media (prefers-color-scheme: dark) {
  .login__error { color: #f0a2a2; }
}
</style>
