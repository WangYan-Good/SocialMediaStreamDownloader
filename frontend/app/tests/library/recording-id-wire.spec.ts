import { readFileSync } from 'node:fs'
import { dirname, resolve } from 'node:path'
import { fileURLToPath } from 'node:url'

import { mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import { listRecordingAssets } from '../../src/api/mediaAssets'
import UserLibraryRecordingTable from '../../src/components/library/UserLibraryRecordingTable.vue'
import { useLibraryStore } from '../../src/stores/library'
import { useLibraryAssetsStore } from '../../src/stores/libraryAssets'
import type { LibraryRecording, RecordingId } from '../../src/types/library'

//
// `recording_record.recording_id` is a MySQL BIGINT UNSIGNED. Its domain reaches
// 18446744073709551615, while a JavaScript number stops being exact above
// 9007199254740991 - so an identity that ever becomes a `number` in this
// application has already been rounded, silently, before anything can check it.
//
// The backend therefore sends decimal text. These tests are the browser half of
// that contract: the text must reach the url, the selection and the store
// unchanged.
//
const BEYOND_SAFE: RecordingId = '9007199254740993'

//
// What that identity becomes if it is ever parsed as a double. Asserting its
// absence is what makes these tests able to fail.
//
const ROUNDED = '9007199254740992'

function stubFetch() {
  const fake = vi.fn((_url: string, _init?: RequestInit) =>
    Promise.resolve(
      new Response(
        JSON.stringify({
          status: 'success',
          code: 200,
          data: {
            resource: { kind: 'recording', recording_id: BEYOND_SAFE },
            storage_state: 'available',
            assets: [],
          },
        }),
        { status: 200, headers: { 'Content-Type': 'application/json' } },
      ),
    ),
  )
  vi.stubGlobal('fetch', fake)
  return fake
}

function recording(overrides: Partial<LibraryRecording> = {}): LibraryRecording {
  return {
    recording_id: BEYOND_SAFE,
    platform: 'douyin',
    room_id: '7123',
    nickname: '主播',
    title: '晚间直播',
    started_at: null,
    finished_at: null,
    created_at: '2026-08-15T09:30:15.250',
    ...overrides,
  }
}

beforeEach(() => {
  setActivePinia(createPinia())
  vi.unstubAllGlobals()
  vi.clearAllMocks()
})

describe('a recording identity on its way to a url', () => {
  it('reaches the endpoint exactly as it was received', async () => {
    const fake = stubFetch()

    await listRecordingAssets(BEYOND_SAFE)

    expect(fake.mock.calls[0][0]).toBe(
      '/api/library/recordings/9007199254740993/assets',
    )
  })

  it('is not rounded on the way', async () => {
    const fake = stubFetch()

    await listRecordingAssets(BEYOND_SAFE)

    expect(String(fake.mock.calls[0][0])).not.toContain(ROUNDED)
  })

  it('reaches the endpoint through the store unchanged', async () => {
    const fake = stubFetch()
    const store = useLibraryAssetsStore()

    await store.loadRecordingAssets(BEYOND_SAFE)

    expect(fake.mock.calls[0][0]).toBe(
      '/api/library/recordings/9007199254740993/assets',
    )
    expect(store.currentResourceKey).toBe(`recording:${BEYOND_SAFE}`)
    expect(store.currentResourceKey).not.toContain(ROUNDED)
  })

  it('reads back the resource the server named, as text', async () => {
    stubFetch()

    const answer = await listRecordingAssets(BEYOND_SAFE)

    expect(answer.resource).toEqual({
      kind: 'recording',
      recording_id: BEYOND_SAFE,
    })
    expect(typeof (answer.resource as { recording_id: unknown }).recording_id).toBe(
      'string',
    )
  })
})

describe('a recording identity on its way through a selection', () => {
  it('is emitted by the table exactly as the row holds it', async () => {
    const table = mount(UserLibraryRecordingTable, {
      props: { recordings: [recording()], selectedId: null },
    })

    await table.get('.table__view').trigger('click')

    const emitted = table.emitted('select')
    expect(emitted).toHaveLength(1)
    expect(emitted?.[0][0]).toBe(BEYOND_SAFE)
    expect(typeof emitted?.[0][0]).toBe('string')
  })

  it('is held by the store exactly as the table emitted it', () => {
    const store = useLibraryStore()

    store.selectRecording(BEYOND_SAFE)

    expect(store.selectedRecordingId).toBe(BEYOND_SAFE)
    expect(store.selectedRecordingId).not.toBe(ROUNDED)
  })

  it('still matches its own row after the round trip', () => {
    //
    // The comparison the table performs to mark a row selected. Two identities
    // that differ only past the safe range must not compare equal, and one that
    // survived intact must.
    //
    const store = useLibraryStore()
    const row = recording()

    store.selectRecording(row.recording_id)

    expect(row.recording_id === store.selectedRecordingId).toBe(true)
    expect(ROUNDED === store.selectedRecordingId).toBe(false)
  })
})

describe('the recording identity flow as written', () => {
  //
  // A source-level assertion, because the failure this guards against does not
  // show up as a wrong answer in a test that uses small ids - `Number('7')` and
  // `parseInt('7')` are both perfectly correct for every identity that exists
  // today. The defect only appears years later, in production, on one row.
  //
  // Scoped to the files an identity actually travels through. There is nothing
  // wrong with `Number()` elsewhere: `person_id` and a page size are quantities,
  // and parsing them is what they are for.
  //
  const FLOW = [
    'src/api/mediaAssets.ts',
    'src/stores/libraryAssets.ts',
    'src/types/library.ts',
    'src/types/mediaAsset.ts',
    'src/components/library/UserLibraryRecordingTable.vue',
    'src/components/library/UserLibraryDetailPanel.vue',
  ]

  const APP_ROOT = resolve(dirname(fileURLToPath(import.meta.url)), '..', '..')

  function sourceOf(relative: string): string {
    return readFileSync(resolve(APP_ROOT, relative), 'utf-8')
  }

  it.each(FLOW)('%s converts no identity to a number', (relative) => {
    const source = sourceOf(relative)

    for (const lossy of [
      /\bNumber\s*\(/,
      /\bparseInt\s*\(/,
      /\bparseFloat\s*\(/,
      /[^\w)\]]\+\s*recording/i,
    ]) {
      expect(source).not.toMatch(lossy)
    }
  })

  it('states the identity type in exactly one place', () => {
    //
    // One authority, so the library row and the asset resource cannot drift
    // into disagreeing about what a recording is called.
    //
    const declarations = FLOW.map(sourceOf).filter((source) =>
      /^\s*export type RecordingId\b/m.test(source),
    )

    expect(declarations).toHaveLength(1)
  })

  it('would have been rounded had it ever been a number', () => {
    //
    // Not a statement about this code - a statement about JavaScript, and the
    // whole reason the contract above exists. `number` was an accepted spelling
    // for this identifier until this phase; this is what accepting it cost.
    //
    expect(String(Number(BEYOND_SAFE))).toBe(ROUNDED)
  })

  it('no longer offers a number as an alternative spelling', () => {
    expect(sourceOf('src/api/mediaAssets.ts')).not.toMatch(/recordingId:\s*number/)
    expect(sourceOf('src/api/mediaAssets.ts')).not.toMatch(/number\s*\|\s*string/)
    expect(sourceOf('src/stores/libraryAssets.ts')).not.toMatch(
      /recordingId:\s*number/,
    )
    expect(sourceOf('src/stores/libraryAssets.ts')).not.toMatch(
      /number\s*\|\s*string/,
    )
    expect(sourceOf('src/types/mediaAsset.ts')).not.toMatch(
      /recording_id:\s*number/,
    )
  })

  it('names that type wherever an identity is carried', () => {
    expect(sourceOf('src/types/library.ts')).toMatch(/recording_id:\s*RecordingId/)
    expect(sourceOf('src/types/mediaAsset.ts')).toMatch(
      /recording_id:\s*RecordingId/,
    )
    expect(sourceOf('src/api/mediaAssets.ts')).toMatch(
      /recordingId:\s*RecordingId/,
    )
    expect(sourceOf('src/stores/libraryAssets.ts')).toMatch(
      /recordingId:\s*RecordingId/,
    )
  })
})
