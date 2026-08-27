<script setup lang="ts">
import { ref, watch } from 'vue'

import { credentialNotice } from '@/components/creators/creatorPresentation'
import { isHttpUrl } from '@/utils/url'
import type { OwnerCredential, OwnerProfile } from '@/types/owner'
import type { PersonIdentityInspection, PersonRole } from '@/types/person'

const props = defineProps<{
  platformProfile: OwnerProfile | null
  platformCredential: OwnerCredential | null
  platformMessage: string | null
  platformError: string | null
  platformLoading: boolean
  localInspection: PersonIdentityInspection | null
  localError: string | null
  localLoading: boolean
}>()

const emit = defineEmits<{ viewPerson: [personId: number] }>()

const avatarFailed = ref(false)
watch(() => props.platformProfile?.avatar_url, () => {
  avatarFailed.value = false
})

const ROLE_LABELS: Readonly<Record<PersonRole, string>> = {
  main: '主账号',
  alt: '备用账号',
  matrix: '矩阵账号',
}

function formatCount(value: number | null): string {
  return value === null ? '—' : value.toLocaleString('zh-CN')
}
</script>

<template>
  <div class="lookup-result">
    <section class="lookup-card" aria-labelledby="lookup-platform-heading">
      <h2 id="lookup-platform-heading" class="lookup-card__title">当前平台信息</h2>
      <p v-if="platformLoading" class="lookup-card__muted">正在读取当前平台信息…</p>
      <p v-else-if="platformError" class="lookup-card__notice" role="alert">
        {{ platformError }}
      </p>
      <template v-else-if="platformProfile">
        <div class="lookup-profile">
          <img
            v-if="isHttpUrl(platformProfile.avatar_url) && !avatarFailed"
            class="lookup-profile__avatar"
            :src="platformProfile.avatar_url ?? ''"
            alt=""
            @error="avatarFailed = true"
          />
          <div v-else class="lookup-profile__avatar lookup-profile__avatar--empty" aria-label="无头像">
            无头像
          </div>
          <div>
            <p class="lookup-profile__name">{{ platformProfile.nickname ?? '未命名主播' }}</p>
            <p class="lookup-card__muted">抖音号 {{ platformProfile.unique_id ?? '—' }}</p>
            <p v-if="platformProfile.signature" class="lookup-profile__signature">
              {{ platformProfile.signature }}
            </p>
          </div>
        </div>
        <dl class="lookup-facts lookup-facts--stats">
          <div><dt>关注</dt><dd>{{ formatCount(platformProfile.following_count) }}</dd></div>
          <div><dt>粉丝</dt><dd>{{ formatCount(platformProfile.follower_count) }}</dd></div>
          <div><dt>作品</dt><dd>{{ formatCount(platformProfile.aweme_count) }}</dd></div>
          <div><dt>获赞</dt><dd>{{ formatCount(platformProfile.total_favorited) }}</dd></div>
        </dl>
        <dl class="lookup-facts">
          <div><dt>uid</dt><dd class="lookup-facts__mono">{{ platformProfile.uid ?? '—' }}</dd></div>
          <div><dt>sec_user_id</dt><dd class="lookup-facts__mono">{{ platformProfile.sec_user_id ?? '—' }}</dd></div>
        </dl>
      </template>
      <p v-else-if="platformMessage" class="lookup-card__notice" role="status">
        {{ platformMessage }}
      </p>
      <p v-else class="lookup-card__muted">主播详情暂时不可用。</p>
      <p
        v-if="platformCredential && credentialNotice(platformCredential.expires_in_days)"
        class="lookup-card__credential"
      >
        {{ credentialNotice(platformCredential.expires_in_days) }}
      </p>
    </section>

    <section class="lookup-card" aria-labelledby="lookup-local-heading">
      <h2 id="lookup-local-heading" class="lookup-card__title">本地记录</h2>
      <p v-if="localLoading" class="lookup-card__muted">正在检查本地记录…</p>
      <p v-else-if="localError" class="lookup-card__notice" role="alert">{{ localError }}</p>
      <template v-else-if="localInspection">
        <p class="lookup-card__state">
          {{ localInspection.known_account ? '本地已记录' : '本地尚无记录' }}
        </p>
        <dl class="lookup-facts">
          <div><dt>账号 ID</dt><dd class="lookup-facts__mono">{{ localInspection.owner.owner_user_id }}</dd></div>
          <div><dt>sec_user_id</dt><dd class="lookup-facts__mono">{{ localInspection.owner.sec_user_id ?? '—' }}</dd></div>
          <div><dt>当前昵称</dt><dd>{{ localInspection.owner.nickname ?? '—' }}</dd></div>
        </dl>
      </template>
    </section>

    <section class="lookup-card" aria-labelledby="lookup-person-heading">
      <h2 id="lookup-person-heading" class="lookup-card__title">人物归属</h2>
      <p v-if="localLoading" class="lookup-card__muted">正在检查人物归属…</p>
      <p v-else-if="localError" class="lookup-card__notice" role="status">
        暂时无法确认人物归属
      </p>
      <template v-else-if="localInspection?.assignment">
        <p class="lookup-card__state">已归属人物</p>
        <dl class="lookup-facts">
          <div><dt>人物</dt><dd>{{ localInspection.assignment.display_name }}</dd></div>
          <div><dt>角色</dt><dd>{{ ROLE_LABELS[localInspection.assignment.role] }}</dd></div>
        </dl>
        <button
          type="button"
          class="lookup-card__action"
          @click="emit('viewPerson', localInspection.assignment.person_id)"
        >
          查看人物
        </button>
      </template>
      <p v-else-if="localInspection" class="lookup-card__muted">
        尚未归属人物，可在“人物”页进行管理。
      </p>
    </section>
  </div>
