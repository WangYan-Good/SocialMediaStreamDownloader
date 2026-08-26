import type { Router } from 'vue-router'

const AUTH_FLOW_ROUTES = new Set(['login', 'forbidden', 'auth-unavailable', 'not-found'])

/** Validate an untrusted redirect query without granting route authorization. */
export function resolveSafeReturnTarget(router: Router, candidate: unknown): string | null {
  if (
    typeof candidate !== 'string' ||
    !candidate.startsWith('/') ||
    candidate.startsWith('//') ||
    candidate.includes('\\')
  ) {
    return null
  }

  try {
    const resolved = router.resolve(candidate)
    if (
      resolved.matched.length === 0 ||
      resolved.matched.some((record) => record.path.includes(':pathMatch')) ||
      (typeof resolved.name === 'string' && AUTH_FLOW_ROUTES.has(resolved.name))
    ) {
      return null
    }
    return resolved.fullPath
  } catch {
    return null
  }
}
