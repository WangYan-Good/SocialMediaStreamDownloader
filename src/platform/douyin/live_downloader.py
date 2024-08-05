##>> test
##<< test
import os
import sys
import yaml
from pathlib import Path
import threading
import urllib.request
from urllib.error import ContentTooShortError 

# extension
import pynput
import keyboard

# third part
from src.base.downloader import Downloader
from platform.douyin.douyin_live_response_dict import Live

#TODO
import f2
from f2.apps.douyin.utils import TokenManager
from f2.apps.douyin.filter import (
    UserPostFilter,
    UserProfileFilter,
    UserCollectionFilter,
    UserCollectsFilter,
    UserMusicCollectionFilter,
    UserMixFilter,
    PostDetailFilter,
    UserLiveFilter,
    UserLive2Filter,
    GetQrcodeFilter,
    CheckQrcodeFilter,
    UserFollowingFilter,
    UserFollowerFilter,
)

# time defination in Timer
TIME_SECOND = 1
TIME_MINUTE = TIME_SECOND * 60
TIME_HOUR   = TIME_MINUTE * 60
TIME_DAY    = TIME_HOUR * 24

TIME_5_MINUTES = 5 * TIME_MINUTE


##
## Live stream file name
##
LIVE_STREAM_FILE_NAME_RE = r"stream-(\d+)_(\w+)\.(?:flv|m3u8)"

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
        save response: True -> user configuration
        url response path: /mnt/nvme/CodeSpace/OpenSource/TikTokDownload/config/build
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
        type: live
        download url: ['https://v.douyin.com/i2DeLnxH/', 'https://v.douyin.com/i21Ne6oS/', 'https://v.douyin.com/i2BHt2mE/', 'https://v.douyin.com/i2AA6GUK/', 'https://v.douyin.com/i2UJMdyQ/', 'https://v.douyin.com/i2yKQLWr/', 'https://v.douyin.com/i2yK7AmW/', 'https://v.douyin.com/i2yK4dwa/', 'https://v.douyin.com/i2yERBCA/', 'https://v.douyin.com/i2aFRVtP/', 'https://v.douyin.com/i2m2PHfU/', 'https://v.douyin.com/iYh1xLq7/', 'https://v.douyin.com/iFQTDaxn/', 'https://v.douyin.com/iFQTVDCH/', 'https://v.douyin.com/iFLBNPNw/', 'https://v.douyin.com/iFefCGHk/', 'https://v.douyin.com/iYe5jEhY/', 'https://v.douyin.com/iFeavMJ4/', 'https://v.douyin.com/iYy5CJLU/', 'https://v.douyin.com/iF32SFoa/', 'https://v.douyin.com/iFRy7hQT/', 'https://v.douyin.com/iFRf18G4/', 'https://v.douyin.com/iFemNNTW/', 'https://v.douyin.com/iY9jqpJ2/', 'https://v.douyin.com/iYHfd3fs/', 'https://v.douyin.com/iY9SWRRJ/', 'https://v.douyin.com/iY9DMX62/', 'https://v.douyin.com/i2uf4BYu/', 'https://v.douyin.com/i2ufkd96/', 'https://v.douyin.com/i2mmYRQp/', 'https://v.douyin.com/i2yvkKW3/', 'https://v.douyin.com/i2ywdvXS/', 'https://v.douyin.com/i2yKxrHU/', 'https://v.douyin.com/i2yK5HeW/', 'https://v.douyin.com/i2yEF2ah/', 'https://v.douyin.com/i2yKEYwh/', 'https://v.douyin.com/i2yKErho/', 'https://v.douyin.com/i2yENeMM/', 'https://v.douyin.com/i2PGPK3m/', 'https://v.douyin.com/i2PGv3Rb/', 'https://v.douyin.com/i2PtNWGu/', 'https://v.douyin.com/i2aGBqKR/', 'https://v.douyin.com/i2aGFoPs/', 'https://v.douyin.com/i2mLKthp/', 'https://v.douyin.com/i2VNCedS/', 'https://v.douyin.com/i2VM3W6o/', 'https://v.douyin.com/i2Vha8Lq/', 'https://v.douyin.com/i2bPGJqu/', 'https://v.douyin.com/i2b5YU7q/', 'https://v.douyin.com/i2b5A9mQ/', 'https://v.douyin.com/i2b5trX9/', 'https://v.douyin.com/i2bH67r8/', 'https://v.douyin.com/i2bHNCaF/', 'https://v.douyin.com/i2bXNumx/', 'https://v.douyin.com/i2gJR1Ta/', 'https://v.douyin.com/i2gXbA3c/', 'https://v.douyin.com/i2g4okCF/', 'https://v.douyin.com/i2goH5wo/', 'https://v.douyin.com/i2pF15f4/', 'https://v.douyin.com/i2pFFwfv/', 'https://v.douyin.com/i2pY9CHP/', 'https://v.douyin.com/i2pYxBQb/', 'https://v.douyin.com/i2pAqHSy/', 'https://v.douyin.com/i2pCNQfq/', 'https://v.douyin.com/i2sNPeF5/', 'https://v.douyin.com/i2sNWL52/', 'https://v.douyin.com/i2sN37gP/', 'https://v.douyin.com/i2sNE3tQ/', 'https://v.douyin.com/i2s2PLxH/', 'https://v.douyin.com/i2shQmjd/', 'https://v.douyin.com/i2s9qP4A/', 'https://v.douyin.com/i2s9xCym/', 'https://v.douyin.com/i2s9V47C/', 'https://v.douyin.com/i2sx2mRV/', 'https://v.douyin.com/i2sWhqSc/', 'https://v.douyin.com/i2sWSQd7/', 'https://v.douyin.com/i2sWvBrp/', 'https://v.douyin.com/i2svcvh9/', 'https://v.douyin.com/i2GB8NUy/', 'https://v.douyin.com/i2GBMudS/', 'https://v.douyin.com/i2GSqjUj/', 'https://v.douyin.com/i2GuxJoc/', 'https://v.douyin.com/i2GuAVpg/', 'https://v.douyin.com/i2GHEvqj/', 'https://v.douyin.com/i2go6kGT/']

