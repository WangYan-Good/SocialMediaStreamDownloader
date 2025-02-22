##<<Base>>
import os
import sys
sys.path.append(os.getcwd())
import re
from pathlib import Path
from time import sleep
from random import randint
from requests import request,get
from urllib.parse import urlparse
from urllib.parse import parse_qs

##<Extension>>
import yaml as yml

##<<Third-part>>
from xbogus import XBogus as XB
from xbogus import XBogusManager as XBM
from backend.src.base.downloader import Downloader
from backend.src.platform.douyin.douyin_header import DouyinHeader
from backend.src.platform.douyin.douyin_url_list_config import UrlListConfig
from backend.src.platform.douyin.douyin_post_config import DouyinPostConfig, DEFAULT_BASE_CONFIG_PATH
from backend.src.platform.douyin.douyin_login import DouyinLogin
from backend.src.platform.douyin.douyin_api import DouyinApi

'''
Basic configuration:
        work space path: /mnt/nvme/CodeSpace/OpenSource/TikTokDownload
        max thread: 0 -> user configuration
        login: True -> user configuration
        folderize: True  -> user configuration
        save path: /mnt/nvme/Vedio  -> user configuration
        base config path: /mnt/nvme/CodeSpace/OpenSource/TikTokDownload/config
        platform: douyin
        platform config path: /mnt/nvme/CodeSpace/OpenSource/TikTokDownload/config/douyin
        [-]save response: True -> user configuration
        [-]url response path: /mnt/nvme/CodeSpace/OpenSource/TikTokDownload/config/build
Header configuration:
        Referer: https://www.douyin.com/
        User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/104.0.0.0 Safari/537.36
Login configuration: -> user configuration
        cookie: FOLLOW_LIVE_POINT_INFO=%22MS4wLjABAAAA4Md_rLi7sUqmSZV9C5-_ez2pu20RhErzFN6szJy8-TM%2F1712548800000%2F0%2F1712486487626%2F0%22; FORCE_LOGIN=%7B%22videoConsumedRemainSeconds%22%3A180%7D; IsDouyinActive=true; LOGIN_STATUS=1; __security_server_data_status=1; _bd_ticket_crypt_cookie=8ca6a6fe3a9ce197c4ce8b4e754d72d3; _bd_ticket_crypt_doamin=2; bd_ticket_guard_client_data=eyJiZC10aWNrZXQtZ3VhcmQtdmVyc2lvbiI6MiwiYmQtdGlja2V0LWd1YXJkLWl0ZXJhdGlvbi12ZXJzaW9uIjoxLCJiZC10aWNrZXQtZ3VhcmQtcmVlLXB1YmxpYy1rZXkiOiJCQVVaYWp0OUZ3WE9RQytwcTlrY1RzaWhML3ZwVm1zNHExVlk3Q09nbUF2SDVlcURwU2FuTjB4VkRkVW5oZGdFbG1DclRqTHo5eXI4a2g3MGcxTERnbUE9IiwiYmQtdGlja2V0LWd1YXJkLXdlYi12ZXJzaW9uIjoxfQ%3D%3D; bd_ticket_guard_client_web_domain=2; download_guide=%220%2F%2F1%22; home_can_add_dy_2_desktop=%220%22; msToken=Nls7KJQiQJIXS11OMDJaeJ95kICughH2z3uUbqMbiQWKUjJlrJUf_QkMW7iwUiL1rUIuBO4jkLtLuDeY2exHi6818dmrVgLgXlHNwka7FXzXTYXDfU-Q; n_mh=ngQEn_iIBeY9pc84MWFmagRvS2A0XGdoFnmNVxQs35U; odin_tt=c15873a466ce9c014a598513e2bd1144adbdb8e52d3b61423d0d0443f3a1391a61746802e83bf44cae75e2ea6638c7c4f5b06b55ad27b0b9fabb4f0e7d234ef9; passport_assist_user=CjxucF5Q-2BCuWWMVhFixDRYbsSwDmyXwKsB4MDEOIe7GOm5mU_2iXnXx6lWBlU7kE6DGBC8VfUiFCep314aSgo835PopTQy5vu4mzUT6pe2dsSKI_U18lHfBMfG9SK_IuPOVYgFYwOIZfiSvsaoVnRhG3FhoY9wBcmfvCoDEIaCzg0Yia_WVCABIgEDI5R9UA%3D%3D; passport_auth_status=22ff69c04b77908489d73bc81c3e370c%2C; passport_auth_status_ss=22ff69c04b77908489d73bc81c3e370c%2C; passport_csrf_token=058d5b854ed17f403cbf0628bdf0c2ea; passport_csrf_token_default=058d5b854ed17f403cbf0628bdf0c2ea; publish_badge_show_info=%221%2C0%2C0%2C1712486487480%22; sessionid=75ab737d0860af5157013018a93a5ce9; sessionid_ss=75ab737d0860af5157013018a93a5ce9; sid_guard=75ab737d0860af5157013018a93a5ce9%7C1712486488%7C5183994%7CThu%2C+06-Jun-2024+10%3A41%3A22+GMT; sid_tt=75ab737d0860af5157013018a93a5ce9; sid_ucp_sso_v1=1.0.0-KDJjMzcwMTQ1YmY1NTAxODk5ZjRhYjQ1MmY3NGRhNGY2ZjJlYzlkYWEKHQjyvs7ghwIQz_DJsAYY7zEgDDD76rnOBTgGQPQHGgJsZiIgMTkwZmVhYjQzYzJmYzE5NmM3MDg3ZWE0MjY1ZTdjYTg; sid_ucp_v1=1.0.0-KDBmNzliYTY5MDc0ZmQ4MjViY2I0OWExNWFmNWJjNDBiN2JkNzg2MzQKGQjyvs7ghwIQ2PDJsAYY7zEgDDgGQPQHSAQaAmxmIiA3NWFiNzM3ZDA4NjBhZjUxNTcwMTMwMThhOTNhNWNlOQ; ssid_ucp_sso_v1=1.0.0-KDJjMzcwMTQ1YmY1NTAxODk5ZjRhYjQ1MmY3NGRhNGY2ZjJlYzlkYWEKHQjyvs7ghwIQz_DJsAYY7zEgDDD76rnOBTgGQPQHGgJsZiIgMTkwZmVhYjQzYzJmYzE5NmM3MDg3ZWE0MjY1ZTdjYTg; ssid_ucp_v1=1.0.0-KDBmNzliYTY5MDc0ZmQ4MjViY2I0OWExNWFmNWJjNDBiN2JkNzg2MzQKGQjyvs7ghwIQ2PDJsAYY7zEgDDgGQPQHSAQaAmxmIiA3NWFiNzM3ZDA4NjBhZjUxNTcwMTMwMThhOTNhNWNlOQ; sso_uid_tt=8e78eb455c711e65284607ee9d24f0e5; sso_uid_tt_ss=8e78eb455c711e65284607ee9d24f0e5; store-region=cn-sh; store-region-src=uid; strategyABtestKey=%221712486413.565%22; stream_player_status_params=%22%7B%5C%22is_auto_play%5C%22%3A0%2C%5C%22is_full_screen%5C%22%3A0%2C%5C%22is_full_webscreen%5C%22%3A0%2C%5C%22is_mute%5C%22%3A1%2C%5C%22is_speed%5C%22%3A1%2C%5C%22is_visible%5C%22%3A1%7D%22; stream_recommend_feed_params=%22%7B%5C%22cookie_enabled%5C%22%3Atrue%2C%5C%22screen_width%5C%22%3A1920%2C%5C%22screen_height%5C%22%3A1080%2C%5C%22browser_online%5C%22%3Atrue%2C%5C%22cpu_core_num%5C%22%3A16%2C%5C%22device_memory%5C%22%3A0%2C%5C%22downlink%5C%22%3A%5C%22%5C%22%2C%5C%22effective_type%5C%22%3A%5C%22%5C%22%2C%5C%22round_trip_time%5C%22%3A0%7D%22; toutiao_sso_user=190feab43c2fc196c7087ea4265e7ca8; toutiao_sso_user_ss=190feab43c2fc196c7087ea4265e7ca8; ttwid=1%7CuRB4ZT3e917sb1oFniTy_Qye8Y79-RhPulrpqwRJXZY%7C1712486408%7C707272f74f3a817ba6d72408eaaaeb63448dd5f7f302b68a4939f96910f7ebd0; uid_tt=29d18b02108cad7ba3c6ebcc3e1c45fe; uid_tt_ss=29d18b02108cad7ba3c6ebcc3e1c45fe; volume_info=%7B%22isUserMute%22%3Afalse%2C%22isMute%22%3Atrue%2C%22volume%22%3A0.5%7D; passport_fe_beating_status=true; =douyin.com; __ac_nonce=066127808008661a1851e; __ac_signature=_02B4Z6wo00f01eUJSOgAAIDBsaIh6X3NznHlOExAAB9S32; architecture=amd64; csrf_session_id=9750084836f0ee25f5dad83576c81dce; device_web_cpu_core=16; device_web_memory_size=-1; dy_sheight=1080; dy_swidth=1920; tt_scid=UmcfqyNrP07Fyrn9f8Rr9Z.yQkzBh2CBm00J-nO9ewyzoYknAk5-EktqRSUqslsS174a; ttcid=d6d75c350e8547c6bdfb6becf54760d228; xgplayer_user_id=779116200301
        msToken: 5rNKkDfGkpKIZNkMb9D66UzslGTynlV8PkyJKfl3mXBTn--Z4GAxWQHSH0LfiVaXPUv0Ch6MDYsvULdNrvdAv3ewn4KLsIwEACvDWMwAE2fS4S3TAAJLNX4mzZFV-Q==
Proxies configuration: -> user configuration
        http: None
        https: None
Downloader configuration:
        type: post
        download url: ['https://v.douyin.com/i2DeLnxH/', 'https://v.douyin.com/i21Ne6oS/', 'https://v.douyin.com/i2BHt2mE/', 'https://v.douyin.com/i2AA6GUK/', 'https://v.douyin.com/i2UJMdyQ/', 'https://v.douyin.com/i2yKQLWr/', 'https://v.douyin.com/i2yK7AmW/', 'https://v.douyin.com/i2yK4dwa/', 'https://v.douyin.com/i2yERBCA/', 'https://v.douyin.com/i2aFRVtP/', 'https://v.douyin.com/i2m2PHfU/', 'https://v.douyin.com/iYh1xLq7/', 'https://v.douyin.com/iFQTDaxn/', 'https://v.douyin.com/iFQTVDCH/', 'https://v.douyin.com/iFLBNPNw/', 'https://v.douyin.com/iFefCGHk/', 'https://v.douyin.com/iYe5jEhY/', 'https://v.douyin.com/iFeavMJ4/', 'https://v.douyin.com/iYy5CJLU/', 'https://v.douyin.com/iF32SFoa/', 'https://v.douyin.com/iFRy7hQT/', 'https://v.douyin.com/iFRf18G4/', 'https://v.douyin.com/iFemNNTW/', 'https://v.douyin.com/iY9jqpJ2/', 'https://v.douyin.com/iYHfd3fs/', 'https://v.douyin.com/iY9SWRRJ/', 'https://v.douyin.com/iY9DMX62/', 'https://v.douyin.com/i2uf4BYu/', 'https://v.douyin.com/i2ufkd96/', 'https://v.douyin.com/i2mmYRQp/', 'https://v.douyin.com/i2yvkKW3/', 'https://v.douyin.com/i2ywdvXS/', 'https://v.douyin.com/i2yKxrHU/', 'https://v.douyin.com/i2yK5HeW/', 'https://v.douyin.com/i2yEF2ah/', 'https://v.douyin.com/i2yKEYwh/', 'https://v.douyin.com/i2yKErho/', 'https://v.douyin.com/i2yENeMM/', 'https://v.douyin.com/i2PGPK3m/', 'https://v.douyin.com/i2PGv3Rb/', 'https://v.douyin.com/i2PtNWGu/', 'https://v.douyin.com/i2aGBqKR/', 'https://v.douyin.com/i2aGFoPs/', 'https://v.douyin.com/i2mLKthp/', 'https://v.douyin.com/i2VNCedS/', 'https://v.douyin.com/i2VM3W6o/', 'https://v.douyin.com/i2Vha8Lq/', 'https://v.douyin.com/i2bPGJqu/', 'https://v.douyin.com/i2b5YU7q/', 'https://v.douyin.com/i2b5A9mQ/', 'https://v.douyin.com/i2b5trX9/', 'https://v.douyin.com/i2bH67r8/', 'https://v.douyin.com/i2bHNCaF/', 'https://v.douyin.com/i2bXNumx/', 'https://v.douyin.com/i2gJR1Ta/', 'https://v.douyin.com/i2gXbA3c/', 'https://v.douyin.com/i2g4okCF/', 'https://v.douyin.com/i2goH5wo/', 'https://v.douyin.com/i2pF15f4/', 'https://v.douyin.com/i2pFFwfv/', 'https://v.douyin.com/i2pY9CHP/', 'https://v.douyin.com/i2pYxBQb/', 'https://v.douyin.com/i2pAqHSy/', 'https://v.douyin.com/i2pCNQfq/', 'https://v.douyin.com/i2sNPeF5/', 'https://v.douyin.com/i2sNWL52/', 'https://v.douyin.com/i2sN37gP/', 'https://v.douyin.com/i2sNE3tQ/', 'https://v.douyin.com/i2s2PLxH/', 'https://v.douyin.com/i2shQmjd/', 'https://v.douyin.com/i2s9qP4A/', 'https://v.douyin.com/i2s9xCym/', 'https://v.douyin.com/i2s9V47C/', 'https://v.douyin.com/i2sx2mRV/', 'https://v.douyin.com/i2sWhqSc/', 'https://v.douyin.com/i2sWSQd7/', 'https://v.douyin.com/i2sWvBrp/', 'https://v.douyin.com/i2svcvh9/', 'https://v.douyin.com/i2GB8NUy/', 'https://v.douyin.com/i2GBMudS/', 'https://v.douyin.com/i2GSqjUj/', 'https://v.douyin.com/i2GuxJoc/', 'https://v.douyin.com/i2GuAVpg/', 'https://v.douyin.com/i2GHEvqj/', 'https://v.douyin.com/i2go6kGT/']

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
  ## Cache
  ##
  __build  = dict()

  ##
  ## class
  ##
  def __init__(self, path: Path = None) -> None:
    if path is None:
       print("WARNING: invalid config path, will use default config")
       path = DEFAULT_BASE_CONFIG_PATH
    
    ##
    ## Initialize attribute
    ##
    self.CONFIG_PATH = path
    super().__init__(path)

    ##
    ## construct aggregation class
    ##
    self.construct_aggregation_class()

  def construct_aggregation_class(self):
    
    try:
      ##
      ## construct member
      ##
      self.config = DouyinPostConfig(self.CONFIG_PATH)
      self.header = DouyinHeader(self.config.header_config_path)
      self.login  = DouyinLogin(self.config.login_config_path)
      self.API    = DouyinApi(self.config.api_config_path)

      ##
      ## update user config
      ## TODO
      ##

      ##
      ## apply user config
      ## TODO
      ##
    except Exception as e:
      print("ERROR: constrcute aggregation member failed!\n{}".format(e))
      raise e

  def set_share_url(self, url:str=None):
    sec_user_id = str()
    if url is None:
       print("ERROR: invalid url")
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
          print("ERROR: sec_user_id note found!")
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
      print("INFO: response url {}".format(response.url))
    
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
          print("save share url html response:")
          print("\turl: {}".format(url))
          print("\tsec_user_id: {}".format(response_url["query"]["sec_uid"]))
          print("INFO: Save file {} success!".format(save_path))
    return response_url["query"]


  def set_sec_user_id(self, sec_user_id):
    self.config.sec_user_id = sec_user_id

  def query_user_post_without_login(self):
    if self.config.login is True:
      print("ERROR: Invalid login config, please confirm it again")
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
        print("ERROR: construct parameter for download post without login failed!\n{}".format(e))
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
            print("save user post html response:")
            print("\turl: {}".format(self.config.share_url))
            print("\tsec_uid: {}".format(self.config.sec_uid))
            print("\tnickname: {}".format(self.config.nickname))
            print("INFO: Save file {} success!".format(save_path))
      ##
      ## TODO
      ##
      print(response.status_code)
      print(response.url)
      print(response.json())
    except Exception as e:
      print("ERROR: query user post without login failed!\n{}".format(e))
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
      print("ERROR: update download post parameters failed!\n{}".format(e))
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
       print("ERROR: construct parameter for download post failed!\n{}".format(e))
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
            print("save user post html response:")
            print("\turl: {}".format(self.config.share_url))
            print("\tsec_user_id: {}".format(self.config.sec_user_id))
            print("\tnickname: {}".format(self.config.nickname))
            print("INFO: Save file {} success!".format(save_path))

      ##
      ## TODO
      ##
      print(response.status_code)
      print(response.json())
    except Exception as e:
      print("ERROR: query user post failed!\n{}".format(e))
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

  def dump_config(self):
    ##
    ## dump member config
    ##
    self.config.dump_config()
    self.header.dump_header()
    self.login.dump_config()
    self.API.dump_config()

    ##
    ## dump post download config
    ##
    print("Douyin post downloader configuration:")
    for k,v in self.__build.items():
      print("\t{}: {}".format(k,v))

  def run(self, params: None = ...) -> None:
     return super().run(params)

def download_test():
  post_downloader = DouyinPostDownloader()
  
  ##
  ## 1. Analysis all shared url from configuration.
  ##
  post_download_url_list = UrlListConfig().get_config_list(SectionName="post")

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
    print('sec_uid: {}'.format(post_downloader.config.sec_user_id))

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
       print("ERROR: request post failed!\n{}".format(e))
       raise e
    '''
    params = dict(post_downloader.max_cursor, post_downloader.page_counts, post_downloader.sec_user_id)
    XBM.model_2_endpoint(post_downloader.header.user_agent, post_downloader.API_USER_POST,)
    endpoint_url = None
    request("get", )
    '''
    # print(post_downloader.douyin_post_config.to_dict())
    # post_downloader.dump_config()
    '''
    if post_downloader.config.save_response is True:
      path = post_downloader.config.build_path + "/" + post_downloader.config.stream_platform + "/" + post_downloader.config.type + "/" + post_downloader.config.nickname + ".yml"
      post_downloader.config.save_config(data=post_downloader.__build, output=Path(path))
      if post_downloader.config.debug is True:
        print("INFO: Save file {} success!".format(path))
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
  post_download_url_list = UrlListConfig().get_config_list(SectionName="post")

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
    print(query_result)
    break
'''