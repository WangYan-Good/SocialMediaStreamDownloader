<script setup lang="ts">
const input = defineModel<string>({ required: true })

defineProps<{
  canResolve: boolean
  resolving: boolean
  locked: boolean
  error: string | null
}>()

defineEmits<{ resolve: [] }>()
</script>

<template>
  <section class="batch-input card">
    <h2 class="card__title">粘贴多个资源</h2>
    <p class="card__hint">
      最多 20 个不同链接。服务端负责提取、去重并逐项解析，不会在解析后自动执行。
    </p>
    <label class="field">
      <span class="field__label">完整分享文本</span>
      <textarea
        v-model="input"
        class="field__input"
        rows="7"
        :disabled="locked"
        placeholder="每行可放一个链接，也可以直接粘贴多段分享文本"
      ></textarea>
    </label>
    <p v-if="error" class="card__error" role="alert">{{ error }}</p>
    <button
      type="button"
      class="button button--primary"
      :disabled="!canResolve || locked"
      @click="$emit('resolve')"
    >
      {{ resolving ? '正在逐项解析…' : '批量解析' }}
    </button>
  </section>
</template>

<style scoped>
.card { display: grid; gap: var(--space-3); padding: var(--space-4); background: var(--color-surface); border: 1px solid var(--color-border); border-radius: var(--radius-2); }
.card__title { margin: 0; font-size: 1rem; }
.card__hint, .field__label { color: var(--color-muted); font-size: 0.8125rem; }
.card__hint { margin: calc(-1 * var(--space-2)) 0 0; }
.field { display: grid; gap: var(--space-1); }
.field__input { width: 100%; padding: var(--space-2); font: inherit; color: inherit; background: var(--color-background); border: 1px solid var(--color-border); border-radius: var(--radius-1); resize: vertical; }
.card__error { margin: 0; color: #a12a2a; font-size: 0.8125rem; }
.button { justify-self: start; padding: var(--space-2) var(--space-4); font: inherit; border: 1px solid var(--color-border); border-radius: var(--radius-1); cursor: pointer; }
.button--primary { color: #fff; background: var(--color-accent); border-color: var(--color-accent); }
.button:disabled, .field__input:disabled { opacity: 0.55; cursor: not-allowed; }
</style>
