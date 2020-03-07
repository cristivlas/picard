from __future__ import print_function
import os
import sys

if sys.version_info.major==3:
    from urllib import parse as urlparse
else:
    assert sys.version_info.major==2
    from urlparse import urlparse

def makedirs(p):
    try:
        os.makedirs(p)
    except OSError as e:
        if not 'already exists' in str(e):
            raise e 
