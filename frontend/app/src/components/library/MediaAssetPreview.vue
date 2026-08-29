<script setup lang="ts">
import { ref, watch } from 'vue'

import type { MediaAsset } from '@/types/mediaAsset'

//
// One asset, rendered in place.
//
// A renderer and nothing else: it is given an asset and a url and decides which
// element shows it. Which asset is open, and when, belongs to the panel above -
// this component has no opinion about that and keeps no state that outlives the
// element it draws.
//
// The element points straight at the endpoint. No `fetch`, no Blob, no object
// url: a video may be tens of gigabytes, and letting the browser make the
// request is what allows it to stream, seek and discard as it goes. It also
// keeps the session cookie doing the authenticating, which a same-origin
// subresource request sends on its own.
//
// Nothing sets `crossorigin`. These are same-origin resources, so there is no
// CORS request to configure: the attribute would switch the element to a CORS
// fetch and buy nothing. (It would not, as is sometimes assumed, drop the
// session cookie - `anonymous` still sends same-origin credentials. The reason
// to leave it off is that it is simply not applicable here.)
//
const props = defineProps<{
  asset: MediaAsset
  src: string
}>()

defineEmits<{ close: [] }>()

//
// The browser's own failure, reported in this application's words.
//
// Media elements do not say why they failed, and the reasons they could give -
// a 404 for a file that has just been deleted, a 401 for a session that has
// expired, a codec the browser declined - are not things a viewer can act on
// differently. There is one useful next step, and it is the download that was
// already on the row.
//
const failed = ref(false)

watch(
  () => props.src,
  () => {
    failed.value = false
  },
)
</script>

<template>
  <figure class="preview">
    <figcaption class="preview__head">
      <span class="preview__name">{{ asset.name }}</span>
      <button type="button" class="preview__close" @click="$emit('close')">
        关闭预览
      </button>
    </figcaption>

    <p v-if="failed" class="preview__note" role="alert">
      预览失败，可尝试下载文件。
    </p>

    <!--
      One element, chosen by what the server said it is willing to render -
      never by this file's extension.
    -->
    <img
      v-else-if="asset.preview_kind === 'image'"
      class="preview__image"
      :src="src"
      :alt="asset.name"
      loading="lazy"
      decoding="async"
      @error="failed = true"
    />

    <!--
      `preload="metadata"` so opening a preview costs a header rather than a
      file. No autoplay and no loop: playing is the viewer's decision, and a
      video that starts itself is a video that starts downloading itself.
    -->
    <video
      v-else-if="asset.preview_kind === 'video'"
      class="preview__video"
      :src="src"
      controls
      preload="metadata"
      playsinline
      @error="failed = true"
    ></video>

    <audio
      v-else-if="asset.preview_kind === 'audio'"
      class="preview__audio"
      :src="src"
      controls
      preload="metadata"
      @error="failed = true"
    ></audio>
  </figure>
</template>

<style scoped>
.preview { margin: var(--space-3) 0 0; padding: var(--space-3); background: var(--color-surface); border: 1px solid var(--color-border); border-radius: var(--radius-1); }
.preview__head { display: flex; align-items: baseline; gap: var(--space-3); margin-bottom: var(--space-2); font-size: 0.8125rem; }
.preview__name { overflow-wrap: anywhere; color: var(--color-muted); }
.preview__close { margin-left: auto; flex: 0 0 auto; padding: 2px var(--space-3); font: inherit; font-size: 0.8125rem; color: inherit; background: transparent; border: 1px solid var(--color-border); border-radius: var(--radius-1); cursor: pointer; }
.preview__note { margin: 0; color: var(--color-muted); font-size: 0.8125rem; }
.preview__image { display: block; max-width: 100%; height: auto; }
.preview__video { display: block; width: 100%; max-height: 60vh; background: #000; }
.preview__audio { display: block; width: 100%; }
</style>
