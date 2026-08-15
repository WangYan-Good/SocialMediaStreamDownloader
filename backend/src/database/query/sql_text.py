##>> Test
import os
import sys
sys.path.append(os.getcwd())
##<< Test


def escape_like(value: str) -> str:
  """Turn a user's search text into a safe ``LIKE`` pattern.

  The text itself always travels as a bound parameter; what this handles is the
  layer underneath that, where ``%`` and ``_`` are wildcards *inside* the bound
  value.  Left alone, a search for ``100%`` matches every row, and a search for
  ``a_b`` matches ``axb`` - not an injection, but a search that quietly answers
  a different question than the one asked.

  Shared rather than copied.  Two escapers eventually disagree about which
  characters matter, and the weaker one is the one that is wrong.
  """
  ##
  ## MySQL LIKE treats \ as the default escape character.  Escape it first so the
  ## wildcards escaped afterwards are not double-processed.
  ##
  escaped = value.replace("\\", "\\\\")
  escaped = escaped.replace("%", "\\%")
  escaped = escaped.replace("_", "\\_")
  return "%{}%".format(escaped)
