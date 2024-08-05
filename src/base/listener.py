## <<Base>>
from abc import ABC, abstractmethod

class Listener(ABC):
  def __init__(self) -> None:
    pass

  @abstractmethod
  def start(self):
    pass

  @abstractmethod
  def stop(self):
    pass

  @abstractmethod
  def add_sub_task(self, func):
    pass

  @abstractmethod
  def del_sub_task(self, func):
    pass