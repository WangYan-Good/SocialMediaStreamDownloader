##<<Base>>
import socket


##
## >>============================= the network bomb =============================>>
##
##
## No unit test in this suite may open a real connection.
##
## This is not a style rule.  A test that reaches douyin is slow, fails when the
## network does, depends on a cookie nobody checked in, and - the reason it is
## blocked rather than merely discouraged - spends the account's request budget.
## The image cdn answers 429 on cumulative volume, so a suite that quietly talks
## to it is spending something the owner cannot get back by waiting.
##
## It has happened.  A test that stubbed one seam stopped stubbing it during a
## refactor, fell through to the real downloader, and fetched a live profile -
## and nothing in the run said so, because a passing test that made a request
## looks exactly like a passing test that did not.  So the seam is enforced from
## underneath instead of trusted from above: whatever a test forgets to stub,
## the connection itself refuses.
##
## A module of its own rather than the body of ``conftest.py``.  pytest may load
## a conftest under a bare name while a test imports it by its dotted path, and
## that is two module objects - two ``RealNetworkAccessDenied`` classes, each
## patching over the other, so which one a caller catches depends on import
## order.  Here the class is defined once and imported the same way by everyone.
##


class RealNetworkAccessDenied(RuntimeError):
  """A unit test tried to open a socket to something outside this process.

  Whatever raised this is missing a stand-in.  Inject the collaborator that
  makes the request - every platform class in this codebase takes one - rather
  than reaching for a way to let the connection through.
  """


def _refuse(*unused_args, **unused_kwargs):
  raise RealNetworkAccessDenied(
    "a unit test tried to open a real network connection; "
    "stub the collaborator that makes the request instead"
  )


##
## Whether the block is already in place.  Idempotent because a conftest can be
## loaded more than once in one run, and arming twice must not leave a second
## copy of anything behind.
##
_installed = False


def install() -> None:
  """Refuse every outbound connection for the rest of this process.

  Both the class method and the module-level helper: ``create_connection`` is
  what most callers reach for, while a client that builds its own socket - which
  urllib3, and therefore ``requests``, does - goes through ``connect``.  Between
  them they cover every http client in this dependency tree.
  """
  global _installed
  if _installed:
    return
  socket.socket.connect = _refuse
  socket.socket.connect_ex = _refuse
  socket.create_connection = _refuse
  _installed = True


def is_installed() -> bool:
  return _installed
