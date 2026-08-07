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
from threading import Lock
from datetime import datetime

## <<Extension>>
import yaml as yml

## <<Third-Part>>
from backend.src.library.baselib                            import set_dict_attr, get_dict_attr, output_dict, save_dict_as_file
from backend.src.base.downloader                            import Downloader
from backend.src.platform.douyin.douyin_header              import DouyinShareHeader, DouyinLiveInfoHeader
from backend.src.platform.douyin.douyin_live_config         import DouyinLiveConfig
from backend.src.platform.douyin.douyin_login               import DouyinLogin
from backend.src.platform.douyin.douyin_url_list_config     import UrlListConfig
from backend.src.platform.douyin.douyin_live_external_info  import LiveExternal
from backend.src.platform.douyin.douyin_api                 import DouyinApi
from backend.src.database.table.share_url                   import DouyinShareUrlTable
from backend.src.database.table.table_import                import import_douyin_live_info_to_database
from backend.src.library.loglib                             import get_logger

## TODO
from backend.src.platform.douyin.xbogus import XBogus as XB
from backend.src.platform.douyin.a_bogus import ABogus as AB

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

  ##
  ## member
  ##
  live_external_info           = None
  live_douyin_listener         = None
  database                     = None

##
## >>============================= private method =============================>>
##
  def __init__(self, config: dict = None) -> None:
    self.database = None
    self._actived_task_number = 0
    self._lock = Lock()
    self.construct_aggregation_class(config)

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
    succeeded = False
    try:
      ##
      ## start download
      ## output message
      ##
      get_logger().info("start download:")
      get_logger().info("\tshare_url:{}\n\tpath:{}\n\tmethod:{}\n\turl:{}\n\tstram:{}\n\tproxies:{}\n\theaders:{}\n\ttimeout:{}".format(share_url, save_path + "/" + file_name, method, url, stream, proxies, headers, timeout))
      get_logger().info("当前总下载数：{}".format(self._actived_task_number))

      if self.config.get_config_dict_attr("$.download.test_mode") is True:
        get_logger().info("test mode enabled, skip live stream file write")
        return None

      ##
      ## create directory
      ##
      if not os.path.exists(save_path):
          get_logger().info("create directory {}".format(save_path))
          os.makedirs(save_path, exist_ok=True)
      
      ##
      ## download live stream
      ##
      self.auto_down(
        url,
        save_path,
        file_name,
        0,
        headers=headers,
        proxies=proxies,
        timeout=timeout,
      )
      succeeded = True
    except Exception as e:
      get_logger().error("request error: {err}".format(err=e))
      get_logger().error("\tname:{}\n\tpath:{}\n\turl:{}\n\tdownload failed!!!\n".format(nickname, save_path + "/" + file_name, url))
      raise
    finally:
      ##
      ## release actived task number
      ##
      self.acquire()
      self._actived_task_number -= 1
      self.release()
      
      ##
      ## update download message
      ##
      if succeeded:
        get_logger().info("name:{} \nurl:{} \ndownload complete!\n".format(nickname, url))
      else:
        get_logger().info("name:{} \nurl:{} \ndownload stopped!\n".format(nickname, url))
      get_logger().info("当前总下载数：{}\n".format(self._actived_task_number))
    return None

