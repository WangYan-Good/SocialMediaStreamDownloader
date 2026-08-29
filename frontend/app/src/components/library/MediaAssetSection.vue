<script setup lang="ts">
import type { MediaAsset, MediaAssetStorageState } from '@/types/mediaAsset'

//
// What is on disk for the resource this panel is showing, and the one thing
// that can be done with it: saving a copy.
//
// Saving happens through a plain same-origin anchor, not through script. A
// recording can be tens of gigabytes, and fetching one into a Blob would hold
// all of it in this tab before a byte reached disk - as well as replacing the
// browser's own download UI, which reports progress and knows where the user
// keeps things.
//
// Resuming an interrupted download is the browser's to do, and it can: the
// server answers `Range` with 206 and validates a resume against a strong
// entity tag, so a continuation that would have spliced two different versions
// of a file together is refused and restarted instead. Nothing here has to
// participate in that - which is the point of leaving the transfer to the
// browser rather than reimplementing it in script.
//
// The cost of that choice is that a failure arrives as the browser's own
// download error rather than as this application's. That is accepted here: a
// wrong answer for a file that vanished between listing and clicking is worth
// less than never loading a video into a tab.
//
// Previewing is offered only where the server said it will render the file,
// and only when somebody asks: opening a detail panel costs metadata, never
// media. The server sends every asset as an attachment on the download route,
// images included, so no stored file becomes something this
// page renders.
//
defineProps<{
  storageState: MediaAssetStorageState | null
  assets: MediaAsset[]
  loading: boolean
  error: string | null
  //
  // How to address one of these files. Supplied by the panel that knows which
  // resource is open, because a url built from a resource identity belongs
  // with the resource rather than with the list that displays it.
  //
  downloadUrlFor: ((asset: MediaAsset) => string) | null
  //
  // Which asset is being previewed, if any. Owned by the panel above: at most
  // one is open at a time, and switching resources or refreshing clears it.
  //
  previewAssetId: string | null
}>()

defineEmits<{ refresh: []; preview: [MediaAsset]; closePreview: [] }>()

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
      Every row here came from the discovery just performed, and the state
      above is `available`. The other states are handled before this list is
      reached, so there is never a download offered for a file this server has
      just said it cannot see.
    -->
    <ul v-else-if="assets.length" class="assets__list">
      <li v-for="asset in assets" :key="asset.asset_id" class="assets__item">
        <span class="assets__kind">{{ kindLabel(asset.kind) }}</span>
        <span class="assets__name">{{ asset.name }}</span>
        <span class="assets__size">{{ readableSize(asset.size_bytes) }}</span>
        <!--
          A same-origin link the browser follows itself. The session cookie
          goes with it, and the server's Content-Disposition makes it a save
          rather than a navigation.
        -->
        <a
          v-if="downloadUrlFor"
          class="assets__download"
          :href="downloadUrlFor(asset)"
          >下载</a
        >
        <!--
          Offered only for what the server said it will render. An asset with
          no preview_kind gets no button at all rather than a disabled one -
          a greyed-out control reads as a fault, and an flv recording being
          download-only is not a fault.
        -->
        <button
          v-if="asset.preview_kind"
          type="button"
          class="assets__preview"
          @click="
            asset.asset_id === previewAssetId
              ? $emit('closePreview')
              : $emit('preview', asset)
          "
        >
          {{ asset.asset_id === previewAssetId ? '关闭预览' : '预览' }}
        </button>
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
.assets__download { flex: 0 0 auto; color: var(--color-accent, inherit); text-decoration: underline; }
.assets__preview { flex: 0 0 auto; padding: 0 var(--space-2); font: inherit; font-size: 0.8125rem; color: inherit; background: transparent; border: 1px solid var(--color-border); border-radius: var(--radius-1); cursor: pointer; }
.assets__preview:focus-visible { outline: 2px solid var(--color-accent, currentColor); outline-offset: 2px; }
.assets__download:focus-visible { outline: 2px solid var(--color-accent, currentColor); outline-offset: 2px; }
</style>
