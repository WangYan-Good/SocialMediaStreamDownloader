#!/usr/bin/env python3
"""Do, as the application process itself, everything the application does to media.

The external topology bind-mounts a host directory that predates the release and
whose ownership must not change. Whether that works is a question about one
identity only: the identity the *application* runs as.

That is not the identity a container starts with. The image's entrypoint runs as
root to stage the mounted configuration and then drops to ``appuser``, and under
rootless Podman those two are different host users - container root maps to the
operator, container ``appuser`` maps into the subordinate range. A probe run as
container root therefore writes the bind mount successfully and proves nothing
about the process that will actually write it. That was the defect this file
exists to close.

So the probe refuses to run as root, refuses to run as any identity other than
the one it was told to expect, and then performs the real sequence: the create,
write, fsync, rename and unlink of a recording, and the hidden recovery journal
and orphan quarantine directories that must be writable or a restart loses its
bookkeeping. Directory fsync is included because the application's own durability
contract includes it - a rename nobody fsynced the parent of is a rename that may
not survive the machine.

Nothing here is destructive. Every path it creates is hidden, is created by this
process, and is removed before it returns.
"""

import argparse
import errno
import os
from pathlib import Path
import sys


##
## The two hidden trees the application keeps beside the media it captures. They
## are named here rather than imported because this runs inside a container whose
## import path may not be the repository's - and because a probe that fails to
## import is a probe that proves nothing.
##
JOURNAL_DIRECTORY_NAME = ".smsd-recording-recovery"
QUARANTINE_DIRECTORY_NAME = ".smsd-recording-orphan-quarantine"

MARKER = "media write probe passed"


def fail(message: str) -> None:
  print("media write probe failed: " + message, file=sys.stderr)
  raise SystemExit(1)


##
## Persist a file the way the application persists one: write, flush, fsync,
## then fsync the directory that now names it. Each step is separate because
## each one can fail on its own, and a bind mount that accepts a write but
## refuses an fsync is a bind mount that loses recordings quietly.
##
def _durable_write(path: Path, payload: bytes) -> None:
  descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
  try:
    os.write(descriptor, payload)
    os.fsync(descriptor)
  finally:
    os.close(descriptor)


def _fsync_directory(path: Path) -> None:
  descriptor = os.open(path, os.O_RDONLY | os.O_DIRECTORY)
  try:
    os.fsync(descriptor)
  finally:
    os.close(descriptor)


def _hidden_state_tree(media_root: Path, name: str, label: str) -> None:
  directory = media_root / name
  try:
    directory.mkdir(mode=0o700, exist_ok=True)
  except OSError as error:
    fail("the {} directory could not be created ({})".format(
      label, errno.errorcode.get(error.errno, type(error).__name__)
    ))

  record = directory / ".smsd-write-probe-{}".format(os.getpid())
  try:
    _durable_write(record, b'{"probe":true}\n')
    _fsync_directory(directory)
  except OSError as error:
    fail("the {} state could not be written ({})".format(
      label, errno.errorcode.get(error.errno, type(error).__name__)
    ))
  finally:
    try:
      record.unlink()
    except OSError:
      pass


def run(arguments) -> int:
  ##
  ## >>===================== who is actually running =====================>>
  ##
  ## Checked before any filesystem work, because every result below is only
  ## meaningful in the name of a specific identity. A probe that silently ran as
  ## somebody else would report a capability the application does not have.
  ##
  uid = os.geteuid()
  gid = os.getegid()
  if uid == 0:
    fail(
      "this proves the application's access and the application does not run "
      "as root; a root probe measures the entrypoint, not the process that "
      "writes the media"
    )
  if uid != arguments.expect_uid:
    fail("running as uid {} rather than the application's {}".format(
      uid, arguments.expect_uid
    ))
  if gid != arguments.expect_gid:
    fail("running as gid {} rather than the application's {}".format(
      gid, arguments.expect_gid
    ))

  media_root = Path(arguments.media_root)
  if not media_root.is_dir():
    fail("the media root is not an existing directory")

  ##
  ## >>======================== read what is there ========================>>
  ##
  ## The tree predates the deployment. An application that can write but cannot
  ## read the library it inherited is not deployed, it is empty.
  ##
  existing = 0
  for current, directories, files in os.walk(media_root, followlinks=False):
    directories[:] = [name for name in directories if not name.startswith(".")]
    for name in files:
      path = Path(current) / name
      try:
        with open(path, "rb") as handle:
          handle.read(1)
      except OSError as error:
        fail("existing media could not be read ({})".format(
          errno.errorcode.get(error.errno, type(error).__name__)
        ))
      existing += 1
  if arguments.require_existing and existing == 0:
    fail("the media root holds nothing to read; this proves no read access")

  ##
  ## >>=============== the lifecycle of one captured recording ===============>>
  ##
  staging = media_root / ".smsd-write-probe-{}.part".format(os.getpid())
  published = media_root / ".smsd-write-probe-{}.flv".format(os.getpid())
  try:
    _durable_write(staging, b"smsd-write-probe")
    os.replace(staging, published)
    _fsync_directory(media_root)
  except OSError as error:
    for path in (staging, published):
      try:
        path.unlink()
      except OSError:
        pass
    fail("a recording could not be captured at the media root ({})".format(
      errno.errorcode.get(error.errno, type(error).__name__)
    ))

  try:
    published.unlink()
    _fsync_directory(media_root)
  except OSError as error:
    fail("a recording could not be removed from the media root ({})".format(
      errno.errorcode.get(error.errno, type(error).__name__)
    ))

  ##
  ## >>==================== the bookkeeping beside it ====================>>
  ##
  _hidden_state_tree(media_root, JOURNAL_DIRECTORY_NAME, "recovery journal")
  _hidden_state_tree(media_root, QUARANTINE_DIRECTORY_NAME, "orphan quarantine")

  print("{}: uid={} gid={} read={}".format(MARKER, uid, gid, existing))
  return 0


def build_parser() -> argparse.ArgumentParser:
  parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
  parser.add_argument("--media-root", required=True)
  parser.add_argument("--expect-uid", required=True, type=int)
  parser.add_argument("--expect-gid", required=True, type=int)
  parser.add_argument("--require-existing", action="store_true")
  return parser


def main(argv=None) -> int:
  return run(build_parser().parse_args(argv))


if __name__ == "__main__":
  raise SystemExit(main())
