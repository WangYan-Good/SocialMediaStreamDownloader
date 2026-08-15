import { request } from './client'
import type { SystemStatus } from '@/types/system'

/**
 * What this server is willing to say about its own state.
 *
 * One request, and the only one this screen makes. The answer is a safe summary
 * the server built from a whitelist; nothing here asks for configuration, logs
 * or anything on disk, because no endpoint offers them.
 *
 * A degraded database is part of a successful answer rather than a failure:
 * reporting it is half of what this endpoint is for, so a failure here means
 * the server could not answer at all.
 */
export function getSystemStatus(signal?: AbortSignal): Promise<SystemStatus> {
  return request<SystemStatus>('/system/status', {
    ...(signal ? { signal } : {}),
  })
}
