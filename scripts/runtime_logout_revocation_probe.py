#!/usr/bin/env python3
"""Disposable Secure Compose proof for logout revocation integrity.

The probe deliberately keeps credentials out of argv and output.  Its state
file exists only inside the disposable application container and is removed
after the recovery proof succeeds.
"""

import argparse
from http.cookiejar import Cookie, CookieJar
import json
import os
from pathlib import Path
import secrets
import sys
import time
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import HTTPCookieProcessor, ProxyHandler, Request, build_opener


BASE_URL = "http://127.0.0.1:5013"
STATE_PATH = Path("/tmp/smsd-logout-revocation-state.json")
SESSION_COOKIE_NAME = "smsd_session"
CSRF_COOKIE_NAME = "smsd_csrf"
CSRF_HEADER_NAME = "X-CSRF-Token"
MARKER = "ok   runtime logout revocation integrity"


def _fail(message):
  raise SystemExit("FAIL: {}".format(message))


def _request(opener, path, *, method="GET", body=None, csrf=None):
  data = None
  headers = {"Accept": "application/json"}
  if body is not None:
    data = json.dumps(body).encode("utf-8")
    headers["Content-Type"] = "application/json"
  if csrf is not None:
    headers[CSRF_HEADER_NAME] = csrf
  request = Request(
    "{}{}".format(BASE_URL, path),
    data=data,
    headers=headers,
    method=method,
  )
  try:
    response = opener.open(request, timeout=10)
  except HTTPError as error:
    response = error
  except (OSError, URLError):
    _fail("application HTTP request failed")

  try:
    payload = json.loads(response.read().decode("utf-8"))
  except (UnicodeDecodeError, json.JSONDecodeError):
    _fail("application returned a non-JSON response")
  return response.status, response.headers, payload


def _cookie_values(jar):
  return {cookie.name: cookie.value for cookie in jar}


def _cookie(name, value):
  host = urlparse(BASE_URL).hostname
  return Cookie(
    version=0,
    name=name,
    value=value,
    port=None,
    port_specified=False,
    domain=host,
    domain_specified=False,
    domain_initial_dot=False,
    path="/",
    path_specified=True,
    secure=False,
    expires=None,
    discard=True,
    comment=None,
    comment_url=None,
    rest={"SameSite": "Strict"},
    rfc2109=False,
  )


def _opener_with(cookies=None):
  jar = CookieJar()
  for name, value in (cookies or {}).items():
    jar.set_cookie(_cookie(name, value))
  return jar, build_opener(ProxyHandler({}), HTTPCookieProcessor(jar))


def _auth_pair(jar):
  values = _cookie_values(jar)
  pair = {
    SESSION_COOKIE_NAME: values.get(SESSION_COOKIE_NAME),
    CSRF_COOKIE_NAME: values.get(CSRF_COOKIE_NAME),
  }
  if not all(isinstance(value, str) and value for value in pair.values()):
    _fail("application did not issue the complete auth cookie pair")
  return pair


def _auth_set_cookie_names(headers):
  names = set()
  for header in headers.get_all("Set-Cookie", []):
    name = header.partition("=")[0].strip()
    if name in (SESSION_COOKIE_NAME, CSRF_COOKIE_NAME):
      names.add(name)
  return names


def _write_state(pair):
  payload = json.dumps(pair, sort_keys=True).encode("utf-8")
  descriptor = os.open(
    STATE_PATH,
    os.O_WRONLY | os.O_CREAT | os.O_TRUNC,
    0o600,
  )
  try:
    os.fchmod(descriptor, 0o600)
    with os.fdopen(descriptor, "wb", closefd=False) as stream:
      stream.write(payload)
      stream.flush()
      os.fsync(stream.fileno())
  finally:
    os.close(descriptor)
  if STATE_PATH.stat().st_mode & 0o077:
    _fail("runtime auth state permissions are not private")


def _read_state():
  try:
    if STATE_PATH.stat().st_mode & 0o077:
      _fail("runtime auth state permissions are not private")
    payload = json.loads(STATE_PATH.read_text(encoding="utf-8"))
  except (OSError, UnicodeDecodeError, json.JSONDecodeError):
    _fail("runtime auth state is missing or invalid")
  if not isinstance(payload, dict):
    _fail("runtime auth state is missing or invalid")
  pair = {
    SESSION_COOKIE_NAME: payload.get(SESSION_COOKIE_NAME),
    CSRF_COOKIE_NAME: payload.get(CSRF_COOKIE_NAME),
  }
  if not all(isinstance(value, str) and value for value in pair.values()):
    _fail("runtime auth state is missing or invalid")
  return pair


def prepare():
  sys.path.insert(0, "/app")
  from backend.src.auth.cli import build_cli_service_factory

  username = "phase15c-{}".format(secrets.token_hex(6))
  password = secrets.token_urlsafe(32)
  try:
    service = build_cli_service_factory()()
    service.create_user(username, password)
  except Exception:
    _fail("could not create the disposable auth account")

  jar, opener = _opener_with()
  status, _, _ = _request(
    opener,
    "/api/auth/login",
    method="POST",
    body={"username": username, "password": password},
  )
  if status != 200:
    _fail("disposable account login did not succeed")
  pair = _auth_pair(jar)
  status, _, _ = _request(opener, "/api/auth/me")
  if status != 200:
    _fail("session was not authenticated before the outage")
  _write_state(pair)


def prove_outage():
  original = _read_state()
  jar, opener = _opener_with(original)
  status, headers, payload = _request(
    opener,
    "/api/auth/logout",
    method="POST",
    csrf=original[CSRF_COOKIE_NAME],
  )
  if status != 503 or payload.get("kind") != "logout_unavailable":
    _fail("database outage logout did not fail closed")
  if _auth_set_cookie_names(headers):
    _fail("database outage logout mutated an auth cookie")
  if _auth_pair(jar) != original:
    _fail("database outage logout changed the browser cookie jar")


def _wait_until_authenticated(opener):
  for _ in range(60):
    status, _, _ = _request(opener, "/api/auth/me")
    if status == 200:
      return
    time.sleep(1)
  _fail("old session did not recover after the database restarted")


def prove_recovery():
  original = _read_state()
  jar, opener = _opener_with(original)
  _wait_until_authenticated(opener)
  status, _, _ = _request(
    opener,
    "/api/auth/logout",
    method="POST",
    csrf=original[CSRF_COOKIE_NAME],
  )
  if status != 200:
    _fail("logout retry did not succeed after database recovery")
  remaining = _cookie_values(jar)
  if SESSION_COOKIE_NAME in remaining or CSRF_COOKIE_NAME in remaining:
    _fail("successful logout did not clear the browser cookie pair")

  _, stale_opener = _opener_with(original)
  status, _, _ = _request(stale_opener, "/api/auth/me")
  if status != 401:
    _fail("successful logout did not revoke the server-side session")
  try:
    STATE_PATH.unlink()
  except OSError:
    _fail("runtime auth state could not be removed")
  print(MARKER)


def main(argv=None):
  parser = argparse.ArgumentParser()
  parser.add_argument("mode", choices=("prepare", "outage", "recovery"))
  mode = parser.parse_args(argv).mode
  if mode == "prepare":
    prepare()
  elif mode == "outage":
    prove_outage()
  else:
    prove_recovery()
  return 0


if __name__ == "__main__":
  raise SystemExit(main())
