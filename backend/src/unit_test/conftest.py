##<<Third-Part>>
from backend.src.unit_test.no_network import install


##
## Armed at import time rather than as an autouse fixture, so it also covers
## module-level code that runs during collection.
##
## The rule itself lives in ``no_network`` - see there for why it exists and why
## it is not written inline here.
##
install()
