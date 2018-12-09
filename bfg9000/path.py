import errno
import functools
import os
from contextlib import contextmanager

from .platforms.basepath import BasePath, Root, InstallRoot, DestDir  # noqa
from .platforms.host import platform_info

Path = platform_info().Path


def abspath(path, type=Path):
    return type.abspath(path)


def install_path(path, install_root, directory=False, cross=None):
    cls = cross.target_platform.Path if cross else type(path)
    if path.root == Root.absolute:
        if not cross:
            raise TypeError('path is absolute')
        return cls(path.suffix, path.root)

    if path.root == Root.srcdir:
        suffix = path.curdir if directory else path.basename()
    else:
        suffix = path.suffix
    return cls(suffix, install_root, destdir=not cross)


def commonprefix(paths):
    if not paths or any(i.root != paths[0].root for i in paths):
        return None

    cls = type(paths[0])
    split = [i.split() for i in paths]
    lo, hi = min(split), max(split)

    for i, bit in enumerate(lo):
        if bit != hi[i]:
            return cls(cls.sep.join(lo[:i]), paths[0].root)
    return cls(cls.sep.join(lo), paths[0].root)


def _wrap_ospath(fn):
    @functools.wraps(fn)
    def wrapper(path, variables=None):
        return fn(path.string(variables))

    return wrapper


exists = _wrap_ospath(os.path.exists)
isdir = _wrap_ospath(os.path.isdir)
isfile = _wrap_ospath(os.path.isfile)


def samefile(path1, path2, variables=None):
    if hasattr(os.path, 'samefile'):
        return os.path.samefile(path1.string(variables),
                                path2.string(variables))
    else:
        # This isn't entirely accurate, but it's close enough, and should only
        # be necessary for Windows with Python 2.x.
        return (os.path.realpath(path1.string(variables)) ==
                os.path.realpath(path2.string(variables)))


def makedirs(path, mode=0o777, exist_ok=False):
    try:
        os.makedirs(path, mode)
    except OSError as e:
        if not exist_ok or e.errno != errno.EEXIST or not os.path.isdir(path):
            raise


# Make an alias since the function below masks the module-level function with
# one of its parameters.
_makedirs = makedirs


@contextmanager
def pushd(dirname, makedirs=False, mode=0o777, exist_ok=False):
    old = os.getcwd()
    if makedirs:
        _makedirs(dirname, mode, exist_ok)

    os.chdir(dirname)
    yield
    os.chdir(old)
