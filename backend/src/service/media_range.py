"""Serving one window of an already-open media file.

Web-neutral, like ``media_asset``: no Flask, no session, no HTTP.  It is handed
a file that has already been opened through the secure boundary and told which
bytes to produce.  Whether the caller may ask has been settled long before -
see the route layer.

Nothing here ever sees a path.  The window is expressed against a descriptor
that was already proven, which is what keeps Range from reintroducing the
re-open this project spent Phase 10B eliminating.
"""

##<<Base>>
import os


##
## How much is read at a time.
##
## A range can be most of a multi-gigabyte recording, so the window is never
## read in one call: memory has to stay flat regardless of what was asked for.
## 64 KiB is comfortably above a page and small enough that a client who hangs
## up is noticed promptly.
##
RANGE_CHUNK_SIZE = 64 * 1024


class BoundedRangeReader:
  """An iterable over exactly ``length`` bytes starting at ``start``.

  Deliberately *not* a file object.  It exposes no ``read`` and no ``fileno``,
  and that absence is the security property rather than an oversight: a WSGI
  server handed something with a descriptor may use ``sendfile`` and copy
  straight from the file to the socket, bypassing every limit expressed in
  Python and sending the rest of the file after the window.  An object that
  offers only iteration cannot be optimised past.

  The underlying file is closed when iteration finishes, when the consumer
  abandons it part way, and when reading fails.  A server that runs for weeks
  cannot leak a descriptor per interrupted download.
  """

  def __init__(self, stream, start: int, length: int):
    self._stream = stream
    self._start = start
    self._remaining = max(0, length)
    self._closed = False

  def __iter__(self):
    ##
    ## Nothing is read for an empty window - not even a seek. A zero-length
    ## range is a legitimate answer and must cost nothing.
    ##
    if self._remaining <= 0:
      self.close()
      return

    try:
      self._stream.seek(self._start, os.SEEK_SET)
      while self._remaining > 0:
        ##
        ## Never more than one chunk, and never more than is still owed. A full
        ## chunk read near the end of the window would pull in bytes past it,
        ## which is exactly the leak this class exists to prevent.
        ##
        chunk = self._stream.read(min(RANGE_CHUNK_SIZE, self._remaining))
        if not chunk:
          ##
          ## The file ended sooner than its own stat promised - it was
          ## truncated while being served. The response stops here rather than
          ## looping forever waiting for bytes that will not arrive.
          ##
          break
        self._remaining -= len(chunk)
        yield chunk
    finally:
      ##
      ## Reached on completion, on an exception, and on the generator being
      ## closed when a consumer stops early.
      ##
      self.close()

  def close(self) -> None:
    """Release the file. Safe to call more than once."""
    if self._closed:
      return
    self._closed = True
    try:
      self._stream.close()
    except Exception:
      ##
      ## The request this belonged to is over either way, and a failure to
      ## close has still released what it could.
      pass


__all__ = ["RANGE_CHUNK_SIZE", "BoundedRangeReader"]