'''

# extension from Downloader
class DouyinLiveDownloader(Downloader):

  ##
  ## Initialize user configuration
  ##
  max_download_thread       = 0
  is_need_login             = True
  folderize                 = True
  download_save_path        = ""
  is_need_save_response     = True
  live_listener             = True
  timeout                   = 0

  ##
  ## Downloader configuration
  ##
  live_download_thread_list           = list()
  actived_download_live_url_list      = list()
  live_share_url_download_status_list = list()
  listen_threading                    = None
  # nickname = ""

  ##
  ## LiveDownloader default configuration
  ## TODO
  ##
  max_download_number    = 0
  current_download_count = 0

  def __init__(self) -> None:
    super().__init__()

  def construct_aggregation_class(self) -> None:
     return super().construct_aggregation_class() 


  def douyin_live_constructor(self, share_url:str) -> None:
      try:          
          ##
          ## Query response of share url link to server
          ##
          self.share_url_response = self.live.query_share_url(url=share_url, header=self.header)
          self.live.construct_live_data(self.share_url_response)

          ##
          ## Construct paramter to request live data
          ##
          self.parameters_of_request_live["X-Bogus"]        = self.live.x_bogus
          self.parameters_of_request_live["verifyFp"]       = VFM.gen_verify_fp()
          self.parameters_of_request_live["type_id"]        = "0"
          self.parameters_of_request_live["live_id"]        = "1"
          self.parameters_of_request_live["room_id"]        = self.live.room_id
          self.parameters_of_request_live["sec_user_id"]    = self.share_url_response["query"].get("sec_user_id", "")
          self.parameters_of_request_live["version_code"]   = "99.99.99"
          self.parameters_of_request_live["app_id"]         = "1128"
          self.parameters_of_request_live["msToken"]        = TokenManager.gen_real_msToken()
          self.parameters_of_request_live["live_api"]       = "https://live.douyin.com/webcast/room/web/enter/"
          self.parameters_of_request_live["live_api_share"] = "https://webcast.amemv.com/webcast/room/reflow/info/"

          '''
          ##
          ## Save share url response
          ##
          if self.save_response is True:
            URL_RESPONSE_PATH = self.url_response_path + "/" + self.live.room_id[0] + ".yml"
            with open(URL_RESPONSE_PATH, 'w', encoding="utf-8") as f:
               yml.safe_dump(self.parameters_of_request_live, f)
               f.close()
               print("save file {} success!".format(URL_RESPONSE_PATH))
          '''
      except (
              exceptions.ProxyError,
              exceptions.SSLError,
              exceptions.ChunkedEncodingError,
              exceptions.ConnectionError,
              exceptions.ReadTimeout):
          print("分享链接 {url} 请求数据失败".format(url=share_url))
      return None


  ##
  ## Get douyin download live stream
  ##
  def get_douyin_live_download_stream(self, url:str = None)->str:
    if url is None:
      print("Invalide url")
      return None
    
    ##
    ##
    ##
    self.douyin_live_constructor(url)
    
    ##
    ## try receive live stream
    ##
    try:
      ##
      ## request for live stream
      ##
      live_response = request (
          method="get", 
          url=self.parameters_of_request_live["live_api_share"],
          params=self.parameters_of_request_live,
          timeout=self.live.timeout,
          headers=self.live.header)
      # 随机延时
      sleep(randint(15, 45) * 0.1)

      ##
      ## transform response to json format
      ##
      live_response_json = live_response.json()
      live_info = UserLive2Filter(live_response_json)
      if live_info.nickname is not None:
        self.nickname = live_info.nickname
      else:
        self.nickname = "Unknown"
      
      ##
      ## save live information
      ##
      if self.save_response is True:
         LIVE_INFORMATION_PATH = self.url_response_path + "/" + live_info.nickname + ".yml"
        #  print(LIVE_INFORMATION_PATH)
         with open(LIVE_INFORMATION_PATH, 'w') as f:
            yml.safe_dump(live_response_json, f)
            f.close()

      ##
      ## live status
      ##
      if live_info.live_status != 2:
         print("当前 {0} 直播已结束".format(live_info.nickname))
         return None
    except Exception as e:
       print(e)
    
    ##
    ## catch live status success
    ## return live stream
    ##
    try:
      print("当前 {0} 正在直播...".format(live_info.nickname))
      
      ##
      ## FULL_HD1
      ##
      if self.flv_clarity == 1 and live_response_json["data"]["room"]["stream_url"]["flv_pull_url"]["FULL_HD1"] is not None:
        self.live_stream_url = live_response_json["data"]["room"]["stream_url"]["flv_pull_url"]["FULL_HD1"]
      elif self.hls_clarity == 1 and live_response_json["data"]["room"]["stream_url"]["hls_pull_url_map"]["FULL_HD1"] is not None:
        self.live_stream_url = live_response_json["data"]["room"]["stream_url"]["hls_pull_url_map"]["FULL_HD1"]
      ##
      ## HD1
      ##
      elif self.flv_clarity == 2 and live_response_json["data"]["room"]["stream_url"]["flv_pull_url"]["HD1"] is not None:
        self.live_stream_url = live_response_json["data"]["room"]["stream_url"]["flv_pull_url"]["HD1"]
      elif self.hls_clarity == 2 and live_response_json["data"]["room"]["stream_url"]["hls_pull_url_map"]["HD1"] is not None:
        self.live_stream_url = live_response_json["data"]["room"]["stream_url"]["hls_pull_url_map"]["HD1"]
      ##
      ## SD1
      ##
      elif self.flv_clarity == 3 and live_response_json["data"]["room"]["stream_url"]["flv_pull_url"]["SD1"] is not None:
        self.live_stream_url = live_response_json["data"]["room"]["stream_url"]["flv_pull_url"]["SD1"]
      elif self.hls_clarity == 3 and live_response_json["data"]["room"]["stream_url"]["hls_pull_url_map"]["SD1"] is not None:
        self.live_stream_url = live_response_json["data"]["room"]["stream_url"]["hls_pull_url_map"]["SD1"]
      ##
      ## SD2
      ##
      elif self.flv_clarity == 4 and live_response_json["data"]["room"]["stream_url"]["flv_pull_url"]["SD2"] is not None:
        self.live_stream_url = live_response_json["data"]["room"]["stream_url"]["flv_pull_url"]["SD2"]
      elif self.hls_clarity == 4 and live_response_json["data"]["room"]["stream_url"]["hls_pull_url_map"]["SD2"] is not None:
        self.live_stream_url = live_response_json["data"]["room"]["stream_url"]["hls_pull_url_map"]["SD2"]

      self.live_stream_name = re.search(LIVE_STREAM_FILE_NAME_RE, self.live_stream_url).group()
    except Exception as e:
       print(e)
       return None
    return self.live_stream_url



  def download_live_stream(self, url:str):
    ##
    ## Define local variable
    ##
    live_download_thread_dict = dict()
    task = ("get", 
            url, 
            self.live_stream_url, 
            self.save_path+"/"+self.nickname, 
            self.live_stream_name, 
            self.nickname, 
            True, 
            self.login_config.proxies.get_proxies(), 
            self.live.header, 
            self.live.timeout)

    ##
    ## add a new download task
    ##
    if self.actived_download_live_url_list.count(url) == 0:
       self.actived_download_live_url_list.append(url)
       live_download_thread_dict["thread"] = threading.Thread(target=self.__request_file__, args=task)
       live_download_thread_dict["share_url"] = url
       self.live_download_thread_list.append(live_download_thread_dict)
       self.live_share_url_download_status_list.append(True)
    else:
       ##
       ## update threading args
       ##
       for index in range(len(self.live_download_thread_list)):
          if self.live_download_thread_list[index]["share_url"] == url:
             
            ##
            ## check live download status
            ##
            if self.live_share_url_download_status_list[index] == True:
               print("live {} download status is true, skiped".format(self.nickname))
               return None
            else:
               self.live_download_thread_list[index]["thread"] = threading.Thread(target=self.__request_file__, args=task)
               self.live_share_url_download_status_list[index] = True
            break
          if index == len(self.live_download_thread_list) - 1:
             print("actived live {} is not found!\nurl: {}".format(self.nickname, self.live_stream_url))
             raise IndexError
    
    ##
    ## start threading
    ##
    self.current_download_count += 1
    for d in self.live_download_thread_list:
      if (d["share_url"] == url):
        d["thread"].start()
        return
    print("live {} does not dound {}".format(self.nickname, url))
    raise IndexError   

  def __request_file__(
    self,
    method: str,
    share_url: str,
    url: str,
    save_path: str,
    file_name: str,
    nickname: str,
    stream: bool,
    proxies,
    headers: dict = None,
    timeout = 10,
    ):
    try:
      print("\nstart download:")
      print("path:{}\n method:{}\n url:{}\n stram:{}\n proxies:{}\n headers:{}\n timeout:{}\n".format(save_path + "/" + file_name, method, url, stream, proxies, headers, timeout))
      print("当前总下载数：{}".format(self.current_download_count))

      if not os.path.exists(save_path):
          print("create directory {}".format(save_path))
          os.makedirs(save_path, exist_ok=True)
      self.auto_down (url, save_path, file_name, 0)
      
      # reset threading status
      self.current_download_count -= 1
      for index in range(len(self.live_download_thread_list)):
         if self.live_download_thread_list[index]["share_url"] == share_url:
            self.live_share_url_download_status_list[index] = False
            break
         if index == len(self.live_download_thread_list) - 1:
            print("live {} status does not found".format(share_url))
            raise IndexError
      print("name:{} \nurl:{} \ndownload complete!\n".format(nickname, url))    
      print("当前总下载数：{}".format(self.current_download_count))
    except Exception as e:
        print("request error: {err}".format(err=e))
        print("\n path:{}\n url:{}\ndownload failed!!!".format(save_path + "/" + file_name, method, url, stream, proxies, headers, timeout))
        return None

  def auto_down (self, url: str, fp: str, fn: str, retry_times: int):
    try:
        file_name = fp + "/" + fn
        while os.path.exists(file_name):
           file_name = fp + "/" + "re_" + str(retry_times) + "_" + fn
           retry_times += 1
        urllib.request.urlretrieve (url, file_name)
    except ContentTooShortError:
        self.auto_down (url, fp, fn, retry_times)

  def create_keyboard_response_thread(self):
     while True:
        print("s: start scan live list")
        print("q: exit live listener")
        opreation = input("operation:")
        if opreation == 's':
           threading.Thread(target=self.start_download_all_live_url).start()
        elif opreation == 'q':
           print("Listener exit succeed!")
           break
        elif opreation == 'exit':
           exit(1)
        else:
           print("Please input a correct operation")

  def start_download_all_live_url(self):
     print("start download all live url!")
     for share_url in self.download_url_list:
       stream_url = self.get_douyin_live_download_stream(share_url)
       if stream_url is None:
         continue
       self.download_live_stream(share_url)  

if __name__ == "__main__":
  live = DouyinLiveDownloader()

  for live_url in live.download_url_list:
    stream_url = live.get_douyin_live_download_stream(live_url)
    if stream_url is None:
      continue
    live.download_live_stream(live_url)

  '''
  listener = threading.Thread(target=live.create_keyboard_response_thread)
  listener.start()
  '''
