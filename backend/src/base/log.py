##<<Base>>
from abc import ABC, abstractmethod

##<<Existension>>

##<<Third-part>>

class Log(ABC):
  def __init__(self) -> None:
    super().__init__()
  
  @abstractmethod
  def enable(self) -> None:
    pass

  @abstractmethod
  def disable(self) -> None:
    pass