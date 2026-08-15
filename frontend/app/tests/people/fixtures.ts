import type { PersonDetail, PersonSummaryItem } from '../../src/types/person'

//
// Shared builders, in a module of their own rather than exported from a spec:
// importing a spec file re-runs its describes in whichever file imported it,
// under that file's setup, and they fail for reasons that have nothing to do
// with the code under test.
//

export function person(overrides: Partial<PersonSummaryItem> = {}): PersonSummaryItem {
  return {
    person_id: 1,
    display_name: '某人',
    directory_name: '某人',
    note: null,
    account_count: 2,
    ...overrides,
  }
}

export function detail(overrides: Partial<PersonDetail> = {}): PersonDetail {
  return {
    accounts: [],
    summary: { aweme_count: 0, live_count: 0 },
    subjects: [],
    photographers: [],
    ...overrides,
  }
}
