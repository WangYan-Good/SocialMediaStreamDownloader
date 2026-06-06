##>> Test
import os
import sys
sys.path.append(os.getcwd())
##<< Test

##
## <<third-party>>
##
from backend.src.platform.platform_dispatcher import PlatformDispatcher
from backend.src.base.log import get_logger

##
## >>================================ test method ===============================>>
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