## <<Base>>
import os
from pathlib import Path
import sys
sys.path.append(os.getcwd())

## <<Extension>>

## <<Third-part>>
from src.base.config import BaseConfig, DEFAULT_BASE_CONFIG_PATH

class DouyinConfig(BaseConfig):

  '''
super:
  save_path: /mnt/nvme2/vedio
  max_thread: 0
  folderize: True
  config_directory: config
  stream_platform: douyin
  build_directory: build
  login: True
  save_response: True
  headers_file: headers.yml
  download_file: download.yml
  base_config_directory: /mnt/nvme/CodeSpace/OpenSource/TikTokDownload/config
  platform_config_path: /mnt/nvme/CodeSpace/OpenSource/TikTokDownload/config/douyin
  header_config_path: /mnt/nvme/CodeSpace/OpenSource/TikTokDownload/config/douyin/headers.yml
  download_config_path: /mnt/nvme/CodeSpace/OpenSource/TikTokDownload/config/douyin/download.yml
  build_path: /mnt/nvme/CodeSpace/OpenSource/TikTokDownload/config/build
sub-class:
  login_config_file: login.yml
  type: post
  post_download_config_file: post.yml
  live_download_config_file: live.yml
  share_url_file: conf.ini
  api: {'DOUYIN_DOMAIN': 'https://www.douyin.com', 'IESDOUYIN_DOMAIN': 'https://www.iesdouyin.com', 'LIVE_DOMAIN': 'https://live.douyin.com', 'LIVE_DOMAIN2': 'https://webcast.amemv.com', 'SSO_DOMAIN': 'https://sso.douyin.com', 'WEBCAST_WSS_DOMAIN': 'wss://webcast5-ws-web-lf.douyin.com', 'TAB_FEED': 'https://www.douyin.com/aweme/v1/web/tab/feed/', 'USER_SHORT_INFO': 'https://www.douyin.com/aweme/v1/web/im/user/info/', 'USER_DETAIL': 'https://www.douyin.com/aweme/v1/web/user/profile/other/', 'BASE_AWEME': 'https://www.douyin.com/aweme/v1/web/aweme/', 'USER_POST': 'https://www.douyin.com/aweme/v1/web/aweme/post/', 'LOCATE_POST': 'https://www.douyin.com/aweme/v1/web/locate/post/', 'POST_SEARCH': 'https://www.douyin.com/aweme/v1/web/general/search/single/', 'POST_DETAIL': 'https://www.douyin.com/aweme/v1/web/aweme/detail/', 'USER_FAVORITE_A': 'https://www.douyin.com/aweme/v1/web/aweme/favorite/', 'USER_FAVORITE_B': 'https://www.iesdouyin.com/web/api/v2/aweme/like/', 'USER_FOLLOWING': 'https://www.douyin.com/aweme/v1/web/user/following/list/', 'USER_FOLLOWER': 'https://www.douyin.com/aweme/v1/web/user/follower/list/', 'MIX_AWEME': 'https://www.douyin.com/aweme/v1/web/mix/aweme/', 'USER_HISTORY': 'https://www.douyin.com/aweme/v1/web/history/read/', 'USER_COLLECTION': 'https://www.douyin.com/aweme/v1/web/aweme/listcollection/', 'USER_COLLECTS': 'https://www.douyin.com/aweme/v1/web/collects/list/', 'USER_COLLECTS_VIDEO': 'https://www.douyin.com/aweme/v1/web/collects/video/list/', 'USER_MUSIC_COLLECTION': 'https://www.douyin.com/aweme/v1/web/music/listcollection/', 'FRIEND_FEED': 'https://www.douyin.com/aweme/v1/web/familiar/feed/', 'FOLLOW_FEED': 'https://www.douyin.com/aweme/v1/web/follow/feed/', 'POST_RELATED': 'https://www.douyin.com/aweme/v1/web/aweme/related/', 'FOLLOW_USER_LIVE': 'https://www.douyin.com/webcast/web/feed/follow/', 'LIVE_INFO': 'https://live.douyin.com/webcast/room/web/enter/', 'LIVE_INFO_ROOM_ID': 'https://webcast.amemv.com/webcast/room/reflow/info/', 'LIVE_USER_INFO': 'https://live.douyin.com/webcast/user/me/', 'SUGGEST_WORDS': 'https://www.douyin.com/aweme/v1/web/api/suggest_words/', 'SSO_LOGIN_GET_QR': 'https://sso.douyin.com/get_qrcode/', 'SSO_LOGIN_CHECK_QR': 'https://sso.douyin.com/check_qrconnect/', 'SSO_LOGIN_CHECK_LOGIN': 'https://sso.douyin.com/check_login/', 'SSO_LOGIN_REDIRECT': 'https://www.douyin.com/login/', 'SSO_LOGIN_CALLBACK': 'https://www.douyin.com/passport/sso/login/callback/', 'POST_COMMENT': 'https://www.douyin.com/aweme/v1/web/comment/list/', 'POST_COMMENT_PUBLISH': 'https://www.douyin.com/aweme/v1/web/comment/publish', 'POST_COMMENT_DELETE': 'https://www.douyin.com/aweme/v1/web/comment/delete/', 'POST_COMMENT_DIGG': 'https://www.douyin.com/aweme/v1/web/comment/digg'}
  '''
  ##
  ## Attribute
  ##
  login_config_path = None
  post_config_path  = None
  live_config_path  = None
  share_url_path    = None

  ##
  ## The part of extension
  ##
  __config                 = dict()

  ##
  ## Initialize douyin live config
  ##
  def __init__(self, path: Path = None):
    if path is None:
      print("WARNNING: Invalid input, will use default config path")
      path = Path(DEFAULT_BASE_CONFIG_PATH)
    
    ##
    ## Initialize super
    ##
    self.BASE_CONFIG_FILE = path
    super().__init__(self.BASE_CONFIG_FILE)

    ##
    ## Parse download config
    ##
    self.__config = self.parse_config(path=Path(self.download_config_path))

    ##
    ## Transform dict to attribute
    ##
    self.__dict__.update(self.__config)
    
    ##
    ## Construct new config path according download config
    ##
    self.__construct_douyin_download_config()

  ##
  ## Construct next level config path
  ##
  def __construct_douyin_download_config(self):
    self.login_config_path = self.platform_config_path + "/" + self.login_config_file
    self.post_config_path  = self.platform_config_path + "/" + self.post_download_config_file
    self.live_config_path  = self.platform_config_path + "/" + self.live_download_config_file
    self.share_url_path    = self.platform_config_path + "/" + self.share_url_file

    self.__config["login_config_path"] = self.login_config_path
    self.__config["post_config_path"]  = self.post_config_path
    self.__config["live_config_path"]  = self.live_config_path
    self.__config["share_url_path"]    = self.share_url_path

  ##
  ## Transform config to dict
  ##
  def to_dict(self) -> dict:
    return self.__config
  
  ##
  ## Transform dict to attribute
  ##
  def dict_to_attr(self, dic:dict = None):
    if dict is None:
      print("ERROR: Invalid input dict")
      return
    pass

  ##
  ##  Dump config
  ##
  def dump_config(self,):
    super().dump_config()

    print("Douyin config:")
    for k,v in self.__config.items():
      print("\t{}: {}".format(k,v))

if __name__ == "__main__":
  post_config = DouyinConfig()
  post_config.dump_config()
  # post_config.save_config(Path(post_config.build_path + "/" + post_config.stream_platform + "/" + "douyin_config.yml"))