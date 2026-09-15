##
## What the application actually needs from its database account, and what to
## say when it has more.
##
## This is a read-only preflight and it deliberately changes nothing. A
## deployment script that widened a grant would be handing itself privileges;
## one that narrowed a grant mid-release would break the writer it is about to
## start. Both are decisions an operator makes with the release in front of
## them, so this only reports.
##
## The direction of the comparison matters. Missing privileges are a release
## blocker - the application will fail at runtime. *Extra* privileges are not a
## blocker; they are a hardening finding, because a working deployment with a
## too-powerful account still works. Conflating the two would either block a
## release for a pre-existing condition or wave through an account that cannot
## run the application.
##
import importlib.util
from pathlib import Path
import unittest


PROJECT_ROOT = Path(__file__).resolve().parents[3]
HELPER = PROJECT_ROOT / "scripts" / "release_db_privileges.py"


def helper_module():
  specification = importlib.util.spec_from_file_location(
    "release_db_privileges", HELPER
  )
  module = importlib.util.module_from_spec(specification)
  specification.loader.exec_module(module)
  return module


class PrivilegeClassificationTest(unittest.TestCase):
  def setUp(self):
    self.module = helper_module()

  def classify(self, grants):
    return self.module.classify_grants(grants, database="smsd")

  def test_exactly_the_needed_privileges_are_sufficient_and_clean(self):
    report = self.classify([
      "GRANT SELECT, INSERT, UPDATE, DELETE, CREATE, DROP, ALTER, INDEX, "
      "REFERENCES ON `smsd`.* TO `app`@`%`"
    ])

    self.assertEqual([], report["missing"])
    self.assertEqual([], report["excessive"])
    self.assertEqual("sufficient", report["verdict"])

  def test_a_missing_privilege_is_a_blocker(self):
    report = self.classify([
      "GRANT SELECT, INSERT, UPDATE ON `smsd`.* TO `app`@`%`"
    ])

    self.assertIn("DELETE", report["missing"])
    self.assertEqual("insufficient", report["verdict"])

  ##
  ## ``ALL PRIVILEGES`` on the application's own schema is how most deployments
  ## are set up. It is not a blocker and it is not nothing.
  ##
  def test_all_privileges_on_the_database_is_sufficient_but_flagged(self):
    report = self.classify(["GRANT ALL PRIVILEGES ON `smsd`.* TO `app`@`%`"])

    self.assertEqual([], report["missing"])
    self.assertEqual("sufficient", report["verdict"])
    self.assertTrue(report["excessive"])

  ##
  ## A global grant is a different thing entirely: it reaches every schema on
  ## the server, including ones this application has no business in.
  ##
  def test_a_global_grant_is_reported_as_excessive(self):
    report = self.classify([
      "GRANT ALL PRIVILEGES ON *.* TO `app`@`%` WITH GRANT OPTION"
    ])

    self.assertEqual([], report["missing"])
    self.assertIn("*.*", " ".join(report["excessive"]))

  def test_grant_option_is_always_called_out(self):
    report = self.classify([
      "GRANT SELECT, INSERT, UPDATE, DELETE, CREATE, DROP, ALTER, INDEX, "
      "REFERENCES ON `smsd`.* TO `app`@`%` WITH GRANT OPTION"
    ])

    self.assertTrue(
      any("GRANT OPTION" in item for item in report["excessive"])
    )

  def test_a_grant_on_another_database_is_not_counted_as_this_one(self):
    report = self.classify(["GRANT ALL PRIVILEGES ON `other`.* TO `app`@`%`"])

    self.assertEqual("insufficient", report["verdict"])
    self.assertTrue(report["missing"])

  ##
  ## Never the credential, and never the row. This runs on a release path whose
  ## output is pasted into tickets.
  ##
  def test_the_report_never_carries_a_password_or_a_host(self):
    report = self.classify([
      "GRANT ALL PRIVILEGES ON `smsd`.* TO `app`@`10.0.0.5` "
      "IDENTIFIED BY PASSWORD '<secret>'"
    ])
    rendered = self.module.render_report(report)

    self.assertNotIn("secret", rendered)
    self.assertNotIn("10.0.0.5", rendered)
    self.assertNotIn("IDENTIFIED", rendered)

  def test_the_rendered_report_names_the_verdict_for_an_operator(self):
    sufficient = self.module.render_report(
      self.classify(["GRANT ALL PRIVILEGES ON `smsd`.* TO `app`@`%`"])
    )
    insufficient = self.module.render_report(
      self.classify(["GRANT SELECT ON `smsd`.* TO `app`@`%`"])
    )

    self.assertIn("SECURITY HARDENING REQUIRED", sufficient)
    self.assertIn("insufficient", insufficient)


class PrivilegeHelperContractTest(unittest.TestCase):
  def test_the_helper_never_writes_to_the_database(self):
    source = HELPER.read_text(encoding="utf-8")

    for forbidden in ("GRANT ", "REVOKE", "DROP ", "ALTER ", "CREATE USER",
                      "SET PASSWORD"):
      ##
      ## Allowed inside the parser, which reads GRANT statements; forbidden as
      ## something this executes.
      ##
      self.assertNotIn(
        'execute("' + forbidden, source, "the helper modifies grants"
      )
    self.assertIn("SHOW GRANTS", source)


if __name__ == "__main__":
  unittest.main()
