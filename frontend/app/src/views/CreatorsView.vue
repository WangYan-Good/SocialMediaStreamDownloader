<script setup lang="ts">
import { storeToRefs } from 'pinia'
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import { RouterLink } from 'vue-router'

import CreatorAccountPanel from '@/components/creators/CreatorAccountPanel.vue'
import CreatorDirectory from '@/components/creators/CreatorDirectory.vue'
import CreatorFilters from '@/components/creators/CreatorFilters.vue'
import PeopleList from '@/components/people/PeopleList.vue'
import PersonDetailPanel from '@/components/people/PersonDetailPanel.vue'
import { useCreatorsStore } from '@/stores/creators'
import { usePeopleStore } from '@/stores/people'
import type { CollaborationRequest } from '@/stores/people'

//
// Two views of the same workspace: the accounts a platform knows about, and the
// people they belong to. Accounts is the default because it is where work
// starts - the identity layer is something you reach for once you already have
// accounts in front of you.
//
type Tab = 'accounts' | 'people'

const store = useCreatorsStore()
const {
  owners,
  ownerTotal,
  page,
  pageCount,
  hasPreviousPage,
  hasNextPage,
  filters,
  selectedOwnerUserId,
  selectedOwner,
  ownersLoading,
  ownersError,
  hasLoadedOwners,
  sessions,
  sessionsLoading,
  sessionsError,
  posts,
  postsLoading,
  postsError,
  hasMorePosts,
  loadedPostCount,
  selectedAwemeIds,
  openedProfile,
  profileLoading,
  profileError,
  probeItems,
  probePolling,
  probeError,
  actionBusy,
  actionError,
  actionNotice,
  lastStartedTaskId,
  preferenceBusy,
  preferenceError,
  preferenceNotice,
} = storeToRefs(store)

const peopleStore = usePeopleStore()
const {
  people,
  peopleError,
  hasLoadedPeople,
  selectedPersonId,
  selectedPerson,
  selectedDetail,
  detailLoading,
  detailError,
  accountSearchResults,
  searching,
  mutating,
  mutationError,
} = storeToRefs(peopleStore)

const tab = ref<Tab>('accounts')
const newPersonName = ref('')
const newPersonNote = ref('')

//
// People are read when the tab is opened, not on arrival: somebody who came
// here to check a live account should not pay for the identity list too.
//
function showTab(next: Tab) {
  tab.value = next
  if (next === 'people' && !hasLoadedPeople.value) {
    void peopleStore.loadPeople()
  }
}

function attachByLink(request: { url: string; role: 'main' | 'alt' | 'matrix' }) {
  if (selectedPersonId.value !== null) {
    void peopleStore.attachAccountByLink(request.url, selectedPersonId.value, request.role)
  }
}

function attach(request: { owner_user_id: string; role: 'main' | 'alt' | 'matrix' }) {
  if (selectedPersonId.value !== null) {
    void peopleStore.attachAccount({
      owner_user_id: request.owner_user_id,
      person_id: selectedPersonId.value,
      role: request.role,
    })
  }
}

function collaborate(request: CollaborationRequest) {
  void peopleStore.addCollaboration(request)
}

function uncollaborate(request: CollaborationRequest) {
  void peopleStore.removeCollaboration(request)
}
const checkedOwnerUserIds = ref<string[]>([])
const profileInput = ref('')

//
// Only the directory is read on arrival. Sessions, posts and probes are all
// per-account and are read when the user opens them - a page of twenty accounts
// would otherwise be sixty requests nobody asked for.
//
onMounted(() => {
  void store.loadOwners()
})

//
// The probe loop belongs to this screen. Nothing here polls on a timer except a
// probe the user started and which has not finished.
//
onBeforeUnmount(() => {
  store.stopProbePolling()
})

const probeItemForSelected = computed(() =>
  selectedOwnerUserId.value ? store.probeItemFor(selectedOwnerUserId.value) : null,
)

const countLabel = computed(() =>
  hasLoadedOwners.value ? `共 ${ownerTotal.value} 个账号` : '',
)

function toggleCheck(ownerUserId: string) {
  checkedOwnerUserIds.value = checkedOwnerUserIds.value.includes(ownerUserId)
    ? checkedOwnerUserIds.value.filter((one) => one !== ownerUserId)
    : [...checkedOwnerUserIds.value, ownerUserId]
}

function openPosts() {
  //
  // A profile that was just opened brought its first page with it. Only a
  // history account has to be read by id.
  //
  if (openedProfile.value) {
    return
  }
  const secUserId = selectedOwner.value?.sec_user_id
  if (secUserId) {
    void store.openPostsForOwner(secUserId)
  }
}

function record() {
  const shareUrl = selectedOwner.value?.live_share_url
  if (shareUrl) {
    void store.startRecording(shareUrl)
  }
}
</script>

