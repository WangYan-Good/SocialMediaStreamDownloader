import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from flask import Flask

from backend.src.web.spa_routes import (
  SPA_DIST_DIR,
  build_spa_blueprint,
)


INDEX_HTML = "<!doctype html><html><head></head><body><div id=\"app\"></div></body></html>"
APP_JS = "console.log('vue');"
APP_CSS = ":root{--color-text:#111}"


class DistDirectory:
  """A stand-in for what ``vite build`` leaves behind."""

  def __init__(self, with_index=True, with_assets=True):
    self._temp = TemporaryDirectory()
    self.path = Path(self._temp.name)
    if with_index:
      (self.path / "index.html").write_text(INDEX_HTML, encoding="utf-8")
    if with_assets:
      assets = self.path / "assets"
      assets.mkdir(parents=True, exist_ok=True)
      (assets / "app.js").write_text(APP_JS, encoding="utf-8")
      (assets / "app.css").write_text(APP_CSS, encoding="utf-8")

  def cleanup(self):
    self._temp.cleanup()


def build_app(dist=None):
  app = Flask(__name__)
  app.config["TESTING"] = True
  app.register_blueprint(
    build_spa_blueprint(dist_dir=None if dist is None else dist.path)
  )
  return app


class SpaEntryPointTest(unittest.TestCase):
  """Every way a browser can arrive at the application shell."""

  def setUp(self):
    self.dist = DistDirectory()
    self.addCleanup(self.dist.cleanup)
    self.client = build_app(self.dist).test_client()

  def test_the_bare_prefix_serves_the_shell(self):
    response = self.client.get("/app")

    self.assertEqual(response.status_code, 200)
    self.assertIn("<div id=\"app\">", response.get_data(as_text=True))

  def test_the_trailing_slash_serves_the_shell(self):
    """Both spellings answer directly.

    A redirect between them would work, but it would also make every
    deep-link test depend on following one, and there is nothing to gain.
    """
    response = self.client.get("/app/")

    self.assertEqual(response.status_code, 200)
    self.assertIn("<div id=\"app\">", response.get_data(as_text=True))

  def test_the_shell_is_html(self):
    response = self.client.get("/app/")

    self.assertIn("text/html", response.headers["Content-Type"])


class DeepLinkTest(unittest.TestCase):
  """Refreshing on a client-side route must not 404.

  The router owns these paths, and the server has never heard of them; handing
  back the shell is what lets the browser resolve them itself.
  """

  def setUp(self):
    self.dist = DistDirectory()
    self.addCleanup(self.dist.cleanup)
    self.client = build_app(self.dist).test_client()

  def test_every_declared_route_falls_back_to_the_shell(self):
    for route in ("overview", "new", "creators", "library", "tasks", "system"):
      with self.subTest(route=route):
        response = self.client.get("/app/" + route)

        self.assertEqual(response.status_code, 200)
        self.assertIn("<div id=\"app\">", response.get_data(as_text=True))

  def test_a_nested_route_falls_back_to_the_shell(self):
    response = self.client.get("/app/tasks/7657271784144009946")

    self.assertEqual(response.status_code, 200)
    self.assertIn("<div id=\"app\">", response.get_data(as_text=True))

  def test_a_route_that_the_router_does_not_know_still_reaches_the_shell(self):
    """The client decides what an unknown route means, not the server."""
    response = self.client.get("/app/no-such-page")

    self.assertEqual(response.status_code, 200)

  def test_a_query_string_does_not_change_the_answer(self):
    response = self.client.get("/app/tasks?state=running")

    self.assertEqual(response.status_code, 200)


class AssetTest(unittest.TestCase):
  """Built files are served as themselves, and missing ones say so."""

  def setUp(self):
    self.dist = DistDirectory()
    self.addCleanup(self.dist.cleanup)
    self.client = build_app(self.dist).test_client()

  def test_a_built_script_is_served(self):
    response = self.client.get("/app/assets/app.js")

    self.assertEqual(response.status_code, 200)
    self.assertEqual(response.get_data(as_text=True), APP_JS)

  def test_a_built_stylesheet_is_served(self):
    response = self.client.get("/app/assets/app.css")

    self.assertEqual(response.status_code, 200)
    self.assertEqual(response.get_data(as_text=True), APP_CSS)

  def test_a_missing_asset_is_not_found(self):
    """The trap this rule exists to avoid.

    Falling back to the shell would hand the browser HTML where it asked for
    JavaScript, and the failure surfaces as a syntax error in a file that looks
    fine - miles from the missing build output that actually caused it.
    """
    response = self.client.get("/app/assets/missing.js")

    self.assertEqual(response.status_code, 404)
    self.assertNotIn("<div id=\"app\">", response.get_data(as_text=True))

  def test_a_missing_file_anywhere_is_not_found(self):
    for path in ("favicon.ico", "manifest.webmanifest", "nested/thing.png"):
      with self.subTest(path=path):
        response = self.client.get("/app/" + path)

        self.assertEqual(response.status_code, 404)

  def test_the_shell_is_still_reachable_after_a_missing_asset(self):
    self.client.get("/app/assets/missing.js")

    self.assertEqual(self.client.get("/app/").status_code, 200)


