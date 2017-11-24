import errno
import os
from enum import Enum
from itertools import chain
from six import iteritems, string_types
from contextlib import contextmanager

from . import safe_str
from .iterutils import isiterable, listify
from .platforms import platform_name

Root = Enum('Root', ['srcdir', 'builddir', 'absolute'])
InstallRoot = Enum('InstallRoot', ['prefix', 'exec_prefix', 'bindir', 'libdir',
                                   'includedir'])
DestDir = Enum('DestDir', ['destdir'])


class Path(safe_str.safe_string):
    __repr_variables = dict(
        [(i, '$({})'.format(i.name)) for i in chain(Root, InstallRoot)] +
        [(DestDir.destdir, '$(DESTDIR)')]
    )

    def __init__(self, path, root=Root.builddir, destdir=False):
        if destdir and root not in InstallRoot:
            raise ValueError('destdir only applies to install paths')
        self.destdir = destdir

        self.suffix = os.path.normpath(path)
        if self.suffix == '.':
            self.suffix = ''

        if os.path.isabs(path):
            self.root = Root.absolute
        elif root == Root.absolute:
            raise ValueError("'{}' is not absolute".format(path))
        else:
            self.root = root

    def parent(self):
        if not self.suffix:
            raise ValueError('already at root')
        return Path(os.path.dirname(self.suffix), self.root)

    def append(self, path):
        return Path(os.path.join(self.suffix, path), self.root)

    def ext(self):
        return os.path.splitext(self.suffix)[1]

    def addext(self, ext):
        return Path(self.suffix + ext, self.root)

    def stripext(self, replace=None):
        name = os.path.splitext(self.suffix)[0]
        if replace:
            name += replace
        return Path(name, self.root)

    def split(self):
        # This is guaranteed to work since `suffix` is normalized.
        return self.suffix.split(os.path.sep)

    def basename(self):
        return os.path.basename(self.suffix)

    def relpath(self, start):
        if os.path.isabs(self.suffix):
            return self.suffix
        else:
            if self.root != start.root:
                raise ValueError('source mismatch')
            return os.path.relpath(self.suffix or '.', start.suffix or '.')

    def reroot(self, root=Root.builddir):
        return Path(self.suffix, root)

    def to_json(self):
        return (self.suffix, self.root.name, self.destdir)

    @staticmethod
    def from_json(data):
        try:
            base = Root[data[1]]
        except KeyError:
            base = InstallRoot[data[1]]
        return Path(data[0], base, data[2])

    def realize(self, variables, executable=False):
        root = variables[self.root] if self.root != Root.absolute else None
        if executable and root is None and os.path.sep not in self.suffix:
            root = '.'

        # Not all platforms (e.g. Windows) support $(DESTDIR), so only emit the
        # destdir variable if it's defined.
        if self.destdir and DestDir.destdir in variables:
            root = variables[DestDir.destdir] + root
        if root is None:
            return self.suffix or '.'
        if not self.suffix:
            return root

        # Join the separator and the suffix first so that we don't end up with
        # unnecessarily-escaped backslashes on Windows. (It doesn't hurt
        # anything; it just looks weird.)
        return root + (os.path.sep + self.suffix)

    def string(self, variables=None):
        path = self
        result = ''

        while True:
            real = path.realize(variables)
            if isinstance(real, safe_str.jbos):
                path, suffix = real.bits
                result = suffix + result
            elif isinstance(real, Path):
                path = real
            else:
                result = real + result
                break

        return result

    def __str__(self):
        raise NotImplementedError()

    def __repr__(self):
        return '`{}`'.format(self.realize(self.__repr_variables))

    def __hash__(self):
        return hash(self.suffix)

    def __eq__(self, rhs):
        return (self.root == rhs.root and self.suffix == rhs.suffix and
                self.destdir == rhs.destdir)

    def __nonzero__(self):
        return self.__bool__()

    def __bool__(self):
        return self.root != Root.builddir or bool(self.suffix)

    def __add__(self, rhs):
        return safe_str.jbos(self, rhs)

    def __radd__(self, lhs):
        return safe_str.jbos(lhs, self)


def abspath(path):
    return Path(os.path.abspath(path), Root.absolute)


def install_path(path, install_root, directory=False, destdir=True):
    if path.root == Root.srcdir:
        suffix = '.' if directory else os.path.basename(path.suffix)
    else:
        suffix = path.suffix
    return Path(suffix, install_root, destdir)


def commonprefix(paths):
    if not paths or any(i.root != paths[0].root for i in paths):
        return None

    split = [i.split() for i in paths]
    lo, hi = min(split), max(split)

    for i, bit in enumerate(lo):
        if bit != hi[i]:
            return Path(os.path.sep.join(lo[:i]), paths[0].root)
    return Path(os.path.sep.join(lo), paths[0].root)


def exists(path):
    return os.path.exists(path.string())


def samefile(path1, path2):
    if hasattr(os.path, 'samefile'):
        return os.path.samefile(path1.string(), path2.string())
    else:
        # This isn't entirely accurate, but it's close enough, and should only
        # be necessary for Windows with Python 2.x.
        return (os.path.realpath(path1.string()) ==
                os.path.realpath(path2.string()))


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
