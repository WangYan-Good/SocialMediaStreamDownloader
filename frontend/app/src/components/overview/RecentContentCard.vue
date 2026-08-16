<script setup lang="ts">
import { RouterLink } from 'vue-router'

import {
  recordedLiveStatusLabel,
  savedCountLabel,
} from '@/components/library/libraryPresentation'
import { formatTimestamp } from '@/utils/time'
import type { LibraryLive, LibraryPost } from '@/types/library'

defineProps<{
  post: LibraryPost | null
  postError: string | null
  live: LibraryLive | null
  liveError: string | null
}>()
</script>

<template>
  <section class="card" aria-labelledby="overview-content-heading">
    <div class="card__head">
      <h2 id="overview-content-heading" class="card__title">最近内容</h2>
      <RouterLink class="card__link" :to="{ name: 'library' }">前往媒体库</RouterLink>
    </div>

    <h3 class="card__subtitle">最近下载的作品</h3>
    <p v-if="postError" class="card__notice" role="status">{{ postError }}</p>
    <p v-else-if="!post" class="card__muted">还没有下载记录。</p>
    <dl v-else class="facts">
      <div class="facts__row"><dt>文案</dt><dd>{{ post.desc || '（无文案）' }}</dd></div>
      <div class="facts__row"><dt>创作者</dt><dd>{{ post.nickname ?? post.owner_user_id ?? '—' }}</dd></div>
      <div class="facts__row"><dt>下载时间</dt><dd>{{ formatTimestamp(post.downloaded_at) }}</dd></div>
      <!--
        The recorded outcome, not a claim about files on disk - and no cover
        image, because aweme_record keeps no cover url and fetching one would
        mean asking the platform to decorate a dashboard.
      -->
      <div class="facts__row"><dt>下载记录</dt><dd>{{ savedCountLabel(post.saved_count, post.media_count) }}</dd></div>
    </dl>

    <h3 class="card__subtitle">最近的直播记录</h3>
    <p v-if="liveError" class="card__notice" role="status">{{ liveError }}</p>
    <p v-else-if="!live" class="card__muted">还没有直播记录。</p>
    <dl v-else class="facts">
      <div class="facts__row"><dt>标题</dt><dd>{{ live.title ?? '—' }}</dd></div>
      <div class="facts__row"><dt>创作者</dt><dd>{{ live.nickname ?? live.owner_user_id ?? '—' }}</dd></div>
      <div class="facts__row"><dt>观察时间</dt><dd>{{ formatTimestamp(live.observed_at) }}</dd></div>
      <!--
        Past tense, always. Whether that room is live at this moment is only
        answerable by a probe, which this page deliberately never runs.
      -->
      <div class="facts__row"><dt>记录状态</dt><dd>{{ recordedLiveStatusLabel(live.room_status) }}</dd></div>
    </dl>
  </section>
</template>

<style scoped>
.card { padding: var(--space-4); background: var(--color-surface); border: 1px solid var(--color-border); border-radius: var(--radius-2); }
.card__head { display: flex; flex-wrap: wrap; align-items: baseline; gap: var(--space-3); margin-bottom: var(--space-2); }
.card__title { margin: 0; font-size: 1rem; }
.card__link { margin-left: auto; color: var(--color-accent); text-decoration: underline; font-size: 0.8125rem; }
.card__subtitle { margin: var(--space-3) 0 var(--space-2); font-size: 0.8125rem; color: var(--color-muted); }
.card__notice { margin: 0; padding: var(--space-2) var(--space-3); background: var(--color-background); border: 1px solid var(--color-border); border-radius: var(--radius-1); font-size: 0.8125rem; }
.card__muted { margin: 0; color: var(--color-muted); font-size: 0.8125rem; }
.facts { margin: 0; display: grid; gap: var(--space-2); }
.facts__row { display: grid; grid-template-columns: 5rem 1fr; gap: var(--space-3); align-items: baseline; }
.facts__row dt { color: var(--color-muted); font-size: 0.8125rem; }
.facts__row dd { margin: 0; font-size: 0.875rem; overflow-wrap: anywhere; }
</style>
