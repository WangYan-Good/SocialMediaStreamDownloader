import { defineStore } from 'pinia'
import { computed, ref } from 'vue'

import { ApiError } from '@/api/client'
import {
  getCurrentUser,
  login as loginRequest,
  logout as logoutRequest,
} from '@/api/auth'
import type { AuthStatus, AuthUser } from '@/types/auth'

/**
 * Who this browser is signed in as.
 *
 * Holds no credential of any kind. The session is a HttpOnly cookie the
 * browser attaches to same-origin requests on its own, which this code can
 * neither read nor write - so there is nothing here to leak, nothing to put in
 * localStorage, and nothing an XSS on the page could carry away.
 *
 * The router consumes this state for navigation UX. It is not authority: every
 * protected resource remains enforced and scoped by the backend.
 */
export const useAuthStore = defineStore('auth', () => {
  const user = ref<AuthUser | null>(null)

  //
  // Starts as 'unknown', never 'anonymous'.
  //
  // "Nobody has asked yet" and "we asked, and nobody" are different facts. A
  // store that assumed the second would render every page in its signed-out
  // shape until the first request came back, then rearrange itself.
  //
  const status = ref<AuthStatus>('unknown')

  const isAuthenticated = computed(() => status.value === 'authenticated')
  const isAdmin = computed(
    () => status.value === 'authenticated' && user.value?.role === 'admin',
  )

  let resolutionInFlight: Promise<AuthStatus> | null = null
  let identityVersion = 0

  function applyAuthenticated(next: AuthUser) {
    user.value = next
    status.value = 'authenticated'
  }

  function applyAnonymous() {
    user.value = null
    status.value = 'anonymous'
  }

  function applyUnavailable() {
    user.value = null
    status.value = 'unavailable'
  }

  function invalidateResolution(): void {
    identityVersion += 1
    resolutionInFlight = null
  }

  function remember(next: AuthUser): void {
    invalidateResolution()
    applyAuthenticated(next)
  }

  function forget(): void {
    invalidateResolution()
    applyAnonymous()
  }

  function beginResolution(): Promise<AuthStatus> {
    if (resolutionInFlight !== null) return resolutionInFlight
    const startedAtVersion = identityVersion

    const request = (async (): Promise<AuthStatus> => {
      try {
        const next = (await getCurrentUser()).user
        if (identityVersion === startedAtVersion) applyAuthenticated(next)
      } catch (caught) {
        if (identityVersion !== startedAtVersion) return status.value
        if (
          caught instanceof ApiError &&
          caught.kind === 'backend' &&
          caught.status === 401
        ) {
          applyAnonymous()
        } else {
          // No backend or transport detail is retained for presentation.
          applyUnavailable()
        }
      }
      return status.value
    })()

    resolutionInFlight = request
    void request.finally(() => {
      if (resolutionInFlight === request) resolutionInFlight = null
    })
    return request
  }

  function ensureInitialized(): Promise<AuthStatus> {
    if (status.value !== 'unknown') return Promise.resolve(status.value)
    return beginResolution()
  }

  function refreshCurrentUser(): Promise<AuthStatus> {
    return beginResolution()
  }

  return {
    user,
    status,
    isAuthenticated,
    isAdmin,

    ensureInitialized,
    refreshCurrentUser,

    /** Record a definitive business-endpoint 401 without another request. */
    markAnonymous: forget,

    /** Compatibility name for callers from the authentication foundation. */
    async loadCurrentUser(): Promise<void> {
      await refreshCurrentUser()
    },

    async login(username: string, password: string): Promise<void> {
      remember((await loginRequest(username, password)).user)
    },

    /**
     * End the session.
     *
     * The local state is cleared whatever the server said. A logout that left
     * the interface looking signed in because the request failed would be the
     * more dangerous of the two possible mistakes.
     */
    async logout(): Promise<void> {
      try {
        await logoutRequest()
      } finally {
        forget()
      }
    },
  }
})
