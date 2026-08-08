import unittest


class ConfigContractTest(unittest.TestCase):
  def load_api(self):
    try:
      from backend.src.library.config_contract import (
        ConfigContractError,
        find_config_contract_issues,
        validate_config_contract,
      )
    except ModuleNotFoundError as exc:
      raise AssertionError("config contract comparator is not implemented") from exc
    return ConfigContractError, find_config_contract_issues, validate_config_contract

  def test_contract_error_retains_immutable_ordered_issues_safely(self):
    ConfigContractError, _, _ = self.load_api()
    secret_marker = "contract-secret-marker"
    expected_issues = (
      "$.database.host",
      "$.platform.douyin.live.hls_stall_timeout",
    )

    error = ConfigContractError(expected_issues)

    self.assertIsInstance(error, ValueError)
    self.assertEqual(expected_issues, error.issues)
    self.assertIsInstance(error.issues, tuple)
    self.assertNotIn(secret_marker, str(error))

  def test_aggregates_missing_deep_fields_in_reference_order(self):
    _, find_issues, _ = self.load_api()

    issues = find_issues(
      {
        "platform": {"douyin": {"live": {"hls_stall_timeout": 30}}},
        "database": {"primary": {"host": "localhost"}},
      },
      {"platform": {"douyin": {"live": {}}}, "database": {"primary": {}}},
    )

    self.assertEqual(
      (
        "$.platform.douyin.live.hls_stall_timeout",
        "$.database.primary.host",
      ),
      issues,
    )

  def test_allows_top_level_and_nested_actual_only_keys(self):
    _, find_issues, _ = self.load_api()

    issues = find_issues(
      {"platform": {"douyin": {"enabled": True}}},
      {
        "platform": {"douyin": {"enabled": False, "extra_nested": "allowed"}},
        "extra_top_level": "allowed",
      },
    )

    self.assertEqual((), issues)

  def test_treats_present_falsy_and_empty_values_as_present(self):
    _, find_issues, _ = self.load_api()

    issues = find_issues(
      {
        "null_value": "required",
        "false_value": "required",
        "zero_value": "required",
        "empty_string": "required",
        "empty_list": "required",
      },
      {
        "null_value": None,
        "false_value": False,
        "zero_value": 0,
        "empty_string": "",
        "empty_list": [],
      },
    )

    self.assertEqual((), issues)

  def test_reports_only_mapping_path_when_actual_child_is_scalar(self):
    _, find_issues, _ = self.load_api()

    issues = find_issues(
      {"platform": {"douyin": {"live": {"enabled": True, "port": 8080}}}},
      {"platform": {"douyin": {"live": "not a mapping"}}},
    )

    self.assertEqual(("$.platform.douyin.live",), issues)

  def test_validation_error_includes_paths_without_actual_secret_value(self):
    _, _, validate_contract = self.load_api()
    secret_marker = "super-secret-marker-that-must-not-appear"

    with self.assertRaises(ValueError) as raised:
      validate_contract(
        {"platform": {"douyin": {"required": True}}},
        {"platform": secret_marker},
      )

    message = str(raised.exception)
    self.assertTrue(message.startswith("configuration contract validation failed: "))
    self.assertIn("$.platform", message)
    self.assertNotIn(secret_marker, message)

  def test_rejects_non_mapping_roots_with_safe_messages(self):
    _, find_issues, validate_contract = self.load_api()

    self.assertEqual(("$",), find_issues({"platform": {}}, "not a mapping"))
    self.assertEqual(
      ("$",),
      find_issues({"platform": {}}, "not a mapping", path="$.nested"),
    )
    with self.assertRaises(ValueError) as actual_root_error:
      validate_contract({"platform": {}}, "secret-actual-root")
    self.assertTrue(
      str(actual_root_error.exception).startswith(
        "configuration contract validation failed: "
      )
    )
    self.assertIn("$", str(actual_root_error.exception))
    self.assertNotIn("secret-actual-root", str(actual_root_error.exception))

    with self.assertRaises(ValueError) as reference_root_error:
      find_issues("not a mapping", {"platform": {}})
    self.assertEqual("reference configuration root must be a mapping", str(reference_root_error.exception))


if __name__ == "__main__":
  unittest.main()
