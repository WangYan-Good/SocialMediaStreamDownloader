##<<Base>>
from random import randint
from time import sleep

##<<Extension>>
from requests import request

##<<Third-part>>
from backend.src.platform.douyin.douyin_api import DouyinApi
from backend.src.platform.douyin.douyin_aweme_config import DouyinAwemeConfig
from backend.src.platform.douyin.douyin_header import DouyinPostInfoHeader
from backend.src.platform.douyin.douyin_login import DouyinLogin
from backend.src.platform.douyin.douyin_session import (
  credential_days_left,
  read_payload,
)


class DouyinOwnerApi:
  """Request plumbing shared by the owner detail and owner post-list calls.

  Both need the same four things - a logged-in header, browser-fingerprint
  parameters, a fresh signature, and the configured proxies - so they live here
  once and the two callers stay thin parsers.
  """

  def __init__(self, config=None, sleeper=None) -> None:
    self.config = (
      config if isinstance(config, DouyinAwemeConfig)
      else DouyinAwemeConfig(config)
    )
    self.API = DouyinApi(
      self.config.get_config_dict_attr("$.platform.douyin.api")
    )
    self.login = DouyinLogin(
      self.config.get_config_dict_attr("$.platform.douyin.login")
    )
    self._sleeper = sleeper if sleeper is not None else self._random_pause

  @staticmethod
  def _random_pause():
    sleep(randint(15, 45) * 0.1)

  def pause(self):
    self._sleeper()

  def proxies(self):
    """Proxies from ``$.platform.douyin.login.proxies``, passed explicitly.

    Without this ``requests`` falls back to HTTP_PROXY/HTTPS_PROXY, which would
    quietly ignore the configured value the rest of the program honours.
    """
    return self.login.proxies.get_proxies_dict()

  def cookie(self):
    """The login cookie these endpoints require."""
    return self.config.get_config_dict_attr(
      "$.platform.douyin.headers.post_info.cookie"
    )

  def credential_days_left(self):
    """Days until the login cookie expires; ``None`` if unreadable."""
    return credential_days_left(self.cookie())

  def headers(self) -> dict:
    """Headers for an owner request - always the logged-in variant.

    Deliberately independent of ``$.download.user_login``.  Both owner endpoints
    return an empty body without a session cookie, so the no-login header cannot
    work here.  Flipping user_login globally would instead change the single-post
    path, which works fine anonymously.
    """
    header = DouyinPostInfoHeader(
      self.config.get_config_dict_attr("$.platform.douyin.headers")
    )
    header.init_header(True)
    return {
      key: value
      for key, value in header.to_dict().items()
      if isinstance(value, str)
    }

  def signed_params(self, extra: dict = None) -> dict:
    """Browser-fingerprint parameters plus a fresh signature."""
    params = self.config.post_params()
    if extra:
      params.update(extra)
    self.config.update_verifyFp()
    verify_fp = self.config.get_config_dict_attr(
      "$.platform.douyin.post.verifyFp"
    )
    if verify_fp is not None:
      params["verifyFp"] = verify_fp
      params["fp"] = verify_fp
    ms_token = self.config.get_config_dict_attr(
      "$.platform.douyin.login.msToken"
    )
    if ms_token is not None:
      params["msToken"] = ms_token
    a_bogus = self.config.update_a_bogus(params)
    if a_bogus is not None:
      params["a_bogus"] = a_bogus
    return params

  def get(self, api_attr: str, extra_params: dict = None) -> dict:
    """Issue one owner request and return its payload.

    Raises ``SessionExpired`` or ``UpstreamRejected`` rather than returning an
    empty answer - see douyin_session for why that distinction matters here.
    """
    url = self.API.get_config_dict_attr(api_attr)
    response = request(
      method="GET",
      url=url,
      params=self.signed_params(extra_params),
      timeout=self.config.owner_max_timeout,
      headers=self.headers(),
      proxies=self.proxies(),
    )
    self.pause()
    return read_payload(response, endpoint=api_attr.rsplit(".", 1)[-1])
