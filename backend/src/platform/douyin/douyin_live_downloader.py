##>> Test
import os
import sys
sys.path.append(os.getcwd())
from re import compile
##<< Test

## <<Base>>
from random import randint
from time import monotonic, sleep
from pathlib import Path
from requests import request
from threading import Lock
from datetime import datetime

## <<Extension>>
import yaml as yml

## <<Third-Part>>
from backend.src.library.baselib                            import set_dict_attr, get_dict_attr, output_dict, save_dict_as_file
from backend.src.base.downloader                            import Downloader
from backend.src.base.file_fetcher                          import ON_EXISTS_UNIQUE, fetch_file
from backend.src.platform.douyin.douyin_header              import DouyinShareHeader, DouyinLiveInfoHeader
from backend.src.platform.douyin.douyin_live_config         import DouyinLiveConfig
from backend.src.platform.douyin.douyin_login               import DouyinLogin
from backend.src.platform.douyin.douyin_live_external_info  import LiveExternal, observed_at
from backend.src.platform.douyin.douyin_live_prober         import DouyinLiveProber
from backend.src.database.table.person_identity              import DouyinPersonIdentityTable
from backend.src.platform.douyin.douyin_owner_directory      import choose_owner_directory
from backend.src.platform.douyin.hls_recorder               import HlsRecorder
from backend.src.platform.douyin.douyin_api                 import DouyinApi
from backend.src.database.table.share_url                   import DouyinShareUrlTable
from backend.src.database.table.table_import                import import_douyin_live_info_to_database
from backend.src.database.schema_guard                      import DatabaseWriteBlocked, get_schema_guard, initialize_schema_guard
from backend.src.library.configlib                          import load_config
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
    self._person_database = None
    self._database_warning_state = None
    self._database_clock = monotonic
    self._database_retry_at = 0.0
    self._database_retry_seconds = 30.0
    self.hls_recorder = HlsRecorder()
    self._actived_task_number = 0
    self._lock = Lock()
    self.construct_aggregation_class(config)

  @staticmethod
  def _reserve_hls_output_path(save_path, file_name):
    directory = Path(save_path)
    duplicate_index = None
    while True:
      prefix = "" if duplicate_index is None else "re_{}_".format(
        duplicate_index
      )
      output_path = directory / (prefix + file_name)
      try:
        output_path.touch(exist_ok=False)
        return output_path
      except FileExistsError:
        duplicate_index = (
          0 if duplicate_index is None else duplicate_index + 1
        )

  def __request_file__(
    self,
    method: str,
    share_url: str,
    url: str,
    save_path: str,
    file_name: str,
    nickname: str,
    stream: bool,
    protocol: str,
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
      get_logger().info(
        "\tpath:{}\n\tmethod:{}\n\tprotocol:{}\n\tstream:{}\n\ttimeout:{}".format(
          save_path + "/" + file_name,
          method,
          protocol,
          stream,
          timeout,
        )
      )
      get_logger().info("当前总下载数：{}".format(self._actived_task_number))

      ##
      ## create directory
      ##
      if not os.path.exists(save_path):
          get_logger().info("create directory {}".format(save_path))
          os.makedirs(save_path, exist_ok=True)
      
      ##
      ## download live stream
      ##
      if self.config.get_config_dict_attr("$.download.test_mode") is True:
        get_logger().info("test mode enabled, skip live stream data download")
      else:
        if protocol == "hls":
          output_path = self._reserve_hls_output_path(save_path, file_name)
          get_logger().info("HLS output reserved: {}".format(output_path))
          stall_timeout = self.config.get_config_dict_attr(
            "$.platform.douyin.live.hls_stall_timeout"
          )
          if stall_timeout is None:
            stall_timeout = max(30, timeout * 3)
          terminate_grace = self.config.get_config_dict_attr(
            "$.platform.douyin.live.hls_terminate_grace"
          )
          if terminate_grace is None:
            terminate_grace = 5
          try:
            self.hls_recorder.record(
              url,
              output_path,
              headers=headers,
              proxies=proxies,
              max_retry=self.config.get_config_dict_attr("$.download.max_retry"),
              io_timeout=timeout,
              stall_timeout=stall_timeout,
              terminate_grace=terminate_grace,
            )
          except BaseException:
            try:
              if output_path.stat().st_size == 0:
                output_path.unlink()
            except BaseException:
              pass
            raise
        else:
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
      get_logger().error(
        "\tname:{}\n\tpath:{}\n\tprotocol:{}\n\tdownload failed!!!\n".format(
          nickname,
          save_path + "/" + file_name,
          protocol,
        )
      )
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
        get_logger().info(
          "name:{} \nprotocol:{} \ndownload complete!\n".format(
            nickname,
            protocol,
          )
        )
      else:
        get_logger().info(
          "name:{} \nprotocol:{} \ndownload stopped!\n".format(
            nickname,
            protocol,
          )
        )
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
      self.live_external_info   = LiveExternal()
      self.live_douyin_listener = DouyinLiveListener()
      self.prober               = DouyinLiveProber(self)
      self._lock                = Lock()
      
      self._database_if_ready()

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

  def run(self, token) -> None:
    
    ##
    ## get url from token
    ##
    url = get_dict_attr(token, "$.url")
    if url is None:
      get_logger().error("invalid url")
      raise ValueError

    ##
    ## download task should be blocked if the number >= max task
    ## TODO
    ##
    ##
    ## attempt attribute for thread
    ##
    build                = dict()
    summary              = dict()
    stream_url           = str()
    stream_name          = str()

    ##
    ##<<=================== resolve share url and read status ==================>>
    ##
    ## The probe owns both platform requests and the live status check.  Expected
    ## failures (timeout, non-200, forbidden payload) come back as an
    ## unsuccessful result and end this run exactly like the inline handling did;
    ## unexpected ones still propagate.
    ##
    probe = self.prober.probe(url)
    if probe.ok is not True:
      return None

    live_response        = probe.response
    live_response_dict   = probe.payload
    room_status          = probe.room_status
    header               = probe.headers

    set_dict_attr(build,   "$.share_info",     probe.share_info)
    set_dict_attr(build,   "$.live_payload",   probe.live_payload)
    set_dict_attr(summary, "$.share_url",      url)
    set_dict_attr(summary, "$.nickname",       probe.nickname)
    set_dict_attr(summary, "$.directory_name", probe.directory_name)
    
    try:
      ##
      ## get live stream flv url and stream name
      ##
      if room_status == 2:
        stream_source = self.live_external_info.get_live_stream_source(
          live_response,
          self.config.get_config_dict_attr("$.platform.douyin.live.flv_clarity"),
          self.config.get_config_dict_attr("$.platform.douyin.live.hls_clarity"),
        )
        stream_url = stream_source.url
        stream_name = stream_source.file_name
        set_dict_attr(summary, "$.stream_url", stream_source.url)
        set_dict_attr(summary, "$.stream_name", stream_source.file_name)
        set_dict_attr(summary, "$.stream_protocol", stream_source.protocol)
        
        ##
        ## output debug information
        ##
        if self.config.get_config_dict_attr("$.server.debug_mode") is True:
          get_logger().info(
            "stream protocol:{}\nstream name:{}".format(
              stream_source.protocol,
              stream_name,
            )
          )
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
      if self._database_if_ready() is not None:
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
          self._mark_database_unavailable()

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

    ##
    ## keep the history list's live status cache aligned with the snapshot that
    ## was just imported, reusing the payload timestamp room_base is keyed on
    ##
    self.database.update_live_status_cache(
      owner_user_id=owner_user_id,
      last_live_status=room_status,
      last_checked_at=observed_at(live_response_dict),
      last_room_id=get_dict_attr(live_response_dict, "$.data.room.id"),
    )

    favorite = get_dict_attr(token, "$.favorite")
    score = get_dict_attr(token, "$.score")
    if favorite is True and score is not None:
      if self.database.is_owner_score_record_exist(owner_user_id) is False:
        self.database.insert_owner_score(owner_user_id=owner_user_id, score=score)
      else:
        origin_score = self.database.get_owner_score_by_user_id(owner_user_id)
        if origin_score != int(score):
          self.database.update_owner_score(owner_user_id, score)

  def _new_database(self):
    return DouyinShareUrlTable(
      host=self.config.get_config_dict_attr("$.database.host"),
      user=self.config.get_config_dict_attr("$.database.username"),
      passwd=self.config.get_config_dict_attr("$.database.password"),
      database=self.config.get_config_dict_attr("$.database.name"),
    )

  def _mark_database_unavailable(self):
    self.database = None
    self._database_retry_at = (
      self._database_clock() + self._database_retry_seconds
    )

  def _identity_count(self, directory_name) -> int:
    """How many distinct identities file under ``directory_name``.

    Answers 1 when it cannot be known: an unknown count must not invent a
    collision that would append a discriminator nobody asked for.
    """
    if not directory_name:
      return 1
    database = self._person_database_for_read()
    if database is None:
      return 1
    try:
      return max(
        1,
        database.count_identities_using_directory_name(directory_name),
      )
    except Exception as e:
      get_logger().warning("identity count failed, assume unique: {}".format(e))
      return 1

  def _person_folder(self, owner_user_id: str):
    """Return this owner's person folder and discriminating id, or ``None``.

    Every failure answers ``None``.  A recording is the thing that cannot be
    repeated - the stream is live now - so nothing about who this owner is may
    ever stand between it and starting.
    """
    if not owner_user_id:
      return None
    database = self._person_database_for_read()
    if database is None:
      return None
    try:
      return database.find_person_folder(owner_user_id)
    except Exception as e:
      get_logger().warning(
        "person directory lookup failed, use the owner's own: {}".format(e)
      )
      return None

  def _person_database_for_read(self):
    """Lazily hold a person table handle, sharing the process-wide pool."""
    if self._person_database is not None:
      return self._person_database
    if self.config.get_config_dict_attr("$.database.enable") is not True:
      return None
    try:
      self._person_database = DouyinPersonIdentityTable(
        host=self.config.get_config_dict_attr("$.database.host"),
        user=self.config.get_config_dict_attr("$.database.username"),
        passwd=self.config.get_config_dict_attr("$.database.password"),
        database=self.config.get_config_dict_attr("$.database.name"),
      )
    except Exception as e:
      get_logger().warning("person table unavailable: {}".format(e))
      return None
    return self._person_database

  def _database_for_read(self):
    if self.database is not None:
      return self.database
    if self.config.get_config_dict_attr("$.database.enable") is not True:
      return None
    if self.database is None:
      now = self._database_clock()
      if now < self._database_retry_at:
        return None
      try:
        self.database = self._new_database()
        self._database_retry_at = 0.0
        if self._database_warning_state == "unavailable":
          self._database_warning_state = None
      except Exception:
        self._mark_database_unavailable()
        if self._database_warning_state != "unavailable":
          get_logger().warning(
            "database unavailable, continue live download without database reads"
          )
          self._database_warning_state = "unavailable"
    return self.database

  def _database_if_ready(self):
    if self.config.get_config_dict_attr("$.database.enable") is not True:
      return None
    guard = get_schema_guard()
    if guard is not None:
      try:
        guard.require_write_ready()
      except DatabaseWriteBlocked:
        snapshot = guard.snapshot
        state = "blocked" if snapshot is None else snapshot.state.value
        if self._database_warning_state != state:
          get_logger().warning(
            "database persistence is {}, continue live download".format(state)
          )
          self._database_warning_state = state
        return None
    return self._database_for_read()

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

  def pause(self):
    """Random 1.5s-4.5s gap between two platform requests.

    Kept here, next to ``query_url``, so both network primitives live in one
    module.  The probe sequence calls back into these rather than importing
    ``request``/``sleep`` itself.
    """
    sleep(randint(15, 45) * 0.1)

  def download_live_stream(self, url: str, params: dict = None, headers=None):
    
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
    ## Resolve the owner folder.  The naming policy is shared with the post path -
    ## see douyin_owner_directory for what it corrects and why - so this only
    ## fetches the two inputs it needs and keeps the existing fallback: a database
    ## problem must not stop a recording, it just costs the correction.
    ##
    nickname_directory = get_dict_attr(params, "$.summary.directory_name")
    owner_user_id = get_dict_attr(
      params,
      "$.external_info.data.room.owner_user_id",
    )
    ##
    ## Asked independently of the record table: whether this owner is a marked
    ## person has nothing to do with whether share_url is readable, and the
    ## recordings have to land beside that person's posts either way.
    ##
    person = self._person_folder(owner_user_id)
    person_directory = person["directory_name"] if person else None
    person_owner = person["main_owner_user_id"] if person else None
    directory_name = choose_owner_directory(
      nickname_directory,
      person_directory=person_directory,
      person_owner_user_id=person_owner,
      owner_count=self._identity_count(person_directory),
    )
    database = self._database_for_read()
    if database is not None:
      try:
        recorded = None
        if database.is_owner_user_id_record_exist(owner_user_id) is True:
          recorded = database.get_directory_name_by_owner_user_id(owner_user_id)
        ##
        ## A marked owner is counted by identity, so the person's own accounts -
        ## which all record the same folder - do not read as a collision.
        ##
        owners = (
          self._identity_count(person_directory) if person_directory
          else database.count_owners_using_directory_name(
            recorded or nickname_directory
          )
        )
        directory_name = choose_owner_directory(
          nickname_directory,
          recorded_directory=recorded,
          owner_user_id=owner_user_id,
          owner_count=owners,
          person_directory=person_directory,
          person_owner_user_id=person_owner,
        )
        if directory_name != nickname_directory:
          get_logger().info(
            "owner {} records under {} rather than {} (recorded={}, owners={})".format(
              owner_user_id,
              directory_name,
              nickname_directory,
              recorded,
              owners,
            )
          )
      except Exception as e:
        get_logger().warning(
          "database directory lookup failed, use live nickname: {}".format(e)
        )
        self._mark_database_unavailable()
        directory_name = choose_owner_directory(
          nickname_directory,
          person_directory=person_directory,
          person_owner_user_id=person_owner,
        )
    save_dir    = self.config.get_config_dict_attr("$.download.save_path")+"/douyin/" + self.config.get_config_dict_attr("$.platform.douyin.download.type") + "/" + directory_name
    
    ##
    ## if tick_naming
    ##
    stream_name = get_dict_attr(params, "$.summary.stream_name")
    stream_protocol = get_dict_attr(params, "$.summary.stream_protocol") or "flv"
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
          stream_protocol,
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
    """Fetch a live stream file, keeping every session as its own file.

    ``retry_times`` is how many attempts the caller has already spent, so the
    remaining budget is what is left of ``$.download.max_retry``.
    """
    max_retry = self.config.get_config_dict_attr("$.download.max_retry")
    remaining_retry = max(0, max_retry - retry_times)
    return fetch_file(
      url,
      fp,
      fn,
      headers=headers,
      proxies=proxies,
      timeout=timeout,
      max_retry=remaining_retry,
      on_exists=ON_EXISTS_UNIQUE,
    )

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


def cancel_live_downloads() -> None:
  with _downloader_lock:
    existing_downloader = downloader
    if existing_downloader is not None:
      existing_downloader.hls_recorder.cancel_all()


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

def download_multiple_live_with_patrolman(urls: list[str]):
  downloader = get_live_downloader()
  ##
  ## construct live downloader
  ##
  if downloader.config.get_config_dict_attr("$.server.debug_mode") is True:
    downloader.dump_config()

  for url in urls:
    item = ListenerItem(func=downloader.run, args=({"url": url},))
    downloader.live_douyin_listener.add_sub_task(item)
  if urls and downloader.live_douyin_listener.is_patrolman_actived() is not True:
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
  database = downloader._database_for_read()
  if database is None:
    get_logger().warning("database unavailable, skip score-based URL lookup")
    return
  favorite_list = database.get_douyin_favorite_live_url()
  for url in favorite_list:
    token["url"] = (
      url.get("live_share_url") if isinstance(url, dict) else url[0]
    )
    token["score"] = None
    token["favorite"] = False
    item = ListenerItem(func=downloader.run, args=(token.copy(),))
    token.clear()
    downloader.live_douyin_listener.add_sub_task(item)
    if downloader.live_douyin_listener.is_patrolman_actived() is not True:
      downloader.live_douyin_listener.start()


def run_score_download_entrypoint():
  config = load_config()
  initialize_schema_guard(config)
  download_live_stream_by_score()
##
## test: download a live stream by url
##
def download_live_test(urls: list[str]):
  downloader = get_live_downloader()
  if downloader.config.get_config_dict_attr("$.server.debug_mode") is True:
    downloader.dump_config()
  for url in urls:
    downloader.run({"url": url})
    
if __name__ == "__main__":
  # download_live()
  # download_live_test()
  run_score_download_entrypoint()
