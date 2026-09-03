##<<Base>>
import os
import sys
sys.path.append(os.getcwd())
from copy import deepcopy
import re
from time import sleep
from random import randint
from requests import request,get
from urllib.parse import urlparse
from urllib.parse import parse_qs

##<Extension>>
import yaml as yml

##<<Third-part>>
from backend.src.base.downloader import Downloader
from backend.src.platform.douyin.douyin_header import DouyinPostInfoHeader
from backend.src.platform.douyin.douyin_post_config import DouyinPostConfig
from backend.src.platform.douyin.douyin_login import DouyinLogin
from backend.src.platform.douyin.douyin_api import DouyinApi
from backend.src.library.configlib import load_config
from backend.src.library.loglib import get_logger
from backend.src.library.safe_diagnostics import post_diagnostic

'''
主页批量作品下载器。

输入是用户主页分享链接，解析出 sec_user_id 后请求 USER_POST（登录）或
IESDOUYIN_USER_POST（未登录）取回作品列表。当前止步于取回列表：不翻页、
不下载文件、也没有调用方。

单个作品的下载不走本模块。
'''
MAX_TIMEOUT = 10
USER_HOME_PAGE_URL_PREFIX = r"v.douyin.com"
DOUYIN_POST_URL_PATTERN = r"user/([^/?]*)"
DOUYIN_POST_REDIRECT_URL_PATTERN = r"sec_uid=([^&]*)"
class DouyinPostDownloader(Downloader):
  '''
  作品下载器：
    input: user 主页分享链接
    output:user 主页作品
  '''

  ##
  ## SEC UID regular expression
  ##

  ##
  ## API
  ##
  # API_USER_POST = r"https://www.douyin.com/aweme/v1/web/aweme/post/"

  ##
  ## Parameters
  ##
  # sec_user_id = str()
  # max_cursor = int()
  # page_counts = int()
  # max_counts = int()

  ##
  ## class
  ##
  def __init__(self, config: dict = None) -> None:
    source = load_config() if config is None else config
    self.config = DouyinPostConfig(source)
    self._source_config = deepcopy(source)
    self.__build = {}
    super().__init__(self._source_config["download"])
    self.construct_aggregation_class(self._source_config)

  def construct_aggregation_class(self, config: dict):
    douyin = config["platform"]["douyin"]
    self.header = DouyinPostInfoHeader(douyin["headers"])
    self.header.init_header(self.config.login)
    self.login = DouyinLogin(douyin["login"])
    self.API = DouyinApi(douyin["api"])

  def set_share_url(self, url:str=None):
    sec_user_id = str()
    if url is None:
       get_logger().error("invalid url")
       raise TypeError
    
    # update share url
    self.config.share_url = url

    ##
    ## update sec_user_id
    ##
    if USER_HOME_PAGE_URL_PREFIX in url:
       self.__update_sec_user_id_by_url()
    else:
        sec_user_id = re.search(pattern=DOUYIN_POST_URL_PATTERN, string=url).group(1)
        if sec_user_id is not None:
          self.set_sec_user_id(sec_user_id)
        else:
          get_logger().error("sec_user_id note found!")
          raise ValueError

  def __update_sec_user_id_by_url(self):

    ##
    ## query share url and receive sec_user_id
    ##
    query = self.query_share_url(self.config.share_url)
    sec_user_id = query["sec_uid"][0]
    self.set_sec_user_id(sec_user_id)

    
  def query_share_url(self, url:str = ""):
    ##
    ## set header
    ##
    header = dict()
    self.header.set_referer(self.API.DOUYIN_DOMAIN)
    header["Referer"]    = self.header.__dict__["Referer"]
    header["User-Agent"] = self.header.__dict__["User-Agent"]


    ##
    ## send GET request
    ##
    response = request("get", self.config.share_url, timeout=self.config.MAX_TIMEOUT, headers=header)
    # self.x_bogus = XB(user_agent=header_dict["User-Agent"]).getXBogus(response.url)

    ##
    ## random delay
    ##
    sleep(randint(15, 45) * 0.1)
    response.raise_for_status()

    ##
    ## debug
    ##
    if self.config.debug is True:
      get_logger().info(
        post_diagnostic(
          "post_response_saved",
          url=response.url,
          status=response.status_code,
        )
      )

    ##
    ## construct return result
    ##
    url = urlparse(response.url)
    response_url             = dict()
    response_url["url"]      = response.url
    response_url["scheme"]   = url.scheme
    response_url["netloc"]   = url.netloc
    response_url["path"]     = url.path
    response_url["params"]   = url.params
    response_url["fragment"] = url.fragment

    ##
    ## url query
    ##
    url_query                  = str(parse_qs(url.query)).replace("\\", "")
    response_url["query"]      = yml.safe_load(url_query)

    ##
    ## cache DOUYIN_DOMAIN result
    ##
    self.__build["share_info"] = response_url.copy()

    ##
    ## save share url respone html
    ##
    if self.config.save_response is True:
      path = self.config.build_path + "/" + self.config.stream_platform + "/" + self.config.type
      file_name = self.config.sec_user_id + ".html"
      save_path = path + "/" + file_name
      response.encoding = "utf-8"
      os.makedirs(os.path.dirname(path), exist_ok=True)
      with open(save_path, 'w', encoding="utf-8") as f:
          yml.safe_dump(response.text, f)
          f.close()
          ##
          ## Never the url, the account or the path it was written to. That the
          ## capture happened is the diagnostic; what it contains is the file.
          ##
          get_logger().info(
            post_diagnostic("post_response_saved", url=response.url)
          )
    return response_url["query"]


  def set_sec_user_id(self, sec_user_id):
    self.config.sec_user_id = sec_user_id

  def query_user_post_without_login(self):
    if self.config.login is True:
      get_logger().error("Invalid login config, please confirm it again")
      raise TypeError
    
    ##
    ## set header referer
    ## e.g. https://www.iesdouyin.com/share/user/MS4wLjABAAAAqGTeSZHx2YaoWi6GWYNgnh79g6JpV9AWArdVOYCG0zM?from_aid=6383&u_code=ki64k3a1&did=MS4wLjABAAAAY3ALqVej4p_r5XxNyipRWcz6h-YYyowoyvqEu5qdzyF6z5WOH4ITCJRtUEn7NAFn&iid=MS4wLjABAAAANwkJuWIRFOzg5uCpDRpMj4OX-QryoDgn-yYlXQnRwQQ&with_sec_did=1&sec_uid=MS4wLjABAAAAqGTeSZHx2YaoWi6GWYNgnh79g6JpV9AWArdVOYCG0zM&from_ssr=1&from=web_code_link
    ##
    header = dict()
    referer = self.API.IESDOUYIN_HEADER_REFERER + self.config.sec_user_id
    params = self.__build["share_info"]["query"]
    referer_param_str = "&".join([f"{k}={v[0]}" for k, v in params.items()])    
    referer = referer + "?" + referer_param_str
    self.header.set_referer(referer)
    header["Accept"]                 = self.header.__dict__["Accept"]
    header["Accept-Encoding"]        = self.header.__dict__["Accept-Encoding"]
    header["Accept-Language"]        = self.header.__dict__["Accept-Language"]
    header["Agw-Js-Conv"]            = self.header.__dict__["Agw-Js-Conv"]
    header["Cookie"]                 = self.header.__dict__["Cookie"]
    header["Priority"]               = self.header.__dict__["Priority"]
    header["Referer"]                = self.header.__dict__["Referer"]
    header["Sec-Ch-Ua"]              = self.header.__dict__["Sec-Ch-Ua"]
    header["Sec-Ch-Ua-Mobile"]       = self.header.__dict__["Sec-Ch-Ua-Mobile"]
    header["Sec-Ch-Ua-Platform"]     = self.header.__dict__["Sec-Ch-Ua-Platform"]
    header["Sec-Fetch-Dest"]         = self.header.__dict__["Sec-Fetch-Dest"]
    header["Sec-Fetch-Mode"]         = self.header.__dict__["Sec-Fetch-Mode"]
    header["Sec-Fetch-Site"]         = self.header.__dict__["Sec-Fetch-Site"]
    header["User-Agent"]             = self.header.__dict__["User-Agent"]

    ##
    ## update user post verify config
    ##
    self.update_user_post_verify_params()

    try:
        ##
        ## constructe params for post
        ##      
        params                                = dict()
        params["reflow_source"]               = self.config.reflow_source
        params["web_id"]                      = self.config.web_id
        params["device_id"]                   = self.config.device_id
        params["aid"]                         = self.config.aid
        params["sec_uid"]                     = self.config.sec_uid
        params["count"]                       = self.config.count
        params["max_cursor"]                  = self.config.max_cursor
        params["reflow_id"]                   = self.config.reflow_id
        params["msToken"]                     = self.login.msToken
        self.config.update_a_bogus(params=params)
        params["a_bogus"]                     = self.config.a_bogus
        # params["X-Bogus"] = self.config.x_bogus
        self.__build["post_params"]           = params.copy()
    except Exception as e:
        get_logger().error(
          post_diagnostic("post_parameters_failed", error=e, state=False)
        )
        raise e

    try:
      ##
      ## send GET request for user post
      ##
      response = get(url=self.API.IESDOUYIN_USER_POST, timeout=self.config.MAX_TIMEOUT, params=params, headers=header)
      response.raise_for_status()

      ##
      ## random delay
      ##
      sleep(randint(15, 45) * 0.1)

      ##
      ## save user post respone html
      ##
      if self.config.save_response is True:
        path = self.config.build_path + "/" + self.config.stream_platform + "/" + self.config.type
        file_name = self.config.nickname + ".html"
        save_path = path + "/" + file_name
        response.encoding = "utf-8"
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(save_path, 'w', encoding="utf-8") as f:
            yml.safe_dump(response.text, f)
            f.close()
            get_logger().info(
              post_diagnostic("post_response_saved", url=response.url)
            )
      ##
      ## The status and the host, and nothing else. The url carries the
      ## signature this program computed and the body is the platform's entire
      ## answer; both used to be written here verbatim.
      ##
      get_logger().info(
        post_diagnostic(
          "post_request_failed" if response.status_code >= 400 else "post_complete",
          url=response.url,
          status=response.status_code,
        )
      )
    except Exception as e:
      get_logger().error(
        post_diagnostic("post_request_failed", error=e, state=False)
      )
      raise e

  def query_user_post(self):
    try:
      ##
      ## set header
      ##
      header = dict()

      ##
      ## set header referer for user post
      ## https://www.douyin.com/user/MS4wLjABAAAAqGTeSZHx2YaoWi6GWYNgnh79g6JpV9AWArdVOYCG0zM'
      ##
      referer = self.API.DOUYIN_DOMAIN + "/user/" + self.config.sec_user_id
      self.header.set_referer(referer)
      header["Accept"]                 = self.header.__dict__["Accept"]
      header["Accept-Encoding"]        = self.header.__dict__["Accept-Encoding"]
      header["Accept-Language"]        = self.header.__dict__["Accept-Language"]
      header["Cookie"]                 = self.header.__dict__["Cookie"]
      header["Priority"]               = self.header.__dict__["Priority"]
      header["Referer"]                = self.header.__dict__["Referer"]
      header["Sec-Ch-Ua"]              = self.header.__dict__["Sec-Ch-Ua"]
      header["Sec-Ch-Ua-Mobile"]       = self.header.__dict__["Sec-Ch-Ua-Mobile"]
      header["Sec-Ch-Ua-Platform"]     = self.header.__dict__["Sec-Ch-Ua-Platform"]
      header["Sec-Fetch-Dest"]         = self.header.__dict__["Sec-Fetch-Dest"]
      header["Sec-Fetch-Mode"]         = self.header.__dict__["Sec-Fetch-Mode"]
      header["Sec-Fetch-Site"]         = self.header.__dict__["Sec-Fetch-Site"]
      header["User-Agent"]             = self.header.__dict__["User-Agent"]

      ##
      ## update user post verify config
      ##
      self.update_user_post_verify_params()
    except Exception as e:
      get_logger().error(
        post_diagnostic("post_parameters_failed", error=e)
      )
      raise e

    try:
      ##
      ## constructe params for post
      ##      
      params                                = dict()
      params["device_platform"]             = self.config.device_platform
      params["aid"]                         = self.config.aid
      params["channel"]                     = self.config.channel
      params["sec_user_id"]                 = self.config.sec_user_id
      params["max_cursor"]                  = self.config.max_cursor
      params["locate_query"]                = self.config.locate_query
      params["show_live_replay_strategy"]   = self.config.show_live_replay_strategy
      params["need_time_list"]              = self.config.need_time_list
      params["time_list_query"]             = self.config.time_list_query
      params["whale_cut_token"]             = self.config.whale_cut_token
      params["cut_version"]                 = self.config.cut_version
      params["count"]                       = self.config.count
      params["publish_video_strategy_type"] = self.config.publish_video_strategy_type
      params["update_version_code"]         = self.config.update_version_code
      params["pc_client_type"]              = self.config.pc_client_type
      params["version_code"]                = self.config.version_code
      params["version_name"]                = self.config.version_name
      params["cookie_enabled"]              = self.config.cookie_enabled
      params["screen_width"]                = self.config.screen_width
      params["screen_height"]               = self.config.screen_height
      params["browser_language"]            = self.config.browser_language
      params["browser_platform"]            = self.config.browser_platform
      params["browser_name"]                = self.config.browser_name
      params["browser_version"]             = self.config.browser_version
      params["browser_online"]              = self.config.browser_online
      params["engine_name"]                 = self.config.engine_name
      params["engine_version"]              = self.config.engine_version
      params["os_name"]                     = self.config.os_name
      params["os_version"]                  = self.config.os_version
      params["cpu_core_num"]                = self.config.cpu_core_num
      params["device_memory"]               = self.config.device_memory
      params["platform"]                    = self.config.platform
      params["downlink"]                    = self.config.downlink
      params["effective_type"]              = self.config.effective_type
      params["round_trip_time"]             = self.config.round_trip_time
      params["webid"]                       = self.config.webid
      params["verifyFp"]                    = self.config.verifyFp
      params["fp"]                          = self.config.fp
      params["msToken"]                     = self.login.msToken
      # self.config.update_a_bogus(params=params)
      params["a_bogus"]                     = self.config.a_bogus
      # params["X-Bogus"] = self.config.x_bogus
      self.__build["post_params"]           = params.copy()
    except Exception as e:
       get_logger().error(
         post_diagnostic("post_parameters_failed", error=e)
       )
       raise e

    try:
      ##
      ## send GET request for user post
      ##
      response = get(url=self.API.USER_POST, timeout=self.config.MAX_TIMEOUT, params=params, headers=header)
      response.raise_for_status()

      ##
      ## random delay
      ##
      sleep(randint(15, 45) * 0.1)

      ##
      ## save user post respone html
      ##
      if self.config.save_response is True:
        path = self.config.build_path + "/" + self.config.stream_platform + "/" + self.config.type
        file_name = self.config.nickname + ".html"
        save_path = path + "/" + file_name
        response.encoding = "utf-8"
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(save_path, 'w', encoding="utf-8") as f:
            yml.safe_dump(response.text, f)
            f.close()
            get_logger().info(
              post_diagnostic("post_response_saved", url=response.url)
            )

      get_logger().info(
        post_diagnostic(
          "post_request_failed" if response.status_code >= 400 else "post_complete",
          url=response.url,
          status=response.status_code,
        )
      )
    except Exception as e:
      get_logger().error(
        post_diagnostic("post_request_failed", error=e, state=False)
      )
      raise e
    

  def update_user_post_verify_params(self):
    ##
    ## update count
    ##
    if self.config.login is True:
      self.config.update_count(self.config.MAX_COUNT_WITH_LOGIN)
    else:
      self.config.update_count(self.config.MAX_COUNT_WITHOUT_LOGIN)

    ##
    ## update verifyFp
    ##
    self.config.update_verifyFp()

    ##
    ## update fp
    ##
    self.config.update_fp()

    ##
    ## update msToken
    ##
    self.login.update_douyin_msToken()

  ##
  ## Deliberately dumps nothing.
  ##
  ## It used to print the downloader, header, login and API configuration and
  ## then every entry of the build dictionary. Between them those carry the
  ## request cookie, ``msToken``, ``verifyFp``, ``a_bogus`` and the signed
  ## parameter set - which is to say the whole of what makes a request to the
  ## platform work as this account.
  ##
  ## There is no safe rendering of that, so there is no rendering of it. What a
  ## diagnostic can honestly say is that a dump was asked for and how many
  ## sections were built, and that is what it says.
  ##
  def dump_config(self):
    get_logger().info(
      post_diagnostic("post_config_dumped", total=len(self.__build))
    )

  def run(self, token: dict) -> None:
    if not isinstance(token, dict) or not isinstance(token.get("url"), str):
      raise ValueError("Post token must contain a URL")
    self.config.update_post_share_url({"share_url": token["url"]})
    if self.config.test_mode:
      return None
    self.set_share_url(token["url"])
    if self.config.login:
      self.query_user_post()
    else:
      self.query_user_post_without_login()

