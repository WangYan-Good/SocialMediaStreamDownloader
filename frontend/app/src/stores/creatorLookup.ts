import { defineStore } from 'pinia'
import { computed, ref } from 'vue'

import { readOwner } from '@/api/owners'
import { inspectPersonAssignment } from '@/api/people'
import { resolveResource } from '@/api/resolve'
import type { OwnerCredential, OwnerProfile } from '@/types/owner'
import type { PersonIdentityInspection } from '@/types/person'
import type { ResolvedResource } from '@/types/resolution'

type OwnerResolution = Extract<ResolvedResource, { resource_type: 'owner' }>
type LookupStatus = 'idle' | 'resolving' | 'reading' | 'settled'

/**
 * One read-only answer about a pasted creator link.
 *
 * This state intentionally does not reuse the action-oriented creators store:
 * posts, downloads, recording and preferences have no place in a lookup. The
 * platform and local answers are also kept apart because they are observations
 * made at different times and either may succeed without the other.
 */
export const useCreatorLookupStore = defineStore('creatorLookup', () => {
  const status = ref<LookupStatus>('idle')
  const resolvedResource = ref<OwnerResolution | null>(null)
  const queryError = ref<string | null>(null)

  const platformProfile = ref<OwnerProfile | null>(null)
  const platformCredential = ref<OwnerCredential | null>(null)
  const platformMessage = ref<string | null>(null)
  const platformError = ref<string | null>(null)
  const platformLoading = ref(false)

  const localInspection = ref<PersonIdentityInspection | null>(null)
  const localError = ref<string | null>(null)
  const localLoading = ref(false)

  let generation = 0
  let inFlight: AbortController | null = null

  const loading = computed(() => status.value === 'resolving' || status.value === 'reading')
  const hasResult = computed(() => resolvedResource.value !== null)

  function clearFacts() {
    status.value = 'idle'
    resolvedResource.value = null
    queryError.value = null
    platformProfile.value = null
    platformCredential.value = null
    platformMessage.value = null
    platformError.value = null
    platformLoading.value = false
    localInspection.value = null
    localError.value = null
    localLoading.value = false
  }

  /** Cancel and forget a result as soon as the form no longer describes it. */
  function invalidate() {
    generation += 1
    inFlight?.abort()
    inFlight = null
    clearFacts()
  }

  async function lookup(rawInput: string): Promise<void> {
    inFlight?.abort()
    const requestGeneration = ++generation
    const controller = new AbortController()
    inFlight = controller
    clearFacts()

    const input = rawInput.trim()
    if (!input) {
      inFlight = null
      return
    }

    status.value = 'resolving'
    let resolution: ResolvedResource
    try {
      resolution = await resolveResource(input, controller.signal)
    } catch {
      if (requestGeneration === generation) {
        queryError.value = '无法解析主播链接'
        status.value = 'settled'
      }
      return
    }

    if (requestGeneration !== generation) {
      return
    }
    if (resolution.resource_type !== 'owner') {
      queryError.value = '该链接不是主播主页，请粘贴主播主页分享链接。'
      status.value = 'settled'
      return
    }

    resolvedResource.value = resolution
    status.value = 'reading'
    platformLoading.value = true
    localLoading.value = true

    const platformRead = readOwner(resolution.resolved_url, controller.signal)
      .then((answer) => {
        if (requestGeneration !== generation) return
        //
        // `/api/owner` currently includes the first post page. Lookup extracts
        // only safe profile facts and immediately drops posts and cursors.
        //
        platformProfile.value = answer.owner
        // Keep this an explicit allow-list. Future additions to the backend's
        // credential metadata must not enter browser state by accident.
        platformCredential.value = { expires_in_days: answer.credential.expires_in_days }
        platformMessage.value = answer.owner_message
      })
      .catch(() => {
        if (requestGeneration === generation) {
          platformError.value = '平台资料暂时无法读取'
        }
      })
      .finally(() => {
        if (requestGeneration === generation) {
          platformLoading.value = false
        }
      })

    const localRead = inspectPersonAssignment(resolution.resolve_id, controller.signal)
      .then((answer) => {
        if (requestGeneration === generation) {
          localInspection.value = answer
        }
      })
      .catch(() => {
        if (requestGeneration === generation) {
          localError.value = '暂时无法确认本地账号归属'
        }
      })
      .finally(() => {
        if (requestGeneration === generation) {
          localLoading.value = false
        }
      })

    await Promise.allSettled([platformRead, localRead])
    if (requestGeneration === generation) {
      status.value = 'settled'
      inFlight = null
    }
  }

  return {
    status,
    loading,
    hasResult,
    resolvedResource,
    queryError,
    platformProfile,
    platformCredential,
    platformMessage,
    platformError,
    platformLoading,
    localInspection,
    localError,
    localLoading,
    lookup,
    invalidate,
  }
})
