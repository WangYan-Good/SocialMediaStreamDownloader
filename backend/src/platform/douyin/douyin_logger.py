##<<Base>>

##<<Extension>>

##<<Third-part>>
from backend.src.base.log import Log

class DouyinLogger(Log):
  def __init__(self) -> None:
    super().__init__()

  def enable(self) -> None:
    return super().enable()
  
  def disable(self) -> None:
    return super().disable()