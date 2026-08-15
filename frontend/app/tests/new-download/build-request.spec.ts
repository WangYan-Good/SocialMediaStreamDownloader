import { describe, expect, it } from 'vitest'

import { buildCreateTaskRequest } from '../../src/composables/useNewDownloadFlow'
import type { ResolvedResource } from '../../src/types/resolution'

const SEC_UID = 'MS4wLjABAAAAGZkW5n1EHZD_TFyQ-QiaISBPemtKFxVVdhLSeoXhh-U'
const AWEME_ID = '7657271784144009946'
const SHORT_LINK = 'https://v.douyin.com/M-kmspLye0o/'

function base() {
  return {
    resolve_id: 'receipt-1',
    platform: 'douyin',
    source_url: SHORT_LINK,
    expires_in_seconds: 600,
  }
}

export const postResolution: ResolvedResource = {
  ...base(),
  resource_type: 'post',
  resolved_url: `https://www.douyin.com/video/${AWEME_ID}`,
  identity: { aweme_id: AWEME_ID },
}

export const liveResolution: ResolvedResource = {
  ...base(),
  resource_type: 'live',
  resolved_url: 'https://live.douyin.com/123456',
  identity: {},
}

export const ownerResolution: ResolvedResource = {
  ...base(),
  resource_type: 'owner',
  resolved_url: `https://www.douyin.com/user/${SEC_UID}`,
  identity: { sec_user_id: SEC_UID },
}

describe('buildCreateTaskRequest', () => {
  it('turns a post into a post download', () => {
    expect(buildCreateTaskRequest(postResolution)).toEqual({
      resolve_id: 'receipt-1',
      task_type: 'post_download',
    })
  })

  it('turns a live room into a recording', () => {
    expect(buildCreateTaskRequest(liveResolution)).toEqual({
      resolve_id: 'receipt-1',
      task_type: 'live_record',
    })
  })

  it('turns an owner into a batch download of everything', () => {
    //
    // The mode has to be stated: the backend requires it, because an owner link
    // on its own does not mean "download the entire back catalogue".
    //
    expect(buildCreateTaskRequest(ownerResolution)).toEqual({
      resolve_id: 'receipt-1',
      task_type: 'owner_batch_download',
      options: { mode: 'all' },
    })
  })

  it('sends exactly the mode and nothing beside it', () => {
    const request = buildCreateTaskRequest(ownerResolution)

    expect(request.task_type).toBe('owner_batch_download')
    if (request.task_type === 'owner_batch_download') {
      expect(Object.keys(request.options)).toEqual(['mode'])
    }
  })

  it('never describes the resource', () => {
    //
    // The whole security boundary of the create endpoint in one assertion: the
    // receipt is the only claim this client makes. An aweme id or a url here
    // would be refused by the backend as an unknown field - and, worse, would
    // mean the browser had a say in what gets downloaded.
    //
    for (const resolution of [postResolution, liveResolution, ownerResolution]) {
      const sent = Object.keys(buildCreateTaskRequest(resolution))

      for (const forbidden of [
        'aweme_id',
        'sec_user_id',
        'room_id',
        'source_url',
        'resolved_url',
        'platform',
        'resource_type',
        'identity',
      ]) {
        expect(sent).not.toContain(forbidden)
      }
    }
  })

  it('sends only the three fields the endpoint accepts', () => {
    expect(Object.keys(buildCreateTaskRequest(postResolution)).sort()).toEqual([
      'resolve_id',
      'task_type',
    ])
    expect(Object.keys(buildCreateTaskRequest(ownerResolution)).sort()).toEqual([
      'options',
      'resolve_id',
      'task_type',
    ])
  })

  it('carries whichever receipt it was given', () => {
    const request = buildCreateTaskRequest({ ...postResolution, resolve_id: 'other' })

    expect(request.resolve_id).toBe('other')
  })

  it('omits options entirely for the types that take none', () => {
    //
    // Not `options: {}` - absent. Both are accepted by the backend, but sending
    // an empty object invites a later reader to think there is something to put
    // in it.
    //
    expect('options' in buildCreateTaskRequest(postResolution)).toBe(false)
    expect('options' in buildCreateTaskRequest(liveResolution)).toBe(false)
  })
})
