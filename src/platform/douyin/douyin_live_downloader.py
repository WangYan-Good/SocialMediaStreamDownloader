##>> Test
import os
import sys
sys.path.append(os.getcwd())
from re import compile
##<< Test

## <<Base>>
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
from src.library.baselib import set_dict_attr, get_dict_attr, output_dict, save_dict_as_file
from src.base.downloader import Downloader, DEFAULT_BASE_CONFIG_PATH
from src.platform.douyin.douyin_header import DouyinShareHeader, DouyinLiveInfoHeader, DouyinHeader
from src.platform.douyin.douyin_live_config import DouyinLiveConfig
from src.platform.douyin.douyin_login import DouyinLogin
from src.platform.douyin.douyin_url_list_config import UrlListConfig
from src.platform.douyin.douyin_live_external_info import LiveExternal
from src.platform.douyin.douyin_api import DouyinApi
from xbogus import XBogus as XB
from a_bogus import ABogus as AB

total_live_number = 0
class DouyinLiveDownloader(Downloader):
##
## >>============================= attribute =============================>>
##
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

##
## >>============================= private method =============================>>
##
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

#  def __construct_query_share_url_params(self, share_url, response_result:dict)->dict:
#    params = dict()
#    try:
#      ##
#      ## Construct paramter to request live data
#      ##
#      # params["verifyFp"]       = self.config.get_config_dict_attr("$.params.verifyFp")
#      params["type_id"]        = self.config.get_config_dict_attr("$.params.type_id") #get_dict_attr("$.params.type_id") # self.config.type_id
#      params["live_id"]        = self.config.get_config_dict_attr("$.params.live_id") # self.config.live_id
#      params["room_id"]        = self.config.get_config_dict_attr("$.params.room_id") # self.config.room_id[0]
#      params["sec_user_id"]    = self.config.get_config_dict_attr("$.params.sec_user_id") # response_result["query"].get("sec_user_id", "")[0]
#      params["version_code"]   = self.config.get_config_dict_attr("$.params.version_code") # self.config.version_code
#      params["app_id"]         = self.config.get_config_dict_attr("$.params.app_id") # self.config.app_id
#      # params["msToken"]        = self.login.msToken#TokenManager.gen_real_msToken()
#      # params["live_api"]       = self.config.live_api#"https://live.douyin.com/webcast/room/web/enter/"
#      # params["live_api_share"] = self.config.live_api_share#"https://webcast.amemv.com/webcast/room/reflow/info/"
#      # params["cookie"]         = self.login.cookie
#      params["X-Bogus"]        = self.config.get_config_dict_attr("$.params.x_bogus") # self.config.x_bogus
#      # self.config.a_bogus = AB().get_value(params, "GET")
#      # params["a_bogus"]   = self.config.a_bogus#
#
#      self.__build["query_external_info_params"]             = params
#    except (
#            exceptions.ProxyError,
#            exceptions.SSLError,
#            exceptions.ChunkedEncodingError,
#            exceptions.ConnectionError,
#            exceptions.ReadTimeout):
#        print("ERROR: Query shared url failed!".format(url=share_url))
#        return None
#    return params

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
      print("\tshare_url:{}\n\tpath:{}\n\tmethod:{}\n\turl:{}\n\tstram:{}\n\tproxies:{}\n\theaders:{}\n\ttimeout:{}".format(share_url, save_path + "/" + file_name, method, url, stream, proxies, headers, timeout))
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
      '''
      print("name:{} \nurl:{} \ndownload complete!\n".format(nickname, url))    
      '''
      print("当前总下载数：{}".format(self.current_download_count))
      '''
      print()
    except Exception as e:
        print("request error: {err}".format(err=e))
        print("\tname:{}\n\tpath:{}\n\turl:{}\n\tdownload failed!!!\n".format(nickname, save_path + "/" + file_name, url))
        return None

##
## >>============================= abstract method =============================>>
##
  def construct_aggregation_class(self):

    try:
      ##
      ## construct member
      ##
      self.config             = DouyinLiveConfig(self.CONFIG_PATH)
      self.login              = DouyinLogin(self.config.get_config_dict_attr("$.login_config_path"))
      self.header             = DouyinShareHeader(self.config.header_config_path)
      self.API                = DouyinApi(self.config.get_config_dict_attr("$.api_config_path"))
      self.url_list           = UrlListConfig(self.config.get_config_dict_attr("$.share_url_path"))
      self.live_external_info = LiveExternal()

      ##
      ## initialize all member
      ##
      self.init_douyin_config()
      self.init_douyin_login()

      ##
      ## update member
      ##
      if self.config.get_config_dict_attr("$.login") is True:
        self.login.login()
      else:
        self.login.update_douyin_cookie()
        # self.header.create_douyin_msToken()
        # self.config.update_verifyFp()
    except Exception as e:
      print("ERROR: constrcute aggregation member failed!\n{}".format(e))
      raise e
  
  def dump_config(self):
    super().dump_config()
    self.url_list.dump_url_list()

  def run(self, url) -> None:

    ##
    ## attempt attribute
    ##
    summary = dict()
    response_result = dict()
    header = dict()
    stream_url = str()
    stream_name = str()

    ##
    ##<<========================== query share url ==========================>>
    ##
    try:
      set_dict_attr(summary, "$.share_url", url)
      if self.config.get_config_dict_attr("$.debug") is True:
        print("Share url: {}".format(url))
      ##
      ## construct header for query share url
      ##
      self.header = DouyinShareHeader(self.config.get_config_dict_attr("$.header_config_path"))
      self.header.init_share_live_header (self.config.get_config_dict_attr("$.login"))

      ##
      ## coustruct header for query share url
      ##
      for k,v in self.header.to_dict().items():
        set_dict_attr(header, "$."+k, v)

      ##
      ## query
      ##
      response = self.query_url(method="get", url=url, params=None, timeout=self.config.get_config_dict_attr("$.MAX_TIMEOUT"), headers=header)
      
      ##
      ## random delay
      ##
      sleep(randint(15, 45) * 0.1)
      response.raise_for_status()
    except Exception as e:
      print("ERROR: Query share url failed! \tstatus:{} \tERROR:{}".format(response.status_code, e))
      return None

    try:
      ##
      ## Transform parse result to dict
      ##
      parse_result = urlparse(response.url)
      set_dict_attr(response_result, "$.url", response.url)
      set_dict_attr(response_result, "$.scheme", parse_result.scheme)
      set_dict_attr(response_result, "$.netloc", parse_result.netloc)
      set_dict_attr(response_result, "$.path", parse_result.path)
      set_dict_attr(response_result, "$.params", parse_result.params)
      set_dict_attr(response_result, "$.fragment", parse_result.fragment)

      ##
      ## parse url query
      ##
      url_query = str(parse_qs(parse_result.query)).replace("\\", "")
      set_dict_attr(response_result, "$.query", yml.safe_load(url_query))
      set_dict_attr(self.__build, "$.share_info", response_result.copy())
    ##
    ##<<========================== query live info ==========================>>
    ##
      params = dict()
      api    = str()
      header.clear()
      if self.config.get_config_dict_attr("$.login") is True:
        pass
      else:
        params = self.construct_live_params_no_login(response_result)
    except Exception as e:
      print("ERROR: Parse share live url failed! {}".format(e))
      return
    
    ##
    ## construct api url
    ##
    api = self.API.get_config_dict_attr("$.LIVE_INFO_ROOM_ID")

    ##
    ## try receive live stream
    ##
    try:
      ##
      ## construct header for query live info
      ##
      self.header = DouyinLiveInfoHeader(self.config.header_config_path)
      self.header.init_header(self.config.get_config_dict_attr("$.login"))
      header = self.header.update_header(self.config.get_config_dict_attr("$.login"), header)
      if self.config.get_config_dict_attr("$.debug") is True:
        print("Url query response:")
        output_dict(params)
        output_dict(header)
        print(api)
      ##
      ## request for live stream
      ##
      live_response = request (
          method="GET", 
          url=api,
          params=params,
          timeout=self.config.get_config_dict_attr("$.MAX_TIMEOUT"),
          headers=header)
      if self.config.get_config_dict_attr("$.debug") is True:
        print("Live external information:")
        output_dict(live_response.json())
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
      set_dict_attr(summary, "$.nickname", self.live_external_info.get_raw_nickname(live_response))
      set_dict_attr(summary, "$.diectory_name", self.live_external_info.get_nickname(live_response))

      ##
      ## live status
      ##
      if self.live_external_info.get_room_status(live_response) != 2:
        print("当前 {0} 直播已结束".format(self.live_external_info.get_raw_nickname(live_response)))
        return None
      else:
        print("当前 {0} 正在直播...".format(self.live_external_info.get_raw_nickname(live_response)))
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
      stream_url, stream_name = self.live_external_info.get_flv_pull_url(live_response, self.config.get_config_dict_attr("$.flv_clarity"))
      set_dict_attr(summary, "$.stream_url", stream_url)
      set_dict_attr(summary, "$.stream_name", stream_name)
      if self.config.get_config_dict_attr("$.debug") is True:
        print("INFO: stream url: {}\nstream name:{}".format(stream_url, stream_name))
    except Exception as e:
      print("ERROR: Try download live stream {} failed! {}".format(url, e))
      raise e
    
    try:
      ##
      ## save live information
      ## example: config/build/douyin/live/_米开朗绿萝_.yml
      ##
      set_dict_attr(self.__build, "$.external_info", live_response.json())
      if self.config.get_config_dict_attr("$.save_response") is True:
        path = self.config.get_config_dict_attr("$.build_path") + "/" + self.config.get_config_dict_attr("$.stream_platform") + "/" + self.config.get_config_dict_attr("$.type") + "/" + self.live_external_info.get_nickname(live_response)  + ".yml"
        set_dict_attr(summary, "$.save_path", path)
        set_dict_attr(self.__build, "$.summary", summary)
        save_dict_as_file(source=self.__build, save_path=Path(path))
        if self.config.get_config_dict_attr("$.debug") is True:
          print("INFO: Save file {} success!".format(path))

      ##
      ## try to download stream url
      ##
      if stream_url is None:
        raise FileNotFoundError
      self.download_live_stream(url)

    except FileNotFoundError:
      print("ERROR: stream url is not found, please double check")
      return None
    except Exception as e:
      print("ERROR: Failed download stream file {}".format(e))
      raise e

##
## >>============================= sub class method =============================>>
##
  def init_douyin_config(self):
    pass

  def init_douyin_login(self):
    pass

  def construct_live_params_no_login(self, query_response:dict=None)->dict:
    if query_response is None:
      raise ValueError

    params = dict()
    ##
    ## Construct live data params
    ##
    if (u:=compile(self.REGULAR_ROOM_ID_LIVE_PATH).findall(get_dict_attr(query_response, "$.path"))) is not None:

      # verify FP
      set_dict_attr(
        params,
        "$.verifyFp", 
        self.config.update_verifyFp())
      
      # type id
      set_dict_attr(
        params,
        "$.type_id", 
        self.config.get_config_dict_attr("$.params_no_login.type_id"))
      
      # live id
      set_dict_attr(
        params,
        "$.live_id",
        self.config.get_config_dict_attr("$.params_no_login.live_id"))
      
      # room id
      set_dict_attr(
        params,
        "$.room_id", 
        compile(self.REGULAR_ROOM_ID).findall(get_dict_attr(query_response, "$.path")).pop())
      
      # sec user id
      set_dict_attr(
        params,
        "$.sec_user_id",
        get_dict_attr(query_response, "$.query.sec_user_id")[0])
      
      # version code
      set_dict_attr(
        params,
        "$.version_code",
        self.config.get_config_dict_attr("$.params_no_login.version_code"))
      
      # app id
      set_dict_attr(
        params,
        "$.app_id",
        self.config.get_config_dict_attr("$.params_no_login.app_id"))
      
      # ms token
      set_dict_attr(
        params,
        "$.msToken",
        self.header.create_douyin_msToken())

      # X-Bogus
      set_dict_attr(
        params,
        "$.X-Bogus", 
        XB(self.header.get_header_dict_attr("$.user-agent")).getXBogus(get_dict_attr(query_response, "$.url")))
    else:
      pass
      # self.config.set_config_dict_attr("$.rid", False)
      # self.config.set_config_dict_attr("$.room_id", None)
      # self.config.set_config_dict_attr("$.web_rid", compile(self.REGULAR_ROOM_ID).findall(get_dict_attr(query_response, "$.path")))

    if self.config.get_config_dict_attr("$.debug") is True:
      output_dict(params)
    
    set_dict_attr(self.__build, "$.live_payload", params)
    return params

  def query_url (self, method, url, params, timeout, headers):
    return request(method=method, url=url, params=params, timeout=timeout, headers=headers)

  def download_live_stream(self, url:str):
    global total_live_number
    ##
    ## Define local variable
    ##
    live_download_thread_dict = dict()
    task = ("get", 
            url, 
            get_dict_attr(self.__build, "$.summary.stream_url"), 
            self.config.get_config_dict_attr("$.save_path")+"/"+ self.config.get_config_dict_attr("$.stream_platform") + "/" + self.config.get_config_dict_attr("$.type") + "/" +get_dict_attr(self.__build, "$.summary.diectory_name"),
            get_dict_attr(self.__build, "$.summary.stream_name"),
            get_dict_attr(self.__build, "$.summary.nickname"),
            True, 
            self.login.proxies.get_proxies_dict(),
            self.header.to_dict(),
            self.config.get_config_dict_attr("$.MAX_TIMEOUT"))
    total_live_number += 1
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

  def auto_down (self, url: str, fp: str, fn: str, retry_times: int):
    try:
        file_name = fp + "/" + fn
        while os.path.exists(file_name):
           file_name = fp + "/" + "re_" + str(retry_times) + "_" + fn
           retry_times += 1
        urlretrieve (url, file_name)
    except ContentTooShortError:
        self.auto_down (url, fp, fn, retry_times)

if __name__ == "__main__":
  downloader = DouyinLiveDownloader()
  if downloader.config.get_config_dict_attr("$.debug") is True:
    downloader.dump_config()
  live_url_list = downloader.url_list.getConfigList("live")
  for url in live_url_list:
    downloader.run(url=url)
    # Thread(target=downloader.run, args=url)
    # break
    sleep(randint(15, 45) * 0.1)
    if downloader.config.max_thread <= total_live_number:
      break
