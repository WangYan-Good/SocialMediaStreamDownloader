##>> Test
import os
import sys
sys.path.append(os.getcwd())
from re import compile
import json
##<< Test

##<<Base>>
from random import randint
from time import sleep
from pathlib import Path
from requests import request, exceptions
from urllib.parse import urlparse, parse_qs
from urllib.error import ContentTooShortError
from urllib.request import urlretrieve
from threading import Thread

## <<Extension>>
import yaml as yml

## <<Third-Part>>
from src.base.header import Header
from src.base.downloader import Downloader, DEFAULT_BASE_CONFIG_PATH
from douyin_live_config import DouyinLiveConfig
from douyin_login import DouyinLogin
from url_list_config import UrlListConfig
from xbogus import XBogus as XB
from a_bogus import ABogus as AB
from live_external_info import LiveExternal

## TODO remove
from verify_fp_manager import VerifyFpManager as VFM
import f2
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
from f2.apps.douyin.utils import TokenManager

class DouyinLiveDownloader(Downloader):
  ##
  ## Attribute
  ##
  url_list = None
  REGULAR_ROOM_ID = r"/douyin/webcast/reflow/(\S+)"
  REGULAR_ROOM_ID_LIVE_PATH = r"/douyin/webcast/reflow/\S+"

  ##
  ## member
  ##
  live_external_info = None

  ##
  ## Cache
  ##
  __build  = dict()

  def __init__(self, path: Path = None) -> None:
    if path is None:
      print("WARNNING: Invalid input, will use default config")
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
    ##
    ## construct member
    ##
    self.config = DouyinLiveConfig(self.CONFIG_PATH)
    self.login  = DouyinLogin(self.config.login_config_path)
    self.header = Header(self.config.header_config_path)
    self.url_list = UrlListConfig(self.config.share_url_path)
    self.live_external_info = LiveExternal()

    ##
    ## update member
    ##
    if self.config.login is True:
      self.login.login()
    else:
      self.login.update_cookie()
      self.login.update_msToken()
      self.config.update_verifyFp()
  
  def dump_config(self):
    super().dump_config()
    self.url_list.dump_url_list()

  def __construct_query_share_url_params(self, share_url, response_result:dict)->dict:
    params = dict()
    try:
      ##
      ## Construct paramter to request live data
      ##
      # params["verifyFp"]       = self.config.verifyFp
      params["type_id"]        = self.config.type_id
      params["live_id"]        = self.config.live_id
      params["room_id"]        = self.config.room_id[0]
      params["sec_user_id"]    = response_result["query"].get("sec_user_id", "")[0]
      params["version_code"]   = self.config.version_code
      params["app_id"]         = self.config.app_id
      # params["msToken"]        = self.login.msToken#TokenManager.gen_real_msToken()
      # params["live_api"]       = self.config.live_api#"https://live.douyin.com/webcast/room/web/enter/"
      # params["live_api_share"] = self.config.live_api_share#"https://webcast.amemv.com/webcast/room/reflow/info/"
      # params["cookie"]         = self.login.cookie
      params["X-Bogus"]        = self.config.x_bogus
      # self.config.a_bogus = AB().get_value(params, "GET")
      # params["a_bogus"]   = self.config.a_bogus

      self.__build["query_external_info_params"]             = params
    except (
            exceptions.ProxyError,
            exceptions.SSLError,
            exceptions.ChunkedEncodingError,
            exceptions.ConnectionError,
            exceptions.ReadTimeout):
        print("ERROR: Query shared url failed!".format(url=share_url))
        return None
    return params

  def construct_live_data(self, query_response:dict=None)->None:
    if query_response is None:
        return None
    ##
    ## Construct live data
    ## Make sure root_id/web_rid
    ## 
    if (u:=compile(self.REGULAR_ROOM_ID_LIVE_PATH).findall(query_response["path"])) is not None:
      self.config.rid = True
      self.config.room_id = compile(self.REGULAR_ROOM_ID).findall(query_response["path"])
      self.config.web_rid = None
    else:
      self.config.rid = False
      self.config.room_id = None
      self.config.web_rid = compile(self.REGULAR_ROOM_ID).findall(query_response["path"])

    if self.config.debug is True:
      print("INFO: rid:{rid} room_id:{room_id} web_rid:{web_rid}".format(rid=self.config.rid, room_id=self.config.room_id, web_rid=self.config.web_rid))

  def query_url (self, method, url, params, timeout, headers):
    return request(method=method, url=url, params=params, timeout=timeout, headers=headers)

  def download_live_stream(self, url:str):
    ##
    ## Define local variable
    ##
    live_download_thread_dict = dict()
    task = ("get", 
            url, 
            self.config.stream_url, 
            self.config.save_path+"/"+ self.config.stream_platform + "/" + self.config.type + "/" +self.config.nickname,
            self.config.stream_name,
            self.config.nickname, 
            True, 
            self.login.proxies.get_proxies_dict(),
            self.header.to_dict(),
            self.config.MAX_TIMEOUT)
    download_thread = Thread(target=self.__request_file__, args=task)
    download_thread.start()
    '''
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
    '''


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
      print("start download:")
      print("\tpath:{}\n\tmethod:{}\n\turl:{}\n\tstram:{}\n\tproxies:{}\n\theaders:{}\n\ttimeout:{}".format(save_path + "/" + file_name, method, url, stream, proxies, headers, timeout))
      # print("当前总下载数：{}".format(self.current_download_count))

      if not os.path.exists(save_path):
          print("create directory {}".format(save_path))
          os.makedirs(save_path, exist_ok=True)
      self.auto_down (url, save_path, file_name, 0)
      
      # reset threading status
      '''
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
      '''
      print()
    except Exception as e:
        print("request error: {err}".format(err=e))
        print("\tname:{}\n\tpath:{}\n\turl:{}\n\tdownload failed!!!\n".format(nickname, save_path + "/" + file_name, url))
        return None

  def auto_down (self, url: str, fp: str, fn: str, retry_times: int):
    try:
        file_name = fp + "/" + fn
        while os.path.exists(file_name):
           file_name = fp + "/" + "re_" + str(retry_times) + "_" + fn
           retry_times += 1
        urlretrieve (url, file_name)
    except ContentTooShortError:
        self.auto_down (url, fp, fn, retry_times)

  def run(self, url) -> None:
    self.config.share_url = url
    response_result = dict()

    try:
      if self.config.debug is True:
        print("Share url: {}".format(url))
      ##
      ## query
      ##
      response = self.query_url(method="get", url=url, params=None, timeout=self.config.MAX_TIMEOUT, headers=self.header.to_dict())
      
      # random delay
      sleep(randint(15, 45) * 0.1)
    except Exception as e:
      print("ERROR: Query share url failed! \tstatus:{} \tERROR:{}".format(response.status_code, e))
      return None
    
    try:
      ##
      ## Transform parse result to dict
      ##
      parse_result = urlparse(response.url)
      response_result["url"]      = response.url
      response_result["scheme"]   = parse_result.scheme
      response_result["netloc"]   = parse_result.netloc
      response_result["path"]     = parse_result.path
      response_result["params"]   = parse_result.params
      response_result["fragment"] = parse_result.fragment

      ##
      ## parse url query
      ##
      url_query = str(parse_qs(parse_result.query)).replace("\\", "")
      response_result["query"]              = yml.safe_load(url_query)
      self.__build["share_info"]            = response_result.copy()

      ##
      ## construct live config from query result
      ##
      self.config.x_bogus = XB(self.header.__dict__["User-Agent"]).getXBogus(response.url)
      self.construct_live_data(response_result)
    except Exception as e:
      print("ERROR: Parse share live url failed! {}".format(e))

    ##
    ## try receive live stream
    ##
    try:
      ##
      ## construct parameters for query share url
      ##
      params = self.__construct_query_share_url_params(url, response_result)
      if self.config.debug is True:
        print("Url query response:")
        for k,v in params.items():
          print("\t{}: {}".format(k,v))
      ##
      ## request for live stream
      ##
      live_response = request (
          method="GET", 
          url=self.config.live_api_share,
          params=params,
          timeout=self.config.MAX_TIMEOUT,
          headers=self.header.to_dict())
      if self.config.debug is True:
        print("Live external information:")
        self.config.dict_regular_output(live_response.json())
    except Exception as e:
      print("ERROR: Query live response failed! {}".format(e))
      raise e
    
    # Dealy random
    sleep(randint(15, 45) * 0.1)

      ##
      ## transform response to json format
      ##
    try:
      live_response.raise_for_status()
      ##
      ## check live status
      ##
      if self.live_external_info.get_status(live_response) != 0:
        raise exceptions.HTTPError
      
      ##
      ## initialize live nickname
      ##
      self.config.nickname = self.live_external_info.get_nickname(live_response)

      ##
      ## save live information
      ##
      self.__build["external_info"] = live_response.json()
      if self.config.save_response is True:
        path = self.config.build_path + "/" + self.config.stream_platform + "/" + self.config.type + "/" + self.config.nickname + ".yml"
        self.config.save_config(data=self.__build, output=Path(path))
        if self.config.debug is True:
          print("INFO: Save file {} success!".format(path))

      ##
      ## live status
      ##
      if self.live_external_info.get_room_status(live_response) != 2:
        print("当前 {0} 直播已结束".format(self.config.nickname))
        return None
      else:
        print("当前 {0} 正在直播...".format(self.config.nickname))
    except exceptions.HTTPError:
      print("ERROR: forbidden, please try via other way {}".format(url))
      ##
      ## TODO
      ##
      return None
    except Exception as e:
      print("ERROR: Transformation response to json failed {}".format(e))
      raise e
    
    try:
      ##
      ## get live stream flv url and stream name
      ##
      self.config.stream_url, self.config.stream_name = self.live_external_info.get_flv_pull_url(live_response, self.config.flv_clarity)
      if self.config.debug is True:
        print("INFO: stream url: {}\nstream name:{}".format(self.config.stream_url, self.config.stream_name))
    except Exception as e:
      print("ERROR: Try download live stream {} failed! {}".format(url, e))
      raise e
    
    try:
      ##
      ## try to download stream url
      ##
      if self.config.stream_url is None:
        raise FileNotFoundError
      self.download_live_stream(self.config.share_url)

    except FileNotFoundError:
      print("ERROR: stream url is not found, please double check")
      return None
    except Exception as e:
      print("ERROR: Failed download stream file {}".format(e))
      raise e
    

if __name__ == "__main__":
  downloader = DouyinLiveDownloader()
  if downloader.config.debug is True:
    downloader.dump_config()
  live_url_list = downloader.url_list.getConfigList("live")
  for url in live_url_list:
    downloader.run(url=url)