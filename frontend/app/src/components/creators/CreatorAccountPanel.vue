<script setup lang="ts">
import { ref } from 'vue'

import CreatorPostTable from '@/components/creators/CreatorPostTable.vue'
import {
  PROBE_STATE_LABELS,
  credentialNotice,
  formatCount,
  isLivingNow,
  lastKnownLiveLabel,
  sessionStatusLabel,
} from '@/components/creators/creatorPresentation'
import { formatTaskTime } from '@/components/tasks/taskPresentation'
import { isHttpUrl } from '@/utils/url'
import type { HistoryOwner, LiveProbeItem, LiveSession } from '@/types/history'
import type { OwnerPost, OwnerRead } from '@/types/owner'

const props = defineProps<{
  owner: HistoryOwner | null
  profile: OwnerRead | null
  probeItem: LiveProbeItem | null
  sessions: LiveSession[]
  sessionsLoading: boolean
  sessionsError: string | null
  posts: OwnerPost[]
  postsLoading: boolean
  postsError: string | null
  hasMorePosts: boolean
  loadedPostCount: number
  selectedAwemeIds: string[]
  actionBusy: boolean
}>()

const emit = defineEmits<{
  openSessions: []
  openPosts: []
  loadMore: []
  togglePost: [string]
  selectAll: []
  clearSelection: []
  downloadSelected: []
  downloadAll: []
  record: []
  close: []
}>()

type Section = 'overview' | 'live' | 'posts'
const section = ref<Section>('overview')

//
// Sections are lazy: opening the panel must not read sessions and posts for an
// account the user only glanced at.
//
function show(next: Section) {
  section.value = next
  if (next === 'live') {
    emit('openSessions')
  }
  if (next === 'posts') {
    emit('openPosts')
  }
}

const allDownloadConfirmed = ref(false)
</script>

