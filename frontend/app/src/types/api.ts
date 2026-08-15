//
// The envelope every backend endpoint answers in.
//
// Success and failure are told apart by `status`, not by the HTTP code alone:
// the code is carried inside the body too, and the two agree, but only one of
// the two shapes has `data` and only the other has `message`.  Typing them as a
// union is what makes reading `data` off a failure a compile error rather than
// an `undefined` three components later.
//

export interface ApiSuccess<T> {
  status: 'success'
  code: number
  data: T
}

export interface ApiFailure {
  status: 'error'
  code: number
  message: string
}

export type ApiEnvelope<T> = ApiSuccess<T> | ApiFailure

//
// Why a request did not produce data.  Kept as a closed set so a caller can
// branch on the cause without matching on message text, which is Chinese prose
// written for a person and free to change.
//
export type ApiErrorKind =
  //
  // The backend answered, in its own envelope, that it refused.
  //
  | 'backend'
  //
  // The request never reached a backend: offline, DNS, connection reset.
  //
  | 'network'
  //
  // Something answered, but not this api: an HTML error page from a proxy, a
  // truncated body, an envelope missing its `status`.
  //
  | 'malformed'
