# base
from pathlib import Path

# extension

# third part
from basic.downloader import Downloader, BASE_CONFIG_PATH

class VedioDownloader(Downloader):
  ##
  ## parameter
  ##

  ##
  ## initialize
  ##
  def __init__(self, path:Path = BASE_CONFIG_PATH) -> None:
    super().__init__(path)

if __name__ == "__main__":
  vedio = VedioDownloader()
  vedio.dump_config()