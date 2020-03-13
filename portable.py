from __future__ import print_function
import os
import sys

if sys.version_info.major==3:
    from urllib.parse import urlparse
    from urllib.request import urlretrieve
else:
    assert sys.version_info.major==2
    from urlparse import urlparse
    from urllib import urlretrieve

def makedirs(p):
    assert p
    if sys.version_info.major==3:
        return os.makedirs(p, exist_ok=True)
    try:
        os.makedirs(p)
    except OSError as e:
        if not ' exists' in str(e):
            raise e 

def rethrow(e, msg):
    e.handled = True
    e.args = [ msg ]
    e.__traceback__ = sys.exc_info()[2]
    raise e
