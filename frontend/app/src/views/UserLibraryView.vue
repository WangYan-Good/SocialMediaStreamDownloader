<script setup lang="ts">
import { storeToRefs } from 'pinia'
import { computed, onMounted, ref } from 'vue'

import UserLibraryDetailPanel from '@/components/library/UserLibraryDetailPanel.vue'
import UserLibraryFilters from '@/components/library/UserLibraryFilters.vue'
import UserLibraryPostTable from '@/components/library/UserLibraryPostTable.vue'
import UserLibraryRecordingTable from '@/components/library/UserLibraryRecordingTable.vue'
import { useLibraryStore } from '@/stores/library'

//
// The user's own view of what has been downloaded.
//
// A second view over the same store rather than a mode flag inside the
// management one. The two answer different questions: this one answers "what
// did I download", and every column it leaves out - the aweme id, the account
// id, the save directory, the fetch route, the person association - describes
// how a record was produced or filed rather than what was downloaded.
//
// The store, the api, the types and the paging are shared unchanged. Nothing
// here re-queries, re-sorts or re-counts; this is a narrower reading of exactly
// the same rows the management screen shows.
//
type Tab = 'posts' | 'lives'

const store = useLibraryStore()
const {
  posts,
  postTotal,
  postPage,
  postPageCount,
  postFilters,
  postLoading,
  postError,
  hasLoadedPosts,
  selectedPostKey,
  selectedPost,

  recordings,
  recordingPage,
  recordingPageCount,
  recordingFilters,
  recordingLoading,
  recordingError,
  hasLoadedRecordings,
  selectedRecordingId,
  selectedRecording,
} = storeToRefs(store)

const tab = ref<Tab>('posts')
const recordingKeyword = ref('')

const TAB_LABELS: Record<Tab, string> = {
  posts: '已下载作品',
  lives: '直播记录',
}

//
// Downloads only, and deliberately nothing else.
//
// The management screen also reads the person roster here to fill its filter.
// This one has no such control, so asking for the roster would be a request for
// a list nothing on the page uses.
//
onMounted(() => {
  void store.loadPosts()
})

function showTab(next: Tab) {
  tab.value = next
  if (next === 'lives' && !hasLoadedRecordings.value) {
    void store.loadRecordings()
  }
}

//
// Whether the user has narrowed the list themselves.
//
// "Nothing here yet" and "nothing matched" are different facts, and telling a
// first-time user with an empty library that their filter matched nothing would
// send them looking for a filter they never set. Sort and order are excluded:
// they are always present and never reduce the result.
//
const postsAreFiltered = computed(() =>
  Boolean(
    postFilters.value.q ||
      postFilters.value.aweme_type ||
      postFilters.value.completion ||
      postFilters.value.person_id ||
      postFilters.value.owner_user_id ||
      postFilters.value.source,
  ),
)

const recordingsAreFiltered = computed(() => Boolean(recordingFilters.value.q))

//
// A failed read, as a result.
//
// The store keeps its own message - "媒体库暂时无法读取：<backend message>" -
// and keeps classifying failures exactly as it did. This only decides what
// reaches the screen, because that message can carry a database or schema
// detail that means nothing to a user and should not be the headline.
//
const READ_FAILED = '暂时无法读取资源，请重试。'

const postCountLabel = computed(() =>
  hasLoadedPosts.value ? `共 ${postTotal.value} 条记录` : '',
)

function searchRecordings() {
  void store.setRecordingFilters({ q: recordingKeyword.value.trim() || undefined })
}
</script>

