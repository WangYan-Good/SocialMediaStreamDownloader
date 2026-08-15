<script setup lang="ts">
import { storeToRefs } from 'pinia'
import { computed, onMounted, ref } from 'vue'

import LibraryDetailPanel from '@/components/library/LibraryDetailPanel.vue'
import LibraryFilters from '@/components/library/LibraryFilters.vue'
import LibraryLiveTable from '@/components/library/LibraryLiveTable.vue'
import LibraryPostTable from '@/components/library/LibraryPostTable.vue'
import PersonWorksPanel from '@/components/library/PersonWorksPanel.vue'
import { useLibraryStore } from '@/stores/library'

//
// Three views over three different schemas, deliberately not merged.
//
// A downloaded post, a recorded broadcast and a collaboration association have
// different columns and mean different things; one table with every column
// optional would show mostly blanks and lose the distinctions this screen
// exists to make.
//
type Tab = 'posts' | 'lives' | 'works'

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

  lives,
  liveTotal,
  livePage,
  livePageCount,
  liveLoading,
  liveError,
  hasLoadedLives,
  selectedLiveKey,
  selectedLive,

  peopleOptions,
  peopleOptionsError,

  selectedPhotographerId,
  personWorks,
  personWorksLoading,
  personWorksError,
} = storeToRefs(store)

const tab = ref<Tab>('posts')
const liveKeyword = ref('')

const TAB_LABELS: Record<Tab, string> = {
  posts: '已下载作品',
  lives: '直播记录',
  works: '拍摄关系关联',
}

//
// Only the first tab is read on arrival, plus the person list the filter needs.
// Live records and collaboration associations are separate queries against
// separate tables, and somebody who came to look at downloads should not pay
// for either.
//
onMounted(() => {
  void store.loadPosts()
  void store.loadPeopleOptions()
})

function showTab(next: Tab) {
  tab.value = next
  if (next === 'lives' && !hasLoadedLives.value) {
    void store.loadLives()
  }
}

const postCountLabel = computed(() =>
  hasLoadedPosts.value ? `共 ${postTotal.value} 条记录` : '',
)
const liveCountLabel = computed(() =>
  hasLoadedLives.value ? `共 ${liveTotal.value} 条记录` : '',
)

function searchLives() {
  void store.setLiveFilters({ q: liveKeyword.value.trim() || undefined })
}
</script>

<template>
  <section class="library">
    <header class="library__header">
      <h1 class="library__title">媒体库</h1>
      <p class="library__hint">
        本机已记录的下载内容索引。这里显示的是数据库中的记录，不是对磁盘文件的检查。
      </p>
    </header>

    <nav class="library__tabs" aria-label="媒体库视角">
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
      <LibraryFilters
        :filters="postFilters"
        :people="peopleOptions"
        :people-error="peopleOptionsError"
        :loading="postLoading"
        @change="store.setPostFilters($event)"
        @refresh="store.loadPosts()"
      />

      <p class="library__status" role="status">
        <span v-if="postCountLabel">{{ postCountLabel }}</span>
      </p>

      <div v-if="postError" class="library__notice" role="alert">
        {{ postError }}
        <button type="button" class="library__action" @click="store.loadPosts()">重试</button>
      </div>

      <p v-if="!hasLoadedPosts && !postError" class="library__placeholder">正在读取媒体库…</p>
      <p v-else-if="hasLoadedPosts && !posts.length" class="library__placeholder">
        没有符合条件的下载记录，可以调整筛选条件。
      </p>
      <LibraryPostTable
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

    <template v-else-if="tab === 'lives'">
      <div class="library__row">
        <label class="library__field">
          <span class="library__label">关键词</span>
          <input
            v-model="liveKeyword"
            class="library__input"
            type="search"
            placeholder="房间号、标题、创作者或人物"
          />
        </label>
        <button type="button" class="library__action" :disabled="liveLoading" @click="searchLives">
          搜索
        </button>
        <button type="button" class="library__action" :disabled="liveLoading" @click="store.loadLives()">
          {{ liveLoading ? '正在读取…' : '刷新' }}
        </button>
      </div>

      <p class="library__status" role="status">
        <span v-if="liveCountLabel">{{ liveCountLabel }}</span>
      </p>

      <div v-if="liveError" class="library__notice" role="alert">
        {{ liveError }}
        <button type="button" class="library__action" @click="store.loadLives()">重试</button>
      </div>

      <p v-if="!hasLoadedLives && !liveError" class="library__placeholder">正在读取直播记录…</p>
      <p v-else-if="hasLoadedLives && !lives.length" class="library__placeholder">
        没有符合条件的直播记录。
      </p>
      <LibraryLiveTable
        v-else-if="lives.length"
        :lives="lives"
        :selected-key="selectedLiveKey"
        :key-of="store.liveKey"
        @select="store.selectLive($event)"
      />

      <div v-if="livePageCount > 1" class="library__pager">
        <button
          type="button"
          class="library__action"
          :disabled="livePage <= 1 || liveLoading"
          @click="store.goToLivePage(livePage - 1)"
        >
          上一页
        </button>
        <span class="library__muted">第 {{ livePage }} / {{ livePageCount }} 页</span>
        <button
          type="button"
          class="library__action"
          :disabled="livePage >= livePageCount || liveLoading"
          @click="store.goToLivePage(livePage + 1)"
        >
          下一页
        </button>
      </div>
    </template>

    <PersonWorksPanel
      v-else
      :people="peopleOptions"
      :selected-photographer-id="selectedPhotographerId"
      :works="personWorks"
      :loading="personWorksLoading"
      :error="personWorksError"
      @select="store.selectPhotographer($event)"
    />

    <LibraryDetailPanel
      v-if="(tab === 'posts' && selectedPost) || (tab === 'lives' && selectedLive)"
      :post="tab === 'posts' ? selectedPost : null"
      :live="tab === 'lives' ? selectedLive : null"
      @close="tab === 'posts' ? store.selectPost(null) : store.selectLive(null)"
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
