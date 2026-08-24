class AuthError(Exception):
  """Anything authentication refuses or cannot do."""


class InvalidCredentials(AuthError):
  """That username and password combination does not sign anybody in.

  Deliberately one exception for three different situations - no such account,
  wrong password, account disabled - because the caller must not be able to
  tell them apart.  Any distinction that reaches a response turns login into an
  oracle for which usernames exist.
  """


class DuplicateUsername(AuthError):
  """That name already belongs to an account."""


class AuthUnavailable(AuthError):
  """Authentication could not be performed at all.

  The database is unreachable, or the schema is behind the code.  Emphatically
  not a failed login: "I could not check" and "that was wrong" are different
  facts, and answering the second when the first is true tells somebody their
  own password is wrong when it is not.
  """
