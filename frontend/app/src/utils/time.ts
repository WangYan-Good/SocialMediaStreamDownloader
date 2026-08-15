/**
 * Show a backend timestamp in the reader's own locale.
 *
 * Every value here comes from a database row, and rows have been written by
 * several generations of this program. One that cannot be parsed is shown as it
 * was stored rather than dropped or guessed at: seeing the raw value is how
 * somebody works out what wrote it, and a single bad timestamp must not be able
 * to take down the table around it.
 *
 * Shared rather than copied. It began beside the task labels and is now used by
 * the creators and library screens too; two copies would eventually disagree
 * about what an empty value looks like.
 */
export function formatTimestamp(value: string | null): string {
  if (!value) {
    return '—'
  }
  const parsed = new Date(value)
  if (Number.isNaN(parsed.getTime())) {
    return value
  }
  return parsed.toLocaleString()
}
