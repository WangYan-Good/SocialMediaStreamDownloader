<script setup lang="ts">
import { computed } from 'vue'

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

const KIND_LABELS = {
  post: '作品',
  owner: '主播',
  live: '直播',
} as const

const kind = computed(() => KIND_LABELS[props.resolved.resource_type])

//
// What the button will actually start. Named per resource because "下载" alone
// would say the same thing for one post as for an entire back catalogue.
//
const ACTION_LABELS = {
  post: '下载该作品',
  owner: '下载全部作品',
  live: '开始录制直播',
} as const

const action = computed(() => ACTION_LABELS[props.resolved.resource_type])

const expiresInMinutes = computed(() =>
  Math.max(1, Math.round(props.resolved.expires_in_seconds / 60)),
)
</script>

<template>
  <section class="card">
    <h2 class="card__title">确认资源</h2>
    <!--
      "解析结果", not "预览". The server answers which resource a link names and
      deliberately stops there: a nickname or a cover would cost another
      platform request, and two of the three need a login that has nothing to do
      with reading a url.
    -->
    <p class="card__hint">以下为服务端解析出的资源身份，确认无误后再创建任务。</p>

    <dl class="facts">
      <div class="facts__row">
        <dt>平台</dt>
        <dd>{{ resolved.platform }}</dd>
      </div>
      <div class="facts__row">
        <dt>类型</dt>
        <dd>{{ kind }}</dd>
      </div>
      <div v-if="resolved.resource_type === 'post'" class="facts__row">
        <dt>作品 ID</dt>
        <dd class="facts__mono">{{ resolved.identity.aweme_id }}</dd>
      </div>
      <div v-else-if="resolved.resource_type === 'owner'" class="facts__row">
        <dt>主播 ID</dt>
        <dd class="facts__mono">{{ resolved.identity.sec_user_id }}</dd>
      </div>
      <div class="facts__row">
        <dt>原始链接</dt>
        <dd>
          <a :href="resolved.source_url" target="_blank" rel="noopener noreferrer">
            {{ resolved.source_url }}
          </a>
        </dd>
      </div>
      <div class="facts__row">
        <dt>解析后链接</dt>
        <dd>
          <a :href="resolved.resolved_url" target="_blank" rel="noopener noreferrer">
            {{ resolved.resolved_url }}
          </a>
        </dd>
      </div>
      <div class="facts__row">
        <dt>凭证有效期</dt>
        <dd>约 {{ expiresInMinutes }} 分钟</dd>
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
        重新解析
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

.facts__mono {
  font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
  font-size: 0.8125rem;
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