##
## >>============================= abstract method =============================>>
##
  def construct_aggregation_class(self, config: dict = None):

    try:
      ##
      ## construct member
      ##
      self.config               = DouyinLiveConfig(config)
      self.login                = DouyinLogin(self.config.get_config_dict_attr("$.platform.douyin.login"))
      self.header               = DouyinShareHeader(self.config.get_config_dict_attr("$.platform.douyin.headers"))
      self.API                  = DouyinApi(self.config.get_config_dict_attr("$.platform.douyin.api"))
      self.url_list             = UrlListConfig(self.config.share_url_path)
      self.live_external_info   = LiveExternal()
      self.live_douyin_listener = DouyinLiveListener()
      self._lock                = Lock()
      
      if (
        self.config.get_config_dict_attr("$.database.enable") is True
        and self.config.get_config_dict_attr("$.download.test_mode") is not True
      ):
        try:
          self.database = DouyinShareUrlTable(
            host=self.config.get_config_dict_attr("$.database.host"),
            user=self.config.get_config_dict_attr("$.database.username"),
            passwd=self.config.get_config_dict_attr("$.database.password"),
            database=self.config.get_config_dict_attr("$.database.name"),
          )
        except Exception as e:
          self.database = None
          get_logger().warning(
            "database unavailable, continue live download without persistence: {}".format(e)
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
      if self.config.get_config_dict_attr("$.download.user_login") is True:
        self.login.login()
      else:
        self.login.update_douyin_cookie()
        # self.header.create_douyin_msToken()
        # self.config.update_verifyFp()
    except Exception as e:
      get_logger().error("construct aggregation member failed!\n{}".format(e))
      raise e
  
  def dump_config(self):
    super().dump_config()
    self.url_list.dump_url_list()

  def run(self, token) -> None:
    
    ##
    ## get url from token
    ##
    url = get_dict_attr(token, "$.url")
    if url is None:
      get_logger().error("invalid url")
      raise ValueError

    if self.config.get_config_dict_attr("$.download.test_mode") is True:
      get_logger().info("test mode enabled, skip live download pipeline")
      return None
    
    ##
    ## download task should be blocked if the number >= max task
    ## TODO
    ##
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
      if self.config.get_config_dict_attr("$.server.debug_mode") is True:
        get_logger().info("Share url: {}".format(url))
      ##
      ## construct header for query share url
      ##
      share_header = DouyinShareHeader(
        self.config.get_config_dict_attr("$.platform.douyin.headers")
      )
      share_header.init_share_live_header(
        self.config.get_config_dict_attr("$.download.user_login")
      )

      ##
      ## construct header for query share url
      ##
      for k,v in share_header.to_dict().items():
        set_dict_attr(header, "$."+k, v)

      ##
      ## query
      ##
      response = self.query_url(
                        method="get", 
                        url=url, 
                        params=None, 
                        timeout=self.config.get_config_dict_attr("$.platform.douyin.live.max_timeout"),
                        headers=header
                        )
      ##
      ## WA: random delay between 1.5s - 4.5s
      ##
      sleep(randint(15, 45) * 0.1)
      response.raise_for_status()
    except TimeoutError:
      get_logger().error("Timeout, please try again later! {}".format(url))
      return None
    except exceptions.ReadTimeout:
      get_logger().error("Read timeout, please try again later! {}".format(url))
      return None
    except UnboundLocalError:
      get_logger().error("UnboundLocalError, please check the code! {}".format(url))
      return None
    except Exception as e:
      status_code = getattr(locals().get("response"), "status_code", "unavailable")
      get_logger().error("Query share url failed! \tstatus:{} \tERROR:{}".format(status_code, e))
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
      if self.config.get_config_dict_attr("$.download.user_login") is True:
        pass
      else:
        params = self.construct_live_params_no_login(
          response_result,
          share_header,
        )
        set_dict_attr(build, "$.live_payload", params)
    except Exception as e:
      get_logger().error("Parse share live url failed! {} {}".format(e, url))
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
      live_header = DouyinLiveInfoHeader(
        self.config.get_config_dict_attr("$.platform.douyin.headers")
      )
      live_header.init_header(
        self.config.get_config_dict_attr("$.download.user_login")
      )
      header = live_header.update_header(
        self.config.get_config_dict_attr("$.download.user_login"),
        header,
      )
      
      ##
      ## output debug information
      ##
      if self.config.get_config_dict_attr("$.server.debug_mode") is True:
        get_logger().info("Url query response:")
        output_dict(params)
        output_dict(header)
        get_logger().info(api)

      ##
      ## request for live stream
      ##
      live_response = request (
          method="GET", 
          url=api,
          params=params,
          timeout=self.config.get_config_dict_attr("$.platform.douyin.live.max_timeout"),
          headers=header
          )
      if live_response.status_code != 200:
        raise exceptions.HTTPError
    except exceptions.HTTPError:
      get_logger().error("Query live response failed! {}".format(live_response.status_code))
      return None
    except TimeoutError:
      get_logger().error("Timeout, please try again later! {}".format(url))
      return None
    except exceptions.ReadTimeout:
      get_logger().error("Read timeout, please try again later! {}".format(url))
      return None
    except Exception as e:
      get_logger().error("Query live response failed! {}".format(e))
      raise e
    
    ##
    ## WA: delay random
    ##
    sleep(randint(15, 45) * 0.1)

    ##
    ## output debug information
    ##
    if self.config.get_config_dict_attr("$.server.debug_mode") is True:
      get_logger().info("Live external information:")
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
        if self.config.get_config_dict_attr("$.server.debug_mode") is True:
          get_logger().error("non-except live status: {}".format(self.live_external_info.get_status(live_response)))
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
        get_logger().info("当前 {0} 直播已结束".format(self.live_external_info.get_raw_nickname(live_response)))
      else:
        get_logger().info("当前 {0} 正在直播...".format(self.live_external_info.get_raw_nickname(live_response)))
    except exceptions.HTTPError:
      get_logger().error("forbidden, please try via other way {}".format(url))
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
      get_logger().error("Transformation response to json failed {}".format(e))
      raise e
    
    try:
      ##
      ## get live stream flv url and stream name
      ##
      if room_status == 2:
        stream_url, stream_name = self.live_external_info.get_flv_pull_url(
          live_response,
          self.config.get_config_dict_attr("$.platform.douyin.live.flv_clarity"),
          self.config.get_config_dict_attr("$.platform.douyin.live.hls_clarity"),
        )
        set_dict_attr(summary, "$.stream_url", stream_url)
        set_dict_attr(summary, "$.stream_name", stream_name)
        
        ##
        ## output debug information
        ##
        if self.config.get_config_dict_attr("$.server.debug_mode") is True:
          get_logger().info("stream url: {}\nstream name:{}".format(stream_url, stream_name))  
    except Exception as e:
      get_logger().error("Try download live stream {} failed! {}".format(url, e))

      ##
      ## save error information
      ##
      if self.config.get_config_dict_attr("$.download.save_error_response") is True:
        set_dict_attr(build, "$.error_response", live_response_dict)
        error_response_path = (
          Path(self.config.get_config_dict_attr("$.download.save_path"))
          / "douyin"
          / self.config.get_config_dict_attr("$.platform.douyin.download.type")
          / "error_response"
          / (self.live_external_info.get_nickname(live_response) + ".yml")
        )
        set_dict_attr(summary, "$.error_response_path", str(error_response_path))
        set_dict_attr(build, "$.summary", summary)
        save_dict_as_file(source=build, save_path=error_response_path)
        if self.config.get_config_dict_attr("$.server.debug_mode") is True:
          get_logger().info("Save error response file {} success!".format(error_response_path))
      raise e
    
    try:
      ##
      ## save live information
      ## example: config/build/douyin/live/_xxx_.yml
      ##
      set_dict_attr(build, "$.external_info", live_response_dict)
      path = (
        Path(self.config.get_config_dict_attr("$.download.save_path"))
        / "douyin"
        / self.config.get_config_dict_attr("$.platform.douyin.download.type")
        / "response"
        / (
          datetime.now().strftime("%Y-%m-%d_%H-%M-%S_")
          + self.live_external_info.get_nickname(live_response)
          + ".yml"
        )
      )
      set_dict_attr(summary, "$.save_path", str(path))
      set_dict_attr(build, "$.summary", summary)
      if self.config.get_config_dict_attr("$.download.save_response") is True:
        save_dict_as_file(source=build, save_path=path)
        
        ##
        ## output debug information
        ##
        if self.config.get_config_dict_attr("$.server.debug_mode") is True:
          get_logger().info("Save file {} success!".format(path))
      
      ##
      ## save share url information into database
      ##
      if self.database is not None:
        try:
          self._persist_live_metadata(
            token,
            url,
            live_response_dict,
            room_status,
          )
        except Exception as e:
          get_logger().warning(
            "database persistence failed, continue live download: {}".format(e)
          )
          self.database = None

      ##
      ## try to download stream url
      ##
      if stream_url is None:
        raise FileNotFoundError
      
      ##
      ## download live stream when live room is active
      ##
      if room_status == 2:
        self.download_live_stream(url, build, headers=header)

    except FileNotFoundError:
      get_logger().error("stream url is not found, please double check")
      return None
    except KeyError:
      get_logger().error("KeyError, please check the code {} {}".format(get_dict_attr(build, "$.summary.nickname"), url))
      return None
    except Exception as e:
      get_logger().error("Failed download stream file {} {} {}".format(get_dict_attr(build, "$.summary.nickname"), url, e))
      raise e

##
## >>============================= sub class method =============================>>
##
  def _persist_live_metadata(self, token, url, live_response_dict, room_status):
    try:
      import_douyin_live_info_to_database(self.database, live_response_dict)
    except Exception as e:
      get_logger().warning(
        "live response database import failed, continue share-url persistence: {}".format(e)
      )

    record_tuple = self.database.get_share_url_table_tuple().copy()
    record_tuple.clear()
    set_dict_attr(record_tuple, "$.owner_user_id", get_dict_attr(live_response_dict, "$.data.room.owner_user_id"))
    set_dict_attr(record_tuple, "$.sec_user_id", get_dict_attr(live_response_dict, "$.data.room.owner.sec_uid"))
    set_dict_attr(record_tuple, "$.nickname", get_dict_attr(live_response_dict, "$.data.room.owner.nickname"))
    set_dict_attr(record_tuple, "$.live_share_url", url)
    set_dict_attr(record_tuple, "$.directory_name", self.live_external_info._replaceT(get_dict_attr(live_response_dict, "$.data.room.owner.nickname")))

    owner_status = get_dict_attr(live_response_dict, "$.data.room.owner.status")
    if owner_status == 1:
      set_dict_attr(record_tuple, "$.user_status", "正常")
    elif owner_status == 0:
      set_dict_attr(record_tuple, "$.user_status", "已注销")

    sleep(randint(1, 5) * 0.1)
    owner_user_id = get_dict_attr(live_response_dict, "$.data.room.owner_user_id")
    if self.database.is_owner_user_id_record_exist(owner_user_id) is True:
      self.database.update_live_share_url_record(record_tuple)
      if room_status == 2:
        self.database.increment_live_actived_count(owner_user_id)
    else:
      self.database.insert_live_share_url_record(record_tuple)

    favorite = get_dict_attr(token, "$.favorite")
    score = get_dict_attr(token, "$.score")
    if favorite is True and score is not None:
      if self.database.is_owner_score_record_exist(owner_user_id) is False:
        self.database.insert_owner_score(owner_user_id=owner_user_id, score=score)
      else:
        origin_score = self.database.get_owner_score_by_user_id(owner_user_id)
        if origin_score != int(score):
          self.database.update_owner_score(owner_user_id, score)

  def acquire(self):
    self._lock.acquire()
  
  def release(self):
    self._lock.release()

  def is_exceed_max_download_task(self):
    max_threads = self.config.get_config_dict_attr("$.download.max_threads")
    return max_threads != 0 and self._actived_task_number >= max_threads

  def init_douyin_config(self):
    pass    

  def init_douyin_login(self):
    pass

  def construct_live_params_no_login(
    self,
    query_response: dict = None,
    header = None,
  ) -> dict:
    if query_response is None:
      raise ValueError

    params = dict()
    header = header or self.header
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
        self.config.get_config_dict_attr("$.platform.douyin.live.params_no_login.type_id"))
      
      # live id
      set_dict_attr(
        params,
        "$.live_id",
        self.config.get_config_dict_attr("$.platform.douyin.live.params_no_login.live_id"))
      
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
        self.config.get_config_dict_attr("$.platform.douyin.live.params_no_login.version_code"))
      
      # app id
      set_dict_attr(
        params,
        "$.app_id",
        self.config.get_config_dict_attr("$.platform.douyin.live.params_no_login.app_id"))
      
      # ms token
      set_dict_attr(
        params,
        "$.msToken",
        header.create_douyin_msToken())

      # X-Bogus
      set_dict_attr(
        params,
        "$.X-Bogus", 
        XB(header.get_header_dict_attr("$.user-agent")).getXBogus(get_dict_attr(query_response, "$.url")))
    else:
      pass
      # self.config.set_config_dict_attr("$.rid", False)
      # self.config.set_config_dict_attr("$.room_id", None)
      # self.config.set_config_dict_attr("$.web_rid", compile(self.REGULAR_ROOM_ID).findall(get_dict_attr(query_response, "$.path")))

    if self.config.get_config_dict_attr("$.server.debug_mode") is True:
      output_dict(params)
    
    return params

  def query_url (self, method, url, params, timeout, headers):
    return request(method=method, url=url, params=params, timeout=timeout, headers=headers)

  def download_live_stream(self, url: str, params: dict = None, headers=None):
    
    ##
    ##
    ##
    if params is None:
      raise ValueError

    if self.config.get_config_dict_attr("$.download.test_mode") is True:
      get_logger().info("test mode enabled, skip live stream file write")
      return None
    
    ##
    ## cache all temp variable for multiple thread
    ##
    stream_url  = get_dict_attr(params, "$.summary.stream_url")
    if stream_url is None:
      raise ValueError
    
    ##
    ## if database is enable, then get the directory name from database
    ##
    directory_name = get_dict_attr(params, "$.summary.directory_name")
    if self.database is not None:
      try:
        owner_user_id = get_dict_attr(
          params,
          "$.external_info.data.room.owner_user_id",
        )
        if self.database.is_owner_user_id_record_exist(owner_user_id) is True:
          directory_name = self.database.get_directory_name_by_owner_user_id(
            owner_user_id
          )
      except Exception as e:
        get_logger().warning(
          "database directory lookup failed, use live nickname: {}".format(e)
        )
        self.database = None
    save_dir    = self.config.get_config_dict_attr("$.download.save_path")+"/douyin/" + self.config.get_config_dict_attr("$.platform.douyin.download.type") + "/" + directory_name
    
    ##
    ## if tick_naming
    ##
    stream_name = get_dict_attr(params, "$.summary.stream_name")
    if self.config.get_config_dict_attr("$.download.tick_naming") is True:
      stream_name = datetime.now().strftime("%Y%m%d%H%M%S") + "_" + stream_name
    
    nickname    = get_dict_attr(params, "$.summary.nickname")
    proxies     = self.login.proxies.get_proxies_dict()
    header      = headers or self.header.to_dict()
    max_timeout = self.config.get_config_dict_attr("$.platform.douyin.live.max_timeout")
    
    ##
    ## start require live stream file
    ##
    max_threads = self.config.get_config_dict_attr("$.download.max_threads")
    while True:
      self.acquire()
      if max_threads == 0 or self._actived_task_number < max_threads:
        self._actived_task_number += 1
        if max_threads != 0 and self._actived_task_number >= max_threads:
          self.live_douyin_listener.stop()
        self.release()
        break
      self.release()
      sleep(0.05)
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

  def auto_down(
    self,
    url: str,
    fp: str,
    fn: str,
    retry_times: int,
    headers: dict = None,
    proxies: dict = None,
    timeout: int = 10,
  ):
    temporary_file = None
    response = None
    try:
        file_name = fp + "/" + fn
        duplicate_index = 0
        while os.path.exists(file_name):
           file_name = fp + "/" + "re_" + str(duplicate_index) + "_" + fn
           duplicate_index += 1
        temporary_file = file_name + ".part"

        if urlparse(url).scheme in ("http", "https"):
          response = request(
            method="GET",
            url=url,
            headers=headers,
            proxies=proxies,
            timeout=timeout,
            stream=True,
          )
          response.raise_for_status()
          written_size = 0
          with open(temporary_file, "wb") as output:
            for chunk in response.iter_content(chunk_size=1024 * 1024):
              if not chunk:
                continue
              output.write(chunk)
              written_size += len(chunk)

          content_length = response.headers.get("Content-Length")
          if content_length is not None and written_size < int(content_length):
            raise ContentTooShortError("incomplete live stream", written_size)
        else:
          urlretrieve(url, temporary_file)

        os.replace(temporary_file, file_name)
    except (ContentTooShortError, exceptions.RequestException, TimeoutError):
        if temporary_file is not None and os.path.exists(temporary_file):
          os.remove(temporary_file)
        max_retry = self.config.get_config_dict_attr("$.download.max_retry")
        if retry_times >= max_retry:
          raise
        return self.auto_down(
          url,
          fp,
          fn,
          retry_times + 1,
          headers=headers,
          proxies=proxies,
          timeout=timeout,
        )
    finally:
      if response is not None and hasattr(response, "close"):
        response.close()

