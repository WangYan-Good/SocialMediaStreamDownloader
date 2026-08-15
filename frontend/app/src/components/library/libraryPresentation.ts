import type {
  LibraryAwemeType,
  LibraryCompletion,
  LibrarySource,
} from '@/types/library'

//
// The words the library uses, in one place.
//
// Nearly every way of getting this screen wrong is a wording problem, because
// the underlying data is honest and the temptation is to overstate it: a record
// is not a file, and something observed is not something happening.
//

export const TYPE_LABELS: Readonly<Record<LibraryAwemeType, string>> = {
  video: '视频',
  image: '图文',
}

export const SOURCE_LABELS: Readonly<Record<LibrarySource, string>> = {
  api: 'API',
  html: 'HTML 兜底',
}

export const COMPLETION_LABELS: Readonly<Record<LibraryCompletion, string>> = {
  complete: '完整记录',
  partial: '部分记录',
}

//
// room.status as the platform wrote it, carried over from the history query.
//
const ROOM_STATUS_LIVING = 2
const ROOM_STATUS_ENDED = 4

/**
 * What a recorded broadcast's status says, in the past tense it belongs to.
 *
 * Deliberately never "正在直播", not even for status 2. This row is a note taken
 * at some point in the past; the only thing that can answer whether somebody is
 * broadcasting right now is a live probe, which is the creators workspace's job
 * and costs a real platform request. An index of records must not appear to
 * know.
 */
export function recordedLiveStatusLabel(status: number | null): string {
  if (status === ROOM_STATUS_LIVING) {
    return '记录时：直播中'
  }
  if (status === ROOM_STATUS_ENDED) {
    return '已结束'
  }
  return '状态未知'
}

/**
 * How much of a download the record says landed.
 *
 * A statement about the row, never about the disk. `saved_count` is what the
 * run reported saving and `media_count` is what it planned to fetch; neither
 * was re-checked against the filesystem, so "记录完成" is as far as this can
 * honestly go. A post that was never finished is also not a *failure* - nothing
 * says an attempt was made and refused.
 */
export function savedCountLabel(
  savedCount: number | null,
  mediaCount: number | null,
): string {
  if (savedCount === null || mediaCount === null) {
    return '—'
  }
  if (savedCount < mediaCount) {
    return `部分 ${savedCount} / ${mediaCount}`
  }
  return `记录完成 ${savedCount} / ${mediaCount}`
}
