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
 * Nothing in the router or the api layer consults this store to decide whether
 * a request is allowed. Phase 8A establishes the role fact and server helper
 * foundation; business authorization and interface guards remain Phase 8B.
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

  function remember(next: AuthUser) {
    user.value = next
    status.value = 'authenticated'
  }

  function forget() {
    user.value = null
    status.value = 'anonymous'
  }

  return {
    user,
    status,
    isAuthenticated,

    /** Ask the server who this browser is. */
    async loadCurrentUser(): Promise<void> {
      try {
        remember((await getCurrentUser()).user)
      } catch (caught) {
        if (caught instanceof ApiError && caught.status === 401) {
          //
          // A definite answer: this browser is nobody.
          //
          forget()
          return
        }
        //
        // Anything else - a 503, an outage, a malformed reply - leaves the
        // question unanswered. Recording it as 'anonymous' would appear to log
        // everybody out whenever the database hiccuped.
        //
        status.value = 'unknown'
        user.value = null
      }
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
