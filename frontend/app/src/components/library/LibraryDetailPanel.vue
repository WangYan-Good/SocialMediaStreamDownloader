<script setup lang="ts">
import {
  SOURCE_LABELS,
  TYPE_LABELS,
  recordedLiveStatusLabel,
  savedCountLabel,
} from '@/components/library/libraryPresentation'
import { formatTimestamp } from '@/utils/time'
import type { LibraryLive, LibraryPost } from '@/types/library'

//
// Built from the row already on screen. Reading one record back by id would be
// a request per click for data the list is holding anyway - the N+1 that turns
// a table into a hundred queries.
//
defineProps<{ post: LibraryPost | null; live: LibraryLive | null }>()

defineEmits<{ close: [] }>()
</script>

<template>
  <aside class="panel" aria-labelledby="library-panel-heading">
    <div class="panel__head">
      <h2 id="library-panel-heading" class="panel__title">
        {{ post ? '作品记录' : '直播记录' }}
      </h2>
      <button type="button" class="panel__close" @click="$emit('close')">关闭</button>
    </div>

    <dl v-if="post" class="facts">
      <div class="facts__row"><dt>作品 ID</dt><dd class="facts__mono">{{ post.aweme_id }}</dd></div>
      <div class="facts__row"><dt>类型</dt><dd>{{ post.aweme_type ? TYPE_LABELS[post.aweme_type] : '—' }}</dd></div>
      <div class="facts__row"><dt>创作者</dt><dd>{{ post.nickname ?? post.owner_user_id ?? '—' }}</dd></div>
      <div class="facts__row"><dt>人物</dt><dd>{{ post.person_display_name ?? '未归并' }}</dd></div>
      <div class="facts__row"><dt>文案</dt><dd>{{ post.desc || '（无文案）' }}</dd></div>
      <div class="facts__row"><dt>发布时间</dt><dd>{{ formatTimestamp(post.create_time) }}</dd></div>
      <div class="facts__row"><dt>下载时间</dt><dd>{{ formatTimestamp(post.downloaded_at) }}</dd></div>
      <div class="facts__row"><dt>下载记录</dt><dd>{{ savedCountLabel(post.saved_count, post.media_count) }}</dd></div>
      <!--
        Shown as text so it can be read and copied by hand. Not a link: this
        server has no endpoint that serves a path, and offering one that looks
        clickable would promise a capability the phase deliberately lacks.
      -->
      <div class="facts__row"><dt>保存目录</dt><dd class="facts__path">{{ post.save_dir ?? '—' }}</dd></div>
      <div class="facts__row"><dt>来源</dt><dd>{{ post.source ? SOURCE_LABELS[post.source] : '—' }}</dd></div>
    </dl>

    <template v-else-if="live">
      <p class="panel__note">
        这是数据库中的直播记录，描述当时观察到的状态，不代表现在是否正在直播。
      </p>
      <dl class="facts">
        <div class="facts__row"><dt>房间号</dt><dd class="facts__mono">{{ live.room_id ?? '—' }}</dd></div>
        <div class="facts__row"><dt>创作者</dt><dd>{{ live.nickname ?? live.owner_user_id ?? '—' }}</dd></div>
        <div class="facts__row"><dt>人物</dt><dd>{{ live.person_display_name ?? '未归并' }}</dd></div>
        <div class="facts__row"><dt>标题</dt><dd>{{ live.title ?? '—' }}</dd></div>
        <div class="facts__row"><dt>记录状态</dt><dd>{{ recordedLiveStatusLabel(live.room_status) }}</dd></div>
        <div class="facts__row"><dt>观察时间</dt><dd>{{ formatTimestamp(live.observed_at) }}</dd></div>
        <div class="facts__row"><dt>开始</dt><dd>{{ formatTimestamp(live.start_time) }}</dd></div>
        <div class="facts__row"><dt>结束</dt><dd>{{ formatTimestamp(live.finish_time) }}</dd></div>
        <div class="facts__row"><dt>状态码</dt><dd>{{ live.status_code ?? '—' }}</dd></div>
        <div v-if="live.directory_name" class="facts__row">
          <dt>目录名</dt><dd class="facts__path">{{ live.directory_name }}</dd>
        </div>
      </dl>
    </template>
  </aside>
</template>

<style scoped>
.panel { padding: var(--space-4); background: var(--color-surface); border: 1px solid var(--color-border); border-radius: var(--radius-2); }
.panel__head { display: flex; align-items: center; gap: var(--space-3); margin-bottom: var(--space-3); }
.panel__title { margin: 0; font-size: 1rem; }
.panel__close { margin-left: auto; padding: 2px var(--space-3); font: inherit; font-size: 0.8125rem; color: inherit; background: var(--color-surface); border: 1px solid var(--color-border); border-radius: var(--radius-1); cursor: pointer; }
.panel__note { margin: 0 0 var(--space-3); padding: var(--space-2) var(--space-3); background: var(--color-background); border: 1px solid var(--color-border); border-radius: var(--radius-1); color: var(--color-muted); font-size: 0.8125rem; }
.facts { margin: 0; display: grid; gap: var(--space-2); }
.facts__row { display: grid; grid-template-columns: 6rem 1fr; gap: var(--space-3); align-items: baseline; }
.facts__row dt { color: var(--color-muted); font-size: 0.8125rem; }
.facts__row dd { margin: 0; font-size: 0.875rem; overflow-wrap: anywhere; }
.facts__mono { font-family: ui-monospace, SFMono-Regular, Menlo, monospace; font-size: 0.8125rem; }
.facts__path { font-family: ui-monospace, SFMono-Regular, Menlo, monospace; font-size: 0.75rem; }
</style>
