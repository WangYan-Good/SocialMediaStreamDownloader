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
from threading import Thread, Lock

## <<Extension>>
import yaml as yml

## <<Third-Part>>
from backend.src.library.baselib import set_dict_attr, get_dict_attr, output_dict, save_dict_as_file
from backend.src.base.downloader import Downloader, DEFAULT_BASE_CONFIG_PATH
from backend.src.platform.douyin.douyin_header import DouyinShareHeader, DouyinLiveInfoHeader, DouyinHeader
from backend.src.platform.douyin.douyin_live_config import DouyinLiveConfig
from backend.src.platform.douyin.douyin_login import DouyinLogin
from backend.src.platform.douyin.douyin_url_list_config import UrlListConfig
from backend.src.platform.douyin.douyin_live_external_info import LiveExternal
from backend.src.platform.douyin.douyin_api import DouyinApi
from backend.src.platform.douyin.douyin_share_url_database import DouyinShareUrlDatabase
from xbogus import XBogus as XB
from a_bogus import ABogus as AB

from backend.src.platform.douyin.douyin_listener import DouyinLiveListener, ListenerItem

# total_live_number = 0
class DouyinLiveDownloader(Downloader):
##
## >>============================= attribute =============================>>
##
  ##
  ## Attribute
  ##
  url_list                  = None
  REGULAR_ROOM_ID           = r"/douyin/webcast/reflow/(\S+)"
  REGULAR_ROOM_ID_LIVE_PATH = r"/douyin/webcast/reflow/\S+"
  _actived_task_number      = 0
  _lock                     = None

  ##
  ## member
  ##
  live_external_info           = None
  live_douyin_listener         = None
  database                     = None

  ##
  ## Cache
  ##
  __build  = dict()

