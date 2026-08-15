import { defineStore } from 'pinia'
import { ref } from 'vue'

import { ApiError } from '@/api/client'
import { getSystemStatus } from '@/api/system'
import type { SystemStatus } from '@/types/system'

/**
 * The system screen's one piece of state.
 *
 * Read once on arrival, then only when somebody asks. Nothing here polls: what
 * this reports changes when an operator changes the server, and each read makes
 * the backend refresh its schema guard - which is a real database round trip.
 * A timer would spend one every few seconds for an answer that almost never
 * moves.
 */
export const useSystemStore = defineStore('system', () => {
  const status = ref<SystemStatus | null>(null)
  const loading = ref(false)
  const error = ref<string | null>(null)
  const hasLoaded = ref(false)

  //
  // When this browser last heard back. Deliberately not the server's own check
  // time: that is a monotonic clock reading, which is not a time of day, and
  // showing it as one would be showing a wrong one.
  //
  const lastUpdatedAt = ref<Date | null>(null)

  //
  // Which read the store is waiting on. Bumped when a read is abandoned, so an
  // answer that arrives after the user left is dropped rather than written into
  // a screen nobody is looking at.
  //
  let generation = 0
  let inFlight: AbortController | null = null

  function abandon(): void {
    generation += 1
    if (inFlight !== null) {
      inFlight.abort()
      inFlight = null
    }
    loading.value = false
  }

  async function load(): Promise<void> {
    if (loading.value) {
      //
      // One read at a time. Every read costs the server a schema check, so
      // three impatient clicks must not become three probes.
      //
      return
    }

    const mine = ++generation
    const controller = new AbortController()
    inFlight = controller
    loading.value = true

    try {
      const answer = await getSystemStatus(controller.signal)
      if (mine !== generation) {
        return
      }
      status.value = answer
      hasLoaded.value = true
      error.value = null
      lastUpdatedAt.value = new Date()
    } catch (caught) {
      if (mine !== generation) {
        return
      }
      //
      // Whatever was last read stays, along with the time it was read. A
      // refresh that could not reach the server says nothing about whether the
      // previous answer was true - and replacing it with nothing would turn a
      // network blip into "the system is unknown".
      //
      error.value =
        caught instanceof ApiError
          ? `暂时无法刷新系统状态：${caught.message}`
          : '暂时无法刷新系统状态'
    } finally {
      if (mine === generation) {
        loading.value = false
        inFlight = null
      }
    }
  }

  return {
    status,
    loading,
    error,
    hasLoaded,
    lastUpdatedAt,
    load,
    abandon,
  }
})
