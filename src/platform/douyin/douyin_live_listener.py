##<<Base>>

##<Extension>>

##<<Third-part>>
from src.base.listener import Listener

class DouyinLiveListener(Listener):
  def __init__(self) -> None:
    super().__init__()
    pass

  def start(self):
    return super().start()
  
  def stop(self):
    return super().stop()
  
  def add_sub_task(self, func):
    return super().add_sub_task(func)
  
  def del_sub_task(self, func):
    return super().del_sub_task(func)