import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from flask import Flask

from backend.src.web.spa_routes import SPA_DIST_DIR, build_spa_blueprint


INDEX_HTML = '<!doctype html><html><body><div id="app"></div></body></html>'
APP_JS = "console.log('vue');"
APP_CSS = ":root{--color-text:#111}"
SHELL_MARKER = '<div id="app">'


class DistDirectory:
  """A controlled stand-in for one Vite production build."""

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

  def write(self, relative: str, contents: str) -> None:
    target = self.path / relative
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(contents, encoding="utf-8")

  def cleanup(self):
    self._temp.cleanup()


def build_app(dist=None):
  app = Flask(__name__)
  app.config["TESTING"] = True
  app.register_blueprint(
    build_spa_blueprint(dist_dir=None if dist is None else dist.path)
  )
  return app


class RootEntryPointTest(unittest.TestCase):
  def setUp(self):
    self.dist = DistDirectory()
    self.addCleanup(self.dist.cleanup)
    self.client = build_app(self.dist).test_client()

  def test_root_serves_the_vue_shell_as_html(self):
    response = self.client.get("/")

    self.assertEqual(200, response.status_code)
    self.assertIn(SHELL_MARKER, response.get_data(as_text=True))
    self.assertIn("text/html", response.headers["Content-Type"])

  def test_query_string_does_not_change_the_shell(self):
    response = self.client.get("/?from=bookmark")

    self.assertEqual(200, response.status_code)
    self.assertIn(SHELL_MARKER, response.get_data(as_text=True))


class RootDeepLinkTest(unittest.TestCase):
  def setUp(self):
    self.dist = DistDirectory()
    self.addCleanup(self.dist.cleanup)
    self.client = build_app(self.dist).test_client()

  def test_all_six_product_routes_serve_the_shell(self):
    for route in ("overview", "new", "creators", "library", "tasks", "system"):
      with self.subTest(route=route):
        response = self.client.get("/" + route)

        self.assertEqual(200, response.status_code)
        self.assertIn(SHELL_MARKER, response.get_data(as_text=True))

  def test_nested_and_unknown_client_routes_serve_the_shell(self):
    for path in ("/tasks/7657271784144009946", "/no-such-page"):
      with self.subTest(path=path):
        response = self.client.get(path)

        self.assertEqual(200, response.status_code)
        self.assertIn(SHELL_MARKER, response.get_data(as_text=True))


class RootAssetTest(unittest.TestCase):
  def setUp(self):
    self.dist = DistDirectory()
    self.addCleanup(self.dist.cleanup)
    self.client = build_app(self.dist).test_client()

  def test_built_assets_are_served_exactly(self):
    script = self.client.get("/assets/app.js")
    stylesheet = self.client.get("/assets/app.css")

    self.assertEqual(200, script.status_code)
    self.assertEqual(APP_JS, script.get_data(as_text=True))
    self.assertEqual(200, stylesheet.status_code)
    self.assertEqual(APP_CSS, stylesheet.get_data(as_text=True))

  def test_missing_assets_and_files_are_not_shell_fallbacks(self):
    for path in (
      "/assets/missing.js",
      "/favicon.ico",
      "/manifest.webmanifest",
      "/nested/thing.png",
    ):
      with self.subTest(path=path):
        response = self.client.get(path)

        self.assertEqual(404, response.status_code)
        self.assertNotIn(SHELL_MARKER, response.get_data(as_text=True))