<template>
  <section class="creators">
    <header class="creators__header">
      <h1 class="creators__title">创作者</h1>
      <p class="creators__hint">
        账号是平台上的一个号；人物是现实中的一个人，可以拥有多个账号。
      </p>
    </header>

    <nav class="creators__tabs" aria-label="创作者视角">
      <button
        v-for="entry in (['accounts', 'people'] as Tab[])"
        :key="entry"
        type="button"
        class="creators__tab"
        :class="{ 'creators__tab--active': tab === entry }"
        :aria-current="tab === entry ? 'true' : undefined"
        @click="showTab(entry)"
      >
        {{ entry === 'accounts' ? '账号' : '人物' }}
      </button>
    </nav>

    <template v-if="tab === 'accounts'">
      <div class="creators__open">
        <label class="creators__field">
          <span class="creators__label">打开主播主页</span>
          <input
            v-model="profileInput"
            class="creators__input"
            type="text"
            placeholder="粘贴主页分享文本或链接"
          />
        </label>
        <button
          type="button"
          class="creators__action"
          :disabled="!profileInput.trim() || profileLoading"
          @click="store.openProfile(profileInput)"
        >
          {{ profileLoading ? '正在打开…' : '打开' }}
        </button>
      </div>
      <p v-if="profileError" class="creators__notice" role="alert">{{ profileError }}</p>

      <CreatorFilters
        :filters="filters"
        :loading="ownersLoading"
        @change="store.setFilters($event)"
        @refresh="store.loadOwners()"
      />

      <div class="creators__probe">
        <button
          type="button"
          class="creators__action"
          :disabled="!checkedOwnerUserIds.length || probePolling"
          @click="store.probeOwners(checkedOwnerUserIds)"
        >
          检查选中（{{ checkedOwnerUserIds.length }}）
        </button>
        <!--
          Stated as a count rather than implied. The legacy page read "nothing
          ticked" as "check the whole page", and a probe is a real platform
          conversation per account.
        -->
        <button
          type="button"
          class="creators__action"
          :disabled="!owners.length || probePolling"
          @click="store.probeOwners(owners.map((one) => one.owner_user_id))"
        >
          检查本页（{{ owners.length }}）
        </button>
        <span v-if="probePolling" class="creators__muted">正在检查…</span>
      </div>
      <p v-if="probeError" class="creators__notice" role="alert">
        {{ probeError }}
        <button type="button" class="creators__action" @click="store.retryProbe()">重试</button>
      </p>

      <p class="creators__status" role="status">
        <span v-if="countLabel">{{ countLabel }}</span>
        <span v-if="actionNotice" class="creators__muted">{{ actionNotice }}</span>
        <RouterLink v-if="lastStartedTaskId" class="creators__link" :to="{ name: 'tasks' }">
          已提交到任务中心（{{ lastStartedTaskId }}）
        </RouterLink>
      </p>
      <p v-if="actionError" class="creators__notice" role="alert">{{ actionError }}</p>

      <div v-if="ownersError" class="creators__notice" role="alert">
        {{ ownersError }}
        <button type="button" class="creators__action" @click="store.loadOwners()">重试</button>
      </div>

      <p v-if="!hasLoadedOwners && !ownersError" class="creators__placeholder">
        正在读取主播列表…
      </p>
      <p v-else-if="hasLoadedOwners && !owners.length" class="creators__placeholder">
        没有符合条件的主播账号，可以调整筛选条件。
      </p>
      <CreatorDirectory
        v-else-if="owners.length"
        :owners="owners"
        :selected-owner-user-id="selectedOwnerUserId"
        :checked-owner-user-ids="checkedOwnerUserIds"
        :probe-items="probeItems"
        @select="store.selectOwner($event)"
        @toggle-check="toggleCheck"
      />

      <div v-if="pageCount > 1" class="creators__pager">
        <button
          type="button"
          class="creators__action"
          :disabled="!hasPreviousPage || ownersLoading"
          @click="store.goToPage(page - 1)"
        >
          上一页
        </button>
        <span class="creators__muted">第 {{ page }} / {{ pageCount }} 页</span>
        <button
          type="button"
          class="creators__action"
          :disabled="!hasNextPage || ownersLoading"
          @click="store.goToPage(page + 1)"
        >
          下一页
        </button>
      </div>

      <CreatorAccountPanel
        v-if="selectedOwner || openedProfile"
        :owner="selectedOwner"
        :profile="openedProfile"
        :probe-item="probeItemForSelected"
        :sessions="sessions"
        :sessions-loading="sessionsLoading"
        :sessions-error="sessionsError"
        :posts="posts"
        :posts-loading="postsLoading"
        :posts-error="postsError"
        :has-more-posts="hasMorePosts"
        :loaded-post-count="loadedPostCount"
        :selected-aweme-ids="selectedAwemeIds"
        :action-busy="actionBusy"
        :preference-busy="preferenceBusy"
        :preference-error="preferenceError"
        :preference-notice="preferenceNotice"
        @open-sessions="selectedOwnerUserId && store.loadSessions(selectedOwnerUserId)"
        @open-posts="openPosts"
        @load-more="store.loadMorePosts()"
        @toggle-post="store.togglePostSelection($event)"
        @select-all="store.selectAllLoadedPosts()"
        @clear-selection="store.clearPostSelection()"
        @download-selected="store.downloadSelectedPosts()"
        @download-all="store.downloadAllPosts()"
        @record="record"
        @save-preference="selectedOwnerUserId && store.savePreference(selectedOwnerUserId, $event)"
        @close="store.clearOwnerSelection()"
      />
    </template>

    <template v-else>
      <div class="creators__open">
        <label class="creators__field">
          <span class="creators__label">新建人物</span>
          <input v-model="newPersonName" class="creators__input" type="text" placeholder="人物名称" />
        </label>
        <label class="creators__field">
          <span class="creators__label">备注</span>
          <input v-model="newPersonNote" class="creators__input" type="text" />
        </label>
        <button
          type="button"
          class="creators__action"
          :disabled="!newPersonName.trim() || mutating"
          @click="peopleStore.createPerson({ display_name: newPersonName, note: newPersonNote })"
        >
          创建
        </button>
      </div>

      <p v-if="mutationError" class="creators__notice" role="alert">{{ mutationError }}</p>

      <div v-if="peopleError" class="creators__notice" role="alert">
        {{ peopleError }}
        <button type="button" class="creators__action" @click="peopleStore.loadPeople()">重试</button>
      </div>

      <p v-if="!hasLoadedPeople && !peopleError" class="creators__placeholder">正在读取人物…</p>
      <p v-else-if="hasLoadedPeople && !people.length" class="creators__placeholder">
        还没有人物。可以先创建一个，再把账号归并到它下面。
      </p>
      <PeopleList
        v-else-if="people.length"
        :people="people"
        :selected-person-id="selectedPersonId"
        @select="peopleStore.selectPerson($event)"
      />

      <PersonDetailPanel
        v-if="selectedPerson"
        :person="selectedPerson"
        :detail="selectedDetail"
        :detail-loading="detailLoading"
        :detail-error="detailError"
        :search-results="accountSearchResults"
        :searching="searching"
        :candidates="peopleStore.collaborationCandidates"
        :mutating="mutating"
        :moves-from="(candidate) => peopleStore.movesAccountFrom(candidate, selectedPersonId ?? -1)"
        @edit="selectedPersonId !== null && peopleStore.updatePerson(selectedPersonId, $event)"
        @remove="selectedPersonId !== null && peopleStore.deletePerson(selectedPersonId)"
        @search="peopleStore.searchAccounts($event)"
        @attach="attach"
        @attach-by-link="attachByLink"
        @detach="peopleStore.detachAccount($event)"
        @add-collaboration="collaborate"
        @remove-collaboration="uncollaborate"
        @close="peopleStore.clearSelection()"
      />
    </template>
  </section>
