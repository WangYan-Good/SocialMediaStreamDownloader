<script setup lang="ts">
import { onBeforeUnmount, ref, shallowRef, watch } from 'vue'

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

//
// >>--------------------------- flv playback ---------------------------<<
//
// A recording written as FLV is not something a browser can decode from a
// `<video src>`. The bundled transmuxer reads the same authorized bytes and
// feeds Media Source Extensions instead - no server-side conversion, no second
// copy of the file, and no second delivery route: it fetches the very same
// `/preview` url, with the same session cookie and the same byte ranges.
//
// The library is loaded only when one of these is actually opened. Most people
// look at images and mp4s, and none of them should pay for a demuxer they never
// use.
//

const flvVideo = ref<HTMLVideoElement | null>(null)

//
// `shallowRef`, because a player is a large object with its own internals -
// making it deeply reactive would have Vue walk all of it for no purpose.
//
const player = shallowRef<{
  destroy: () => void
  detachMediaElement: () => void
  unload: () => void
  load: () => void
  attachMediaElement: (element: HTMLMediaElement) => void
  on: (event: string, listener: (...args: unknown[]) => void) => void
} | null>(null)

//
// Which attempt is current.
//
// Loading the library is asynchronous, and a viewer can close the preview or
// open a different asset while the import is still in flight. Without this, the
// import would resolve into a player for something nobody is looking at any
// more - attached to an element that has been removed, streaming a file that is
// no longer open.
//
let generation = 0

function teardown(): void {
  const current = player.value
  player.value = null
  if (current === null) return
  try {
    //
    // In this order, per the library's own lifecycle: stop reading, let go of
    // the element, then release the player.
    //
    current.unload()
    current.detachMediaElement()
    current.destroy()
  } catch {
    //
    // A teardown that fails has still released what it could, and the preview
    // it belonged to is already gone.
    //
  }
}

async function startFlv(): Promise<void> {
  teardown()
  const mine = ++generation
  failed.value = false

  let mpegts
  try {
    //
    // Dynamic, so the transmuxer becomes its own chunk and is fetched on the
    // first FLV preview rather than on first paint.
    //
    mpegts = (await import('mpegts.js')).default
  } catch {
    failed.value = true
    return
  }

  //
  // The viewer moved on while the module was loading.
  //
  if (mine !== generation) return

  if (!mpegts.isSupported()) {
    //
    // No Media Source Extensions, or no support for what this needs. Saying so
    // plainly is better than an element that silently never plays.
    //
    failed.value = true
    return
  }

  const element = flvVideo.value
  if (element === null) {
    failed.value = true
    return
  }

  let created
  try {
    created = mpegts.createPlayer(
      {
        type: 'flv',
        //
        // A file that finished recording, not a live stream. `isLive` would
        // enable latency chasing and disable the seeking this depends on.
        //
        isLive: false,
        url: props.src,
        //
        // Same-origin, so no CORS mode is wanted; credentials are what the
        // endpoint authenticates with.
        //
        cors: false,
        withCredentials: true,
      },
      {
        //
        // Seek with byte ranges - the transport Phase 10C built. The
        // alternative appends query parameters, which this endpoint neither
        // accepts nor should.
        //
        seekType: 'range',
        lazyLoad: true,
        deferLoadAfterSourceOpen: true,
        //
        // One thread for now. A worker would add its own lifecycle and
        // compatibility questions to a feature that does not yet need them.
        //
        enableWorker: false,
        enableWorkerForMSE: false,
      },
    )

    created.on(mpegts.Events.ERROR, () => {
      //
      // Network, demux, or a codec the browser will not decode - H.265 inside
      // an FLV is perfectly possible and perfectly unplayable here. None of
      // those distinctions help a viewer, and the useful next step is the
      // download already on the row.
      //
      failed.value = true
      teardown()
    })

    created.attachMediaElement(element)
    created.load()
  } catch {
    failed.value = true
    teardown()
    return
  }

  //
  // Checked again: creating and attaching yields to the event loop, and the
  // viewer may have closed the preview in between.
  //
  if (mine !== generation) {
    try {
      created.unload()
      created.detachMediaElement()
      created.destroy()
    } catch {
      // Nothing further to do; the attempt is already abandoned.
    }
    return
  }

  player.value = created
  //
  // Deliberately no `play()`. Starting playback is the viewer's decision, and a
  // recording that starts itself is a recording that starts downloading itself.
  //
}

watch(
  () => [props.src, props.asset.preview_kind] as const,
  ([, kind]) => {
    failed.value = false
    //
    // Any change invalidates whatever was running: a different asset, a
    // different resource, or a refresh that re-read the file list.
    //
    generation += 1
    teardown()
    if (kind === 'flv') {
      void startFlv()
    }
  },
  { immediate: true, flush: 'post' },
)

onBeforeUnmount(() => {
  generation += 1
  teardown()
})
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

    <!--
      No `src`. These bytes are not a source the browser can read directly - the
      transmuxer attaches to this element and supplies it through Media Source
      Extensions instead. Setting `src` as well would make the browser try to
      decode raw FLV and fail.
    -->
    <video
      v-else-if="asset.preview_kind === 'flv'"
      ref="flvVideo"
      class="preview__video"
      controls
      playsinline
      preload="metadata"
      @error="failed = true"
    ></video>
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
