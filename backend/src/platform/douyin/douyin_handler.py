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
from backend.src.platform.douyin.douyin_aweme_downloader import download_multiple_aweme
from backend.src.platform.douyin.douyin_aweme_url       import classify_aweme_url
from backend.src.platform.douyin.douyin_live_downloader import download_multiple_live
from backend.src.library.loglib                         import get_logger

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

def douyin_handler(token:dict, context:dict=None):
  """Follow one share link and route what it turns out to be.

  ``context`` carries the dependencies of *this* dispatch - currently the
  task-aware post runner - and is deliberately a separate argument rather than
  another key in ``token``.  The token is user data: it is copied, logged and
  handed to downloaders, and a service object travelling inside it would end up
  somewhere it has no business being.  Omitting it keeps the legacy behaviour,
  so existing callers and scripts are unaffected.
  """
  if token is None:
    get_logger().error("invalid url list")
    raise ValueError

  live_token_list  = list()
  aweme_token_list = list()

  ##
  ## token["url"]: str
  ## token["score"]: int
  ##
  url = get_dict_attr(token, "$.url")
  if url is None:
    get_logger().error("invalid url")
    return
  ##
  ## query url
  ##
  ## The share link is followed once, here, and both branches below read the
  ## resolved url.  Neither classification costs an extra request.
  ##
  ##
  ## The status of that last hop is deliberately not a gate.  Only ``response.url``
  ## is read below - the body is never touched - and redirects have already been
  ## followed by the time we get here, so the link is resolved whatever the final
  ## page answers.  Douyin serves a share link opened outside the app with 444
  ## after redirecting perfectly well, which a ``!= 200`` check turned into
  ## "pasted a link, nothing downloaded" for every image post shared that way.
  ##
  ## A link that genuinely leads nowhere still stops below, where the resolved url
  ## fails to classify and is reported together with this status.
  ##
  response = request('GET', url)

  ##
  ## sort the resolved url into a live room or a single post
  ##
  try:
    if is_douyin_live_url(response.url):
      live_token_list.append(token)
    elif classify_aweme_url(response.url) is not None:
      ##
      ## Hand the resolved url and id down with the token.  The share link was
      ## already followed above, and a short link carries no id of its own, so
      ## without this the post path would have to spend a second request
      ## rediscovering what is already known here.
      ##
      aweme_token = token.copy()
      set_dict_attr(aweme_token, "$.resolved_url", response.url)
      set_dict_attr(aweme_token, "$.aweme_id", classify_aweme_url(response.url))
      aweme_token_list.append(aweme_token)
    else:
      ##
      ## user home pages and anything unrecognised land here.  This used to be a
      ## silent drop, which left "I pasted a link and nothing happened" with no
      ## trace to follow.
      ##
      get_logger().warning(
        "no douyin handler for resolved url {} (from {}, status {})".format(
          response.url,
          url,
          response.status_code,
        )
      )
      return
  except Exception as e:
    get_logger().error("{}".format(e))
    return

  ##
  ## start multiple thread to download living
  ##
  if live_token_list:
    try:
      download_multiple_live(live_token_list)
    except Exception as e:
      get_logger().error("download multiple live failed! {}".format(e))
      return

  ##
  ## submit single posts to the post pool
  ##
  if aweme_token_list:
    ##
    ## Only now is the link known to be a post, which is why the task is created
    ## here and not when the request arrived: a live link or a profile link
    ## reaching this function would otherwise have already produced a post task
    ## that describes work nobody is doing.
    ##
    runner = context.get("direct_post_service") if context else None
    try:
      if runner is not None:
        for aweme_token in aweme_token_list:
          runner.submit(aweme_token)
      else:
        download_multiple_aweme(aweme_token_list)
    except Exception as e:
      get_logger().error("download multiple aweme failed! {}".format(e))
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