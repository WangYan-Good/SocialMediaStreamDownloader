//
// What the authentication endpoints answer.
//
// Two fields, and deliberately no more. There is no role here because there is
// no authorization yet, and a role in this type is a field some component will
// start branching on before the decisions behind it have been made.
//
// There is no session token here either, and there never will be: the token
// lives in a HttpOnly cookie the browser attaches on its own and this
// application cannot read. That is the point of it being HttpOnly - anywhere
// the page can hold a token, an XSS on the page can read one.
//
export interface AuthUser {
  user_id: number
  username: string
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
// Three states rather than a boolean. "Not yet asked" and "asked, nobody" are
// different, and collapsing them makes every page render its signed-out shape
// for as long as the first request takes.
//
export type AuthStatus = 'unknown' | 'anonymous' | 'authenticated'
