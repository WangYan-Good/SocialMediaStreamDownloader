##<<Test>>
import os
import sys
sys.path.append(os.getcwd())
from time import sleep
from src.platform.douyin.douyin_url_list_config import UrlListConfig

##<<Base>>
import time
from threading import Thread

##<Extension>>

##<<Third-part>>
from src.base.listener import Listener

class ListenerItem():
##
## >>============================= attribute =============================>>
##
  ##
  ## The thread related download task
  ##
  _thread          = None

  ##
  ## A tuple of related parameters for input of thread
  ##
  _args            = None

  ##
  ## thrget of the thread
  ##
  _target          = None

  ##
  ## indecate and specifiec the task thread
  ##
  _identify        = None
##
## >>============================= private method =============================>>
##
  ##
  ## the thread is initialized once the item initialized
  ## it does not allow to be modified
  ## it only support to be started
  ##
  def __init__(self, func:any = None, args:tuple = None) -> None:
    if not isinstance(args, tuple):
      print("ERROR: input parameter does not correct!")
      raise ValueError
    
    ##
    ## initialize class member
    ##
    self._args     = args
    self._target   = func
    self._identify = self._generate_item_identify()
    self._thread   = Thread(target=self._target, args=self._args)


  ##
  ## generate listen item specificed identify
  ##
  def _generate_item_identify(self):
    return int(round(time.time() * 1000000))

##
## >>============================= sub class method =============================>>
##
  ##
  ## check wether the status of listener item is actived
  ##
  def is_item_actived(self):
    return self._thread.is_alive()
  
  ##
  ## get listener's identify
  ## the identify could indecate the thread specificted
  ##
  def get_item_identify(self):
    return self._identify
  
  ##
  ## active listener item and start execute sub-task
  ##
  def start_item(self):
    try:
      self._thread.start()
    except RuntimeError:
      self._thread = Thread(target=self._target, args=self._args)
      self._thread.start()
  
  ##
  ## dump listener item
  ##
  def dump_item(self):
    print("\tidentify: {}".format(self._identify))
    print("\targs: {}\n".format(self._args))

class DouyinLiveListener(Listener):
##
## >>============================= attribute =============================>>
##
  ##
  ## A list related listened item
  ##
  _listen_list        = list()

  ##
  ## total count in the listener list
  ##
  _total_count      = int()

  ##
  ## The cursor indecate the executed location of the task in the listened list
  ##
  _cursor           = int()

  ##
  ## patrol thread, it will generated when listener instance is initialized
  ## the thread aim to manage the status of listener, control it start or stop,
  ## including add listener item into list and start the sub-task download thread
  ##
  _patrol_thread    = None

  ##
  ## stop patrol thread
  ##
  _stop_thread       = None

  ##
  ## a flag indecate that whether the patrol down need to work
  ##
  _is_need_listening = bool()

  ##
  ## a flag indecate need to end the listener
  ##
  _is_end_listening = bool()

##
## >>============================= private method =============================>>
##
  def __init__(self) -> None:
    self._cursor = 0
    self._total_count = 0
    self._is_need_listening = False
    self._is_end_listening  = False
    self._patrol_thread = Thread(target=self.patrolman)
    self._stop_thread   = Thread(target=self._stop)
    self._stop_thread.daemon = True

##
## >>============================= abstract method =============================>>
##
  ##
  ## start to listen sub task and enable download
  ##
  def start(self):
    ##
    ## caculate total listener item count
    ##
    self._total_count = len(self._listen_list)

    ##
    ## set listening flag is true
    ##
    self._is_need_listening = True

    ##
    ## start enable stop thread and listener the condition
    ##
    self._stop_thread.start()

    ##
    ## alway execute patrolman thread when flag is true
    ##
    self._patrol_thread.start()

  ##
  ## stop to listen sub task and enable download
  ##
  def stop(self):
    self._is_need_listening = False

  ##
  ## stop listen sub task
  ##
  def _stop(self):
    while True:
      if input() == 'quit':
        self._is_need_listening = False
        break
    print("INFO: stop listener succeed.")

  ##
  ## add sub task and append it into list
  ##
  def add_sub_task(self, item:ListenerItem):
    if self.is_sub_task_exist(item.get_item_identify()):
      print("INFO: Target {} has exist in the listen list".format(item.get_item_identify()))
      return
    else:
      self._listen_list.append(item)
      self._total_count += 1
    # print("INFO: Add target {} succeed!".format(item.get_item_identify()))

  ##
  ## delete a specific sub task according identify
  ##
  def del_sub_task(self, identify):
    try:
      for item in self._listen_list:
        if identify == item.identify:
          self._listen_list.remove(item)
          print("INFO: Delete target {} succeed".format(identify))
    except ValueError:
      print("INFO: Target {} does not found".format(identify))
    except Exception as e:
      print("ERROR: Delete sub-task failed {}".format(identify))

##
## >>============================= sub class method =============================>>
##
  ##
  ## search sub-task and make sure whether sub-task has been added
  ##
  def is_sub_task_exist(self, identify)->bool:
    for item in self._listen_list:
      if item.get_item_identify() == identify:
        return True
    return False

  ##
  ## patrolman function
  ##
  def patrolman(self): 
    ##
    ## active patrolman and start listener thread
    ##
    
    ##
    ## loop all listener item and actived
    ##
    index = 0
    while index < len(self._listen_list) and self._is_need_listening is True:
      
      ##
      ## set cursor and indecate current item
      ##
      self._cursor = index

      ##
      ## scan listener list and start thread
      ##
      if self._listen_list[self._cursor]._thread.is_alive() is not True:
        self._listen_list[self._cursor].start_item()
      
      ##
      ## start from first item if current item is the last
      ##
      sleep(1)
      if self._listen_list[self._cursor].get_item_identify() == self._listen_list[-1].get_item_identify():
        index = 0
      else:  
        index += 1

  ##
  ## check wether the status of patrolman is actived
  ## if ACTIVED, True will be returned
  ## if DEACTIVED, False will be returned
  ##
  def is_patrolman_actived(self):
    return self._patrol_thread.is_alive()

##
## for unit test
##
def output(url:str):
  sleep(5) # sleep 5s
  print(url)

def test_listen_item():
  url_list = UrlListConfig(None).getConfigList("live")
  # listener = DouyinLiveListener(output)
  for url in url_list:
    listen_item = ListenerItem(func=output, args=(url,))
    
    # expect: false
    print("thread is alive: {}".format(listen_item.is_item_actived()))
    listen_item.start_item()
    
    # expect: true
    print("thread is alive: {}".format(listen_item.is_item_actived()))
    
    # expect: false
    sleep(7)
    print("thread is alive: {}".format(listen_item.is_item_actived()))

    # dump
    print("dump {} item details:".format(url))
    listen_item.dump_item()
    break

def test_douyin_live_listener():
  url_list = UrlListConfig(None).getConfigList("post")
  live_listener = DouyinLiveListener()
  for url in url_list:
    listen_item = ListenerItem(func=output, args=(url,))
    live_listener.add_sub_task(listen_item)
  live_listener.start()
  sleep(10)
  live_listener.stop()

##
## test
##
if __name__ == "__main__":
  # test_listen_item()
  test_douyin_live_listener()