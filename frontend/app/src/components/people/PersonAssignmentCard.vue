<script setup lang="ts">
import { computed, onBeforeUnmount, ref, watch } from 'vue'

import {
  usePersonAssignmentFlow,
  type PersonAssignmentApi,
} from '@/composables/usePersonAssignmentFlow'
import type {
  DemotedRole,
  PersonAssignmentResult,
  PersonRole,
  PersonSummaryItem,
} from '@/types/person'
import { ROLE_LABELS } from './personPresentation'

//
// Adding an account: paste a link, say who it belongs to, say what it is.
//
// This replaces the two-step flow the people tab used to open with - name an
// empty person, find them again, then attach an account - which asked for a
// decision (what to call somebody) before the information needed to make it (who
// the account turns out to be) existed.
//
// The card is presentation. What a link names, what may be submitted, and what
// each refusal means all live in the flow, where they can be tested without
// mounting anything.
//

const props = defineProps<{
  people: PersonSummaryItem[]
  /** Injected by the tests; production leaves it alone and gets the real api. */
  api?: Partial<PersonAssignmentApi>
  /**
   * Set by the person detail panel, where the target is whichever person is
   * open. The "create a new person" half of the card disappears with it.
   */
  fixedPersonId?: number
  /** Re-read whatever the write changed.  Awaited, so a failure is reportable. */
  refresh?: (result: PersonAssignmentResult | null) => Promise<void>
}>()

const emit = defineEmits<{
  assigned: [result: PersonAssignmentResult]
  'open-person': [personId: number]
}>()

const flow = usePersonAssignmentFlow({
  ...(props.api ? { api: props.api } : {}),
  ...(props.fixedPersonId === undefined ? {} : { fixedPersonId: props.fixedPersonId }),
  onPeopleChanged: async (result) => {
    if (props.refresh) {
      await props.refresh(result)
    }
  },
})

const {
  rawInput,
  resolution,
  targetKind,
  selectedPersonId,
  displayName,
  note,
  role,
  phase,
  resolveError,
  assignmentError,
  refreshWarning,
  result,
  conflict,
  canResolve,
  canSubmit,
} = flow

//
// A late answer must not be written into state that has been thrown away.
//
onBeforeUnmount(() => flow.dispose())

watch(result, (next) => {
  if (next !== null) {
    emit('assigned', next)
  }
})

const RESOURCE_LABELS: Readonly<Record<string, string>> = {
  owner: '主页',
  post: '作品',
  live: '直播',
}

//
// What the resolution is allowed to say.
//
// Only the kind of resource. A receipt names a resource, not an owner: the
// nickname and the account id are read during the assignment itself, so showing
// them here would mean inventing them. The resolved url is left out too - a
// share url can carry a signature.
//
const previewLabel = computed(() =>
  resolution.value === null ? '' : (RESOURCE_LABELS[resolution.value.resource_type] ?? '链接'),
)

//
// `null` is not a value a `<select>` can hold, and '' is not a role. The proxy
// keeps "nothing chosen" representable without letting it reach the request.
//
const roleValue = computed<string>({
  get: () => role.value ?? '',
  set: (next) => {
    role.value = next === '' ? null : (next as PersonRole)
  },
})

const personValue = computed<string>({
  get: () => (selectedPersonId.value === null ? '' : String(selectedPersonId.value)),
  set: (next) => {
    selectedPersonId.value = next === '' ? null : Number(next)
  },
})

const demoteTo = ref<DemotedRole | ''>('')
watch(conflict, () => {
  //
  // Never carried between conflicts: it is an answer to one particular main
  // being in the way.
  //
  demoteTo.value = ''
})

const accountConflict = computed(() =>
  conflict.value?.kind === 'account_already_attached' ? conflict.value : null,
)
const mainConflict = computed(() =>
  conflict.value?.kind === 'main_account_conflict' ? conflict.value : null,
)
const strandedConflict = computed(() =>
  conflict.value?.kind === 'last_main_removal_conflict' ? conflict.value : null,
)

const successText = computed(() => {
  if (result.value === null) {
    return ''
  }
  const name = result.value.display_name
  return result.value.created_person
    ? `已创建人物「${name}」并添加账号。`
    : `已将账号添加到「${name}」。`
})
</script>

