##>> Test
import os
import sys
sys.path.append(os.getcwd())
##<< Test

## <<Base>>
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Optional
from urllib.parse import urlparse, parse_qs

## <<Extension>>
import yaml as yml
from requests import exceptions

## <<Third-Part>>
from backend.src.library.baselib                            import set_dict_attr, get_dict_attr
from backend.src.library.safe_diagnostics                  import live_diagnostic
from backend.src.platform.douyin.douyin_header              import DouyinShareHeader, DouyinLiveInfoHeader
from backend.src.platform.douyin.douyin_live_external_info  import observed_at
from backend.src.library.loglib                             import get_logger


##
## room.status carried by the live payload: 2 = broadcasting, 4 = finished.
##
ROOM_STATUS_LIVING = 2

##
## Platform status codes seen often enough to deserve their own wording.
## Anything else falls back to the raw code so nothing is silently swallowed.
##
_REJECTION_REASONS = {
  10033: "平台暂时拒绝查询（10033），稍后重试",
}


def _describe_rejection(live_response, platform_status) -> dict:
  """Extract the platform's own explanation for a non-zero status code."""
  message = None
  prompts = None
  try:
    payload = live_response.json()
    message = get_dict_attr(payload, "$.data.message")
    prompts = get_dict_attr(payload, "$.data.prompts")
  except Exception:
    ##
    ## An unreadable body must not mask the status code we already have.
    ##
    pass

  reason = _REJECTION_REASONS.get(platform_status)
  if reason is None:
    reason = "平台拒绝了本次查询（{}）".format(platform_status)
  return {
    "status_code": platform_status,
    "message": message,
    "prompts": prompts,
    "reason": reason,
  }


@dataclass(frozen=True)
class LiveProbeResult:
  """Outcome of asking the platform whether one share url is broadcasting.

  A probe answers a question; it never downloads.  When ``ok`` is False the
  failure was already logged and ``error`` carries a short reason suitable for
  showing in the UI.
  """

  url: str
  ok: bool = False
  room_status: Optional[int] = None
  owner_user_id: Optional[str] = None
  room_id: Optional[str] = None
  nickname: Optional[str] = None
  directory_name: Optional[str] = None
  title: Optional[str] = None
  checked_at: Optional[datetime] = None
  error: Optional[str] = None
  ##
  ## Raw material the download path needs so it does not have to re-request.
  ## ``response`` is the live-info HTTP response itself: stream extraction reads
  ## it directly, so carrying it here is what keeps a download to two requests.
  ##
  payload: dict = field(default_factory=dict)
  share_info: dict = field(default_factory=dict)
  live_payload: dict = field(default_factory=dict)
  headers: dict = field(default_factory=dict)
  response: Any = None

  @property
  def is_living(self) -> bool:
    return self.room_status == ROOM_STATUS_LIVING


class DouyinLiveProber:
  """Resolves a share url and reads its live room status.

  This owns the request *sequence* only.  The two network primitives it needs -
  ``query_url`` and ``pause`` - stay on the collaborating downloader so that the
  whole platform conversation is issued from a single module.

  The collaborator must expose ``config``, ``API``, ``live_external_info``,
  ``query_url(method, url, params, timeout, headers)``, ``pause()`` and
  ``construct_live_params_no_login(share_info, header)``.
  """

