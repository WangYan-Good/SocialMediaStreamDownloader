<script setup lang="ts">
import { computed } from 'vue'

import type { MediaAsset, MediaAssetStorageState } from '@/types/mediaAsset'

//
// What is on disk for the resource this panel is showing.
//
// Read-only, and deliberately inert. Nothing here links to a file, plays one
// or offers to save one: this phase answers what exists, and an anchor with
// nothing behind it would be an affordance that invites the route it lacks.
//
// The only action is to ask again - somebody who deleted files by hand wants
// the page to agree with them.
//
defineProps<{
  storageState: MediaAssetStorageState | null
  assets: MediaAsset[]
  loading: boolean
  error: string | null
}>()

defineEmits<{ refresh: [] }>()

const KIND_LABELS: Readonly<Record<string, string>> = {
  video: '视频',
  image: '图片',
  music: '音频',
  cover: '封面',
  recording: '录制文件',
}

//
// What each state means, said as a result rather than as a cause.
//
// `unavailable` deliberately explains nothing further: the reason is a fact
// about the server's own filesystem - a path that escaped its root, a symlink,
// a permission error - and none of it is a browser's business.
//
const STATE_MESSAGES: Readonly<Record<MediaAssetStorageState, string>> = {
  available: '',
  missing: '文件已不在当前下载目录中。',
  empty: '目录存在，但没有发现可识别的媒体文件。',
  unavailable: '暂时无法安全确认文件状态。',
}

function kindLabel(kind: string): string {
  return KIND_LABELS[kind] ?? kind
}

/**
 * A size somebody can read.
 *
 * Binary units, because that is what a file manager shows for the same file.
 */
function readableSize(bytes: number): string {
  if (!Number.isFinite(bytes) || bytes < 0) return '—'
  if (bytes < 1024) return `${bytes} B`
  const units = ['KB', 'MB', 'GB', 'TB']
  let value = bytes / 1024
  let unit = 0
  while (value >= 1024 && unit < units.length - 1) {
    value /= 1024
    unit += 1
  }
  //
  // One decimal below 100, none above: "1.5 MB" is useful, "1.5 GB" is useful,
  // "523.4 MB" is noise.
  //
  const rendered = value >= 100 ? Math.round(value).toString() : value.toFixed(1)
  return `${rendered} ${units[unit]}`
}
</script>

<template>
  <section class="assets">
    <div class="assets__head">
      <h3 class="assets__title">文件状态</h3>
      <button
        type="button"
        class="assets__refresh"
        :disabled="loading"
        @click="$emit('refresh')"
      >
        {{ loading ? '正在读取…' : '刷新' }}
      </button>
    </div>

    <p v-if="loading && !assets.length" class="assets__note">正在读取文件状态…</p>

    <p v-else-if="error" class="assets__note" role="alert">{{ error }}</p>

    <p
      v-else-if="storageState && storageState !== 'available'"
      class="assets__note"
    >
      {{ STATE_MESSAGES[storageState] }}
    </p>

    <!--
      A list, never links. See the note at the top of this file.
    -->
    <ul v-else-if="assets.length" class="assets__list">
      <li v-for="asset in assets" :key="asset.asset_id" class="assets__item">
        <span class="assets__kind">{{ kindLabel(asset.kind) }}</span>
        <span class="assets__name">{{ asset.name }}</span>
        <span class="assets__size">{{ readableSize(asset.size_bytes) }}</span>
      </li>
    </ul>
  </section>
</template>

<style scoped>
.assets { margin-top: var(--space-4); padding-top: var(--space-3); border-top: 1px solid var(--color-border); }
.assets__head { display: flex; align-items: center; gap: var(--space-3); margin-bottom: var(--space-2); }
.assets__title { margin: 0; font-size: 0.875rem; }
.assets__refresh { margin-left: auto; padding: 2px var(--space-3); font: inherit; font-size: 0.8125rem; color: inherit; background: var(--color-surface); border: 1px solid var(--color-border); border-radius: var(--radius-1); cursor: pointer; }
.assets__refresh:disabled { opacity: 0.55; cursor: not-allowed; border-style: dashed; }
.assets__note { margin: 0; color: var(--color-muted); font-size: 0.8125rem; }
.assets__list { list-style: none; margin: 0; padding: 0; display: grid; gap: var(--space-1); }
.assets__item { display: flex; align-items: baseline; gap: var(--space-3); font-size: 0.8125rem; }
.assets__kind { flex: 0 0 3.5rem; color: var(--color-muted); }
.assets__name { flex: 1 1 auto; overflow-wrap: anywhere; }
.assets__size { flex: 0 0 auto; color: var(--color-muted); }
</style>
