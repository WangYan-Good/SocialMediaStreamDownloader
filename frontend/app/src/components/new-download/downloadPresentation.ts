import type { ResourceType } from '@/types/resolution'

//
// How the download screens read to someone who has never heard of a receipt.
//
// Presentation only. Nothing here changes what the server decided, how a
// failure was classified, or which request gets sent - the flow composables
// still hold every one of those rules. This file decides which words that
// reach the screen, and it exists because two of the three screens showed the
// same internal vocabulary in two slightly different ways.
//

const PLATFORM_LABELS: Readonly<Record<string, string>> = {
  douyin: '抖音',
}

/**
 * The platform under the name its users call it.
 *
 * An unknown value passes through unchanged rather than becoming "未知平台":
 * the wire value is at least true, and a placeholder would hide the fact that
 * a platform was added without anyone naming it here.
 */
export function platformLabel(platform: string): string {
  return PLATFORM_LABELS[platform.toLowerCase()] ?? platform
}

const KIND_LABELS: Readonly<Record<ResourceType, string>> = {
  post: '作品',
  owner: '主播',
  live: '直播',
}

export function resourceKindLabel(type: ResourceType): string {
  return KIND_LABELS[type]
}

//
// What the button will actually start.
//
// All three begin with "开始下载"/"开始录制" so the main action reads the same
// way throughout, but the owner one still spells out that this is the whole
// back catalogue - that difference is the entire reason its tick-box exists,
// and flattening all three to "开始下载" would quietly remove the warning.
//
const ACTION_LABELS: Readonly<Record<ResourceType, string>> = {
  post: '开始下载',
  owner: '开始下载全部作品',
  live: '开始录制直播',
}

export function downloadActionLabel(type: ResourceType): string {
  return ACTION_LABELS[type]
}

//
// Whether a message was written for a person.
//
// The backend already answers refusals in the user's language, so the test is
// not "is this Chinese" for its own sake - it is the cheapest reliable way to
// tell that sentence apart from a browser's "Failed to fetch" or a stray
// exception string, neither of which is ever written in it.
//
function writtenForAUser(message: string): boolean {
  return /[㐀-鿿]/.test(message)
}

function looksLikeTransportFailure(message: string): boolean {
  return /failed to fetch|networkerror|network|offline|connection|timeout/i.test(message)
}

/**
 * Why the content could not be identified, as a result rather than a cause.
 *
 * A backend refusal is passed straight through - it knows why it refused and
 * already says so readably. Anything else is replaced wholesale rather than
 * appended to, because the useful half of "解析失败：Failed to fetch" is the
 * half the user cannot read.
 */
export function resolveFailureMessage(message: string | null): string | null {
  if (!message) {
    return null
  }
  if (looksLikeTransportFailure(message)) {
    return '网络连接失败，请检查网络后重试。'
  }
  return writtenForAUser(message) ? message : '暂时无法识别内容，请稍后重试。'
}

/**
 * Why the download could not be started.
 *
 * The expired receipt wins over whatever the backend called it, because it is
 * the one failure with a remedy the user can act on, and the remedy - identify
 * the link again - is what they need to be told.
 */
export function createFailureMessage(
  message: string | null,
  receiptExpired: boolean,
): string | null {
  if (receiptExpired) {
    return '链接识别结果已过期，请重新识别。'
  }
  if (!message) {
    return null
  }
  if (looksLikeTransportFailure(message)) {
    return '暂时无法开始下载，请检查网络后重试。'
  }
  return writtenForAUser(message) ? message : '暂时无法开始下载，请稍后重试。'
}

/**
 * Why the download's status could not be read.
 *
 * Deliberately ignores the underlying message instead of passing it through.
 * The flow builds "暂时无法获取任务状态：Failed to fetch" for its own state, and
 * that string would satisfy any "written for a user" test on the strength of
 * its prefix while carrying the transport's words to the screen anyway.
 *
 * Neither branch says the download failed. A status that cannot be read is not
 * an outcome, and claiming one here would be this screen inventing it.
 */
export function trackingFailureMessage(
  message: string | null,
  recordMissing: boolean,
): string | null {
  if (recordMissing) {
    return '下载记录不存在或已过期，请前往所有任务查看。'
  }
  if (!message) {
    return null
  }
  return '暂时无法获取下载状态，请稍后重试。'
}