##
## >>============================= private method =============================>>
##
  def __init__(self, context) -> None:
    if context is None:
      raise ValueError("probe context is required")
    self._context = context

  @property
  def _config(self):
    return self._context.config

  def _debug_enabled(self) -> bool:
    return self._config.get_config_dict_attr("$.server.debug_mode") is True

  def _live_timeout(self):
    return self._config.get_config_dict_attr("$.platform.douyin.live.max_timeout")

  def _resolve_share_url(self, url: str, header: dict):
    """Follow the share url and return ``(response, share_header)``."""
    share_header = DouyinShareHeader(
      self._config.get_config_dict_attr("$.platform.douyin.headers")
    )
    share_header.init_share_live_header(
      self._config.get_config_dict_attr("$.download.user_login")
    )
    for key, value in share_header.to_dict().items():
      set_dict_attr(header, "$." + key, value)

    response = self._context.query_url(
      method="get",
      url=url,
      params=None,
      timeout=self._live_timeout(),
      headers=header,
    )
    ##
    ## WA: random delay between 1.5s - 4.5s
    ##
    self._context.pause()
    response.raise_for_status()
    return response, share_header

  @staticmethod
  def _parse_share_response(response) -> dict:
    parse_result = urlparse(response.url)
    share_info = dict()
    set_dict_attr(share_info, "$.url", response.url)
    set_dict_attr(share_info, "$.scheme", parse_result.scheme)
    set_dict_attr(share_info, "$.netloc", parse_result.netloc)
    set_dict_attr(share_info, "$.path", parse_result.path)
    set_dict_attr(share_info, "$.params", parse_result.params)
    set_dict_attr(share_info, "$.fragment", parse_result.fragment)

    url_query = str(parse_qs(parse_result.query)).replace("\\", "")
    set_dict_attr(share_info, "$.query", yml.safe_load(url_query))
    return share_info

  def _request_live_info(self, params: dict, header: dict):
    live_header = DouyinLiveInfoHeader(
      self._config.get_config_dict_attr("$.platform.douyin.headers")
    )
    live_header.init_header(
      self._config.get_config_dict_attr("$.download.user_login")
    )
    header = live_header.update_header(
      self._config.get_config_dict_attr("$.download.user_login"),
      header,
    )

    api = self._context.API.get_config_dict_attr("$.LIVE_INFO_ROOM_ID")
    if self._debug_enabled():
      get_logger().info(live_diagnostic("live_info_request", url=api))

    live_response = self._context.query_url(
      method="GET",
      url=api,
      params=params,
      timeout=self._live_timeout(),
      headers=header,
    )
    if live_response.status_code != 200:
      raise exceptions.HTTPError
    if self._debug_enabled():
      get_logger().info(
        live_diagnostic(
          "live_info_response",
          url=api,
          status=live_response.status_code,
        )
      )
    return live_response, header

