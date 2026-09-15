#!/usr/bin/env python3
"""Decide whether a reference names the artifact a release is allowed to run.

One validator, used by every script that hands something to a container engine,
because the alternative is three regular expressions that agree until one of
them is edited.

What makes a reference acceptable is narrow on purpose:

  - the project's own repository on GHCR, spelled exactly, so a digest from
    somebody else's repository is not "a canonical digest" merely by being a
    digest;
  - addressed by ``@sha256:`` and never by a tag. ``latest`` and ``sha-abc123``
    name an intention that whoever controls the registry can repoint after the
    review; a digest names the bytes.

The reason this matters beyond tidiness is what the release scripts *do* with an
image. The backup and the restore drill mount the operator's configuration into
it - the file holding the production database password - and then run the
image's own code against a database. An image nobody has pinned is an image
somebody can replace, and replacing it hands over the credential. So the
reference is settled before the configuration is read, let alone mounted.
"""

import argparse
import re
import sys


##
## The repository this project publishes to. Lowercase because an OCI reference
## is, and pinned because "any repository on ghcr.io" is not an authority.
##
CANONICAL_REPOSITORY = "ghcr.io/wangyan-good/socialmediastreamdownloader"

CANONICAL_IMAGE = re.compile(
  re.escape(CANONICAL_REPOSITORY) + r"@sha256:[0-9a-f]{64}\Z"
)


class ImageIdentityError(ValueError):
  """The reference may not be used by a release command."""


def require_canonical_image(reference) -> str:
  """Return ``reference`` if it is a canonical release digest, or refuse it."""
  if not isinstance(reference, str) or not reference:
    raise ImageIdentityError("an image reference is required")
  if CANONICAL_IMAGE.fullmatch(reference) is None:
    ##
    ## Deliberately without echoing the reference back. This runs on a path
    ## whose output is pasted into tickets, and an operator who mistyped a
    ## private registry host does not need it quoted into one.
    ##
    raise ImageIdentityError(
      "image must be a canonical digest of {} - a tag names an intention, "
      "a digest names the artifact".format(CANONICAL_REPOSITORY)
    )
  return reference


def main(argv=None) -> int:
  parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
  parser.add_argument("command", choices=["require-canonical"])
  parser.add_argument("reference")
  arguments = parser.parse_args(argv)
  try:
    require_canonical_image(arguments.reference)
  except ImageIdentityError as error:
    print("image identity refused: {}".format(error), file=sys.stderr)
    return 1
  return 0


if __name__ == "__main__":
  raise SystemExit(main())