def download_test():
  post_downloader = DouyinPostDownloader()
  
  ##
  ## 1. Analysis all shared url from configuration.
  ##
  post_download_url_list = []

  ##
  ## 2. Enmulate client to login server.
  ##

  ##
  ## 3. Loop all shared url X.
  ##
  for share_url in post_download_url_list:
    
    ##
    ## 4. Create threading for the user who is related shared url X.
    ##

    ##
    ## 5. Send shared url X to server and get all
    ##
    
    ##
    ## Test
    ## 1. load default configuration
    ## 2. override configuration by user command
    ##

    ##
    ## Get sec uid
    ##
    # share_url = 'https://www.douyin.com/user/MS4wLjABAAAA_IqUVAcx23x8fJZk0iJhmmyu8YytCUSkcZA33xW9198'
    # if USER_HOME_PAGE_URL_PREFIX in share_url:
    #   # query_result = post_downloader.query_share_url(url=share_url)
    #   #  post_downloader.sec_user_id = query_result["query"]["sec_uid"]
    #   # post_downloader.config.sec_user_id = query_result["query"]["sec_uid"]
    # else:
    #    sec_user_id = re.search(pattern=DOUYIN_POST_URL_PATTERN, string=share_url).group(1)
    #    post_downloader.set_sec_user_id(sec_user_id)
    post_downloader.set_share_url(share_url)
    get_logger().info(
      post_diagnostic("post_skipped", owner_user_id=post_downloader.config.sec_user_id)
    )

    ##
    ## Query user home page
    ##
    try:
      ##
      ## query user post
      ##
      if post_downloader.config.login is True:
        post_downloader.query_user_post()
      else:
        post_downloader.query_user_post_without_login()    
    except Exception as e:
       post_downloader.dump_config()
       get_logger().error(
         post_diagnostic("post_request_failed", error=e)
       )
       raise e
    '''
    params = dict(post_downloader.max_cursor, post_downloader.page_counts, post_downloader.sec_user_id)
    XBM.model_2_endpoint(post_downloader.header.user_agent, post_downloader.API_USER_POST,)
    endpoint_url = None
    request("get", )
    '''
    # get_logger().info(post_downloader.douyin_post_config.to_dict())
    # post_downloader.dump_config()
    '''
    if post_downloader.config.save_response is True:
      path = post_downloader.config.build_path + "/" + post_downloader.config.stream_platform + "/" + post_downloader.config.type + "/" + post_downloader.config.nickname + ".yml"
      post_downloader.config.save_config(data=post_downloader.__build, output=Path(path))
      if post_downloader.config.debug is True:
        get_logger().info("Save file {} success!".format(path))
    '''
    break

'''
Steps:
1. Analysis all shared url from configuration.
2. Enmulate client to login server.
3. Loop all shared url X.
4. Create threading for the user who is related shared url X.
5. Send shared url X to server and get all
'''
if __name__ == "__main__":
   ##
   ## for test, download post vedio
   ##
   download_test()
  # DouyinPostDownloader().dump_config()
'''
  post_downloader = PostDownloader()
  
  ##
  ## 1. Analysis all shared url from configuration.
  ##
  post_download_url_list = []

  ##
  ## 2. Enmulate client to login server.
  ##

  ##
  ## 3. Loop all shared url X.
  ##
  for share_url in post_download_url_list:
    
    ##
    ## 4. Create threading for the user who is related shared url X.
    ##

    ##
    ## 5. Send shared url X to server and get all
    ##
    
    ##
    ## Test
    ## 1. load default configuration
    ## 2. override configuration by user command
    ##
    query_result = post_downloader.query_share_url(url=share_url)
    get_logger().info(query_result)
    break
'''
