##>> Test
import os
import sys
sys.path.append(os.getcwd())
##<< Test

##
## 解析抖音分享链接
## 确定是哪种类型的分享链接
## 1. 作品
## 2. 直播
## 3. 用户主页
##

def douyin_handler(url):
  print("[douyin] progressing: {}".format(url))
  # 模拟处理耗时
  import time
  time.sleep(2)
  print(f"[douyin] 链接处理完成: {url}")