<template>
  <section class="card">
    <h2 class="card__title">添加账号 / 人物</h2>
    <p class="card__hint">
      粘贴主页、作品或直播的分享链接。人物会在确认时一并创建，不需要先建好再回来找。
    </p>

    <label class="field">
      <span class="field__label">分享链接</span>
      <input
        v-model="rawInput"
        data-test="assignment-input"
        class="field__input"
        type="text"
        placeholder="粘贴主页、作品或直播分享链接"
      />
    </label>

    <div class="card__actions">
      <button
        type="button"
        data-test="assignment-resolve"
        class="card__action"
        :disabled="!canResolve"
        @click="flow.resolve()"
      >
        {{ phase === 'resolving' ? '解析中…' : '解析' }}
      </button>
    </div>

    <p v-if="resolveError" data-test="assignment-resolve-error" class="card__notice" role="alert">
      {{ resolveError }}
    </p>

    <template v-if="resolution && phase !== 'success'">
      <p data-test="assignment-preview" class="card__preview">
        已识别资源：{{ previewLabel }}
      </p>

      <template v-if="fixedPersonId === undefined">
        <fieldset class="card__group">
          <legend class="field__label">归属</legend>
          <label class="card__choice">
            <input v-model="targetKind" type="radio" value="new" data-test="assignment-target-new" />
            <span>创建新人物</span>
          </label>
          <label class="card__choice">
            <input
              v-model="targetKind"
              type="radio"
              value="existing"
              data-test="assignment-target-existing"
            />
            <span>归并到已有人物</span>
          </label>
        </fieldset>

        <template v-if="targetKind === 'new'">
          <label class="field">
            <span class="field__label">人物名称（可选）</span>
            <input
              v-model="displayName"
              data-test="assignment-name"
              class="field__input"
              type="text"
              placeholder="留空则根据账号信息自动生成"
            />
          </label>
          <label class="field">
            <span class="field__label">备注（可选）</span>
            <input v-model="note" data-test="assignment-note" class="field__input" type="text" />
          </label>
        </template>

        <label v-else class="field">
          <span class="field__label">人物</span>
          <select v-model="personValue" data-test="assignment-person" class="field__input">
            <option value="">请选择人物</option>
            <option v-for="one in people" :key="one.person_id" :value="String(one.person_id)">
              {{ one.display_name }}
            </option>
          </select>
        </label>
      </template>

      <label class="field">
        <span class="field__label">账号类型</span>
        <select v-model="roleValue" data-test="assignment-role" class="field__input">
          <option value="">请选择</option>
          <option value="main">{{ ROLE_LABELS.main }}</option>
          <option value="alt">{{ ROLE_LABELS.alt }}</option>
          <option value="matrix">{{ ROLE_LABELS.matrix }}</option>
        </select>
      </label>

      <div class="card__actions">
        <button
          type="button"
          data-test="assignment-submit"
          class="card__action card__action--primary"
          :disabled="!canSubmit"
          @click="flow.submit()"
        >
          {{ phase === 'submitting' ? '提交中…' : '确认添加' }}
        </button>
      </div>
    </template>

    <div v-if="conflict" data-test="assignment-conflict" class="card__conflict" role="alert">
      <template v-if="accountConflict">
        <p>
          该账号当前属于「{{ accountConflict.current_person.display_name ?? '未命名人物' }}」。
          继续会把它移到这次选择的人物名下。
        </p>
        <div class="card__actions">
          <button type="button" class="card__action" @click="flow.cancelConflict()">取消</button>
          <button
            type="button"
            data-test="assignment-open-person"
            class="card__action"
            @click="emit('open-person', accountConflict.current_person.person_id)"
          >
            打开原人物
          </button>
          <button
            type="button"
            data-test="assignment-confirm-move"
            class="card__action card__action--primary"
            @click="flow.confirmMove()"
          >
            确认移动
          </button>
        </div>
      </template>

      <template v-else-if="mainConflict">
        <p>
          当前人物已有大号：{{ mainConflict.current_main.nickname ?? mainConflict.current_main.owner_user_id }}。
          若要把这个账号设为大号，请选择原大号改为什么。
        </p>
        <label class="field">
          <span class="field__label">原大号改为</span>
          <select v-model="demoteTo" data-test="assignment-demote-to" class="field__input">
            <option value="">请选择</option>
            <option value="alt">{{ ROLE_LABELS.alt }}</option>
            <option value="matrix">{{ ROLE_LABELS.matrix }}</option>
          </select>
        </label>
        <div class="card__actions">
          <button type="button" class="card__action" @click="flow.cancelConflict()">取消</button>
          <button
            type="button"
            data-test="assignment-confirm-replace"
            class="card__action card__action--primary"
            :disabled="demoteTo === ''"
            @click="flow.confirmReplaceMain(demoteTo === '' ? null : demoteTo)"
          >
            确认替换大号
          </button>
        </div>
      </template>

      <template v-else-if="strandedConflict">
        <!--
          No confirmation of any kind. The folders this protects are not written
          down anywhere else, so there is no version of it the user could agree
          to - the way forward is to give that person a main of their own first.
        -->
        <p>
          这个账号是「{{ strandedConflict.source_person.display_name ?? '原人物' }}」的大号，
          原人物的其它账号都按它的目录归档。请先为原人物指定新的大号，再移动此账号。
        </p>
        <div class="card__actions">
          <button type="button" class="card__action" @click="flow.cancelConflict()">取消</button>
          <button
            type="button"
            data-test="assignment-open-person"
            class="card__action"
            @click="emit('open-person', strandedConflict.source_person.person_id)"
          >
            打开原人物
          </button>
        </div>
      </template>
    </div>

    <p v-if="assignmentError" data-test="assignment-error" class="card__notice" role="alert">
      {{ assignmentError }}
    </p>

    <div v-if="phase === 'success' && result" data-test="assignment-success" class="card__success">
      <p>{{ successText }}</p>
      <dl class="card__facts">
        <div><dt>账号类型</dt><dd>{{ ROLE_LABELS[result.role] }}</dd></div>
        <div><dt>账号 ID</dt><dd>{{ result.owner_user_id }}</dd></div>
      </dl>
      <p v-if="refreshWarning" class="card__notice">{{ refreshWarning }}</p>
      <div class="card__actions">
        <button
          type="button"
          data-test="assignment-again"
          class="card__action"
          @click="flow.reset()"
        >
          继续添加另一个账号
        </button>
      </div>
    </div>
  </section>
