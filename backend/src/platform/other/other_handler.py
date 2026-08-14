##>> Test
import os
import sys
sys.path.append(os.getcwd())
##<< Test

def other_handler(url_list:list, context:dict=None):
    ##
    ## ``context`` is unused here but accepted because the dispatcher passes the
    ## dependencies of a dispatch to every handler it calls, not only to douyin's.
    ##
    pass