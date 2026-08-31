import unittest

from backend.src.library.safe_diagnostics import live_diagnostic, safe_url_host


class SafeUrlHostTest(unittest.TestCase):
  def test_malformed_urls_never_fall_back_to_input_text(self):
    for value in (
      "not a url",
      "https://example.test:invalid/path?token=SECRET",
      "https://[invalid",
      "https://exa\nmple.test/path",
    ):
      with self.subTest(value=value):
        self.assertEqual("unknown", safe_url_host(value))

  def test_only_the_normalized_hostname_survives(self):
    self.assertEqual(
      "live.example.test",
      safe_url_host(
        "https://user:password@LIVE.Example.Test:8443/live?token=SECRET"
      ),
    )


class LiveDiagnosticContractTest(unittest.TestCase):
  def test_unknown_events_are_rejected(self):
    with self.assertRaises(ValueError):
      live_diagnostic("caller_controlled_event")

  def test_fields_are_sanitized_and_exception_messages_are_absent(self):
    message = live_diagnostic(
      "live_info_response",
      status=-1,
      room_id="room id with spaces",
      protocol="signed=SECRET",
      error=RuntimeError("SECRET_EXCEPTION_MESSAGE"),
      state="truthy-but-not-boolean",
    )

    self.assertEqual(
      "live diagnostic event=live_info_response status=unknown "
      "room_id=unknown protocol=unknown error=RuntimeError state=false",
      message,
    )
    self.assertNotIn("SECRET", message)


if __name__ == "__main__":
  unittest.main()
