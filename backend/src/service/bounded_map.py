##<<Base>>
from concurrent.futures import FIRST_COMPLETED, wait

##<<Third-part>>
from backend.src.library.loglib import get_logger


def run_bounded(items, worker, pool=None, limit: int = 1) -> None:
  """Apply ``worker`` to every item, with at most ``limit`` running at once.

  Returns only once every item has finished, so a caller may treat the return
  as "all of it is done" and mark its own work complete.

  ``items`` may be a generator that costs something to advance - the owner walk
  spends a request to yield the next page of posts - so it is pulled one item at
  a time as capacity frees up, never drained up front.

  Without a pool, or at a limit below two, items run inline in order.  That is
  the default path and is exactly what the caller did before this existed, which
  is what makes the default configuration a no-op rather than a rewrite.
  """
  if pool is None or not isinstance(limit, int) or limit < 2:
    for item in items:
      _run_one(worker, item)
    return

  pending = set()
  for item in items:
    if len(pending) >= limit:
      ##
      ## Wait for capacity rather than for the whole batch: the next item is not
      ## even pulled from the source until there is somewhere to run it.
      ##
      finished, pending = wait(pending, return_when=FIRST_COMPLETED)
      _collect(finished)
    pending.add(pool.submit(_run_one, worker, item))

  if pending:
    finished, _ = wait(pending)
    _collect(finished)


def _run_one(worker, item) -> None:
  """Run one item, keeping its failure from ending the batch.

  One post failing is an ordinary outcome of a long download; the remaining
  posts are still worth fetching.
  """
  try:
    worker(item)
  except Exception as e:
    get_logger().warning("batch item failed: {}".format(e))


def _collect(finished) -> None:
  """Retrieve every result so nothing fails silently inside a future.

  A future holds its exception until someone asks for it.  Without this, an
  error raised outside ``_run_one``'s own guard would be discarded and the batch
  would report success.
  """
  for future in finished:
    try:
      future.result()
    except Exception as e:
      get_logger().warning("batch item failed: {}".format(e))
