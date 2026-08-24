<script setup lang="ts">
import {
  TYPE_LABELS,
  creatorName,
  recordedLiveStatusLabel,
  savedCountLabel,
} from '@/components/library/libraryPresentation'
import { formatTimestamp } from '@/utils/time'
import type { LibraryLive, LibraryPost } from '@/types/library'

//
// Built from the row already on screen, exactly as the management panel is:
// reading one record back by id would be a request per click for data the list
// is already holding.
//
// The aweme id, the save directory, the fetch route, the status code, the
// directory name and the person association are all absent. Each of them
// describes how the record was produced or filed rather than what was
// downloaded, and none of them is something a user acts on.
//
defineProps<{ post: LibraryPost | null; live: LibraryLive | null }>()

defineEmits<{ close: [] }>()
</script>

<template>
  <aside class="panel" aria-labelledby="user-library-panel-heading">
    <div class="panel__head">
      <h2 id="user-library-panel-heading" class="panel__title">
        {{ post ? '作品详情' : '直播详情' }}
      </h2>
      <button type="button" class="panel__close" @click="$emit('close')">关闭</button>
    </div>

    <dl v-if="post" class="facts">
      <div class="facts__row">
        <dt>类型</dt><dd>{{ post.aweme_type ? TYPE_LABELS[post.aweme_type] : '—' }}</dd>
      </div>
      <div class="facts__row"><dt>创作者</dt><dd>{{ creatorName(post.nickname) }}</dd></div>
      <div class="facts__row"><dt>文案</dt><dd>{{ post.desc || '（无文案）' }}</dd></div>
      <div class="facts__row"><dt>发布时间</dt><dd>{{ formatTimestamp(post.create_time) }}</dd></div>
      <div class="facts__row"><dt>下载时间</dt><dd>{{ formatTimestamp(post.downloaded_at) }}</dd></div>
      <div class="facts__row">
        <dt>下载情况</dt><dd>{{ savedCountLabel(post.saved_count, post.media_count) }}</dd>
      </div>
    </dl>

    <template v-else-if="live">
      <p class="panel__note">
        这是当时的直播记录，描述记录下来的情况，不代表现在是否正在直播。
      </p>
      <dl class="facts">
        <div class="facts__row"><dt>主播</dt><dd>{{ creatorName(live.nickname) }}</dd></div>
        <div class="facts__row"><dt>标题</dt><dd>{{ live.title ?? '—' }}</dd></div>
        <div class="facts__row">
          <dt>记录状态</dt><dd>{{ recordedLiveStatusLabel(live.room_status) }}</dd>
        </div>
        <div class="facts__row"><dt>开始</dt><dd>{{ formatTimestamp(live.start_time) }}</dd></div>
        <div class="facts__row"><dt>结束</dt><dd>{{ formatTimestamp(live.finish_time) }}</dd></div>
        <div class="facts__row"><dt>记录时间</dt><dd>{{ formatTimestamp(live.observed_at) }}</dd></div>
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
</style>
