<script setup lang="ts">
import { computed } from 'vue'

import {
  downloadActionLabel,
  platformLabel,
  resourceKindLabel,
} from '@/components/new-download/downloadPresentation'
import type { ResolvedResource } from '@/types/resolution'

const props = defineProps<{
  resolved: ResolvedResource
  canCreate: boolean
  creating: boolean
  needsOwnerConfirmation: boolean
  error: string | null
  receiptExpired: boolean
}>()

const ownerConfirmed = defineModel<boolean>('ownerConfirmed', { required: true })

defineEmits<{ create: []; reresolve: [] }>()

const kind = computed(() => resourceKindLabel(props.resolved.resource_type))
const platform = computed(() => platformLabel(props.resolved.platform))
const action = computed(() => downloadActionLabel(props.resolved.resource_type))
</script>

<template>
  <section class="card">
    <h2 class="card__title">识别结果</h2>
    <!--
      Identity-level, and that is the whole answer the server gives. A nickname
      or a cover would each cost another platform request and two of the three
      need a login, so nothing of that kind is claimed here.

      What used to sit in this list - the aweme id, the sec_user_id, the
      followed short link, the receipt's remaining life - is all still doing its
      job underneath. None of it is something a user has to read to know whether
      the right thing was recognised; the kind of resource and the link they
      pasted answer that.
    -->
    <p class="card__hint">请确认下面的内容是否正确，确认后即可开始下载。</p>

    <dl class="facts">
      <div class="facts__row">
        <dt>内容类型</dt>
        <dd>{{ kind }}</dd>
      </div>
      <div class="facts__row">
        <dt>来源</dt>
        <dd>{{ platform }}</dd>
      </div>
      <div class="facts__row">
        <dt>你粘贴的链接</dt>
        <dd>
          <a :href="resolved.source_url" target="_blank" rel="noopener noreferrer">
            {{ resolved.source_url }}
          </a>
        </dd>
      </div>
    </dl>

    <div v-if="needsOwnerConfirmation" class="confirm">
      <label class="confirm__label">
        <input v-model="ownerConfirmed" type="checkbox" class="confirm__box" />
        <span>我确认要下载该主播的<strong>全部作品</strong></span>
      </label>
      <p class="confirm__note">这会遍历该主播的整个作品列表，可能需要很长时间。</p>
    </div>

    <p v-if="error" class="card__error" role="alert">{{ error }}</p>

    <div class="card__actions">
      <button
        v-if="!receiptExpired"
        type="button"
        class="button button--primary"
        :disabled="!canCreate || creating"
        @click="$emit('create')"
      >
        {{ creating ? '正在创建…' : action }}
      </button>
      <button v-else type="button" class="button" @click="$emit('reresolve')">
        重新识别
      </button>
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

.facts {
  margin: 0;
  display: grid;
  gap: var(--space-2);
}

.facts__row {
  display: grid;
  grid-template-columns: 7rem 1fr;
  gap: var(--space-3);
  align-items: baseline;
}

.facts__row dt {
  color: var(--color-muted);
  font-size: 0.8125rem;
}

.facts__row dd {
  margin: 0;
  font-size: 0.875rem;
  /* A resolved url is long and has no spaces to break at. */
  overflow-wrap: anywhere;
}


.confirm {
  margin-top: var(--space-4);
  padding: var(--space-3);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-1);
  background: var(--color-background);
}

.confirm__label {
  display: flex;
  gap: var(--space-2);
  align-items: flex-start;
  font-size: 0.875rem;
  cursor: pointer;
}

.confirm__box {
  margin-top: 3px;
}

.confirm__note {
  margin: var(--space-1) 0 0 calc(var(--space-2) + 13px);
  color: var(--color-muted);
  font-size: 0.8125rem;
}

.card__error {
  margin: var(--space-3) 0 0;
  color: #a12a2a;
  font-size: 0.8125rem;
}

.card__actions {
  margin-top: var(--space-4);
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

.button:disabled {
  opacity: 0.55;
  cursor: not-allowed;
  border-style: dashed;
}

@media (prefers-color-scheme: dark) {
  .card__error {
    color: #f0a2a2;
  }
}
</style>
