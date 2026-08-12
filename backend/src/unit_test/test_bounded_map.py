import unittest
from concurrent.futures import ThreadPoolExecutor
from threading import Lock

from backend.src.service.bounded_map import run_bounded


class PeakCounter:
  """记录同时在跑的 worker 峰值。

  用计数器而不是 sleep 来观测并发：sleep 竞速在负载高的机器上会假失败，
  而峰值计数在任何调度顺序下都成立。
  """

  def __init__(self):
    self._guard = Lock()
    self.running = 0
    self.peak = 0
    self.seen = []

  def worker(self, item):
    with self._guard:
      self.running += 1
      self.peak = max(self.peak, self.running)
      self.seen.append(item)
    try:
      return item
    finally:
      with self._guard:
        self.running -= 1


class RunBoundedTest(unittest.TestCase):
  def test_without_a_pool_every_item_runs_in_order(self):
    counter = PeakCounter()

    run_bounded([1, 2, 3], counter.worker)

    self.assertEqual(counter.seen, [1, 2, 3])
    self.assertEqual(counter.peak, 1)

  def test_a_limit_of_one_stays_serial_even_with_a_pool(self):
    """默认配置必须与今天的代码路径等价，哪怕池是可用的。"""
    counter = PeakCounter()
    with ThreadPoolExecutor(max_workers=4) as pool:
      run_bounded(range(8), counter.worker, pool=pool, limit=1)

    self.assertEqual(counter.peak, 1)
    self.assertEqual(len(counter.seen), 8)

  def test_every_item_runs_exactly_once(self):
    counter = PeakCounter()
    with ThreadPoolExecutor(max_workers=4) as pool:
      run_bounded(range(20), counter.worker, pool=pool, limit=4)

    self.assertEqual(sorted(counter.seen), list(range(20)))

  def test_a_failing_item_does_not_stop_the_rest(self):
    seen = []
    guard = Lock()

    def worker(item):
      with guard:
        seen.append(item)
      if item == 2:
        raise RuntimeError("boom")

    with ThreadPoolExecutor(max_workers=2) as pool:
      run_bounded(range(6), worker, pool=pool, limit=2)

    self.assertEqual(sorted(seen), list(range(6)))

  def test_it_returns_only_after_every_item_finished(self):
    """job 依赖这一点：返回即代表可以把任务标记为完成。"""
    counter = PeakCounter()
    with ThreadPoolExecutor(max_workers=4) as pool:
      run_bounded(range(12), counter.worker, pool=pool, limit=3)

    self.assertEqual(counter.running, 0)
    self.assertEqual(len(counter.seen), 12)

  def test_a_lazy_source_is_pulled_as_capacity_frees_up(self):
    """翻页要花一次请求，所以不能一次把生成器抽干再开始下载。"""
    pulled = []

    def source():
      for index in range(10):
        pulled.append(index)
        yield index

    started = []
    guard = Lock()

    def worker(item):
      with guard:
        started.append(item)

    with ThreadPoolExecutor(max_workers=2) as pool:
      run_bounded(source(), worker, pool=pool, limit=2)

    self.assertEqual(sorted(started), list(range(10)))
    self.assertEqual(pulled, list(range(10)))


if __name__ == "__main__":
  unittest.main()
