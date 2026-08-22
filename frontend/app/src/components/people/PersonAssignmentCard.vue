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
  inspection,
  inspectError,
  heldByFixedPerson,
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
// Who already holds the pasted account, or `null` when nobody does.
//
const existingAssignment = computed(() => inspection.value?.assignment ?? null)

//
// The account as the platform describes it now - shown instead of inventing one
// from the resolution, which names a resource rather than an owner.
//
const accountLabel = computed(() => {
  const owner = inspection.value?.owner ?? null
  if (owner === null) {
    return ''
  }
  //
  // The id when there is no nickname: genuinely absent for an account nobody
  // has downloaded, and an empty line would look like a rendering fault.
  //
  return owner.nickname ?? owner.owner_user_id
})

//
// Which of the three sentences this is.
//
// Written out rather than derived in the template, because the difference
// between them is the whole point of the step: "already yours", "known but
// unfiled" and "new" lead to three different offers, and the middle one is the
// commonest and the easiest to mistake for the first.
//
const identityNotice = computed(() => {
  if (existingAssignment.value !== null) {
    return heldByFixedPerson.value
      ? '该账号已经在这个人物下。'
      : '该账号已经存在，无需重复添加。'
  }
  if (inspection.value?.known_account) {
    //
    // A `share_url` row means a download happened, not that anybody was
    // created. Saying "this person already exists" here would be false and
    // would leave the account unfilable.
    //
    return '该账号已经存在，但尚未归入人物。'
  }
  if (inspection.value !== null) {
    return `已识别账号：${accountLabel.value}`
  }
  return ''
})

//
// The form is for filing an account. It stays away while the check is still
// running - so "we have not asked" never looks like "it is new" - and while the
// answer is that somebody already holds it.
//
// It also stays away when the check *failed*, for the same reason rather than a
// different one: an unanswered check leaves "is this already filed?" unknown,
// and a form offering 创建新人物 turns that unknown into an invitation. The
// 解析 button above re-runs the check.
//
const formVisible = computed(
  () =>
    resolution.value !== null &&
    inspectError.value === null &&
    (phase.value === 'resolved' ||
      phase.value === 'submitting' ||
      phase.value === 'conflict' ||
      phase.value === 'failed'),
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

    <!--
      The check failed, and the form below is about to offer "create a new
      person" without anything having verified that it is new. The backend still
      refuses a duplicate inside its transaction, so this costs a caution rather
      than the whole operation - but the caution has to be visible, because
      "could not check" and "it is new" look identical once the warning is gone.
    -->
    <p v-if="inspectError" data-test="assignment-inspect-error" class="card__notice" role="alert">
      {{ inspectError }}
    </p>

    <p v-if="phase === 'inspecting'" data-test="assignment-inspecting" class="card__preview">
      正在确认该账号是否已经存在…
    </p>

    <template v-if="resolution && phase !== 'success' && phase !== 'inspecting'">
      <p data-test="assignment-preview" class="card__preview">
        <!--
          The account, then the kind of link it came from. Before the check
          existed this could only say "已识别资源：直播", because a resolution
          names a resource and not an owner - the nickname is read by the
          server during the inspection, so it is a fact by the time it appears
          here rather than a guess.
        -->
        {{ identityNotice }}<span v-if="identityNotice"> </span>（{{ previewLabel }}）
      </p>

      <div
        v-if="existingAssignment"
        data-test="assignment-existing"
        class="card__existing"
      >
        <dl class="card__facts card__facts--stacked">
          <div><dt>账号</dt><dd>{{ accountLabel }}</dd></div>
          <div><dt>账号 ID</dt><dd>{{ inspection?.owner.owner_user_id }}</dd></div>
          <!--
            Both names are shown, unreconciled. A streamer who renamed
            themselves legitimately reads "账号：程小程 / 人物：程儿": the
            person keeps the name somebody typed, because renaming is its own
            deliberate operation.
          -->
          <div><dt>人物</dt><dd>{{ existingAssignment.display_name }}</dd></div>
          <div><dt>账号类型</dt><dd>{{ ROLE_LABELS[existingAssignment.role] }}</dd></div>
          <div><dt>状态</dt><dd>已归入人物</dd></div>
        </dl>
        <div class="card__actions">
          <button
            type="button"
            data-test="assignment-open-existing"
            class="card__action"
            @click="emit('open-person', existingAssignment.person_id)"
          >
            打开人物
          </button>
          <!--
            Secondary, and deliberately so. Pasting a filed account is usually a
            duplicate; occasionally it is a spare being promoted or an account
            being moved. Offering the form by default is what put the duplicate
            one click away in the first place.
          -->
          <button
            type="button"
            data-test="assignment-adjust"
            class="card__action"
            @click="flow.adjustAssignment()"
          >
            调整归属
          </button>
        </div>
      </div>

      <template v-if="fixedPersonId === undefined && formVisible">
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

      <template v-if="formVisible">
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
          <!--
            Only ever shown having arrived here from the existing state, so
            "cancel" has somewhere to go back to.
          -->
          <button
            v-if="existingAssignment"
            type="button"
            data-test="assignment-cancel-adjust"
            class="card__action"
            @click="flow.cancelAdjustment()"
          >
            取消
          </button>
        </div>
      </template>
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

.card__existing,
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

/*
  Five labelled rows rather than the success card's two, so they stack into a
  grid instead of running off the edge of a narrow panel.
*/
.card__facts--stacked {
  display: grid;
  grid-template-columns: 5rem 1fr;
  gap: 0.25rem 0.75rem;
}

.card__facts--stacked > div {
  display: contents;
}

.card__facts dt {
  color: var(--muted, #666);
}

.card__facts dd {
  margin: 0;
}
</style>
