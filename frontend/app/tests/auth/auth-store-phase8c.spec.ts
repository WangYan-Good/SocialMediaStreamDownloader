import { createPinia, setActivePinia } from 'pinia'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import { getCurrentUser, login, logout } from '../../src/api/auth'
import { ApiError } from '../../src/api/client'
import { useAuthStore } from '../../src/stores/auth'

vi.mock('../../src/api/auth', () => ({
  getCurrentUser: vi.fn(),
  login: vi.fn(),
  logout: vi.fn(),
}))

const mockedMe = vi.mocked(getCurrentUser)
const mockedLogin = vi.mocked(login)
const mockedLogout = vi.mocked(logout)
const ALICE = { user_id: 1, username: 'alice', role: 'user' as const }
const OPERATOR = { user_id: 2, username: 'operator', role: 'admin' as const }

function backendFailure(status: number) {
  return new ApiError({
    kind: 'backend',
    status,
    code: status,
    message: status === 401 ? '未登录' : '认证服务暂时不可用',
  })
}

function deferred<T>() {
  let resolve: (value: T) => void = () => {}
  const promise = new Promise<T>((settle) => {
    resolve = settle
  })
  return { promise, resolve }
}

beforeEach(() => {
  setActivePinia(createPinia())
  vi.clearAllMocks()
  mockedMe.mockResolvedValue({ user: ALICE })
  mockedLogin.mockResolvedValue({ user: ALICE })
  mockedLogout.mockResolvedValue(undefined)
})