##
## >>============================= sub class method =============================>>
##
  def probe(self, url: str) -> LiveProbeResult:
    """Ask the platform whether ``url`` is broadcasting right now.

    Returns a result rather than raising for the expected failure modes
    (timeouts, non-200 responses, forbidden payloads); those are ordinary
    outcomes when probing a batch of owners and must not abort the batch.
    Unexpected errors still propagate, matching the download path's behaviour.
    """
    if url is None:
      raise ValueError("url is required")

    header = dict()

    ##
    ##<<========================== query share url ==========================>>
    ##
    try:
      if self._debug_enabled():
        get_logger().info(live_diagnostic("share_url_request", url=url))
      response, share_header = self._resolve_share_url(url, header)
    except TimeoutError as e:
      get_logger().error(live_diagnostic("share_url_failed", url=url, error=e))
      return LiveProbeResult(url=url, error="请求超时")
    except exceptions.ReadTimeout as e:
      get_logger().error(live_diagnostic("share_url_failed", url=url, error=e))
      return LiveProbeResult(url=url, error="请求超时")
    except UnboundLocalError as e:
      get_logger().error(live_diagnostic("share_url_failed", url=url, error=e))
      return LiveProbeResult(url=url, error="分享链接解析失败")
    except Exception as e:
      status_code = getattr(locals().get("response"), "status_code", "unavailable")
      get_logger().error(
        live_diagnostic(
          "share_url_failed",
          url=url,
          status=status_code,
          error=e,
        )
      )
      return LiveProbeResult(url=url, error="分享链接请求失败")

    ##
    ##<<========================== build live payload =======================>>
    ##
    try:
      share_info = self._parse_share_response(response)
      if self._config.get_config_dict_attr("$.download.user_login") is True:
        params = dict()
      else:
        header.clear()
        params = self._context.construct_live_params_no_login(
          share_info,
          share_header,
        )
    except Exception as e:
      get_logger().error(
        live_diagnostic("share_url_parse_failed", url=url, error=e)
      )
      return LiveProbeResult(url=url, error="分享链接解析失败")

    ##
    ##<<========================== query live info ==========================>>
    ##
    try:
      live_response, header = self._request_live_info(params, header)
    except exceptions.HTTPError as e:
      status_code = getattr(locals().get("live_response"), "status_code", "unavailable")
      get_logger().error(
        live_diagnostic(
          "live_info_failed", url=url, status=status_code, error=e
        )
      )
      return LiveProbeResult(
        url=url,
        error="直播信息请求失败",
        share_info=share_info,
        live_payload=params,
      )
    except TimeoutError as e:
      get_logger().error(live_diagnostic("live_info_failed", url=url, error=e))
      return LiveProbeResult(
        url=url, error="请求超时", share_info=share_info, live_payload=params
      )
    except exceptions.ReadTimeout as e:
      get_logger().error(live_diagnostic("live_info_failed", url=url, error=e))
      return LiveProbeResult(
        url=url, error="请求超时", share_info=share_info, live_payload=params
      )
    except Exception as e:
      get_logger().error(live_diagnostic("live_info_failed", url=url, error=e))
      raise e

    ##
    ## WA: delay random
    ##
    self._context.pause()

    if self._debug_enabled():
      get_logger().info(
        live_diagnostic(
          "live_info_response", url=url, status=live_response.status_code
        )
      )

    ##
    ##<<========================== read live status =========================>>
    ##
    external_info = self._context.live_external_info
    rejection = None
    try:
      live_response.raise_for_status()

      platform_status = external_info.get_status(live_response)
      if platform_status != 0:
        ##
        ## The platform explains itself in the body; carrying that into the log
        ## and the UI is the difference between a diagnosable failure and a bare
        ## "forbidden".  Not gated behind debug_mode: without it an operator has
        ## nothing to act on.
        ##
        rejection = _describe_rejection(live_response, platform_status)
        raise exceptions.HTTPError

      payload = live_response.json()
      nickname = external_info.get_raw_nickname(live_response)
      directory_name = external_info.get_nickname(live_response)
      room_status = external_info.get_room_status(live_response)

      if room_status != ROOM_STATUS_LIVING:
        get_logger().info("当前 {0} 直播已结束".format(nickname))
      else:
        get_logger().info("当前 {0} 正在直播...".format(nickname))
    except exceptions.HTTPError:
      if rejection is None:
        get_logger().error(live_diagnostic("live_query_rejected", url=url))
        reason = "平台拒绝了本次查询"
      else:
        get_logger().error(
          live_diagnostic(
            "live_query_rejected",
            url=url,
            status=rejection["status_code"],
          )
        )
        reason = rejection["reason"]
      return LiveProbeResult(
        url=url,
        error=reason,
        share_info=share_info,
        live_payload=params,
      )
    except Exception as e:
      get_logger().error(
        live_diagnostic("live_response_parse_failed", url=url, error=e)
      )
      raise e

    ##
    ## The payload types both ids as numbers while every table and every response
    ## the UI consumes uses strings, so normalise once here.
    ##
    owner_user_id = get_dict_attr(payload, "$.data.room.owner_user_id")
    room_id = get_dict_attr(payload, "$.data.room.id")
    return LiveProbeResult(
      url=url,
      ok=True,
      room_status=room_status,
      owner_user_id=None if owner_user_id is None else str(owner_user_id),
      room_id=None if room_id is None else str(room_id),
      nickname=nickname,
      directory_name=directory_name,
      title=get_dict_attr(payload, "$.data.room.title"),
      checked_at=observed_at(payload),
      payload=payload,
      share_info=share_info,
      live_payload=params,
      headers=header,
      response=live_response,
    )
