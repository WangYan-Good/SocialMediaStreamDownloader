import unittest

from backend.src.platform.douyin.douyin_url_hosts import (
  host_of,
  hostname,
  is_content_host,
  is_live_host,
  is_short_link_host,
  matches,
)


class HostnameTest(unittest.TestCase):
  def test_a_plain_host_is_returned_lowercased(self):
    self.assertEqual(hostname("WWW.Douyin.COM"), "www.douyin.com")

  def test_a_port_is_dropped(self):
    self.assertEqual(hostname("www.douyin.com:443"), "www.douyin.com")

  def test_credentials_are_dropped_and_the_real_host_wins(self):
    """``https://www.douyin.com@evil.test/`` really points at evil.test.

    Reading the part before the @ as the host is how a lookalike url gets
    treated as ours.
    """
    self.assertEqual(hostname("www.douyin.com@evil.test"), "evil.test")

  def test_a_trailing_dot_is_dropped(self):
    self.assertEqual(hostname("www.douyin.com."), "www.douyin.com")

  def test_credentials_with_a_port(self):
    self.assertEqual(hostname("user:pw@evil.test:8443"), "evil.test")


class MatchesTest(unittest.TestCase):
  def test_an_exact_domain_matches(self):
    self.assertTrue(matches("douyin.com", "douyin.com"))

  def test_a_subdomain_matches(self):
    self.assertTrue(matches("www.douyin.com", "douyin.com"))

  def test_a_suffix_that_is_not_a_subdomain_does_not_match(self):
    self.assertFalse(matches("notdouyin.com", "douyin.com"))

  def test_a_longer_host_containing_the_domain_does_not_match(self):
    self.assertFalse(matches("douyin.com.evil.test", "douyin.com"))


class HostRoleTest(unittest.TestCase):
  def test_content_hosts(self):
    for netloc in ("www.douyin.com", "douyin.com", "m.douyin.com",
                   "www.iesdouyin.com", "iesdouyin.com"):
      with self.subTest(netloc=netloc):
        self.assertTrue(is_content_host(netloc))

  def test_lookalikes_are_not_content_hosts(self):
    for netloc in ("douyin.com.evil.test", "notdouyin.com",
                   "fake-douyin.com", "example.test"):
      with self.subTest(netloc=netloc):
        self.assertFalse(is_content_host(netloc))

  def test_live_hosts(self):
    for netloc in ("live.douyin.com", "webcast.amemv.com"):
      with self.subTest(netloc=netloc):
        self.assertTrue(is_live_host(netloc))

  def test_a_live_host_is_also_a_content_host(self):
    """Overlap is deliberate: callers reject live *after* accepting the domain."""
    self.assertTrue(is_content_host("live.douyin.com"))
    self.assertTrue(is_live_host("live.douyin.com"))

  def test_short_link_host(self):
    self.assertTrue(is_short_link_host("v.douyin.com"))
    self.assertFalse(is_short_link_host("www.douyin.com"))
    self.assertFalse(is_short_link_host("v.douyin.com.evil.test"))


class HostOfTest(unittest.TestCase):
  def test_a_whole_url(self):
    self.assertEqual(
      host_of("https://www.douyin.com/user/MS4wLjABAAAA?x=1"),
      "www.douyin.com",
    )

  def test_empty_input(self):
    for value in ("", "   ", None, 42):
      with self.subTest(value=value):
        self.assertEqual(host_of(value), "")


if __name__ == "__main__":
  unittest.main()
