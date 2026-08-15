<script setup lang="ts">
import { computed, ref } from 'vue'

import { ROLE_LABELS, directoryLabel } from '@/components/people/personPresentation'
import { PERSON_ROLES } from '@/types/person'
import type {
  AccountSearchResult,
  PersonDetail,
  PersonRole,
  PersonSummaryItem,
} from '@/types/person'
import type { CollaborationRequest } from '@/stores/people'

const props = defineProps<{
  person: PersonSummaryItem
  detail: PersonDetail | null
  detailLoading: boolean
  detailError: string | null
  searchResults: AccountSearchResult[]
  searching: boolean
  candidates: PersonSummaryItem[]
  mutating: boolean
  //
  // Which person an account would be taken from, or null when nothing is being
  // taken. Computed by the store, which knows the current person.
  //
  movesFrom: (candidate: AccountSearchResult) => number | null
}>()

const emit = defineEmits<{
  edit: [{ display_name?: string; note?: string }]
  remove: []
  search: [string]
  attach: [{ owner_user_id: string; role: PersonRole }]
  attachByLink: [{ url: string; role: PersonRole }]
  detach: [string]
  addCollaboration: [CollaborationRequest]
  removeCollaboration: [CollaborationRequest]
  close: []
}>()

const editName = ref(props.person.display_name)
const editNote = ref(props.person.note ?? '')
const keyword = ref('')
const attachRole = ref<PersonRole>('alt')
const linkInput = ref('')
const linkRole = ref<PersonRole>('alt')
const collaborationDirection = ref<'shot' | 'shotBy'>('shot')
const collaborationOther = ref<number | null>(null)
const collaborationNote = ref('')

function submitEdit() {
  //
  // Only what actually changed. An unchanged field would be a write with no
  // meaning behind it.
  //
  const fields: { display_name?: string; note?: string } = {}
  if (editName.value.trim() && editName.value.trim() !== props.person.display_name) {
    fields.display_name = editName.value.trim()
  }
  if (editNote.value.trim() !== (props.person.note ?? '')) {
    fields.note = editNote.value.trim()
  }
  emit('edit', fields)
}

function confirmRemove() {
  //
  // Destructive and not undoable. What it does and does not touch is stated in
  // full, because "delete person" reads like it might remove downloads.
  //
  const agreed = window.confirm(
    '删除人物会移除账号归属和合作关系，但不会移动或删除已经下载的文件。确定删除吗？',
  )
  if (agreed) {
    emit('remove')
  }
}

function attach(candidate: AccountSearchResult) {
  const from = props.movesFrom(candidate)
  if (from !== null) {
    //
    // The backend upserts, so this is a move rather than a copy. Saying so
    // first is the only thing standing between a click and an account
    // disappearing from somebody else.
    //
    const agreed = window.confirm(
      `该账号当前属于人物 #${from}，继续会将其移动到当前人物。确定继续吗？`,
    )
    if (!agreed) {
      return
    }
  }
  emit('attach', { owner_user_id: candidate.owner_user_id, role: attachRole.value })
}

const canAddCollaboration = computed(
  () => collaborationOther.value !== null && !props.mutating,
)
</script>

