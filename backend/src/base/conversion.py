##<<Base>>
import os
from re import compile
from pathlib import Path

##<<Extension>>
import ffmpeg

FORMAT_SUFFIX_REGULAR = r'\.([a-zA-Z0-9]{1,})$'

class StreamConversion():
  def __init__(self) -> None:
    pass

  def video_conversion(self, input:str = None, output:str = None):
    '''
    input_suffix  = compile(FORMAT_SUFFIX_REGULAR).findall(input)
    # output_suffix = compile(FORMAT_SUFFIX_REGULAR).findall(output)
    print("INFO: input {}".format(input))
    print("INFO: output {}".format(output))

    ffmpeg.input(input, format=input_suffix).output(output).run()
    print("INFO: convention succeed!")
    '''

if __name__ == "__main__":
  path1 = "/mnt/nvme2/vedio/live/_米开朗绿萝_/stream-115469151408489135_or4.flv"
  path2 = "/mnt/nvme2/vedio/live/_米开朗绿萝_/stream-115469151408489135_or4.mp4"
  # path2 = "./nvme2/vedio/live/_米开朗绿萝_/stream-115469151408489135_or4.flv"
  try:
    StreamConversion().video_conversion(input=path1, output=path2)
  except Exception as e:
    raise e