##
## >>============================= private method =============================>>
##
  def __init__(self, path: Path = None) -> None:
    if path is None:
      print("WARNING: invalid input, will use default config")
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
      ##
      ## start download
      ## output message
      ##
      print("start download:")
      print("\tshare_url:{}\n\tpath:{}\n\tmethod:{}\n\turl:{}\n\tstram:{}\n\tproxies:{}\n\theaders:{}\n\ttimeout:{}".format(share_url, save_path + "/" + file_name, method, url, stream, proxies, headers, timeout))
      print("当前总下载数：{}".format(self._actived_task_number))

      ##
      ## create directory
      ##
      if not os.path.exists(save_path):
          print("create directory {}".format(save_path))
          os.makedirs(save_path, exist_ok=True)
      
      ##
      ## download live stream
      ##
      if self.config.get_config_dict_attr("$.test_mode") is not True:
        self.auto_down (url, save_path, file_name, 0)
      
      ##
      ## reset actived number
      ##
      self._actived_task_number -= 1
      
      ##
      ## update download message
      ##
      print("name:{} \nurl:{} \ndownload complete!\n".format(nickname, url))    
      print("当前总下载数：{}".format(self._actived_task_number))
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
      self.config               = DouyinLiveConfig(self.CONFIG_PATH)
      self.login                = DouyinLogin(self.config.get_config_dict_attr("$.login_config_path"))
      self.header               = DouyinShareHeader(self.config.header_config_path)
      self.API                  = DouyinApi(self.config.get_config_dict_attr("$.api_config_path"))
      self.url_list             = UrlListConfig(self.config.get_config_dict_attr("$.share_url_path"))
      self.live_external_info   = LiveExternal()
      self.live_douyin_listener = DouyinLiveListener()
      self._lock                = Lock()
      
      if self.config.get_config_dict_attr("$.database_enable") is True:
        self.database             = DouyinShareUrlDatabase (
                                      host=self.config.get_config_dict_attr("$.database_ip"),
                                      user=self.config.get_config_dict_attr("$.database_user"),
                                      passwd=self.config.get_config_dict_attr("$.database_password"),
                                      database=self.config.get_config_dict_attr("$.database_name")
                                    )
      else:
        self.database             = None

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
    ## download task should be blocked if the number >= max task
    ## TODO
    ##
    output_fuse = False
    while self._actived_task_number >= self.config.get_config_dict_attr("$.max_thread") and self.config.get_config_dict_attr("$.max_thread") != 0:

      # stop download if listener is end
      if self.live_douyin_listener.is_listening_ending() is True and output_fuse is False:
        print("INFO: download task {} is interrupt because of listener stop.".format(url))
        output_fuse = True
        
    
    ##
    ## attempt attribute for thread
    ##
    build                = dict()
    summary              = dict()
    response_result      = dict()
    live_response_dict   = dict()
    header               = dict()
    stream_url           = str()
    stream_name          = str()

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
      ## construct header for query share url
      ##
      for k,v in self.header.to_dict().items():
        set_dict_attr(header, "$."+k, v)

      ##
      ## query
      ##
      response = self.query_url(
                        method="get", 
                        url=url, 
                        params=None, 
                        timeout=self.config.get_config_dict_attr("$.MAX_TIMEOUT"), 
                        headers=header)

      ##
      ## random delay between 1.5s - 4.5s
      ##
      sleep(randint(15, 45) * 0.1)
      response.raise_for_status()
    except TimeoutError:
      print("ERROR: Timeout, please try again later! {}".format(url))
      return None
    except exceptions.ReadTimeout:
      print("ERROR: Read timeout, please try again later! {}".format(url))
      return None
    except UnboundLocalError:
      print("ERROR: UnboundLocalError, please check the code! {}".format(url))
      return None
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
      set_dict_attr(build, "$.share_info", response_result.copy())
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
      print("ERROR: Parse share live url failed! {} {}".format(e, url))
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
      if live_response.status_code != 200:
        raise exceptions.HTTPError
    except exceptions.HTTPError:
      print("ERROR: Query live response failed! {}".format(live_response.status_code))
      return None
    except TimeoutError:
      print("ERROR: Timeout, please try again later! {}".format(url))
      return None
    except exceptions.ReadTimeout:
      print("ERROR: Read timeout, please try again later! {}".format(url))
      return None
    except Exception as e:
      print("ERROR: Query live response failed! {}".format(e))
      raise e
    
    # delay random
    sleep(randint(15, 45) * 0.1)
    if self.config.get_config_dict_attr("$.debug") is True:
      print("Live external information:")
      output_dict(live_response.json())

    ##
    ## transform response to json format
    ##
    try:
      live_response.raise_for_status()
      ##
      ## check live status
      ##
      if self.live_external_info.get_status(live_response) != 0:
        if self.config.get_config_dict_attr("$.debug") is True:
          print("ERROR: non-except live status: {}".format(self.live_external_info.get_status(live_response)))
        raise exceptions.HTTPError
      
      ##
      ## initialize live nickname
      ##
      live_response_dict = live_response.json()
      set_dict_attr(summary, "$.nickname", self.live_external_info.get_raw_nickname(live_response))
      set_dict_attr(summary, "$.directory_name", self.live_external_info.get_nickname(live_response))

      ##
      ## live room status
      ## 2: live
      ## 4: end
      ##
      room_status = self.live_external_info.get_room_status(live_response)
      if room_status != 2:
        print("当前 {0} 直播已结束".format(self.live_external_info.get_raw_nickname(live_response)))
      else:
        print("当前 {0} 正在直播...".format(self.live_external_info.get_raw_nickname(live_response)))
    except exceptions.HTTPError:
      print("ERROR: forbidden, please try via other way {}".format(url))
      ##
      ## TODO save external information
      ##

      ##
      ## TODO store information into database
      ##
      
      ##
      ## TODO handle the case when status_code != 0
      ##
      return None
    except Exception as e:
      print("ERROR: Transformation response to json failed {}".format(e))
      raise e
    
    try:
      ##
      ## get live stream flv url and stream name
      ##
      if room_status == 2:
        stream_url, stream_name = self.live_external_info.get_flv_pull_url(live_response, self.config.get_config_dict_attr("$.flv_clarity"))
        set_dict_attr(summary, "$.stream_url", stream_url)
        set_dict_attr(summary, "$.stream_name", stream_name)
        if self.config.get_config_dict_attr("$.debug") is True:
          print("INFO: stream url: {}\nstream name:{}".format(stream_url, stream_name))  
    except TypeError:
      ##
      ## save error information
      ##
      if self.config.get_config_dict_attr("$.save_error_response") is True:
        set_dict_attr(build, "$.error_response", live_response_dict)
        error_response_path = self.config.get_config_dict_attr("$.build_path") + "/" + self.config.get_config_dict_attr("$.stream_platform") + "/" + self.config.get_config_dict_attr("$.type") + "/error_response/" + self.live_external_info.get_nickname(live_response)  + ".yml"
        set_dict_attr(summary, "$.error_response_path", error_response_path)
        set_dict_attr(build, "$.summary", summary)
        save_dict_as_file(source=params, save_path=Path(error_response_path))
        if self.config.get_config_dict_attr("$.debug") is True:
          print("INFO: Save error response file {} success!".format(error_response_path))
      return None
    except Exception as e:
      print("ERROR: Try download live stream {} failed! {}".format(url, e))
      raise e
    
    try:
      ##
      ## save live information
      ## example: config/build/douyin/live/_xxx_.yml
      ##
      set_dict_attr(build, "$.external_info", live_response_dict)
      path = self.config.get_config_dict_attr("$.build_path") + "/" + self.config.get_config_dict_attr("$.stream_platform") + "/" + self.config.get_config_dict_attr("$.type") + "/" + self.live_external_info.get_nickname(live_response)  + ".yml"
      set_dict_attr(summary, "$.save_path", path)
      set_dict_attr(build, "$.summary", summary)
      if self.config.get_config_dict_attr("$.save_response") is True:
        set_dict_attr(build, "$.live_payload", get_dict_attr(self.__build, "$.live_payload"))
        save_dict_as_file(source=build, save_path=Path(path))
        if self.config.get_config_dict_attr("$.debug") is True:
          print("INFO: Save file {} success!".format(path))
      
      ##
      ## save share url information into database
      ##
      if self.database is not None:
        ##
        ## construct record tuple
        ##
        record_tuple  = self.database.get_share_url_table_tuple().copy()
        record_tuple.clear()
        set_dict_attr(record_tuple, "$.owner_user_id",  get_dict_attr(live_response_dict, "$.data.room.owner_user_id"))
        set_dict_attr(record_tuple, "$.sec_user_id",    get_dict_attr(live_response_dict, "$.data.room.owner.sec_uid"))
        set_dict_attr(record_tuple, "$.nickname",       get_dict_attr(live_response_dict, "$.data.room.owner.nickname"))
        set_dict_attr(record_tuple, "$.live_share_url", url)
        set_dict_attr(record_tuple, "$.directory_name", self.live_external_info.get_nickname(live_response))
        
        owner_status = get_dict_attr(live_response_dict, "$.data.room.owner.status")
        if owner_status == 1:
          set_dict_attr(record_tuple, "$.user_status",    "正常")
        elif owner_status == 0:
          set_dict_attr(record_tuple, "$.user_status",    "已注销")

        ##
        ## random wait for 0.1s - 0.5s to avoid being blocked
        ## store record into database
        ##
        sleep(randint(1, 5) * 0.1)
        if self.database.is_owner_user_id_record_exist(get_dict_attr(live_response_dict, "$.data.room.owner_user_id")) is True:
          ##
          ## update live share url record
          ##
          self.database.update_live_share_url_record(record_tuple)
        else:
          ##
          ## insert live share url record
          ##
          self.database.insert_live_share_url_record(record_tuple)

      ##
      ## try to download stream url
      ##
      if stream_url is None:
        raise FileNotFoundError
      
      ##
      ## download live stream when live room is active
      ##
      if room_status == 2:
        self.download_live_stream(url, build)

    except FileNotFoundError:
      print("ERROR: stream url is not found, please double check")
      return None
    except TimeoutError:
      print("WARNING: timeout, wait 5s and try again")
      sleep(5)
      self.run(url)
      return None
    except KeyError:
      print("ERROR: KeyError, please check the code {} {}".format(get_dict_attr(build, "$.summary.nickname"), url))
      return None
    except Exception as e:
      print("ERROR: Failed download stream file {} {} {}".format(get_dict_attr(build, "$.summary.nickname"), url, e))
      raise e