<template>
  <section class="library">
    <header class="library__header">
      <h1 class="library__title">我的资源</h1>
      <!--
        Accurate rather than reassuring. Nothing here has looked at the disk, so
        the page may not imply the media is still where it was put.
      -->
      <p class="library__hint">
        这里显示已完成的下载记录和直播记录；如果文件之后被移动或删除，记录仍可能保留。
      </p>
    </header>

    <nav class="library__tabs" aria-label="资源分类">
      <button
        v-for="(label, entry) in TAB_LABELS"
        :key="entry"
        type="button"
        class="library__tab"
        :class="{ 'library__tab--active': tab === entry }"
        :aria-current="tab === entry ? 'true' : undefined"
        @click="showTab(entry as Tab)"
      >
        {{ label }}
      </button>
    </nav>

    <template v-if="tab === 'posts'">
      <UserLibraryFilters
        :filters="postFilters"
        :loading="postLoading"
        @change="store.setPostFilters($event)"
        @refresh="store.loadPosts()"
      />

      <p class="library__status" role="status">
        <span v-if="postCountLabel">{{ postCountLabel }}</span>
      </p>

      <div v-if="postError" class="library__notice" role="alert">
        {{ READ_FAILED }}
        <button type="button" class="library__action" @click="store.loadPosts()">重试</button>
      </div>

      <p v-if="!hasLoadedPosts && !postError" class="library__placeholder">
        正在读取你的下载记录…
      </p>
      <p v-else-if="hasLoadedPosts && !posts.length" class="library__placeholder">
        {{ postsAreFiltered ? '没有符合条件的内容。' : '还没有下载作品。' }}
      </p>
      <UserLibraryPostTable
        v-else-if="posts.length"
        :posts="posts"
        :selected-key="selectedPostKey"
        :key-of="store.postKey"
        @select="store.selectPost($event)"
      />

      <div v-if="postPageCount > 1" class="library__pager">
        <button
          type="button"
          class="library__action"
          :disabled="postPage <= 1 || postLoading"
          @click="store.goToPostPage(postPage - 1)"
        >
          上一页
        </button>
        <span class="library__muted">第 {{ postPage }} / {{ postPageCount }} 页</span>
        <button
          type="button"
          class="library__action"
          :disabled="postPage >= postPageCount || postLoading"
          @click="store.goToPostPage(postPage + 1)"
        >
          下一页
        </button>
      </div>
    </template>

    <template v-else>
      <div class="library__row">
        <label class="library__field">
          <span class="library__label">关键词</span>
          <input
            v-model="recordingKeyword"
            class="library__input"
            type="search"
            placeholder="搜索主播或标题"
          />
        </label>
        <button type="button" class="library__action" :disabled="recordingLoading" @click="searchRecordings">
          搜索
        </button>
        <button
          type="button"
          class="library__action"
          :disabled="recordingLoading"
          @click="store.loadRecordings()"
        >
          {{ recordingLoading ? '正在读取…' : '刷新' }}
        </button>
      </div>

      <div v-if="recordingError" class="library__notice" role="alert">
        {{ READ_FAILED }}
        <button type="button" class="library__action" @click="store.loadRecordings()">重试</button>
      </div>

      <p v-if="!hasLoadedRecordings && !recordingError" class="library__placeholder">
        正在读取直播记录…
      </p>
      <p v-else-if="hasLoadedRecordings && !recordings.length" class="library__placeholder">
        {{ recordingsAreFiltered ? '没有符合条件的内容。' : '还没有直播记录。' }}
      </p>
      <UserLibraryRecordingTable
        v-else-if="recordings.length"
        :recordings="recordings"
        :selected-id="selectedRecordingId"
        @select="store.selectRecording($event)"
      />

      <div v-if="recordingPageCount > 1" class="library__pager">
        <button
          type="button"
          class="library__action"
          :disabled="recordingPage <= 1 || recordingLoading"
          @click="store.goToRecordingPage(recordingPage - 1)"
        >
          上一页
        </button>
        <span class="library__muted">第 {{ recordingPage }} / {{ recordingPageCount }} 页</span>
        <button
          type="button"
          class="library__action"
          :disabled="recordingPage >= recordingPageCount || recordingLoading"
          @click="store.goToRecordingPage(recordingPage + 1)"
        >
          下一页
        </button>
      </div>
    </template>

    <UserLibraryDetailPanel
      v-if="(tab === 'posts' && selectedPost) || (tab === 'lives' && selectedRecording)"
      :post="tab === 'posts' ? selectedPost : null"
      :recording="tab === 'lives' ? selectedRecording : null"
      @close="tab === 'posts' ? store.selectPost(null) : store.selectRecording(null)"
    />
  </section>
</template>

<style scoped>
.library { display: grid; gap: var(--space-4); }
.library__header { margin-bottom: var(--space-1); }
.library__title { margin: 0; font-size: 1.375rem; }
.library__hint { margin: var(--space-1) 0 0; color: var(--color-muted); font-size: 0.8125rem; }
.library__tabs { display: flex; gap: var(--space-2); border-bottom: 1px solid var(--color-border); }
.library__tab { padding: var(--space-2) var(--space-4); font: inherit; color: var(--color-muted); background: none; border: none; border-bottom: 2px solid transparent; cursor: pointer; }
.library__tab--active { color: var(--color-text); border-bottom-color: var(--color-accent); font-weight: 600; }
.library__row { display: flex; flex-wrap: wrap; align-items: flex-end; gap: var(--space-3); }
.library__field { display: flex; flex-direction: column; gap: var(--space-1); flex: 1 1 20rem; }
.library__label { font-size: 0.75rem; color: var(--color-muted); }
.library__input { width: 100%; padding: var(--space-1) var(--space-2); font: inherit; color: inherit; background: var(--color-surface); border: 1px solid var(--color-border); border-radius: var(--radius-1); }
.library__status { display: flex; flex-wrap: wrap; gap: var(--space-4); margin: 0; color: var(--color-muted); font-size: 0.8125rem; }
.library__muted { color: var(--color-muted); font-size: 0.8125rem; }
.library__notice { display: flex; flex-wrap: wrap; align-items: center; gap: var(--space-3); margin: 0; padding: var(--space-3); background: var(--color-background); border: 1px solid var(--color-border); border-radius: var(--radius-1); font-size: 0.8125rem; }
.library__action { padding: var(--space-2) var(--space-3); font: inherit; font-size: 0.8125rem; color: inherit; background: var(--color-surface); border: 1px solid var(--color-border); border-radius: var(--radius-1); cursor: pointer; }
.library__action:disabled { opacity: 0.55; cursor: not-allowed; border-style: dashed; }
.library__pager { display: flex; align-items: center; gap: var(--space-3); }
.library__placeholder { margin: 0; padding: var(--space-5); background: var(--color-surface); border: 1px solid var(--color-border); border-radius: var(--radius-2); color: var(--color-muted); text-align: center; }
</style>
