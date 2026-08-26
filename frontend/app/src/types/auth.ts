//
// What the authentication endpoints answer.
//
// Identity plus the server-owned role fact. The frontend uses it to shape
// navigation; backend authorization remains the security authority.
//
// There is no session token here either, and there never will be: the token
// lives in a HttpOnly cookie the browser attaches on its own and this
// application cannot read. That is the point of it being HttpOnly - anywhere
// the page can hold a token, an XSS on the page can read one.
//
export type AppUserRole = 'user' | 'admin'

export interface AuthUser {
  user_id: number
  username: string
  role: AppUserRole
}

export interface AuthUserPayload {
  user: AuthUser
}

export interface LoginRequest {
  username: string
  password: string
}

//
// Where the interface believes it stands.
//
// Four states rather than a boolean. In particular, `unknown` means the first
// check has not completed; an attempted check that could not answer is
// `unavailable` and is never silently retried by ordinary navigation.
//
export type AuthStatus = 'unknown' | 'anonymous' | 'authenticated' | 'unavailable'
