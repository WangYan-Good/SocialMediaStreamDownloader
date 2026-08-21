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
## blocked here rather than merely discouraged - spends the account's request
## budget.  The image cdn answers 429 on cumulative volume, so a suite that
## quietly talks to it is spending something the owner cannot get back by
## waiting.
##
## It has happened.  A test that stubbed one seam stopped stubbing it during a
## refactor, fell through to the real downloader, and fetched a live profile -
## and nothing in the run said so, because a passing test that made a request
## looks exactly like a passing test that did not.  So the seam is enforced from
## underneath instead of trusted from above: whatever a test forgets to stub,
## the connection itself refuses.
##
## Installed at import time rather than as an autouse fixture, so it covers
## module-level code that runs during collection too.
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
## Patched on the class and on the module-level helper, which is the pair that
## every http client in this dependency tree ends up going through - requests
## and urllib3 included.  Nothing above them needs to know this happened.
##
socket.socket.connect = _refuse
socket.socket.connect_ex = _refuse
socket.create_connection = _refuse
