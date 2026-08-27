<script setup lang="ts">
import { computed, ref } from 'vue'

const props = defineProps<{ loading: boolean }>()
const emit = defineEmits<{ submit: [input: string]; changed: [] }>()

const input = ref('')
const canSubmit = computed(() => input.value.trim().length > 0 && !props.loading)

function noteInputChanged() {
  emit('changed')
}

function submit() {
  if (canSubmit.value) {
    emit('submit', input.value.trim())
  }
}
</script>

<template>
  <form class="lookup-form" @submit.prevent="submit">
    <label class="lookup-form__field">
      <span class="lookup-form__label">主播主页</span>
      <input
        v-model="input"
        name="creator-lookup"
        class="lookup-form__input"
        type="text"
        autocomplete="off"
        placeholder="粘贴主播主页分享文本或链接"
        @input="noteInputChanged"
      />
    </label>
    <button type="submit" class="lookup-form__submit" :disabled="!canSubmit">
      {{ loading ? '正在查询…' : '查询' }}
    </button>
  </form>
</template>

<style scoped>
.lookup-form { display: flex; align-items: flex-end; gap: var(--space-3); }
.lookup-form__field { display: flex; flex: 1 1 24rem; flex-direction: column; gap: var(--space-1); }
.lookup-form__label { color: var(--color-muted); font-size: 0.75rem; }
.lookup-form__input { width: 100%; padding: var(--space-2) var(--space-3); font: inherit; color: inherit; background: var(--color-surface); border: 1px solid var(--color-border); border-radius: var(--radius-1); }
.lookup-form__submit { padding: var(--space-2) var(--space-4); font: inherit; font-size: 0.8125rem; color: inherit; background: var(--color-surface); border: 1px solid var(--color-border); border-radius: var(--radius-1); cursor: pointer; }
.lookup-form__submit:disabled { cursor: not-allowed; opacity: 0.55; border-style: dashed; }
@media (max-width: 36rem) { .lookup-form { align-items: stretch; flex-direction: column; } }
</style>
