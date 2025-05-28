##>> Test
import os
import sys
sys.path.append(os.getcwd())
##<< Test

##
## <<Base>>
##
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import urlparse

##
## <<Third-Part>>
##
from backend.src.library.baselib import set_dict_attr
from backend.src.base.config import BaseConfig
from backend.src.platform.douyin.douyin_handler import douyin_handler
from backend.src.platform.other.other_handler import other_handler
from backend.src.base.log import get_logger

# 定义一个事件分发器
class PlatformDispatcher:
##
## >>============================= attribute =============================>>
##
  __event_list      = ['douyin', 'other']
  __handler_dict    = {'douyin': douyin_handler, 'other':other_handler}

##
## >>============================= private method =============================>>
##
  def __init__(self):
    self.handlers  = dict()
    self.executors = dict()

  ##
  ## other register handler
  ##
  def __handle_other(self, url):
    pass

  ##
  ## register handler
  ##
  def __platform_register_handler(self, event, handler, max_threads=1):
    
    ##
    ## check attribute
    ##
    if event is None or handler is None:
      get_logger().error("invalid attribute of registered handler")
      raise ValueError

    ##
    ## initialize handler
    ##
    self.handlers[event] = handler
    
    ##
    ## initialize executor
    ##
    self.executors[event] = ThreadPoolExecutor(max_workers=max_threads)

##
## >>============================= abstract method =============================>>
##

##
## >>============================= sub class method =============================>>
##
  def register(self):
    ##
    ## register handler
    ## TODO max_threads
    ##
    for event, handler in self.__handler_dict.items():
      self.__platform_register_handler(event, handler, 1)

  ##
  ## dispatch event
  ##
  def dispatch(self, jsonData=None):
    ##
    ## extended data related to the event
    ##
    token = dict()
    
    ##
    ## check attribute
    ##
    if jsonData is None:
      get_logger().error("invalid attribute of dispatch")
      raise ValueError
    
    ##
    ## split jsonData
    ##
    urls = jsonData.get('urls')
    if urls is None:
      get_logger().error("invalid attribute of urls")
      raise ValueError
    if not isinstance(urls, list):
      get_logger().error("invalid attribute of urls")
      raise ValueError
    if len(urls) == 0:
      get_logger().error("invalid attribute of urls")
      raise ValueError
    
    url_dict = {item:list() for item in self.__event_list}
    
    for url in urls:
      
      ##
      ## extract domain
      ##
      domain = urlparse(url).netloc

      ##
      ## check domain and create event
      ##
      try:
        for event in self.__event_list:
          if event in domain:
            
            ##
            ## set extended data
            ##
            set_dict_attr(token, "$.url", url)
            set_dict_attr(token, "$.score", jsonData.get('score'))
            set_dict_attr(token, "$.favorite", jsonData.get('favorite'))
            
            ##
            ## tail insert extended data into url_dict list
            ##
            url_dict.get(event).append(token.copy())
      except:
        get_logger().error("invalid domain: {}".format(domain))
        event = 'other'
      token.clear()

    ##
    ## dispatch event
    ##
    for event, token_list in url_dict.items():
      if self.handlers.get(event) is not None:
        ##
        ## dispatch event
        ##
        get_logger().info("dispatching event: {}".format(event))
        
        
        ##
        ## submit handler
        ##
        self.executors[event].submit(self.handlers[event], token_list)
      else:
        get_logger().error("invalid event: {}".format(event))

##
## >>================================ test method ===============================>>
##

##
## >>================================ main method ===============================>>
##

if __name__ == "__main__":
  ##
  ## register dispatcher
  ##
  dispatcher = PlatformDispatcher()
  dispatcher.register()

  ##
  ## test urls
  ##
  urls = [
      "https://www.douyin.com/video/1",
      "https://www.douyin.com/video/2",
      "https://www.douyin.com/video/3",
      "https://www.bilibili.com/video/BV1",
      "https://www.bilibili.com/video/BV2",
      "https://www.bilibili.com/video/BV3",
      "https://www.bilibili.com/video/BV4",
      "https://www.example.com/page1",
      "https://www.example.com/page2",
  ]

  # 分发处理链接
  for url in urls:
      dispatcher.dispatch(url)

  # 主线程继续执行其他任务
  get_logger().info("主线程继续运行...")