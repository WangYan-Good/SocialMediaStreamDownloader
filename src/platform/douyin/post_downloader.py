##<<Base>>
import os
import sys

##
## import current path as work space
##
WORK_SPACE = os.path.dirname(sys.path[0])
sys.path.append(os.path.join(WORK_SPACE))
# print(WORK_SPACE)
# sys.path.append(os.path.join(WORK_SPACE))
# sys.path.append(os.path.join(sys.path[0]))

import re
from pathlib import Path
from time import sleep
from random import randint
from requests import request
from urllib.parse import urlparse
from urllib.parse import parse_qs

##<Extension>>
import yaml as yml

##<<Third-part>>
from header import Header
from xbogus import XBogus as XB
from xbogus import XBogusManager as XBM
from basic_config import BASE_CONFIG_PATH
from douyin_downloader import DouyinDownloader
from url_list_config import UrlListConfig
from post_config import DouyinPostConfig

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
class PostDownloader(DouyinDownloader):

  ##
  ## SEC UID regular expression
  ##
  USER_HOME_PAGE_URL_PREFIX = r"v.douyin.com"
  DOUYIN_POST_URL_PATTERN = r"user/([^/?]*)"
  DOUYIN_POST_REDIRECT_URL_PATTERN = r"sec_uid=([^&]*)"

  ##
  ## API
  ##
  API_USER_POST = r"https://www.douyin.com/aweme/v1/web/aweme/post/"

  ##
  ## Parameters
  ##
  sec_user_id = str()
  max_cursor = int()
  page_counts = int()
  max_counts = int()
  __douyin_post_config_dict = dict()

  ##
  ## class
  ##
  douyin_post_config = DouyinPostConfig()

  def __init__(self, path: Path = BASE_CONFIG_PATH) -> None:
    super().__init__(path)
    # self.max_cursor = self.__douyin_post_config_dict["max_cursor"]
    # self.page_counts = self.__douyin_post_config_dict["page_counts"]
    # self.max_counts = self.__douyin_post_config_dict["max_counts"]

  def query_share_url(self, url:str = "", timeout=MAX_TIMEOUT, header:Header = None):
    response_url = dict()
    header_dict = dict()
    ##
    ## Preparetion
    ##
    self.live_link_share = url
    self.timeout = timeout
    if header is None:
        header_dict["Referer"] = self.header.referer
        header_dict["User-Agent"] = self.header.user_agent
    else:
        header_dict["Referer"] = header.referer
        header_dict["User-Agent"] = header.user_agent
    response = request("get", self.live_link_share, timeout=self.timeout, headers=header_dict)
    self.x_bogus = XB(user_agent=header_dict["User-Agent"]).getXBogus(response.url)

    # random delay
    sleep(randint(15, 45) * 0.1)

    if response.status_code in {200}:
       pass
    else:
       print("ERROR: Query sec_uid failed")

    url = urlparse(response.url)
    response_url["scheme"] = url.scheme
    response_url["netloc"] = url.netloc
    response_url["path"] = url.path
    response_url["params"] = url.params
    response_url["fragment"] = url.fragment

    # url query
    url_query = str(parse_qs(url.query)).replace("\\", "")
    response_url["query"] = yml.safe_load(url_query)
    return response_url

  def to_dict(self):
    self.__douyin_post_config_dict = self.douyin_post_config.to_dict().copy()
    # self.__douyin_post_config_dict["max_cursor"] = self.max_cursor
    # self.__douyin_post_config_dict["max_counts"] = self.max_counts
    # self.__douyin_post_config_dict["page_counts"] = self.page_counts
    self.__douyin_post_config_dict["sec_user_id"] = self.sec_user_id
    # self.__douyin_post_config_dict["nickname"] = self.nickname
     

  def dump_config(self, out_putlog_file: Path = False):
    super().dump_config(out_putlog_file)
    self.douyin_post_config.dump_config()

    print("Douyin POST Downloader Configuration:")
    # print("\tmax cursor: {}".format(self.max_cursor))
    # print("\tmax counts: {}".format(self.max_counts))
    # print("\tpage counts: {}".format(self.page_counts))
    print("\tsec user id: {}".format(self.sec_user_id))


def download_test():
  post_downloader = PostDownloader()
  
  ##
  ## 1. Analysis all shared url from configuration.
  ##
  post_download_url_list = UrlListConfig().getConfigList(SectionName="post")

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
    if post_downloader.USER_HOME_PAGE_URL_PREFIX in share_url:
       query_result = post_downloader.query_share_url(url=share_url)
       post_downloader.sec_user_id = query_result["query"]["sec_uid"]
    else:
       post_downloader.sec_user_id = re.search(pattern=post_downloader.DOUYIN_POST_URL_PATTERN, string=share_url).group(1)
    print('sec_uid: {}'.format(post_downloader.sec_user_id))

    ##
    ## Query user home page
    ##
    '''
    params = dict(post_downloader.max_cursor, post_downloader.page_counts, post_downloader.sec_user_id)
    XBM.model_2_endpoint(post_downloader.header.user_agent, post_downloader.API_USER_POST,)
    endpoint_url = None
    request("get", )
    '''
    # print(post_downloader.douyin_post_config.to_dict())
    print(post_downloader.dump_config())



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
'''
  post_downloader = PostDownloader()
  
  ##
  ## 1. Analysis all shared url from configuration.
  ##
  post_download_url_list = UrlListConfig().getConfigList(SectionName="post")

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