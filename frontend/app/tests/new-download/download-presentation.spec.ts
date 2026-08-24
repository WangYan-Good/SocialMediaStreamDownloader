import { describe, expect, it } from 'vitest'

import {
  createFailureMessage,
  downloadActionLabel,
  platformLabel,
  resolveFailureMessage,
  resourceKindLabel,
  trackingFailureMessage,
} from '../../src/components/new-download/downloadPresentation'

//
// The backend already answers in the user's language - "暂不支持该平台的链接",
// "无法解析该短链接，请稍后重试". So the job here is not to translate it: it is
// to let those through untouched and to stop the two kinds of text that are not
// written for a user - a browser transport failure, and this app's own internal
// vocabulary - from reaching the screen as the main message.
//

describe('naming the resource in words a user already knows', () => {
  it('gives the platform its own name rather than its wire value', () => {
    expect(platformLabel('douyin')).toBe('抖音')
    expect(platformLabel('DOUYIN')).toBe('抖音')
  })

  it('passes an unknown platform through rather than inventing a name', () => {
    expect(platformLabel('bilibili')).toBe('bilibili')
  })

  it('names each resource kind', () => {
    expect(resourceKindLabel('post')).toBe('作品')
    expect(resourceKindLabel('owner')).toBe('主播')
    expect(resourceKindLabel('live')).toBe('直播')
  })

  it('says what pressing the button will start', () => {
    expect(downloadActionLabel('post')).toBe('开始下载')
    //
    // The owner and live labels stay distinct. "开始下载" alone would read the
    // same for one post as for an entire back catalogue, and that difference is
    // the reason the owner tick-box exists at all.
    //
    expect(downloadActionLabel('owner')).toBe('开始下载全部作品')
    expect(downloadActionLabel('live')).toBe('开始录制直播')
  })
})

describe('turning a failed identification into a result', () => {
  it('says nothing when nothing failed', () => {
    expect(resolveFailureMessage(null)).toBeNull()
  })

  it('keeps a refusal the backend already worded for a user', () => {
    expect(resolveFailureMessage('暂不支持该平台的链接')).toBe('暂不支持该平台的链接')
    expect(resolveFailureMessage('一次只能解析一个链接')).toBe('一次只能解析一个链接')
  })

  it('replaces a browser transport failure with what it means', () => {
    expect(resolveFailureMessage('Failed to fetch')).toBe('网络连接失败，请检查网络后重试。')
    expect(resolveFailureMessage('NetworkError when attempting to fetch')).toBe(
      '网络连接失败，请检查网络后重试。',
    )
  })

  it('replaces any other internal text rather than showing it', () => {
    for (const internal of [
      'resource unsupported',
      "KeyError: 'aweme_id'",
      'Traceback (most recent call last)',
    ]) {
      expect(resolveFailureMessage(internal)).toBe('暂时无法识别内容，请稍后重试。')
    }
  })
})

describe('turning a failed start into a result', () => {
  it('asks for a fresh identification when the receipt aged out', () => {
    //
    // The remedy, not the cause. "解析结果不存在或已过期" is the backend's own
    // wording and is accurate, but "receipt"/"解析" is this program's vocabulary
    // rather than the user's.
    //
    expect(createFailureMessage('解析结果不存在或已过期，请重新解析', true)).toBe(
      '链接识别结果已过期，请重新识别。',
    )
  })

  it('says nothing when nothing failed', () => {
    expect(createFailureMessage(null, false)).toBeNull()
  })

  it('keeps a refusal the backend already worded for a user', () => {
    expect(createFailureMessage('该主播暂时无法下载', false)).toBe('该主播暂时无法下载')
  })

  it('replaces transport and internal text with a download-shaped result', () => {
    expect(createFailureMessage('Failed to fetch', false)).toBe(
      '暂时无法开始下载，请检查网络后重试。',
    )
    expect(createFailureMessage('refused 500', false)).toBe(
      '暂时无法开始下载，请稍后重试。',
    )
  })
})

describe('turning an unreadable status into a result', () => {
  it('says nothing when nothing failed', () => {
    expect(trackingFailureMessage(null, false)).toBeNull()
  })

  it('says the record is gone rather than that the download failed', () => {
    expect(trackingFailureMessage('任务记录不存在或已过期', true)).toBe(
      '下载记录不存在或已过期，请前往所有任务查看。',
    )
  })

  it('says the status is unavailable without repeating the transport reason', () => {
    //
    // The flow composes "暂时无法获取任务状态：Failed to fetch" for its own
    // state. Passing the whole string through would put the transport's words
    // on screen just because the prefix happened to be Chinese, so the reason
    // is dropped here rather than appended.
    //
    expect(trackingFailureMessage('暂时无法获取任务状态：Failed to fetch', false)).toBe(
      '暂时无法获取下载状态，请稍后重试。',
    )
  })

  it('never claims the download itself failed', () => {
    const message = trackingFailureMessage('暂时无法获取任务状态', false)

    expect(message).not.toContain('失败')
  })
})