##
## >>============================= sub class method =============================>>
##
  def acquire(self):
    self._lock.acquire()
  
  def release(self):
    self._lock.release()

  def is_exceed_max_download_task(self):
    if self._actived_task_number >= self.config.get_config_dict_attr("$.max_thread"):
      return True
    else:
      return False

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

  def download_live_stream(self, url:str, params:dict=None):
    
    ##
    ##
    ##
    if params is None:
      raise ValueError
    
    ##
    ## cache all temp variable for multiple thread
    ##
    stream_url  = get_dict_attr(params, "$.summary.stream_url")
    if stream_url is None:
      raise ValueError
    
    ##
    ## if database is enable, then get the directory name from database
    ##
    if self.config.get_config_dict_attr("$.database_enable") is True and self.database.is_live_share_url_record_exist(url) is True:
      directory_name = self.database.get_owner_nickname_by_live_share_url(url)
    else:
      directory_name = get_dict_attr(params, "$.summary.directory_name")
    save_dir    = self.config.get_config_dict_attr("$.save_path")+"/"+ self.config.get_config_dict_attr("$.stream_platform") + "/" + self.config.get_config_dict_attr("$.type") + "/" + directory_name
    stream_name = get_dict_attr(params, "$.summary.stream_name")
    nickname    = get_dict_attr(params, "$.summary.nickname")
    proxies     = self.login.proxies.get_proxies_dict()
    header      = self.header.to_dict()
    max_timeout = self.config.get_config_dict_attr("$.MAX_TIMEOUT")
    
    ##
    ## start require live stream file
    ##
    self.acquire()
    ##
    ## setting max thread will work here
    ## download wil be blocked if (actived task number >= max_thread and max_thread != 0)
    ##
    while self._actived_task_number >= self.config.get_config_dict_attr("$.max_thread") and self.config.get_config_dict_attr("$.max_thread") != 0:
      pass
    
    ##
    ## add actived task
    ##
    self._actived_task_number += 1
    
    ##
    ## check max thread
    ##
    if self._actived_task_number >= self.config.get_config_dict_attr("$.max_thread") and self.config.get_config_dict_attr("$.max_thread") != 0:
      self.live_douyin_listener.stop()
    self.release()
    self.__request_file__(
          "get", 
          url, 
          stream_url, 
          save_dir,
          stream_name,
          nickname,
          True, 
          proxies,
          header,
          max_timeout)

  def auto_down (self, url: str, fp: str, fn: str, retry_times: int):
    try:
        file_name = fp + "/" + fn
        while os.path.exists(file_name):
           file_name = fp + "/" + "re_" + str(retry_times) + "_" + fn
           retry_times += 1
        urlretrieve (url, file_name)
    except ContentTooShortError:
        self.auto_down (url, fp, fn, retry_times)