##
## >>================================ public method ===============================>>
##
downloader = None
_downloader_lock = Lock()


def get_live_downloader():
  global downloader
  if downloader is None:
    with _downloader_lock:
      if downloader is None:
        downloader = DouyinLiveDownloader()
  return downloader


def download_single_live(url):
  downloader = get_live_downloader()
  ##
  ## construct live downloader
  ##
  if downloader.config.get_config_dict_attr("$.server.debug_mode") is True:
    downloader.dump_config()
  
  ##
  ## start download live
  ##  
  try:
    return downloader.run({"url": url})
  except Exception as e:
    raise e

def download_multiple_live_with_patrolman():
  downloader = get_live_downloader()
  ##
  ## construct live downloader
  ##
  if downloader.config.get_config_dict_attr("$.server.debug_mode") is True:
    downloader.dump_config()

  ##
  ## get live url list
  ##
  live_url_list = downloader.url_list.get_config_list("live")
  for url in live_url_list:
    item = ListenerItem(func=downloader.run, args=({"url": url},))
    downloader.live_douyin_listener.add_sub_task(item)
    if downloader.live_douyin_listener.is_patrolman_actived() is not True:
      downloader.live_douyin_listener.start()

def download_multiple_live(token_list:list):
  downloader = get_live_downloader()
  ##
  ## construct live downloader
  ##
  if downloader.config.get_config_dict_attr("$.server.debug_mode") is True:
    downloader.dump_config()

  ##
  ## get live url list
  ##
  for token in token_list:
    item = ListenerItem(func=downloader.run, args=(token,))
    item.start_item()