class PathTraversalTest(unittest.TestCase):
  """Nothing outside the build output may be read through this route."""

  def setUp(self):
    self.dist = DistDirectory()
    self.addCleanup(self.dist.cleanup)
    self.outside = self.dist.path.parent / "outside-secret.txt"
    self.outside.write_text("SECRET", encoding="utf-8")
    self.addCleanup(lambda: self.outside.unlink(missing_ok=True))
    self.client = build_app(self.dist).test_client()

  def test_a_traversal_never_reads_a_neighbouring_file(self):
    for path in (
      "/app/../outside-secret.txt",
      "/app/..%2foutside-secret.txt",
      "/app/assets/../../outside-secret.txt",
      "/app/....//outside-secret.txt",
    ):
      with self.subTest(path=path):
        response = self.client.get(path)

        self.assertNotIn("SECRET", response.get_data(as_text=True))

  def test_an_absolute_looking_path_reads_nothing(self):
    response = self.client.get("/app//etc/hostname")

    self.assertNotIn("root", response.get_data(as_text=True))
    self.assertNotEqual(response.status_code, 200)


class MissingBuildTest(unittest.TestCase):
  """A checkout that has never run ``npm run build`` must stay diagnosable."""

  def setUp(self):
    self.dist = DistDirectory(with_index=False, with_assets=False)
    self.addCleanup(self.dist.cleanup)
    self.client = build_app(self.dist).test_client()

  def test_the_shell_reports_that_it_was_never_built(self):
    """Not a 404 and not a crash.

    404 would read as "wrong url"; the truth is that the url is right and the
    build output is absent, which is a one-command fix if the response says so.
    """
    response = self.client.get("/app/")

    self.assertEqual(response.status_code, 503)
    body = response.get_json()
    self.assertEqual(body["status"], "error")
    self.assertEqual(body["code"], 503)
    self.assertIn("npm run build", body["message"])

  def test_a_deep_link_reports_the_same_thing(self):
    response = self.client.get("/app/tasks")

    self.assertEqual(response.status_code, 503)

  def test_an_asset_is_still_simply_not_found(self):
    response = self.client.get("/app/assets/app.js")

    self.assertEqual(response.status_code, 404)


class DefaultLocationTest(unittest.TestCase):
  """Where the build output is expected to be, stated once."""

  def test_the_default_points_at_the_vite_build_output(self):
    self.assertEqual(SPA_DIST_DIR.parts[-3:], ("frontend", "app", "dist"))

  def test_the_blueprint_can_be_built_without_a_directory_present(self):
    """Importing and registering must never depend on a build having run."""
    app = build_app(None)

    self.assertIn("spa", app.blueprints)


class CoexistenceTest(unittest.TestCase):
  """The new shell is added beside what exists; it replaces nothing."""

  def build_full_app(self):
    import server
    from backend.src.unit_test.config_fixture import unified_config

    class FakeDispatcher:
      def register(self):
        pass

      def dispatch(self, payload, context=None):
        pass

    return server.create_app(
      unified_config(),
      FakeDispatcher(),
      schema_guard_factory=lambda config: object(),
    )

  def test_the_legacy_home_page_is_unchanged(self):
    """``/`` stays the working product until the new one has caught up."""
    app = self.build_full_app()

    response = app.test_client().get("/")

    self.assertEqual(response.status_code, 200)
    body = response.get_data(as_text=True)
    self.assertIn("Social Media Stream Downloader", body)
    self.assertNotIn("<div id=\"app\"></div>", body)

  def test_the_json_api_is_not_swallowed_by_the_shell(self):
    """A catch-all that reached ``/api`` would answer HTML to every request."""
    app = self.build_full_app()
    client = app.test_client()

    listing = client.get("/api/tasks")
    self.assertEqual(listing.status_code, 200)
    self.assertEqual(listing.get_json()["status"], "success")

    resolved = client.post("/api/resolve", json={"input": "not a link"})
    self.assertEqual(resolved.status_code, 400)
    self.assertEqual(resolved.get_json()["status"], "error")

  def test_the_shell_route_is_reachable_on_a_configured_app(self):
    app = self.build_full_app()

    response = app.test_client().get("/app/")

    ##
    ## 200 when the frontend has been built, 503 when it has not.  Both are the
    ## route answering; what must never happen is 404, which would mean it was
    ## not registered at all.
    ##
    self.assertIn(response.status_code, (200, 503))

  def test_the_legacy_static_files_are_untouched(self):
    app = self.build_full_app()

    response = app.test_client().get("/static/css/index.css")

    self.assertEqual(response.status_code, 200)


if __name__ == "__main__":
  unittest.main()
