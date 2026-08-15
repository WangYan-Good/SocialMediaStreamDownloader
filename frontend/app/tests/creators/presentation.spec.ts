import { describe, expect, it } from 'vitest'

import {
  credentialNotice,
  lastKnownLiveLabel,
  sessionStatusLabel,
} from '../../src/components/creators/creatorPresentation'

//
// The words themselves, tested apart from the components that show them. What
// this workspace says about live status is the whole point of the screen, and
// most of the ways to get it wrong are wording rather than wiring.
//

describe('what the configured login has left', () => {
  it('says nothing when the backend did not say', () => {
    expect(credentialNotice(null)).toBeNull()
  })

  it('reports one that has already expired', () => {
    expect(credentialNotice(-1)).toContain('已过期')
  })

  it('warns on the last day before expiry', () => {
    expect(credentialNotice(0)).toContain('即将过期')
  })

  it('still warns on the sixth day', () => {
    expect(credentialNotice(6)).toContain('即将过期')
  })

  it('states the remaining life once it is healthy', () => {
    //
    // A plain statement rather than silence: "no banner" is indistinguishable
    // from "nobody checked", and the backend went to the trouble of counting.
    //
    const notice = credentialNotice(30)
    expect(notice).toContain('30')
    expect(notice).not.toContain('即将过期')
    expect(notice).not.toContain('已过期')
  })
})

describe('one recorded broadcast', () => {
  //
  // A session row *is* that broadcast. Borrowing the directory's cache wording
  // would label a specific past session "上次：…", which reads as though the row
  // were describing something other than itself.
  //
  it('states its own status', () => {
    expect(sessionStatusLabel(2)).toBe('直播中')
    expect(sessionStatusLabel(4)).toBe('已结束')
  })

  it('admits when the status was never recorded', () => {
    expect(sessionStatusLabel(null)).toBe('未知')
  })

  it('never borrows the directory cache wording', () => {
    expect(sessionStatusLabel(2)).not.toContain('上次')
    expect(sessionStatusLabel(4)).not.toContain('上次')
  })
})

describe('what the directory last saw', () => {
  it('keeps the past tense that separates a cache from the present', () => {
    //
    // The distinction the whole accounts tab rests on: a cached status is not
    // evidence about now. Only a probe answers that.
    //
    expect(lastKnownLiveLabel(2)).toBe('上次：直播中')
    expect(lastKnownLiveLabel(4)).toBe('上次：已结束')
    expect(lastKnownLiveLabel(null)).toBe('上次：未检查')
    expect(lastKnownLiveLabel(2)).not.toBe('正在直播')
  })
})