def download_live():
  ##
  ## construct live downloader
  ##
  downloader = DouyinLiveDownloader()
  if downloader.config.get_config_dict_attr("$.debug") is True:
    downloader.dump_config()

  ##
  ## get live url list
  ##
  live_url_list = downloader.url_list.get_config_list("live")
  for url in live_url_list:
    item = ListenerItem(func=downloader.run, args=(url,))
    downloader.live_douyin_listener.add_sub_task(item)
    if downloader.live_douyin_listener.is_patrolman_actived() is not True:
      downloader.live_douyin_listener.start()

##
## >>================================ test method ===============================>>
##

##
## test: import share live url to database
##
def import_share_live_url_to_database(url:str):
  pass

##
## test: download a live stream by url
##
def download_live_test():
  downloader = DouyinLiveDownloader()
  if downloader.config.get_config_dict_attr("$.debug") is True:
    downloader.dump_config()
  live_url_list = downloader.url_list.get_config_list("live")
  for url in live_url_list:
    try:
      downloader.run(url=url)
      # if downloader.config.get_config_dict_attr("$.max_thread") <= total_live_number and downloader.config.get_config_dict_attr("$.max_thread") != 0:
      break
    except Exception:
      continue
    
if __name__ == "__main__":
  download_live()
  # download_live_test()