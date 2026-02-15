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
from backend.src.base.platform_config import PlatformConfig
from backend.src.base.log import get_logger

"""Platform dispatcher to handle different social media platforms"""

class PlatformDispatcher:
##
## >>============================= attribute =============================>>
##
  def __init__(self, config_path=None):
    self.handlers  = dict()
    self.executors = dict()
    self.platform_config = PlatformConfig(config_path)
    self.__event_list = self.platform_config.get_platform_list()
    self.__handler_dict = self.platform_config.get_handler_dict()
  
  def shutdown(self):
    """Shutdown all thread executors to free resources"""
    get_logger().info("Starting platform dispatcher shutdown process")
    for event, executor in self.executors.items():
      try:
        get_logger().info(f"Shutting down executor for event: {event}")
        executor.shutdown(wait=True)  # Wait for tasks to complete
        get_logger().info(f"Executor for event {event} has been shut down successfully")
      except Exception as e:
        get_logger().error(f"Error shutting down executor for event {event}: {e}")
    get_logger().info("Platform dispatcher shutdown process completed")

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

  def dispatch(self, jsonData=None, completion_callback=None):
    """
    Dispatch events based on URL domains to appropriate handlers

    Args:
        jsonData (dict): Contains 'urls' list and optional 'score'/'favorite' values
        completion_callback (callable, optional): Function to call when all tasks complete
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

    get_logger().info(f"Starting dispatch for {len(urls)} URLs")

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
        # Check if the domain matches any of the platform's domains
        platform_domains = self.platform_config.get_domains_for_platform(event)
        if any(domain_part in domain for domain_part in platform_domains):
          matched = True
          # Set extended data
          set_dict_attr(token, "$.url", url)
          set_dict_attr(token, "$.score", jsonData.get('score'))
          set_dict_attr(token, "$.favorite", jsonData.get('favorite'))

          # Tail insert extended data into url_dict list
          url_dict.get(event).append(token.copy())
          get_logger().info(f"Matched URL {url} to platform: {event}")
          break  # Only match one event per URL

      if not matched:
        # If no specific platform matched, assign to 'other'
        set_dict_attr(token, "$.url", url)
        set_dict_attr(token, "$.score", jsonData.get('score'))
        set_dict_attr(token, "$.favorite", jsonData.get('favorite'))
        url_dict.get('other').append(token.copy())
        get_logger().info(f"No specific platform matched for URL {url}, assigned to 'other'")

      token.clear()

    # Track total number of tasks submitted
    total_tasks = sum(len(tokens) for tokens in url_dict.values())
    get_logger().info(f"Total tasks to dispatch: {total_tasks}")
    
    # Dispatch event
    for event, token_list in url_dict.items():
      if self.handlers.get(event) is not None:
        # Dispatch event
        get_logger().info(f"Dispatching event: {event} with {len(token_list)} items")

        # Submit handler
        for token in token_list:
          try:
            # Wrap the handler with completion callback if provided
            if completion_callback:
              wrapped_handler = self._wrap_with_completion(self.handlers[event], completion_callback)
              future = self.executors[event].submit(wrapped_handler, token)
              get_logger().info(f"Submitted task for {event} with URL: {token.get('$.url', 'unknown')}")
            else:
              future = self.executors[event].submit(self.handlers[event], token)
              get_logger().info(f"Submitted task for {event} with URL: {token.get('$.url', 'unknown')}")
          except Exception as e:
            get_logger().error(f"Failed to submit task for event {event}: {e}")
            # Continue with other tokens even if one submission fails
      else:
        get_logger().warning(f"No handler registered for event: {event}")
    
    get_logger().info(f"Dispatch completed. Total tasks submitted: {total_tasks}")

  def _wrap_with_completion(self, handler, completion_callback):
    """Wrap a handler with a completion callback"""
    def wrapper(*args, **kwargs):
      try:
        result = handler(*args, **kwargs)
        completion_callback(args[0] if args else None)  # Pass token to callback
        return result
      except Exception as e:
        get_logger().error(f"Error in handler: {e}")
        completion_callback(args[0] if args else None)  # Pass token to callback even on error
        raise
    return wrapper

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