<template>
  <aside class="panel" aria-labelledby="person-panel-heading">
    <div class="panel__head">
      <h2 id="person-panel-heading" class="panel__title">{{ person.display_name }}</h2>
      <button type="button" class="panel__close" @click="emit('close')">关闭</button>
    </div>

    <dl class="facts">
      <div class="facts__row"><dt>目录</dt><dd>{{ directoryLabel(person.directory_name) }}</dd></div>
      <div class="facts__row"><dt>账号数</dt><dd>{{ person.account_count }}</dd></div>
      <div v-if="detail" class="facts__row">
        <dt>作品 / 录播</dt>
        <dd>{{ detail.summary.aweme_count }} / {{ detail.summary.live_count }}</dd>
      </div>
    </dl>

    <p v-if="detailLoading" class="panel__muted">正在读取人物详情…</p>
    <p v-else-if="detailError" class="panel__notice" role="alert">{{ detailError }}</p>

    <section class="panel__section">
      <h3 class="panel__subtitle">编辑</h3>
      <label class="field"><span class="field__label">名称</span>
        <input v-model="editName" class="field__input" type="text" />
      </label>
      <label class="field"><span class="field__label">备注</span>
        <input v-model="editNote" class="field__input" type="text" />
      </label>
      <div class="panel__actions">
        <button type="button" class="panel__action" :disabled="mutating" @click="submitEdit">
          保存
        </button>
        <button type="button" class="panel__action panel__action--danger" :disabled="mutating" @click="confirmRemove">
          删除人物
        </button>
      </div>
    </section>

    <section v-if="detail" class="panel__section">
      <h3 class="panel__subtitle">账号（{{ detail.accounts.length }}）</h3>
      <ul class="rows">
        <li v-for="one in detail.accounts" :key="one.owner_user_id" class="rows__row">
          <span>{{ one.nickname ?? one.owner_user_id }}</span>
          <span class="rows__muted">{{ ROLE_LABELS[one.role] }}</span>
          <span class="rows__mono">{{ one.owner_user_id }}</span>
          <button type="button" class="panel__action" :disabled="mutating" @click="emit('detach', one.owner_user_id)">
            解除归并
          </button>
        </li>
      </ul>
    </section>

    <section class="panel__section">
      <h3 class="panel__subtitle">添加账号</h3>
      <div class="panel__row">
        <label class="field field--grow"><span class="field__label">搜索已知账号</span>
          <input v-model="keyword" class="field__input" type="search" placeholder="昵称或目录名" />
        </label>
        <label class="field"><span class="field__label">身份</span>
          <select v-model="attachRole" class="field__input">
            <option v-for="role in PERSON_ROLES" :key="role" :value="role">{{ ROLE_LABELS[role] }}</option>
          </select>
        </label>
        <button type="button" class="panel__action" :disabled="!keyword.trim() || searching" @click="emit('search', keyword)">
          搜索
        </button>
      </div>

      <ul v-if="searchResults.length" class="rows">
        <li v-for="one in searchResults" :key="one.owner_user_id" class="rows__row">
          <span>{{ one.nickname ?? one.owner_user_id }}</span>
          <span class="rows__mono">{{ one.owner_user_id }}</span>
          <!--
            The folder, because nicknames repeat and change. It is what tells
            two similar-looking accounts apart, and what a mistaken attachment
            would go on to fill with somebody else's downloads.
          -->
          <span class="rows__muted">{{ directoryLabel(one.directory_name) }}</span>
          <span v-if="one.person_id !== null" class="rows__muted">
            已属于人物 #{{ one.person_id }}{{ one.role ? `（${ROLE_LABELS[one.role]}）` : '' }}
          </span>
          <span v-else class="rows__muted">未归并</span>
          <button type="button" class="panel__action" :disabled="mutating" @click="attach(one)">
            挂到此人
          </button>
        </li>
      </ul>

      <div class="panel__row">
        <label class="field field--grow"><span class="field__label">按分享链接添加</span>
          <input v-model="linkInput" class="field__input" type="text" placeholder="粘贴主页、作品或直播链接" />
        </label>
        <label class="field"><span class="field__label">身份</span>
          <select v-model="linkRole" class="field__input">
            <option v-for="role in PERSON_ROLES" :key="role" :value="role">{{ ROLE_LABELS[role] }}</option>
          </select>
        </label>
        <button
          type="button"
          class="panel__action"
          :disabled="!linkInput.trim() || mutating"
          @click="emit('attachByLink', { url: linkInput, role: linkRole })"
        >
          按链接添加
        </button>
      </div>
    </section>

    <section v-if="detail" class="panel__section">
      <h3 class="panel__subtitle">合作关系</h3>
      <!--
        Two lists, not one. "Filmed" and "was filmed by" are different facts,
        and somebody who does both would otherwise collapse into an
        undifferentiated list of people they have worked with.
      -->
      <p class="panel__muted">TA 拍摄过（{{ detail.subjects.length }}）</p>
      <ul class="rows">
        <li v-for="one in detail.subjects" :key="`s-${one.person_id}`" class="rows__row">
          <span>{{ one.display_name }}</span>
          <span v-if="one.note" class="rows__muted">{{ one.note }}</span>
          <button
            type="button"
            class="panel__action"
            :disabled="mutating"
            @click="emit('removeCollaboration', { direction: 'shot', otherPersonId: one.person_id })"
          >
            解除
          </button>
        </li>
      </ul>

      <p class="panel__muted">拍摄过 TA（{{ detail.photographers.length }}）</p>
      <ul class="rows">
        <li v-for="one in detail.photographers" :key="`p-${one.person_id}`" class="rows__row">
          <span>{{ one.display_name }}</span>
          <span v-if="one.note" class="rows__muted">{{ one.note }}</span>
          <button
            type="button"
            class="panel__action"
            :disabled="mutating"
            @click="emit('removeCollaboration', { direction: 'shotBy', otherPersonId: one.person_id })"
          >
            解除
          </button>
        </li>
      </ul>

      <div class="panel__row">
        <label class="field"><span class="field__label">关系方向</span>
          <select v-model="collaborationDirection" class="field__input">
            <option value="shot">当前人物拍摄了…</option>
            <option value="shotBy">当前人物被…拍摄</option>
          </select>
        </label>
        <label class="field field--grow"><span class="field__label">对方</span>
          <select v-model="collaborationOther" class="field__input">
            <option :value="null">请选择</option>
            <option v-for="one in candidates" :key="one.person_id" :value="one.person_id">
              {{ one.display_name }}
            </option>
          </select>
        </label>
        <label class="field field--grow"><span class="field__label">备注</span>
          <input v-model="collaborationNote" class="field__input" type="text" />
        </label>
        <button
          type="button"
          class="panel__action"
          :disabled="!canAddCollaboration"
          @click="
            collaborationOther !== null &&
              emit('addCollaboration', {
                direction: collaborationDirection,
                otherPersonId: collaborationOther,
                note: collaborationNote,
              })
          "
        >
          添加
        </button>
      </div>
    </section>
  </aside>
