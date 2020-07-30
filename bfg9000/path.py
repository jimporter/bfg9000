import functools
import os
from contextlib import contextmanager

from .platforms.basepath import BasePath, Root, InstallRoot, DestDir  # noqa
from .platforms.host import platform_info

Path = platform_info().Path


def abspath(path, type=Path):
    return type.abspath(path)


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
islink = _wrap_ospath(os.path.islink)


def samefile(path1, path2, variables=None):
    return os.path.samefile(path1.string(variables),
                            path2.string(variables))


@contextmanager
def pushd(dirname, makedirs=False, mode=0o777, exist_ok=False):
    old = os.getcwd()
    if makedirs:
        os.makedirs(dirname, mode, exist_ok)

    os.chdir(dirname)
    try:
        yield
    finally:
        os.chdir(old)