</template>

<style scoped>
.creators { display: grid; gap: var(--space-4); }
.creators__header { margin-bottom: var(--space-1); }
.creators__title { margin: 0; font-size: 1.375rem; }
.creators__hint { margin: var(--space-1) 0 0; color: var(--color-muted); font-size: 0.8125rem; }
.creators__tabs { display: flex; gap: var(--space-2); border-bottom: 1px solid var(--color-border); }
.creators__tab { padding: var(--space-2) var(--space-4); font: inherit; color: var(--color-muted); background: none; border: none; border-bottom: 2px solid transparent; cursor: pointer; }
.creators__tab--active { color: var(--color-text); border-bottom-color: var(--color-accent); font-weight: 600; }
.creators__open { display: flex; align-items: flex-end; gap: var(--space-3); }
.creators__field { display: flex; flex-direction: column; gap: var(--space-1); flex: 1 1 20rem; }
.creators__label { font-size: 0.75rem; color: var(--color-muted); }
.creators__input { width: 100%; padding: var(--space-1) var(--space-2); font: inherit; color: inherit; background: var(--color-surface); border: 1px solid var(--color-border); border-radius: var(--radius-1); }
.creators__probe { display: flex; flex-wrap: wrap; align-items: center; gap: var(--space-3); }
.creators__status { display: flex; flex-wrap: wrap; gap: var(--space-4); margin: 0; color: var(--color-muted); font-size: 0.8125rem; }
.creators__link { color: var(--color-accent); text-decoration: underline; }
.creators__muted { color: var(--color-muted); font-size: 0.8125rem; }
.creators__notice { display: flex; flex-wrap: wrap; align-items: center; gap: var(--space-3); margin: 0; padding: var(--space-3); background: var(--color-background); border: 1px solid var(--color-border); border-radius: var(--radius-1); font-size: 0.8125rem; }
.creators__action { padding: var(--space-2) var(--space-3); font: inherit; font-size: 0.8125rem; color: inherit; background: var(--color-surface); border: 1px solid var(--color-border); border-radius: var(--radius-1); cursor: pointer; }
.creators__action:disabled { opacity: 0.55; cursor: not-allowed; border-style: dashed; }
.creators__pager { display: flex; align-items: center; gap: var(--space-3); }
.creators__placeholder { margin: 0; padding: var(--space-5); background: var(--color-surface); border: 1px solid var(--color-border); border-radius: var(--radius-2); color: var(--color-muted); text-align: center; }
</style>