</template>

<style scoped>
.panel { padding: var(--space-4); background: var(--color-surface); border: 1px solid var(--color-border); border-radius: var(--radius-2); }
.panel__head { display: flex; align-items: center; gap: var(--space-3); margin-bottom: var(--space-3); }
.panel__title { margin: 0; font-size: 1rem; }
.panel__close { margin-left: auto; padding: 2px var(--space-3); font: inherit; font-size: 0.8125rem; color: inherit; background: var(--color-surface); border: 1px solid var(--color-border); border-radius: var(--radius-1); cursor: pointer; }
.panel__section { margin-top: var(--space-4); padding-top: var(--space-3); border-top: 1px solid var(--color-border); }
.panel__subtitle { margin: 0 0 var(--space-2); font-size: 0.875rem; }
.panel__muted { margin: var(--space-2) 0 var(--space-1); color: var(--color-muted); font-size: 0.8125rem; }
.panel__notice { margin: var(--space-2) 0; padding: var(--space-2) var(--space-3); background: var(--color-background); border: 1px solid var(--color-border); border-radius: var(--radius-1); font-size: 0.8125rem; }
.panel__row { display: flex; flex-wrap: wrap; align-items: flex-end; gap: var(--space-3); margin-top: var(--space-2); }
.panel__actions { display: flex; gap: var(--space-2); margin-top: var(--space-3); }
.panel__action { padding: var(--space-2) var(--space-3); font: inherit; font-size: 0.8125rem; color: inherit; background: var(--color-surface); border: 1px solid var(--color-border); border-radius: var(--radius-1); cursor: pointer; }
.panel__action--danger { color: #a12a2a; border-color: #e6a9a9; }
.panel__action:disabled { opacity: 0.55; cursor: not-allowed; border-style: dashed; }
.field { display: flex; flex-direction: column; gap: var(--space-1); }
.field--grow { flex: 1 1 12rem; }
.field__label { font-size: 0.75rem; color: var(--color-muted); }
.field__input { width: 100%; padding: var(--space-1) var(--space-2); font: inherit; color: inherit; background: var(--color-background); border: 1px solid var(--color-border); border-radius: var(--radius-1); }
.facts { margin: 0; display: grid; gap: var(--space-2); }
.facts__row { display: grid; grid-template-columns: 7rem 1fr; gap: var(--space-3); align-items: baseline; }
.facts__row dt { color: var(--color-muted); font-size: 0.8125rem; }
.facts__row dd { margin: 0; font-size: 0.875rem; }
.rows { list-style: none; margin: 0; padding: 0; display: grid; gap: var(--space-1); }
.rows__row { display: flex; flex-wrap: wrap; align-items: center; gap: var(--space-3); padding: var(--space-1) 0; border-bottom: 1px solid var(--color-border); font-size: 0.8125rem; }
.rows__muted { color: var(--color-muted); }
.rows__mono { font-family: ui-monospace, SFMono-Regular, Menlo, monospace; }
</style>
