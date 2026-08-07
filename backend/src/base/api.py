##<<Base>>
from abc import ABC, abstractmethod



class Api(ABC):
  def __init__(self, config: dict) -> None:
    if not isinstance(config, dict):
      raise ValueError("API configuration must be a mapping")
    super().__init__()

  @abstractmethod
  def dump_config(self):
    pass