class ReservedNamespaceTest(unittest.TestCase):
  def setUp(self):
    self.dist = DistDirectory()
    for namespace in ("api", "static", "legacy"):
      self.dist.write(namespace + "/leak.html", "DIST SECRET " + namespace)
    self.addCleanup(self.dist.cleanup)
    self.client = build_app(self.dist).test_client()

  def test_reserved_namespaces_are_refused_before_dist_access(self):
    for namespace in ("api", "static", "legacy"):
      with self.subTest(namespace=namespace):
        response = self.client.get("/{}/leak.html".format(namespace))

        self.assertEqual(404, response.status_code)
        body = response.get_data(as_text=True)
        self.assertNotIn("DIST SECRET", body)
        self.assertNotIn(SHELL_MARKER, body)

  def test_unknown_reserved_paths_are_not_vue_routes(self):
    for path in (
      "/api/definitely-not-an-endpoint",
      "/static",
      "/static/",
      "/static/definitely-not-found.css",
      "/legacy",
      "/legacy/",
      "/legacy/definitely-not-a-page",
    ):
      with self.subTest(path=path):
        response = self.client.get(path)

        self.assertEqual(404, response.status_code)
        self.assertNotIn(SHELL_MARKER, response.get_data(as_text=True))


class CompatibilityRedirectTest(unittest.TestCase):
  def setUp(self):
    self.dist = DistDirectory()
    self.addCleanup(self.dist.cleanup)
    self.client = build_app(self.dist).test_client()

  def assertTemporaryRedirect(self, source: str, target: str):
    response = self.client.get(source, follow_redirects=False)

    self.assertEqual(302, response.status_code)
    self.assertEqual(target, response.headers["Location"])
    self.assertTrue(response.headers["Location"].startswith("/"))
    self.assertFalse(response.headers["Location"].startswith("//"))

  def test_old_entry_points_redirect_to_root_equivalents(self):
    for source, target in (
      ("/app", "/"),
      ("/app/", "/"),
      ("/app/overview", "/overview"),
      ("/app/library", "/library"),
      ("/app/tasks", "/tasks"),
      ("/app/assets/app.js", "/assets/app.js"),
    ):
      with self.subTest(source=source):
        self.assertTemporaryRedirect(source, target)

  def test_redirect_preserves_the_query_string(self):
    self.assertTemporaryRedirect(
      "/app/tasks?state=running&owner=42",
      "/tasks?state=running&owner=42",
    )

  def test_double_slash_can_never_become_an_external_redirect(self):
    response = self.client.get(
      "/app//evil.example/path", follow_redirects=False
    )

    self.assertEqual(302, response.status_code)
    location = response.headers["Location"]
    self.assertEqual("/evil.example/path", location)
    self.assertFalse(location.startswith("//"))
    self.assertNotIn("http://", location)
    self.assertNotIn("https://", location)


class PathTraversalTest(unittest.TestCase):
  def setUp(self):
    self.dist = DistDirectory()
    self.addCleanup(self.dist.cleanup)
    self.outside = self.dist.path.parent / "outside-secret.txt"
    self.outside.write_text("SECRET", encoding="utf-8")
    self.addCleanup(lambda: self.outside.unlink(missing_ok=True))
    self.client = build_app(self.dist).test_client()

  def test_traversal_never_reads_a_neighbouring_file(self):
    for path in (
      "/../outside-secret.txt",
      "/%2e%2e/outside-secret.txt",
      "/assets/../../outside-secret.txt",
      "/legacy/../outside-secret.txt",
    ):
      with self.subTest(path=path):
        response = self.client.get(path)

        self.assertNotIn("SECRET", response.get_data(as_text=True))


class MissingBuildTest(unittest.TestCase):
  def setUp(self):
    self.dist = DistDirectory(with_index=False, with_assets=False)
    self.addCleanup(self.dist.cleanup)
    self.client = build_app(self.dist).test_client()

  def test_root_and_deep_links_report_the_missing_build(self):
    for path in ("/", "/tasks"):
      with self.subTest(path=path):
        response = self.client.get(path)

        self.assertEqual(503, response.status_code)
        body = response.get_json()
        self.assertEqual("error", body["status"])
        self.assertEqual(503, body["code"])
        self.assertIn("npm run build", body["message"])

  def test_a_missing_asset_remains_not_found(self):
    response = self.client.get("/assets/app.js")

    self.assertEqual(404, response.status_code)


