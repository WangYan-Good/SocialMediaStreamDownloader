import type { PersonRole } from '@/types/person'

//
// Wire values stay wire values; these are only what a user reads.
//
export const ROLE_LABELS: Readonly<Record<PersonRole, string>> = {
  main: '大号',
  alt: '小号',
  matrix: '矩阵号',
}

/**
 * What to show when a person has no folder yet.
 *
 * A directory comes from the account marked `main`, so a person without one
 * simply has not had a main account chosen. Inventing a name here would create
 * a folder the backend never agreed to.
 */
export function directoryLabel(directoryName: string | null): string {
  return directoryName ?? '尚未由大号确定目录'
}
