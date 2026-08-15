import type { SystemDatabaseState } from '@/types/system'

//
// The words the system page uses, in one place.
//

/** How each schema state reads, beside the sentence the server sent. */
export const DATABASE_STATE_LABELS: Readonly<Record<SystemDatabaseState, string>> = {
  ready: '已就绪',
  unavailable: '当前不可用',
  blocked: '架构状态阻止写入',
  disabled: '数据库持久化已禁用',
  unknown: '无法确认',
}

//
// Colour is never the only signal: every badge carries one of these words, so
// the state is readable without seeing the styling at all.
//
export const DATABASE_STATE_TONES: Readonly<Record<SystemDatabaseState, string>> = {
  ready: 'ok',
  unavailable: 'bad',
  blocked: 'bad',
  disabled: 'muted',
  unknown: 'muted',
}

/**
 * A configured switch, said in words.
 *
 * `null` is its own answer - the server had nothing configured there - and is
 * shown as unknown rather than quietly becoming "off".
 */
export function switchLabel(value: boolean | null): string {
  if (value === null) {
    return '未知'
  }
  return value ? '开启' : '关闭'
}

/** The same, for things that read better as enabled or disabled. */
export function enabledLabel(value: boolean | null): string {
  if (value === null) {
    return '未知'
  }
  return value ? '已启用' : '已禁用'
}

export function numberLabel(value: number | null): string {
  return value === null ? '未知' : String(value)
}

export function textLabel(value: string | null): string {
  return value === null || value === '' ? '未知' : value
}
