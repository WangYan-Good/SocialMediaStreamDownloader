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

"""Platform dispatcher to handle different social media platforms"""

class PlatformDispatcher:
##
## >>============================= attribute =============================>>
##
  __event_list      = ['douyin', 'other']
  __handler_dict    = {'douyin': douyin_handler, 'other':other_handler}
  
  def __init__(self):
    self.handlers  = dict()
    self.executors = dict()
  
  def shutdown(self):
    """Shutdown all thread executors to free resources"""
    for event, executor in self.executors.items():
      try:
        executor.shutdown(wait=True)  # Wait for tasks to complete
        get_logger().info(f"Executor for event {event} has been shut down")
      except Exception as e:
        get_logger().error(f"Error shutting down executor for event {event}: {e}")

##
## >>============================= private method =============================>>
##
  ##
  ## other register handler
  ##
  def __handle_other(self, url):
    pass

  ##
  ## register handler
  ##
  def __platform_register_handler(self, event, handler, max_threads=1):
    """Register a handler for a specific platform event"""
    
    # Check attribute
    if event is None or handler is None:
      get_logger().error("Invalid attribute of registered handler")
      raise ValueError("Event and handler cannot be None")

    # Initialize handler
    self.handlers[event] = handler

    # Initialize executor
    try:
        self.executors[event] = ThreadPoolExecutor(max_workers=max_threads)
    except Exception as e:
        get_logger().error(f"Failed to create ThreadPoolExecutor for event {event}: {e}")
        raise

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

  def dispatch(self, jsonData=None):
    """
    Dispatch events based on URL domains to appropriate handlers
    
    Args:
        jsonData (dict): Contains 'urls' list and optional 'score'/'favorite' values
    Raises:
        ValueError: If jsonData is invalid or missing required fields
    """
    # Extended data related to the event
    token = dict()

    # Check attribute
    if jsonData is None:
      get_logger().error("Invalid attribute of dispatch")
      raise ValueError("jsonData cannot be None")

    # Split jsonData
    urls = jsonData.get('urls')
    if urls is None:
      get_logger().error("Invalid attribute of urls")
      raise ValueError("'urls' field is required in jsonData")
    if not isinstance(urls, list):
      get_logger().error("Invalid attribute of urls")
      raise ValueError("'urls' field must be a list")
    if len(urls) == 0:
      get_logger().error("Invalid attribute of urls")
      raise ValueError("'urls' field cannot be empty")

    url_dict = {event:list() for event in self.__event_list}

    for url in urls:
      # Extract domain
      try:
        parsed_url = urlparse(url)
        if not parsed_url.netloc:
          get_logger().error(f"Invalid URL: {url}")
          continue  # Skip invalid URLs
          
        domain = parsed_url.netloc
      except Exception as e:
        get_logger().error(f"Error parsing URL {url}: {e}")
        continue  # Skip invalid URLs

      # Check domain and create event
      matched = False
      for event in self.__event_list:
        if event in domain:
          matched = True
          # Set extended data
          set_dict_attr(token, "$.url", url)
          set_dict_attr(token, "$.score", jsonData.get('score'))
          set_dict_attr(token, "$.favorite", jsonData.get('favorite'))

          # Tail insert extended data into url_dict list
          url_dict.get(event).append(token.copy())
          break  # Only match one event per URL
      
      if not matched:
        # If no specific platform matched, assign to 'other'
        set_dict_attr(token, "$.url", url)
        set_dict_attr(token, "$.score", jsonData.get('score'))
        set_dict_attr(token, "$.favorite", jsonData.get('favorite'))
        url_dict.get('other').append(token.copy())

      token.clear()

    # Dispatch event
    for event, token_list in url_dict.items():
      if self.handlers.get(event) is not None:
        # Dispatch event
        get_logger().info(f"Dispatching event: {event} with {len(token_list)} items")

        # Submit handler
        for token in token_list:
          try:
            self.executors[event].submit(self.handlers[event], token)
          except Exception as e:
            get_logger().error(f"Failed to submit task for event {event}: {e}")
            # Continue with other tokens even if one submission fails
      else:
        get_logger().warning(f"No handler registered for event: {event}")

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