##
## >>================================ test method ===============================>>
##

##
## download live stream by database
##
def download_live_stream_by_score():
  downloader = get_live_downloader()
  token = dict()
  if downloader.config.get_config_dict_attr("$.server.debug_mode") is True:
    downloader.dump_config()
  favorite_list = downloader.database.get_douyin_favorite_live_url()
  for url in favorite_list:
    token["url"] = url[0]
    token["score"] = None
    token["favorite"] = False
    item = ListenerItem(func=downloader.run, args=(token.copy(),))
    token.clear()
    downloader.live_douyin_listener.add_sub_task(item)
    if downloader.live_douyin_listener.is_patrolman_actived() is not True:
      downloader.live_douyin_listener.start()
##
## test: download a live stream by url
##
def download_live_test():
  downloader = get_live_downloader()
  if downloader.config.get_config_dict_attr("$.server.debug_mode") is True:
    downloader.dump_config()
  live_url_list = downloader.url_list.get_config_list("live")
  for url in live_url_list:
    try:
      downloader.run({"url": url})
      # if downloader.config.get_config_dict_attr("$.max_thread") <= total_live_number and downloader.config.get_config_dict_attr("$.max_thread") != 0:
      break
    except Exception:
      continue
    
if __name__ == "__main__":
  # download_live()
  # download_live_test()
  download_live_stream_by_score()
