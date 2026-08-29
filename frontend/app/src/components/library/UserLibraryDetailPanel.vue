<script setup lang="ts">
import { storeToRefs } from 'pinia'
import { computed, onBeforeUnmount, ref, watch } from 'vue'

import {
  postAssetDownloadUrl,
  postAssetPreviewUrl,
  recordingAssetDownloadUrl,
  recordingAssetPreviewUrl,
} from '@/api/mediaAssets'
import MediaAssetPreview from '@/components/library/MediaAssetPreview.vue'
import MediaAssetSection from '@/components/library/MediaAssetSection.vue'
import {
  TYPE_LABELS,
  creatorName,
  savedCountLabel,
} from '@/components/library/libraryPresentation'
import { useLibraryAssetsStore } from '@/stores/libraryAssets'
import { formatTimestamp } from '@/utils/time'
import type { LibraryPost, LibraryRecording } from '@/types/library'
import type { MediaAsset } from '@/types/mediaAsset'

//
// Built from the safe row already on screen: reading one record back by id
// would be a request per click for data the list already holds.
//
// Server filing fields are absent from this wire contract and therefore cannot
// accidentally appear in the detail view.
//
const props = defineProps<{ post: LibraryPost | null; recording: LibraryRecording | null }>()

defineEmits<{ close: [] }>()

//
// What is on disk, asked for here and nowhere else.
//
// Lazily, and per resource. The list endpoints stay database-only, so browsing
// a page of twenty-five rows performs no filesystem work at all; opening one
// row is what makes the server look. Anything else would turn a page view into
// twenty-five directory scans.
//
const assetsStore = useLibraryAssetsStore()
const { assets, storageState, loading, error } = storeToRefs(assetsStore)

watch(
  () =>
    props.post
      ? `post:${props.post.platform}:${props.post.aweme_id}`
      : props.recording
        ? `recording:${props.recording.recording_id}`
        : null,
  () => {
    if (props.post) {
      void assetsStore.loadPostAssets(props.post.platform, props.post.aweme_id)
    } else if (props.recording) {
      void assetsStore.loadRecordingAssets(props.recording.recording_id)
    } else {
      assetsStore.clear()
    }
  },
  { immediate: true },
)

//
// How to address a file of whichever resource is open.
//
// Built here rather than in the list, because the parent identity is what makes
// the address meaningful: the server matches an asset id against a fresh
// discovery of *this* resource, so the same id addressed to another resource
// buys nothing. The identity is passed along exactly as it arrived - a
// recording id is text precisely so that it can be, and narrowing it here would
// address a different recording.
//
const downloadUrlFor = computed<((asset: MediaAsset) => string) | null>(() => {
  const post = props.post
  if (post) {
    return (asset) =>
      postAssetDownloadUrl(post.platform, post.aweme_id, asset.asset_id)
  }
  const recording = props.recording
  if (recording) {
    return (asset) =>
      recordingAssetDownloadUrl(recording.recording_id, asset.asset_id)
  }
  return null
})

//
// Which asset is open for preview - at most one, and only because somebody
// asked.
//
// Held here rather than in a store. It lives exactly as long as this panel
// does, and putting it in `useLibraryStore` would give it a lifetime longer
// than the thing it describes.
//
// One at a time on purpose: an image set can hold thirty files, and thirty
// media elements would be thirty requests for media nobody has asked to see.
//
const previewAsset = ref<MediaAsset | null>(null)

function closePreview(): void {
  previewAsset.value = null
}

function openPreview(asset: MediaAsset): void {
  previewAsset.value = asset
}

//
// Switching resources ends the preview immediately.
//
// Without this the panel would show one resource's details above another
// resource's media - and would keep streaming it.
//
watch(
  () => [props.post?.aweme_id ?? null, props.recording?.recording_id ?? null],
  closePreview,
)

//
// Re-reading the file list ends it too.
//
// The point of refreshing is that the disk may have changed. The same asset id
// can name different bytes afterwards, so an element still pointed at the old
// representation would be showing something that no longer exists.
//
function refreshAssets(): void {
  closePreview()
  void assetsStore.refresh()
}

//
// And an asset that has gone from the list cannot stay open.
//
watch(assets, (current) => {
  const open = previewAsset.value
  if (open === null) return
  if (!current.some((one) => one.asset_id === open.asset_id)) {
    closePreview()
  }
})

//
// Where the open asset is rendered from. Same construction as the download
// address: parent identity plus asset id, built here rather than handed out by
// the server.
//
const previewSrc = computed<string | null>(() => {
  const asset = previewAsset.value
  if (asset === null) return null

  const post = props.post
  if (post) {
    return postAssetPreviewUrl(post.platform, post.aweme_id, asset.asset_id)
  }
  const recording = props.recording
  if (recording) {
    return recordingAssetPreviewUrl(recording.recording_id, asset.asset_id)
  }
  return null
})

//
// The panel closing is the end of this resource's state. Leaving it behind
// would flash the previous resource's files under the next one opened.
//
onBeforeUnmount(() => {
  closePreview()
  assetsStore.clear()
})
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

    <template v-else-if="recording">
      <dl class="facts">
        <div class="facts__row"><dt>主播</dt><dd>{{ creatorName(recording.nickname) }}</dd></div>
        <div class="facts__row"><dt>标题</dt><dd>{{ recording.title ?? '—' }}</dd></div>
        <div class="facts__row"><dt>开始</dt><dd>{{ formatTimestamp(recording.started_at) }}</dd></div>
        <div class="facts__row"><dt>结束</dt><dd>{{ formatTimestamp(recording.finished_at) }}</dd></div>
        <div class="facts__row"><dt>录制时间</dt><dd>{{ formatTimestamp(recording.created_at) }}</dd></div>
      </dl>
    </template>

    <MediaAssetSection
      :storage-state="storageState"
      :assets="assets"
      :loading="loading"
      :error="error"
      :download-url-for="downloadUrlFor"
      :preview-asset-id="previewAsset?.asset_id ?? null"
      @refresh="refreshAssets"
      @preview="openPreview"
      @close-preview="closePreview"
    />

    <!--
      Rendered only once somebody has asked. Opening a detail panel reads
      metadata and nothing else.
    -->
    <MediaAssetPreview
      v-if="previewAsset && previewSrc"
      :asset="previewAsset"
      :src="previewSrc"
      @close="closePreview"
    />
  </aside>
</template>

<style scoped>
.panel { padding: var(--space-4); background: var(--color-surface); border: 1px solid var(--color-border); border-radius: var(--radius-2); }
.panel__head { display: flex; align-items: center; gap: var(--space-3); margin-bottom: var(--space-3); }
.panel__title { margin: 0; font-size: 1rem; }
.panel__close { margin-left: auto; padding: 2px var(--space-3); font: inherit; font-size: 0.8125rem; color: inherit; background: var(--color-surface); border: 1px solid var(--color-border); border-radius: var(--radius-1); cursor: pointer; }
.facts { margin: 0; display: grid; gap: var(--space-2); }
.facts__row { display: grid; grid-template-columns: 6rem 1fr; gap: var(--space-3); align-items: baseline; }
.facts__row dt { color: var(--color-muted); font-size: 0.8125rem; }
.facts__row dd { margin: 0; font-size: 0.875rem; overflow-wrap: anywhere; }
</style>
