<script setup lang="ts">
import { computed, ref, watch } from 'vue'

import type { HistoryOwner, OwnerPreferenceUpdate } from '@/types/history'

const props = defineProps<{
  owner: HistoryOwner
  busy: boolean
  error: string | null
  notice: string | null
}>()

const emit = defineEmits<{ save: [OwnerPreferenceUpdate] }>()

const favorite = ref(false)
const score = ref(0)

function resetDraft() {
  favorite.value = props.owner.favorite
  score.value = props.owner.score ?? 0
}

watch(
  () => [props.owner.owner_user_id, props.owner.favorite, props.owner.score] as const,
  resetDraft,
  { immediate: true },
)

const scoreValid = computed(
  () => Number.isInteger(score.value) && score.value >= 0 && score.value <= 100,
)

const canSave = computed(() => !props.busy && (!favorite.value || scoreValid.value))

function save() {
  if (!canSave.value) {
    return
  }
  emit(
    'save',
    favorite.value
      ? { favorite: true, score: score.value }
      : { favorite: false },
  )
}
</script>

<template>
  <form class="preference" @submit.prevent="save">
    <div class="preference__head">
      <h3 class="preference__title">监听偏好</h3>
      <label class="preference__favorite">
        <input v-model="favorite" type="checkbox" :disabled="busy" />
        <span>收藏主播</span>
      </label>
    </div>

    <div class="preference__score">
      <label for="creator-preference-score">评分</label>
      <input
        id="creator-preference-score"
        v-model.number="score"
        type="range"
        min="0"
        max="100"
        :disabled="!favorite || busy"
      />
      <input
        v-model.number="score"
        class="preference__number"
        type="number"
        min="0"
        max="100"
        :disabled="!favorite || busy"
        aria-label="评分数值"
      />
    </div>

    <p class="preference__hint">
      收藏与评分会持久化，供评分监听入口读取；这里不会动态重建已运行的监听队列。
    </p>
    <p v-if="favorite && !scoreValid" class="preference__error" role="alert">
      评分必须是 0 到 100 的整数。
    </p>
    <p v-else-if="error" class="preference__error" role="alert">{{ error }}</p>
    <p v-if="notice" class="preference__notice" role="status">{{ notice }}</p>

    <button type="submit" class="preference__save" :disabled="!canSave">
      {{ busy ? '正在保存…' : '保存偏好' }}
    </button>
  </form>
</template>

<style scoped>
.preference { display: grid; gap: var(--space-3); margin-top: var(--space-4); padding: var(--space-3); background: var(--color-background); border: 1px solid var(--color-border); border-radius: var(--radius-1); }
.preference__head { display: flex; align-items: center; justify-content: space-between; gap: var(--space-3); }
.preference__title { margin: 0; font-size: 0.9375rem; }
.preference__favorite { display: flex; align-items: center; gap: var(--space-2); font-size: 0.875rem; cursor: pointer; }
.preference__score { display: grid; grid-template-columns: 3rem minmax(8rem, 1fr) 5rem; align-items: center; gap: var(--space-2); font-size: 0.8125rem; }
.preference__number { width: 100%; padding: var(--space-1) var(--space-2); font: inherit; color: inherit; background: var(--color-surface); border: 1px solid var(--color-border); border-radius: var(--radius-1); }
.preference__hint, .preference__notice, .preference__error { margin: 0; font-size: 0.8125rem; }
.preference__hint, .preference__notice { color: var(--color-muted); }
.preference__error { color: #a12a2a; }
.preference__save { justify-self: start; padding: var(--space-2) var(--space-3); font: inherit; font-size: 0.8125rem; color: #fff; background: var(--color-accent); border: 1px solid var(--color-accent); border-radius: var(--radius-1); cursor: pointer; }
.preference__save:disabled, .preference input:disabled { opacity: 0.55; cursor: not-allowed; }
@media (prefers-color-scheme: dark) { .preference__error { color: #f0a2a2; } }
</style>
