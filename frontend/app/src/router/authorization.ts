import type { Pinia } from 'pinia'
import type {
  NavigationGuard,
  RouteLocationNormalized,
  RouteLocationRaw,
  Router,
} from 'vue-router'

import { useAuthStore } from '@/stores/auth'
import { resolveSafeReturnTarget } from './returnTarget'

declare module 'vue-router' {
  interface RouteMeta {
    requiresAuth?: boolean
    requiresAdmin?: boolean
  }
}

function withReturnTarget(
  router: Router,
  name: 'login' | 'auth-unavailable',
  target: unknown,
): RouteLocationRaw {
  const redirect = resolveSafeReturnTarget(router, target)
  return redirect ? { name, query: { redirect } } : { name }
}

type AuthStore = ReturnType<typeof useAuthStore>

/** The one frontend navigation policy, reusable after a stale-role refresh. */
export function authorizationRedirect(
  router: Router,
  to: RouteLocationNormalized,
  auth: AuthStore,
): RouteLocationRaw | null {
  if (to.name === 'auth-unavailable') {
    if (auth.status === 'unavailable') return null
    if (auth.status === 'anonymous') {
      return withReturnTarget(router, 'login', to.query.redirect)
    }
    return resolveSafeReturnTarget(router, to.query.redirect) ?? { name: 'user-home' }
  }

  if (auth.status === 'unavailable') {
    return withReturnTarget(router, 'auth-unavailable', to.fullPath)
  }

  if (to.name === 'login') {
    if (auth.status === 'authenticated') {
      return resolveSafeReturnTarget(router, to.query.redirect) ?? { name: 'user-home' }
    }
    return null
  }

  if (to.meta.requiresAuth && auth.status === 'anonymous') {
    return withReturnTarget(router, 'login', to.fullPath)
  }

  if (to.meta.requiresAdmin && !auth.isAdmin) {
    return { name: 'forbidden' }
  }

  return null
}

export function createAuthorizationGuard(router: Router, pinia: Pinia): NavigationGuard {
  return async (to) => {
    const auth = useAuthStore(pinia)
    await auth.ensureInitialized()
    return authorizationRedirect(router, to, auth) ?? true
  }
}

export function installAuthorizationGuard(router: Router, pinia: Pinia): void {
  router.beforeEach(createAuthorizationGuard(router, pinia))
}

export async function reevaluateCurrentAuthorization(
  router: Router,
  pinia: Pinia,
): Promise<void> {
  const redirect = authorizationRedirect(
    router,
    router.currentRoute.value,
    useAuthStore(pinia),
  )
  if (redirect !== null) await router.replace(redirect)
}
