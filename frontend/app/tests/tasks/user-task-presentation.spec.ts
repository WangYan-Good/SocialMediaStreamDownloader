import { describe, expect, it } from 'vitest'

import {
  itemSummary,
  taskNote,
  userResultFields,
} from '../../src/components/tasks/user/userTaskPresentation'
import type { TaskItem } from '../../src/types/task'

function item(state: TaskItem['state'], key = 'x'): TaskItem {
  return { key, state, message: null, metadata: {} }
}

//
// The backend already writes task.message in the user's language - "下载失败",
// "已保存 2 / 3 个媒体文件", "直播录制已停止". So this is not a translation
// layer, and deliberately is not built like one: it passes that text through
// and only withholds the shapes that were never written for a person.
//

describe('what a task says about itself', () => {
  it('keeps a message the runner already wrote for a user', () => {
    for (const written of [
      '下载失败',
      '已保存 2 / 3 个媒体文件',
      '直播录制已停止',
      '作品已被删除',
    ]) {
      expect(taskNote(written)).toBe(written)
    }
  })

  it('says nothing when the task said nothing', () => {
    expect(taskNote(null)).toBeNull()
    expect(taskNote('   ')).toBeNull()
  })

  it('withholds text that was never meant for a person', () => {
    for (const internal of [
      'KeyError: aweme_id',
      'Traceback (most recent call last)',
      'ConnectionResetError(104)',
      'sqlalchemy.exc.OperationalError',
    ]) {
      expect(taskNote(internal)).toBe('任务遇到问题，请稍后重试。')
    }
  })
})

describe('which results a user is shown', () => {
  it('reports what was saved out of how many', () => {
    const fields = userResultFields({
      result: { saved_count: 2, media_count: 3, partial: true },
    })

    expect(fields).toEqual([
      { key: 'saved_count', label: '已保存', value: '2' },
      { key: 'media_count', label: '媒体总数', value: '3' },
      { key: 'partial', label: '部分完成', value: '是' },
    ])
  })

  it('never leaks the operational half of the same result object', () => {
    //
    // These sit beside the counts in exactly the same metadata blob. A user
    // detail that rendered the whole object would publish a filesystem path
    // and the streaming protocol along with them.
    //
    const fields = userResultFields({
      result: {
        saved_count: 1,
        save_dir: '/mnt/video/somebody',
        output_path: '/mnt/video/somebody/live.flv',
        protocol: 'flv',
        owner_user_id: '5885',
        test_mode: true,
        room_status: 2,
        nickname: '某位主播',
      },
    })
    const keys = fields.map((one) => one.key)

    expect(keys).toEqual(['saved_count'])
  })

  it('says nothing when the task recorded no result', () => {
    expect(userResultFields({})).toEqual([])
    expect(userResultFields({ result: null })).toEqual([])
    expect(userResultFields({ result: 'not an object' })).toEqual([])
  })

  it('passes a recorded reason through only when a person could read it', () => {
    expect(userResultFields({ result: { reason: '作品已被删除' } })).toEqual([
      { key: 'reason', label: '原因', value: '作品已被删除' },
    ])
    expect(userResultFields({ result: { reason: 'HTTPError 403' } })).toEqual([])
  })
})

describe('summarising the work items', () => {
  it('counts the items by state rather than naming them', () => {
    //
    // An item's key is the aweme id the downloader was working on. It
    // identifies the work to the program, and means nothing to the person who
    // asked for it, so the count is the honest thing to show.
    //
    const summary = itemSummary([
      item('success'),
      item('success'),
      item('failed'),
      item('skipped'),
      item('running'),
      item('pending'),
    ])

    expect(summary).toEqual([
      { state: 'success', label: '已完成', count: 2 },
      { state: 'failed', label: '失败', count: 1 },
      { state: 'skipped', label: '已跳过', count: 1 },
      { state: 'running', label: '进行中', count: 1 },
      { state: 'pending', label: '排队中', count: 1 },
    ])
  })

  it('leaves out the states nothing is in', () => {
    expect(itemSummary([item('success')])).toEqual([
      { state: 'success', label: '已完成', count: 1 },
    ])
  })

  it('has nothing to say about a task with no items', () => {
    expect(itemSummary([])).toEqual([])
  })
})
