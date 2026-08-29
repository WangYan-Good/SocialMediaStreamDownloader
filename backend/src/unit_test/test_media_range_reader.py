##<<Base>>
import io
import unittest

##<<Third-part>>
from backend.src.service.media_range import BoundedRangeReader, RANGE_CHUNK_SIZE


class Counting(io.BytesIO):
  """A file that remembers how it was read."""

  def __init__(self, payload):
    super().__init__(payload)
    self.read_sizes = []
    self.closed_count = 0

  def read(self, size=-1):
    self.read_sizes.append(size)
    return super().read(size)

  def close(self):
    self.closed_count += 1
    super().close()


class BoundedRangeReaderTest(unittest.TestCase):
  """Reads exactly one window of a file, and never a byte past it."""

  def payload(self, length=1000):
    return bytes(one % 251 for one in range(length))

  def test_it_yields_exactly_the_requested_window(self):
    body = self.payload()
    reader = BoundedRangeReader(Counting(body), 100, 200)

    self.assertEqual(body[100:300], b"".join(reader))

  def test_it_yields_exactly_the_requested_length(self):
    ##
    ## The count matters as much as the content: a wrapper that returned the
    ## rest of the file after the window would still "contain" the right bytes.
    ##
    reader = BoundedRangeReader(Counting(self.payload()), 10, 10)

    self.assertEqual(10, len(b"".join(reader)))

  def test_it_starts_where_it_was_told_to(self):
    body = self.payload()
    source = Counting(body)

    produced = b"".join(BoundedRangeReader(source, 500, 4))

    self.assertEqual(body[500:504], produced)

  def test_it_reaches_the_last_byte_of_a_file(self):
    body = self.payload(10)

    self.assertEqual(body[9:10], b"".join(BoundedRangeReader(Counting(body), 9, 1)))

  def test_a_zero_length_window_yields_nothing_and_reads_nothing(self):
    source = Counting(self.payload())

    self.assertEqual(b"", b"".join(BoundedRangeReader(source, 5, 0)))
    self.assertEqual([], source.read_sizes)

  def test_it_never_asks_for_more_than_one_chunk_at_a_time(self):
    """A range of several gigabytes must not become one read call.

    The whole reason this exists rather than ``stream.read(length)``.
    """
    source = Counting(self.payload(1000))

    b"".join(BoundedRangeReader(source, 0, 1000))

    self.assertTrue(source.read_sizes)
    for size in source.read_sizes:
      self.assertLessEqual(size, RANGE_CHUNK_SIZE)

  def test_it_never_asks_for_more_than_it_still_needs(self):
    ##
    ## The last read of a window is short. Asking for a full chunk and
    ## discarding the tail would pull in bytes past the window.
    ##
    ## The file is exactly the size of the window here, so every read can be
    ## satisfied and the sequence of requested sizes is the whole story.
    ##
    source = Counting(self.payload(RANGE_CHUNK_SIZE + 7))

    produced = b"".join(BoundedRangeReader(source, 0, RANGE_CHUNK_SIZE + 7))

    self.assertEqual(RANGE_CHUNK_SIZE + 7, len(produced))
    self.assertEqual([RANGE_CHUNK_SIZE, 7], source.read_sizes)

  def test_it_stops_when_the_file_ends_early(self):
    """A file truncated mid-stream ends the response rather than hanging."""
    source = Counting(self.payload(50))

    produced = b"".join(BoundedRangeReader(source, 40, 100))

    self.assertEqual(10, len(produced))

  def test_it_closes_the_file_when_it_is_done(self):
    source = Counting(self.payload())

    b"".join(BoundedRangeReader(source, 0, 100))

    self.assertEqual(1, source.closed_count)

  def test_it_closes_the_file_when_it_is_abandoned_part_way(self):
    """A client that hangs up mid-download must not leak the descriptor."""
    source = Counting(self.payload())
    reader = BoundedRangeReader(source, 0, 1000)

    iterator = iter(reader)
    next(iterator)
    reader.close()

    self.assertEqual(1, source.closed_count)

  def test_it_closes_the_file_when_reading_fails(self):
    class Broken(Counting):
      def read(self, size=-1):
        raise OSError("device went away")

    source = Broken(self.payload())

    with self.assertRaises(OSError):
      b"".join(BoundedRangeReader(source, 0, 100))

    self.assertEqual(1, source.closed_count)

  def test_it_does_not_expose_a_descriptor_that_would_bypass_the_window(self):
    """The bypass this class is shaped to prevent.

    A WSGI server handed a file-like object with ``fileno()`` may use
    ``sendfile`` and copy the descriptor straight to the socket - ignoring
    ``read()`` entirely, and with it the window. An object without a descriptor
    to find cannot be optimised past.
    """
    reader = BoundedRangeReader(Counting(self.payload()), 10, 10)

    self.assertFalse(hasattr(reader, "fileno"))
    self.assertFalse(hasattr(reader, "read"))

  def test_it_reveals_nothing_about_where_the_file_lives(self):
    reader = BoundedRangeReader(Counting(self.payload()), 10, 10)

    for forbidden in ("path", "name", "save_dir", "root"):
      self.assertFalse(hasattr(reader, forbidden))