</template>

<style scoped>
.lookup-result { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: var(--space-4); align-items: start; }
.lookup-card { display: grid; gap: var(--space-3); padding: var(--space-4); background: var(--color-surface); border: 1px solid var(--color-border); border-radius: var(--radius-2); }
.lookup-card__title { margin: 0; font-size: 1rem; }
.lookup-card__muted, .lookup-card__state, .lookup-card__credential { margin: 0; color: var(--color-muted); font-size: 0.8125rem; }
.lookup-card__state { color: var(--color-text); font-weight: 600; }
.lookup-card__notice { margin: 0; padding: var(--space-3); background: var(--color-background); border: 1px solid var(--color-border); border-radius: var(--radius-1); font-size: 0.8125rem; }
.lookup-card__credential { padding-top: var(--space-2); border-top: 1px solid var(--color-border); }
.lookup-profile { display: flex; gap: var(--space-3); align-items: center; min-width: 0; }
.lookup-profile__avatar { flex: 0 0 auto; width: 56px; height: 56px; border-radius: 50%; object-fit: cover; }
.lookup-profile__avatar--empty { display: grid; place-items: center; color: var(--color-muted); background: var(--color-background); border: 1px solid var(--color-border); font-size: 0.6875rem; }
.lookup-profile__name { margin: 0; font-weight: 600; }
.lookup-profile__signature { margin: var(--space-1) 0 0; font-size: 0.8125rem; overflow-wrap: anywhere; }
.lookup-facts { display: grid; gap: var(--space-2); margin: 0; font-size: 0.8125rem; }
.lookup-facts--stats { grid-template-columns: repeat(2, minmax(0, 1fr)); }
.lookup-facts div { display: grid; grid-template-columns: minmax(5rem, auto) minmax(0, 1fr); gap: var(--space-2); }
.lookup-facts dt { color: var(--color-muted); }
.lookup-facts dd { margin: 0; overflow-wrap: anywhere; }
.lookup-facts__mono { font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace; }
.lookup-card__action { justify-self: start; padding: var(--space-2) var(--space-3); font: inherit; font-size: 0.8125rem; color: inherit; background: var(--color-surface); border: 1px solid var(--color-border); border-radius: var(--radius-1); cursor: pointer; }
@media (max-width: 60rem) { .lookup-result { grid-template-columns: 1fr; } }
</style>
