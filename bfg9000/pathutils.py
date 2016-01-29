import errno
import os


def makedirs(path, mode=0o777, exist_ok=False):
    try:
        os.makedirs(path)
    except OSError as e:
        if not exist_ok or e.errno != errno.EEXIST or not os.path.isdir(path):
            raise


class pushd(object):
    def __init__(self, dirname):
        self.cwd = dirname

    def __enter__(self):
        self.old = os.getcwd()
        os.chdir(self.cwd)
        return self

    def __exit__(self, type, value, traceback):
        os.chdir(self.old)


def samefile(path1, path2):
    if hasattr(os.path, 'samefile'):
        return os.path.samefile(path1, path2)
    else:
        # This isn't entirely accurate, but it's close enough, and should only
        # be necessary for Windows with Python 2.x.
        return os.path.realpath(path1) == os.path.realpath(path2)
