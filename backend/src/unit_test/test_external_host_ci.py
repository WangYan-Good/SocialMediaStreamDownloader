##
## The job has to actually run, and it has to prove what it claims.
##
## Two failure modes this guards against, both of which look green.
##
## The first is a suite that skipped. The reflink tests skip themselves when the
## filesystem cannot clone, so a runner without a reflink-capable scratch
## filesystem would report success having proved nothing about the one mechanism
## the external topology depends on. That is why the job mounts an XFS image and
## why a skip is a hard failure.
##
## The second is mistaking a stub for the real thing. The engine in these tests
## is a bash script that records its arguments; it proves the contract - which
## refusals fire, in what order, what never reaches a command line - and it
## proves nothing whatsoever about rootless Podman. The real behaviour is a
## separate gate on the production host, and the workflow must not blur them.
##
from pathlib import Path
import unittest

import yaml


PROJECT_ROOT = Path(__file__).resolve().parents[3]
WORKFLOW = PROJECT_ROOT / ".github" / "workflows" / "ci.yml"
JOB = "external_host"


class ExternalHostCiJobTest(unittest.TestCase):
  def setUp(self):
    self.text = WORKFLOW.read_text(encoding="utf-8")
    self.workflow = yaml.safe_load(self.text)
    self.job = self.workflow["jobs"][JOB]

  def test_the_job_exists_and_is_named_for_what_it_proves(self):
    self.assertEqual("External-host deployment tests", self.job["name"])

  def test_it_reads_the_checkout_and_nothing_else(self):
    self.assertEqual({"contents": "read"}, self.job["permissions"])

  ##
  ## A real MySQL, pinned to the same digest the rest of the project uses. Not
  ## `latest`, for the reason the MySQL job already gives.
  ##
  def test_it_runs_against_a_pinned_real_mysql(self):
    image = self.job["services"]["mysql"]["image"]

    self.assertTrue(image.startswith("mysql:8.0.46@sha256:"))
    self.assertNotIn("latest", image)

  ##
  ## Without this the snapshot tests skip and the job is green having proved
  ## nothing about reflink.
  ##
  def test_it_provides_a_reflink_capable_filesystem(self):
    steps = "\n".join(str(step) for step in self.job["steps"])

    self.assertIn("mkfs.xfs -m reflink=1", steps)
    self.assertIn("TMPDIR", steps)

  def test_a_skipped_proof_fails_the_job(self):
    steps = "\n".join(str(step) for step in self.job["steps"])

    self.assertIn("skipped", steps)
    self.assertIn("FAIL: the external-host suite skipped a proof", steps)

  ##
  ## Every external suite is listed. A file that exists but is never run is a
  ## test nobody is getting the benefit of.
  ##
  def test_every_external_suite_is_run(self):
    steps = "\n".join(str(step) for step in self.job["steps"])
    directory = PROJECT_ROOT / "backend" / "src" / "unit_test"

    external = sorted(
      path.name for path in directory.glob("test_external_*.py")
    )
    for name in external:
      if name == "test_external_host_ci.py":
        continue
      with self.subTest(suite=name):
        self.assertIn(name, steps)

  ##
  ## The line this job must never be allowed to blur.
  ##
  def test_the_job_says_it_is_not_a_real_engine_proof(self):
    index = self.text.index("  external_host:")
    preamble = self.text[max(0, index - 1200):index]

    self.assertIn("stub", preamble)
    self.assertIn("real-infra gate", preamble)

  ##
  ## The image build and the promotion must both wait for this. A topology the
  ## release cannot deploy to is not a release, so an external-host failure has
  ## to stop promotion the same way a backend failure does.
  ##
  def test_the_image_and_promotion_jobs_wait_for_it(self):
    for downstream in ("image", "publish_tested_image"):
      with self.subTest(job=downstream):
        self.assertIn(JOB, self.workflow["jobs"][downstream]["needs"])

  def test_the_job_starts_no_compose_stack(self):
    steps = "\n".join(str(step) for step in self.job["steps"])

    for forbidden in ("run-docker.sh", "docker compose", "release_deploy.sh"):
      self.assertNotIn(forbidden, steps)


if __name__ == "__main__":
  unittest.main()
