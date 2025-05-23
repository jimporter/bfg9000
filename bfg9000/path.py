import functools
import ntpath
import os
from contextlib import contextmanager

from .platforms.basepath import (BasePath, Root, InstallRoot,  # noqa: F401
                                 DestDir)
from .platforms.host import platform_info

Path = platform_info().Path


def abspath(path, type=Path, **kwargs):
    return type.abspath(path, **kwargs)


def commonprefix(paths):
    if not paths or any(i.root != paths[0].root for i in paths):
        return None

    cls = type(paths[0])
    split = [i.split() for i in paths]
    lo, hi = min(split), max(split)

    for i, bit in enumerate(lo):
        if bit != hi[i]:
            return cls(cls.sep.join(lo[:i]), paths[0].root, directory=True)
    return cls(cls.sep.join(lo), paths[0].root, directory=(lo != hi))


def uniquetrees(paths):
    def ischild(a, b):
        for i, j in zip(a, b):
            if i != j:
                return False
        return True

    if not paths:
        return []

    paths = [(i, [i.root.value] + i.split()) for i in paths]
    paths.sort(key=lambda i: i[1])
    piter = iter(paths)

    p, last = next(piter)
    uniques = [p]
    for p, bits in piter:
        if not ischild(last, bits):
            last = bits
            uniques.append(p)
    return uniques


def _wrap_ospath(fn):
    @functools.wraps(fn)
    def wrapper(path, variables=None):
        if isinstance(path, BasePath):
            path = path.string(variables)
        return fn(path)

    return wrapper


def _issemiabs(path):
    # Like `isabs`, but returns True for drive-relative absolute paths on
    # Windows. (This is how `isabs` worked prior to Python 3.13.)
    if ( os.path is ntpath and len(path) and
         path[0] in (ntpath.sep, ntpath.altsep) ):
        return True
    return os.path.isabs(path)


exists = _wrap_ospath(os.path.exists)
isdir = _wrap_ospath(os.path.isdir)
isfile = _wrap_ospath(os.path.isfile)
islink = _wrap_ospath(os.path.islink)
issemiabs = _wrap_ospath(_issemiabs)


def samefile(path1, path2, variables=None):
    return os.path.samefile(path1.string(variables),
                            path2.string(variables))


def getmtime_ns(path, variables=None, strict=True):
    try:
        return os.stat(path.string(variables)).st_mtime_ns
    except Exception:
        if strict:
            raise
        return 0


def touch(path, variables=None):
    os.utime(path.string(variables), None)


def listdir(path, variables=None):
    dirs, nondirs = [], []
    try:
        names = os.listdir(path.string(variables))
        for name in names:
            curpath = path.append(name)
            if isdir(curpath, variables):
                dirs.append(curpath.as_directory())
            else:
                nondirs.append(curpath)
    except OSError:
        pass
    return dirs, nondirs


def walk(top, variables=None):
    if not exists(top, variables):
        return
    dirs, nondirs = listdir(top, variables)
    yield top, dirs, nondirs
    for d in dirs:
        if not islink(d, variables):
            for i in walk(d, variables):
                yield i


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
