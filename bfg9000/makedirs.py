import errno
import os

def makedirs(path, mode=0o777, exist_ok=False):
    try:
        os.makedirs(path)
    except OSError as e:
        if not exist_ok or e.errno != errno.EEXIST or not os.path.isdir(path):
            raise
