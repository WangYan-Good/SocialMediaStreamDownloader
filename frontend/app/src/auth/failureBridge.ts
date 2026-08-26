import type { Pinia } from 'pinia'
import type { Router } from 'vue-router'

import {
  setAuthorizationFailureHandler,
  type AuthorizationFailureEvent,
} from '@/api/client'
import { reevaluateCurrentAuthorization } from '@/router/authorization'
import { useAuthStore } from '@/stores/auth'

const AUTH_ENDPOINTS = new Set(['/auth/login', '/auth/me', '/auth/logout'])

function isAuthEndpoint(path: string): boolean {
  return AUTH_ENDPOINTS.has(path.split('?', 1)[0])
}

export function installAuthFailureBridge(router: Router, pinia: Pinia): () => void {
  const auth = useAuthStore(pinia)

  const handle = async (event: AuthorizationFailureEvent): Promise<void> => {
    if (isAuthEndpoint(event.path)) return

    if (event.status === 401) {
      auth.markAnonymous()
      await reevaluateCurrentAuthorization(router, pinia)
      return
    }

    if (event.status === 403 && event.backendKind === 'forbidden') {
      await auth.refreshCurrentUser()
      await reevaluateCurrentAuthorization(router, pinia)
    }
  }

  setAuthorizationFailureHandler(handle)
  return () => setAuthorizationFailureHandler(null)
}