class DefaultLocationTest(unittest.TestCase):
  def test_default_location_is_the_vite_build_output(self):
    self.assertEqual(("frontend", "app", "dist"), SPA_DIST_DIR.parts[-3:])

  def test_registration_does_not_require_a_build(self):
    app = build_app(None)

    self.assertIn("spa", app.blueprints)


class CoexistenceTest(unittest.TestCase):
  """The configured application keeps every HTTP namespace in its own lane."""

  def setUp(self):
    self.dist = DistDirectory()
    self.addCleanup(self.dist.cleanup)

  def build_full_app(self, dist=None):
    import server
    from backend.src.unit_test.config_fixture import unified_config
    from unittest.mock import patch

    selected = self.dist if dist is None else dist
    with patch("backend.src.web.spa_routes.SPA_DIST_DIR", selected.path):
      app = server.create_app(
        config=unified_config(),
        schema_guard_factory=lambda config: object(),
      )
    return app

  def test_root_is_vue_and_retired_legacy_documents_are_tombstones(self):
    app = self.build_full_app()
    client = app.test_client()

    root = client.get("/")
    self.assertEqual(200, root.status_code)
    self.assertIn(SHELL_MARKER, root.get_data(as_text=True))
    self.assertNotIn("sidebar-menu-text", root.get_data(as_text=True))

    for path in ("/legacy", "/legacy/"):
      with self.subTest(path=path):
        legacy = client.get(path)
        self.assertEqual(404, legacy.status_code)
        body = legacy.get_data(as_text=True)
        self.assertNotIn(SHELL_MARKER, body)

  def test_api_and_vue_assets_coexist_while_legacy_static_is_retired(self):
    app = self.build_full_app()
    client = app.test_client()

    listing = client.get("/api/tasks")
    self.assertEqual(401, listing.status_code)
    self.assertEqual("error", listing.get_json()["status"])

    self.assertEqual(APP_JS, client.get("/assets/app.js").get_data(as_text=True))
    for path in ("/static/css/index.css", "/static/js/submit.js"):
      with self.subTest(path=path):
        response = client.get(path)
        self.assertEqual(404, response.status_code)
        self.assertNotIn(SHELL_MARKER, response.get_data(as_text=True))

  def test_unknown_reserved_paths_remain_real_404s(self):
    app = self.build_full_app()
    client = app.test_client()

    for path in (
      "/api/definitely-not-an-endpoint",
      "/static/definitely-not-found.css",
      "/legacy/definitely-not-a-page",
    ):
      with self.subTest(path=path):
        response = client.get(path)
        self.assertEqual(404, response.status_code)
        self.assertNotIn(SHELL_MARKER, response.get_data(as_text=True))

  def test_root_post_has_no_legacy_replacement(self):
    app = self.build_full_app()
    client = app.test_client()

    response = client.post("/", json={})

    self.assertEqual(405, response.status_code)

  def test_missing_vue_build_is_visible_and_legacy_remains_retired(self):
    missing = DistDirectory(with_index=False, with_assets=False)
    self.addCleanup(missing.cleanup)
    app = self.build_full_app(missing)
    client = app.test_client()

    self.assertEqual(503, client.get("/").status_code)
    self.assertEqual(503, client.get("/tasks").status_code)
    legacy = client.get("/legacy/")
    self.assertEqual(404, legacy.status_code)
    self.assertNotIn(SHELL_MARKER, legacy.get_data(as_text=True))

  def test_retired_flask_surfaces_are_absent_from_the_url_map(self):
    app = self.build_full_app()
    rules = list(app.url_map.iter_rules())

    self.assertNotIn("static", {rule.endpoint for rule in rules})
    self.assertNotIn("legacy_index", {rule.endpoint for rule in rules})
    self.assertFalse(any(str(rule) in ("/legacy", "/legacy/") for rule in rules))
    root_methods = set().union(
      *(rule.methods for rule in rules if str(rule) == "/")
    )
    self.assertNotIn("POST", root_methods)


if __name__ == "__main__":
  unittest.main()