<template>
  <aside class="panel" aria-labelledby="creator-panel-heading">
    <div class="panel__head">
      <h2 id="creator-panel-heading" class="panel__title">
        {{ profile?.owner?.nickname ?? owner?.nickname ?? '主播' }}
      </h2>
      <button type="button" class="panel__close" @click="emit('close')">关闭</button>
    </div>

    <nav class="panel__tabs" aria-label="主播信息分区">
      <button
        v-for="tab in (['overview', 'live', 'posts'] as Section[])"
        :key="tab"
        type="button"
        class="panel__tab"
        :class="{ 'panel__tab--active': section === tab }"
        :aria-current="section === tab ? 'true' : undefined"
        @click="show(tab)"
      >
        {{ tab === 'overview' ? '概览' : tab === 'live' ? '直播' : '作品' }}
      </button>
    </nav>

    <section v-if="section === 'overview'">
      <div v-if="profile?.owner" class="profile">
        <img
          v-if="isHttpUrl(profile.owner.avatar_url)"
          class="profile__avatar"
          :src="profile.owner.avatar_url ?? ''"
          alt=""
        />
        <div>
          <p class="profile__name">{{ profile.owner.nickname }}</p>
          <p class="profile__muted">抖音号 {{ profile.owner.unique_id ?? '—' }}</p>
          <p v-if="profile.owner.signature" class="profile__signature">
            {{ profile.owner.signature }}
          </p>
          <p class="profile__muted">
            粉丝 {{ formatCount(profile.owner.follower_count) }} ·
            关注 {{ formatCount(profile.owner.following_count) }} ·
            作品 {{ formatCount(profile.owner.aweme_count) }} ·
            获赞 {{ formatCount(profile.owner.total_favorited) }}
          </p>
        </div>
      </div>
      <!--
        The profile and the post list are read independently by the backend, so
        one failing must not hide the other.
      -->
      <p v-else-if="profile?.owner_message" class="panel__notice" role="status">
        {{ profile.owner_message }}
      </p>

      <p
        v-if="profile && credentialNotice(profile.credential.expires_in_days)"
        class="panel__notice"
        role="status"
      >
        {{ credentialNotice(profile.credential.expires_in_days) }}
      </p>

      <dl v-if="owner" class="facts">
        <div class="facts__row"><dt>owner_user_id</dt><dd class="facts__mono">{{ owner.owner_user_id }}</dd></div>
        <div class="facts__row"><dt>sec_user_id</dt><dd class="facts__mono">{{ owner.sec_user_id ?? '—' }}</dd></div>
        <div class="facts__row"><dt>目录名</dt><dd>{{ owner.directory_name ?? '—' }}</dd></div>
        <div class="facts__row"><dt>收藏 / 评分</dt><dd>{{ owner.favorite ? `★ ${formatCount(owner.score)}` : '—' }}</dd></div>
        <div class="facts__row"><dt>开播次数</dt><dd>{{ formatCount(owner.actived_count) }}</dd></div>
        <div class="facts__row"><dt>账号状态</dt><dd>{{ owner.user_status ?? '—' }}</dd></div>
        <div class="facts__row"><dt>最后已知状态</dt><dd>{{ lastKnownLiveLabel(owner.last_live_status) }}</dd></div>
        <div class="facts__row"><dt>最后检查</dt><dd>{{ formatTaskTime(owner.last_checked_at) }}</dd></div>
      </dl>
    </section>

    <section v-else-if="section === 'live'">
      <p class="panel__line">
        本次检查：{{ probeItem ? PROBE_STATE_LABELS[probeItem.state] : '未检查' }}
        <span v-if="probeItem?.cached" class="panel__muted">（缓存）</span>
      </p>
      <!--
        Offered only when *this* probe said the room is live. The database cache
        is not evidence about now, and a record button driven by it would start
        a recording of nothing.
      -->
      <button
        v-if="isLivingNow(probeItem?.state)"
        type="button"
        class="panel__action"
        :disabled="actionBusy"
        @click="emit('record')"
      >
        开始录制
      </button>

      <p v-if="sessionsLoading" class="panel__muted">正在读取直播记录…</p>
      <p v-else-if="sessionsError" class="panel__notice" role="alert">{{ sessionsError }}</p>
      <p v-else-if="!sessions.length" class="panel__muted">没有直播记录。</p>
      <div v-else class="table-scroll">
        <table class="table">
          <thead>
            <tr>
              <th scope="col">时间</th><th scope="col">房间</th><th scope="col">标题</th>
              <th scope="col">状态</th><th scope="col">开始</th><th scope="col">结束</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="(row, index) in sessions" :key="`${row.room_id}-${index}`">
              <td class="panel__muted">{{ formatTaskTime(row.observed_at) }}</td>
              <td class="facts__mono">{{ row.room_id ?? '—' }}</td>
              <td>{{ row.title ?? '—' }}</td>
              <td>{{ sessionStatusLabel(row.room_status) }}</td>
              <td class="panel__muted">{{ formatTaskTime(row.start_time) }}</td>
              <td class="panel__muted">{{ formatTaskTime(row.finish_time) }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </section>

    <section v-else>
      <p v-if="!owner?.sec_user_id && !profile" class="panel__notice" role="status">
        该历史记录没有可用于读取作品的 sec_user_id
      </p>
      <template v-else>
        <p class="panel__line">
          已加载 {{ loadedPostCount }} 个作品
          <span v-if="profile?.owner?.aweme_count" class="panel__muted">
            （平台统计 {{ profile.owner.aweme_count }}）
          </span>
        </p>

        <p v-if="postsError" class="panel__notice" role="alert">{{ postsError }}</p>

        <CreatorPostTable
          :posts="posts"
          :selected-aweme-ids="selectedAwemeIds"
          @toggle="emit('togglePost', $event)"
        />

        <div class="panel__actions">
          <button type="button" class="panel__action" @click="emit('selectAll')">
            全选已加载
          </button>
          <button type="button" class="panel__action" @click="emit('clearSelection')">
            清空选择
          </button>
          <button
            type="button"
            class="panel__action"
            :disabled="!hasMorePosts || postsLoading"
            @click="emit('loadMore')"
          >
            {{ postsLoading ? '正在读取…' : hasMorePosts ? '加载更多' : '没有更多' }}
          </button>
          <button
            type="button"
            class="panel__action panel__action--primary"
            :disabled="!selectedAwemeIds.length || actionBusy"
            @click="emit('downloadSelected')"
          >
            下载选中（{{ selectedAwemeIds.length }}）
          </button>
        </div>

        <div class="confirm">
          <label class="confirm__label">
            <input v-model="allDownloadConfirmed" type="checkbox" />
            <span>我确认要下载该主播的<strong>全部作品</strong></span>
          </label>
          <button
            type="button"
            class="panel__action"
            :disabled="!allDownloadConfirmed || actionBusy"
            @click="emit('downloadAll')"
          >
            下载全部作品
          </button>
        </div>
      </template>
    </section>
  </aside>
</template>

<style scoped>
.panel { padding: var(--space-4); background: var(--color-surface); border: 1px solid var(--color-border); border-radius: var(--radius-2); }
.panel__head { display: flex; align-items: center; gap: var(--space-3); margin-bottom: var(--space-3); }
.panel__title { margin: 0; font-size: 1rem; }
.panel__close { margin-left: auto; padding: 2px var(--space-3); font: inherit; font-size: 0.8125rem; color: inherit; background: var(--color-surface); border: 1px solid var(--color-border); border-radius: var(--radius-1); cursor: pointer; }
.panel__tabs { display: flex; gap: var(--space-2); margin-bottom: var(--space-3); border-bottom: 1px solid var(--color-border); }
.panel__tab { padding: var(--space-2) var(--space-3); font: inherit; font-size: 0.875rem; color: var(--color-muted); background: none; border: none; border-bottom: 2px solid transparent; cursor: pointer; }
.panel__tab--active { color: var(--color-text); border-bottom-color: var(--color-accent); font-weight: 600; }
.panel__line { margin: 0 0 var(--space-3); font-size: 0.875rem; }
.panel__muted { color: var(--color-muted); font-size: 0.8125rem; }
.panel__notice { margin: var(--space-2) 0; padding: var(--space-2) var(--space-3); background: var(--color-background); border: 1px solid var(--color-border); border-radius: var(--radius-1); font-size: 0.8125rem; }
.panel__actions { display: flex; flex-wrap: wrap; gap: var(--space-2); margin-top: var(--space-3); }
.panel__action { padding: var(--space-2) var(--space-3); font: inherit; font-size: 0.8125rem; color: inherit; background: var(--color-surface); border: 1px solid var(--color-border); border-radius: var(--radius-1); cursor: pointer; }
.panel__action--primary { background: var(--color-accent); border-color: var(--color-accent); color: #fff; }
.panel__action:disabled { opacity: 0.55; cursor: not-allowed; border-style: dashed; }
.confirm { display: flex; flex-wrap: wrap; align-items: center; gap: var(--space-3); margin-top: var(--space-4); padding: var(--space-3); background: var(--color-background); border: 1px solid var(--color-border); border-radius: var(--radius-1); font-size: 0.875rem; }
.confirm__label { display: flex; gap: var(--space-2); align-items: center; cursor: pointer; }
.profile { display: flex; gap: var(--space-3); margin-bottom: var(--space-3); }
.profile__avatar { width: 56px; height: 56px; border-radius: 50%; object-fit: cover; }
.profile__name { margin: 0; font-weight: 600; }
.profile__muted { margin: 2px 0 0; color: var(--color-muted); font-size: 0.8125rem; }
.profile__signature { margin: var(--space-1) 0 0; font-size: 0.8125rem; overflow-wrap: anywhere; }
.facts { margin: 0; display: grid; gap: var(--space-2); }
.facts__row { display: grid; grid-template-columns: 8rem 1fr; gap: var(--space-3); align-items: baseline; }
.facts__row dt { color: var(--color-muted); font-size: 0.8125rem; }
.facts__row dd { margin: 0; font-size: 0.875rem; overflow-wrap: anywhere; }
.facts__mono { font-family: ui-monospace, SFMono-Regular, Menlo, monospace; font-size: 0.8125rem; }
.table-scroll { overflow-x: auto; }
.table { width: 100%; border-collapse: collapse; font-size: 0.875rem; }
.table th, .table td { padding: var(--space-2) var(--space-3); border-bottom: 1px solid var(--color-border); text-align: left; white-space: nowrap; }
.table th { color: var(--color-muted); font-size: 0.75rem; font-weight: 600; }
</style>
