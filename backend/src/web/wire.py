"""How internal identities are spelled for a browser.

One direction only.  Values arrive from the url through Flask's own converters,
which is where text becomes an identity again; this module is the other side of
that boundary and turns an identity back into text.
"""


def recording_id_to_wire(value) -> str:
  """``recording_record.recording_id`` as canonical decimal text.

  A string, not a number, because the column is ``BIGINT UNSIGNED``.  Its domain
  reaches 18446744073709551615 while a JavaScript number stops being exact above
  9007199254740991, so a JSON number is not an identity-preserving wire for it -
  a browser would silently round the identity and then ask for a different
  recording.  That the ids in any one table are small today is a fact about that
  table, not about the contract.

  ``type(...) is not int`` rather than isinstance, matching ``_require_identifier``
  in the query layer: ``True`` is an ``int`` in Python and would serialize as
  "1", which is a real recording's identity.

  Raises rather than inventing a spelling.  ``str(None)`` is "None" and
  ``str(7.0)`` is "7.0"; both would reach a browser looking like identities and
  come back as url segments.  Nothing here should ever receive one, so the honest
  answer is a fault the route boundary reports - not a value.
  """
  if type(value) is not int or value < 1:
    raise ValueError("recording_id must be a positive integer")
  return str(value)


__all__ = ["recording_id_to_wire"]