describe('the four-state authentication bootstrap', () => {
  it('starts unknown and becomes authenticated after one initial check', async () => {
    const auth = useAuthStore()

    expect(auth.status).toBe('unknown')
    await auth.ensureInitialized()

    expect(auth.status).toBe('authenticated')
    expect(auth.user).toEqual(ALICE)
  })

  it('records a definitive 401 as anonymous', async () => {
    mockedMe.mockRejectedValue(backendFailure(401))
    const auth = useAuthStore()

    await auth.ensureInitialized()

    expect(auth.status).toBe('anonymous')
    expect(auth.user).toBeNull()
  })

  it('records 503, network, and malformed failures as unavailable', async () => {
    const failures = [
      backendFailure(503),
      new ApiError({ kind: 'network', status: null, code: null, message: 'socket reset' }),
      new ApiError({ kind: 'malformed', status: 200, code: null, message: 'bad envelope' }),
    ]

    for (const failure of failures) {
      setActivePinia(createPinia())
      mockedMe.mockRejectedValueOnce(failure)
      const auth = useAuthStore()

      await auth.ensureInitialized()

      expect(auth.status).toBe('unavailable')
      expect(auth.user).toBeNull()
    }
  })

  it('does not treat a malformed HTTP 401 as a definitive anonymous result', async () => {
    mockedMe.mockRejectedValue(
      new ApiError({
        kind: 'malformed',
        status: 401,
        code: null,
        message: 'bad envelope',
      }),
    )
    const auth = useAuthStore()

    await auth.ensureInitialized()

    expect(auth.status).toBe('unavailable')
    expect(auth.user).toBeNull()
  })

  it('shares one in-flight request between concurrent initialization calls', async () => {
    const pending = deferred<{ user: typeof ALICE }>()
    mockedMe.mockReturnValue(pending.promise)
    const auth = useAuthStore()

    const first = auth.ensureInitialized()
    const second = auth.ensureInitialized()

    expect(mockedMe).toHaveBeenCalledTimes(1)
    pending.resolve({ user: ALICE })
    await Promise.all([first, second])
    expect(auth.status).toBe('authenticated')
  })

  it('does not turn ordinary navigation from unavailable into an implicit retry', async () => {
    mockedMe.mockRejectedValueOnce(backendFailure(503))
    const auth = useAuthStore()
    await auth.ensureInitialized()

    await auth.ensureInitialized()

    expect(auth.status).toBe('unavailable')
    expect(mockedMe).toHaveBeenCalledTimes(1)
  })

  it('allows an explicit refresh from unavailable to authenticate', async () => {
    mockedMe.mockRejectedValueOnce(backendFailure(503)).mockResolvedValueOnce({ user: OPERATOR })
    const auth = useAuthStore()
    await auth.ensureInitialized()

    await auth.refreshCurrentUser()

    expect(auth.status).toBe('authenticated')
    expect(auth.user).toEqual(OPERATOR)
    expect(auth.isAdmin).toBe(true)
    expect(mockedMe).toHaveBeenCalledTimes(2)
  })

  it('allows an explicit refresh to discover an expired session', async () => {
    const auth = useAuthStore()
    await auth.ensureInitialized()
    mockedMe.mockRejectedValueOnce(backendFailure(401))

    await auth.refreshCurrentUser()

    expect(auth.status).toBe('anonymous')
    expect(auth.user).toBeNull()
  })

  it('shares an explicit refresh with initialization already in flight', async () => {
    const pending = deferred<{ user: typeof ALICE }>()
    mockedMe.mockReturnValue(pending.promise)
    const auth = useAuthStore()

    const initialize = auth.ensureInitialized()
    const refresh = auth.refreshCurrentUser()

    expect(mockedMe).toHaveBeenCalledTimes(1)
    pending.resolve({ user: ALICE })
    await Promise.all([initialize, refresh])
  })

  it('does not let an older refresh undo a definitive business 401', async () => {
    const pending = deferred<{ user: typeof OPERATOR }>()
    mockedMe.mockReturnValue(pending.promise)
    const auth = useAuthStore()
    const refresh = auth.refreshCurrentUser()

    auth.markAnonymous()
    pending.resolve({ user: OPERATOR })
    await refresh

    expect(auth.status).toBe('anonymous')
    expect(auth.user).toBeNull()
  })

  it('does not let an older refresh restore identity after logout', async () => {
    const pending = deferred<{ user: typeof OPERATOR }>()
    mockedMe.mockReturnValue(pending.promise)
    mockedLogout.mockResolvedValue(undefined)
    const auth = useAuthStore()
    const refresh = auth.refreshCurrentUser()

    await auth.logout()
    pending.resolve({ user: OPERATOR })
    await refresh

    expect(auth.status).toBe('anonymous')
    expect(auth.user).toBeNull()
  })

  it.each([
    backendFailure(503),
    new ApiError({
      kind: 'network',
      status: null,
      code: null,
      message: 'socket reset',
    }),
    new ApiError({
      kind: 'malformed',
      status: 503,
      code: null,
      message: 'bad envelope',
    }),
  ])('preserves the known identity when logout rejects', async (failure) => {
    mockedLogout.mockRejectedValueOnce(failure)
    const auth = useAuthStore()
    await auth.ensureInitialized()

    await expect(auth.logout()).rejects.toBe(failure)

    expect(auth.status).toBe('authenticated')
    expect(auth.user).toEqual(ALICE)
  })

  it('does not invalidate an in-flight identity refresh when logout fails', async () => {
    const pending = deferred<{ user: typeof OPERATOR }>()
    const failure = backendFailure(503)
    mockedMe.mockResolvedValueOnce({ user: ALICE }).mockReturnValueOnce(pending.promise)
    mockedLogout.mockRejectedValueOnce(failure)
    const auth = useAuthStore()
    await auth.ensureInitialized()
    const refresh = auth.refreshCurrentUser()

    await expect(auth.logout()).rejects.toBe(failure)
    expect(auth.status).toBe('authenticated')
    expect(auth.user).toEqual(ALICE)

    pending.resolve({ user: OPERATOR })
    await refresh

    expect(auth.status).toBe('authenticated')
    expect(auth.user).toEqual(OPERATOR)
  })

  it('does not let an older refresh overwrite a successful login', async () => {
    const pending = deferred<{ user: typeof OPERATOR }>()
    mockedMe.mockReturnValue(pending.promise)
    const auth = useAuthStore()
    const refresh = auth.refreshCurrentUser()

    await auth.login('alice', 'password')
    pending.resolve({ user: OPERATOR })
    await refresh

    expect(auth.status).toBe('authenticated')
    expect(auth.user).toEqual(ALICE)
  })
})
