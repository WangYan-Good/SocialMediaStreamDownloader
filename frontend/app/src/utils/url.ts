/**
 * Whether a value is safe to put in an `href` or an `src`.
 *
 * `rel="noopener noreferrer"` does nothing about the dangerous cases: with
 * `javascript:` or `data:` the scheme *is* the payload, and a click - or, for an
 * image, a load - runs it. Everything this application displays as a link or a
 * picture comes from a platform payload, a database row or a user's paste, so a
 * url is checked rather than trusted.
 *
 * Shared rather than copied. It began in the task detail panel and is now used
 * by avatars and covers as well; two copies would eventually disagree about
 * which schemes are acceptable, and the weaker one would be the hole.
 */
export function isHttpUrl(value: unknown): boolean {
  if (typeof value !== 'string') {
    return false
  }
  try {
    const parsed = new URL(value.trim())
    return parsed.protocol === 'http:' || parsed.protocol === 'https:'
  } catch {
    //
    // Not an absolute url at all - a relative path, a bare word, an empty
    // string. Nothing to link to and nothing to load.
    //
    return false
  }
}
