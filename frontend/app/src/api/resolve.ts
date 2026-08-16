import { request } from './client'
import type {
  BatchResolveResult,
  ResolveRequest,
  ResolvedResource,
} from '@/types/resolution'

/**
 * Ask the server what a pasted link is.
 *
 * Answers identity only - which resource, not what is currently in it - and the
 * receipt that later proves this server resolved it.  Nothing is started.
 */
export function resolveResource(input: string): Promise<ResolvedResource> {
  const body: ResolveRequest = { input }
  return request<ResolvedResource>('/resolve', { method: 'POST', body })
}

export function resolveResources(input: string): Promise<BatchResolveResult> {
  const body: ResolveRequest = { input }
  return request<BatchResolveResult>('/resolve/batch', { method: 'POST', body })
}
