##<<Base>>
from pathlib import Path
from abc import ABC, abstractmethod



class Api(ABC):
  def __init__(self, path:Path|str = None) -> None:
    super().__init__()

  @abstractmethod
  def dump_config(self):
    pass