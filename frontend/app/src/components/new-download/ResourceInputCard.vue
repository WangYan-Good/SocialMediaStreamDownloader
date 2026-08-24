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
  <section class="card">
    <h2 class="card__title">粘贴分享链接</h2>
    <p class="card__hint">
      作品、主播主页、直播都可以。整段分享文字直接粘贴即可，会自动从中取出链接。
    </p>

    <label class="field">
      <span class="field__label">分享文本或链接</span>
      <textarea
        v-model="input"
        class="field__input"
        rows="4"
        :disabled="locked"
        placeholder="4.33 复制打开抖音，看看【…的作品】 https://v.douyin.com/…"
      ></textarea>
    </label>

    <!--
      Assertive rather than polite: this replaces what the user just asked for,
      and they are waiting on it.
    -->
    <p v-if="error" class="field__error" role="alert">{{ error }}</p>

    <div class="card__actions">
      <button
        type="button"
        class="button button--primary"
        :disabled="!canResolve || locked"
        @click="$emit('resolve')"
      >
        {{ resolving ? '正在识别…' : '识别内容' }}
      </button>
      <span v-if="locked" class="card__note">当前下载进行中，如需重新开始请等待其结束。</span>
    </div>
  </section>
</template>

<style scoped>
.card {
  padding: var(--space-4);
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-2);
}

.card__title {
  margin: 0;
  font-size: 1rem;
}

.card__hint {
  margin: var(--space-1) 0 var(--space-3);
  color: var(--color-muted);
  font-size: 0.8125rem;
}

.field {
  display: block;
}

.field__label {
  display: block;
  margin-bottom: var(--space-1);
  font-size: 0.8125rem;
  color: var(--color-muted);
}

.field__input {
  width: 100%;
  padding: var(--space-2);
  font: inherit;
  color: inherit;
  background: var(--color-background);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-1);
  resize: vertical;
}

.field__input:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.field__error {
  margin: var(--space-2) 0 0;
  color: #a12a2a;
  font-size: 0.8125rem;
}

.card__actions {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  margin-top: var(--space-3);
}

.card__note {
  color: var(--color-muted);
  font-size: 0.8125rem;
}

.button {
  padding: var(--space-2) var(--space-4);
  font: inherit;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-1);
  background: var(--color-surface);
  color: inherit;
  cursor: pointer;
}

.button--primary {
  background: var(--color-accent);
  border-color: var(--color-accent);
  color: #fff;
}

/*
 * Disabled is stated three ways - cursor, opacity and a dashed edge - because
 * a button that is merely paler reads as a styling choice, not as unavailable.
 */
.button:disabled {
  opacity: 0.55;
  cursor: not-allowed;
  border-style: dashed;
}

@media (prefers-color-scheme: dark) {
  .field__error {
    color: #f0a2a2;
  }
}
</style>
