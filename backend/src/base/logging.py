##<<Base>>

##<<Existension>>

##<<Third-part>>

class BaseLogging():
##
## >>============================= attribute =============================>>
##
  __enable = False

##
## >>============================= private method =============================>>
##
  def __init__(self) -> None:
    super().__init__()

##
## >>============================= abstract method =============================>>
##

##
## >>============================= sub class method =============================>>
##
  def enable(self) -> None:
    self.__enable = True

  def disable(self) -> None:
    self.__enable = False

##
## >>================================ test method ===============================>>
##

##
## >>================================ main method ===============================>>
##