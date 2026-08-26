import type { App } from 'vue'
import type { Pinia } from 'pinia'
import type { Router } from 'vue-router'

import { installAuthFailureBridge } from '@/auth/failureBridge'
import { installAuthorizationGuard } from '@/router/authorization'

/** Install auth navigation before mounting, so protected views never flicker. */
export async function bootstrapApplication(
  app: App,
  pinia: Pinia,
  router: Router,
  mountTarget: string | Element,
): Promise<void> {
  app.use(pinia)
  installAuthorizationGuard(router, pinia)
  installAuthFailureBridge(router, pinia)
  app.use(router)
  await router.isReady()
  app.mount(mountTarget)
}
