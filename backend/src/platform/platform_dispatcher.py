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
from backend.src.base.config import BaseConfig
from backend.src.platform.douyin.douyin_handler import douyin_handler

# 定义一个事件分发器
class PlatformDispatcher:
##
## >>============================= attribute =============================>>
##
  __event_list      = ['douyin', 'other']
  __handler_dict    = {'douyin': douyin_handler, 'other':None}

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
      print("ERROR: invalid attribute of registered handler")
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
    ## max thread
    ##
    base_config = BaseConfig()
    max_thread = base_config.get_config_dict_attr("$.max_thread")
    
    
    ##
    ## register handler
    ## TODO max_threads
    ##
    for event, handler in self.__handler_dict.items():
      self.__platform_register_handler(event, handler, max_thread)

  ##
  ## dispatch event
  ##
  def dispatch(self, urls:list):
    ##
    ## split urls
    ##
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
            url_dict.get(event).append(url)
      except:
        print("ERROR: Invalid domain: {}".format(domain))
        event = 'other'

    ##
    ## dispatch event
    ##
    for event, url_list in url_dict.items():
      if self.handlers.get(event) is not None:
        ##
        ## dispatch event
        ##
        print("INFO: dispatching event: {}".format(event))
        
        
        ##
        ## submit handler
        ##
        self.executors[event].submit(self.handlers[event], url_list)
      else:
        print("ERROR: Invalid event: {}".format(event))

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
  print("主线程继续运行...")