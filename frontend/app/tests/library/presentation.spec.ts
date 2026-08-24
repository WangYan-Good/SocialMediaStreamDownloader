import { describe, expect, it } from 'vitest'

import {
  COMPLETION_LABELS,
  SOURCE_LABELS,
  TYPE_LABELS,
  creatorName,
  recordedLiveStatusLabel,
  savedCountLabel,
} from '../../src/components/library/libraryPresentation'

//
// The library reports records, and almost every way of getting it wrong is a
// wording problem: saying a file exists when only a record does, or saying
// somebody is broadcasting when a row says they were.
//

describe('what a recorded live status means', () => {
  it('says a broadcast was live at the moment it was observed', () => {
    //
    // Never "正在直播". This row is a note somebody took in the past, and the
    // only thing that can answer the present tense is a probe - which belongs
    // to the creators workspace, not to an index of what was recorded.
    //
    const label = recordedLiveStatusLabel(2)

    expect(label).toContain('记录时')
    expect(label).not.toBe('正在直播')
  })

  it('says a finished broadcast has finished', () => {
    expect(recordedLiveStatusLabel(4)).toBe('已结束')
  })

  it('admits when the status was never recorded', () => {
    expect(recordedLiveStatusLabel(null)).toBe('状态未知')
    expect(recordedLiveStatusLabel(99)).toBe('状态未知')
  })
})

describe('what a download record says about the files', () => {
  it('reports a complete record as a record, not as files on disk', () => {
    //
    // Nothing in this phase looked at the filesystem. "记录完成" is a claim
    // about the row; "文件完整" would be a claim about the disk.
    //
    const label = savedCountLabel(3, 3)

    expect(label).toContain('记录完成')
    expect(label).not.toContain('文件')
  })

  it('reports a partial record with both counts', () => {
    const label = savedCountLabel(1, 3)

    expect(label).toContain('部分')
    expect(label).toContain('1')
    expect(label).toContain('3')
    expect(label).not.toContain('丢失')
  })

  it('never calls an unfinished download a failure', () => {
    expect(savedCountLabel(0, 2)).not.toContain('失败')
  })

  it('says nothing definite when the counts are missing', () => {
    expect(savedCountLabel(null, null)).toBe('—')
  })
})

describe('the vocabularies the backend writes', () => {
  it('names both post types', () => {
    expect(TYPE_LABELS.video).toBe('视频')
    expect(TYPE_LABELS.image).toBe('图文')
  })

  it('names both fetch routes', () => {
    expect(SOURCE_LABELS.api).toBe('API')
    expect(SOURCE_LABELS.html).toContain('HTML')
  })

  it('names both completion states', () => {
    expect(COMPLETION_LABELS.complete).toContain('完整记录')
    expect(COMPLETION_LABELS.partial).toContain('部分记录')
  })
})

describe('naming a creator to a user', () => {
  it('uses the nickname when there is one', () => {
    expect(creatorName('某位主播')).toBe('某位主播')
  })

  it('says the creator is unknown rather than exposing an account id', () => {
    //
    // The management tables fall back to owner_user_id, which is right there:
    // an operator looking at an unnamed row still needs something to go on. A
    // user does not, and the identifier means nothing to them.
    //
    expect(creatorName(null)).toBe('未知创作者')
    expect(creatorName('')).toBe('未知创作者')
    expect(creatorName('   ')).toBe('未知创作者')
  })
})
