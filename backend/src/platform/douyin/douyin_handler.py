##>> Test
import os
import sys
sys.path.append(os.getcwd())
##<< Test

## <<Base>>
from requests import request

## <<Third-Part>>
from backend.src.library.baselib                        import get_dict_attr, set_dict_attr
from backend.src.platform.douyin.douyin_api             import DouyinApi
from backend.src.platform.douyin.douyin_live_downloader import download_multiple_live
from backend.src.base.log                               import get_logger

##
## handler douyin live url
##
def douyin_live_handler(url):
  get_logger().info("[douyin] progressing: {}".format(url))
  if url is None:
    get_logger().error("invalid url")
    raise ValueError
  
  pass

##
## handle douyin user main page url
##
def douyin_user_main_page_handler(url):
  get_logger().info("[douyin] progressing: {}".format(url))
  if url is None:
    get_logger().error("invalid url")
    raise ValueError
  
  pass

##
## handle douyin video post url
##
def douyin_video_post_handler(url):
  get_logger().info("[douyin] progressing: {}".format(url))
  if url is None:
    get_logger().error("invalid url")
    raise ValueError
  
  pass

##
## check if the url is a douyin live url
##
def is_douyin_live_url(url):
  
  ##
  ## check if the url is valid
  ##
  if url is None:
    get_logger().error("invalid url")
    raise ValueError
  
  ##
  ## create douyin api
  ##
  api = DouyinApi()
  
  ##
  ## compare the url with the api
  ##
  if api.get_config_dict_attr("$.LIVE_DOMAIN") in url or \
    api.get_config_dict_attr("$.LIVE_DOMAIN2") in url:
    return True
  return False  

##
## 解析抖音分享链接
## 确定是哪种类型的分享链接
## 1. 作品
## 2. 直播
## 3. 用户主页
##

def douyin_handler(token_list:list):
  if token_list is None:
    get_logger().error("invalid url list")
    raise ValueError
  
  live_token_list = list()
  
  ##
  ## token["url"]: str
  ## token["score"]: int
  ##
  for token in token_list:
    url = get_dict_attr(token, "$.url")
    if url is None:
      get_logger().error("invalid url")
      continue
    ##
    ## query url
    ##
    response = request('GET', url)
    if response.status_code != 200:
      get_logger().error("request failed")
      continue

    ##
    ## compare the user with the api
    ##
    try:
      if is_douyin_live_url(response.url):
        live_token_list.append(token)
    except Exception as e:
      get_logger().error("{}".format(e))
      continue
    
    ##
    ## start multiple thread to download living
    ##
    try:
      download_multiple_live(live_token_list)
    except Exception as e:
      get_logger().error("download multiple live failed! {}".format(e))
      return
  
  return

##
## test
##
if __name__ == "__main__":
  urls = [
    "https://v.douyin.com/i5rWLJWc/"
  ]
  
  for url in urls:
    douyin_handler(url)
##<< Test