</template>

<style scoped>
.card {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
  padding: 1rem;
  border: 1px solid var(--border, #d8d8d8);
  border-radius: 0.5rem;
  background: var(--surface, #fff);
}

.card__title {
  margin: 0;
  font-size: 1rem;
}

.card__hint,
.card__preview {
  margin: 0;
  font-size: 0.85rem;
  color: var(--muted, #666);
}

.field {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.field__label {
  font-size: 0.8rem;
  color: var(--muted, #666);
}

.field__input {
  padding: 0.4rem 0.5rem;
  border: 1px solid var(--border, #d8d8d8);
  border-radius: 0.25rem;
  font: inherit;
}

.card__group {
  display: flex;
  gap: 1rem;
  align-items: center;
  margin: 0;
  padding: 0;
  border: 0;
}

.card__choice {
  display: inline-flex;
  gap: 0.3rem;
  align-items: center;
  font-size: 0.9rem;
}

.card__actions {
  display: flex;
  gap: 0.5rem;
  flex-wrap: wrap;
}

.card__action {
  padding: 0.35rem 0.75rem;
  border: 1px solid var(--border, #d8d8d8);
  border-radius: 0.25rem;
  background: transparent;
  font: inherit;
  cursor: pointer;
}

.card__action:disabled {
  opacity: 0.5;
  cursor: default;
}

.card__action--primary {
  border-color: var(--accent, #2f6feb);
  color: var(--accent, #2f6feb);
}

.card__notice {
  margin: 0;
  font-size: 0.85rem;
  color: var(--danger, #b3261e);
}

.card__conflict,
.card__success {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  padding: 0.75rem;
  border: 1px solid var(--border, #d8d8d8);
  border-radius: 0.25rem;
  font-size: 0.9rem;
}

.card__facts {
  display: flex;
  gap: 1.5rem;
  margin: 0;
  font-size: 0.85rem;
}

.card__facts dt {
  color: var(--muted, #666);
}

.card__facts dd {
  margin: 0;
}
</style>
