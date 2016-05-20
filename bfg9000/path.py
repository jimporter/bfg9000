import errno
import os
from enum import Enum
from itertools import chain
from six import iteritems

from . import safe_str

Root = Enum('Root', ['srcdir', 'builddir', 'absolute'])
InstallRoot = Enum('InstallRoot', ['prefix', 'bindir', 'libdir', 'includedir'])


class Path(safe_str.safe_string):
    def __init__(self, path, root=Root.builddir):
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
        # This is guaranteed to work since `suffix` is normalized
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

    def to_json(self):
        return (self.suffix, self.root.name)

    @staticmethod
    def from_json(data):
        try:
            base = Root[data[1]]
        except:
            base = InstallRoot[data[1]]
        return Path(data[0], base)

    def realize(self, variables, executable=False):
        root = variables[self.root] if self.root != Root.absolute else None
        if executable and root is None and os.path.sep not in self.suffix:
            root = '.'

        if root is None:
            return self.suffix or '.'
        if not self.suffix:
            return root

        # Join the separator and the suffix first so that we don't end up with
        # unnecessarily-escaped backslashes on Windows. (It doesn't hurt
        # anything; it just looks weird.)
        return root + (os.path.sep + self.suffix)

    def string(self, variables=None):
        return self.realize({k: v.string() if isinstance(v, Path) else v
                             for k, v in iteritems(variables or {})})

    def __str__(self):
        raise NotImplementedError()

    def __repr__(self):
        variables = {i: '$({})'.format(i.name) for i in
                     chain(Root, InstallRoot)}
        return '`{}`'.format(self.realize(variables))

    def __hash__(self):
        return hash(self.suffix)

    def __eq__(self, rhs):
        return self.root == rhs.root and self.suffix == rhs.suffix

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


def install_path(path, install_root):
    if path.root == Root.srcdir:
        suffix = os.path.basename(path.suffix)
    else:
        suffix = path.suffix
    return Path(suffix, install_root)


def commonprefix(paths):
    if not paths or any(i.root != paths[0].root for i in paths):
        return None

    split = [i.split() for i in paths]
    lo, hi = min(split), max(split)

    for i, bit in enumerate(lo):
        if bit != hi[i]:
            return Path(os.path.sep.join(lo[:i]), paths[0].root)
    return Path(os.path.sep.join(lo), paths[0].root)


def makedirs(path, mode=0o777, exist_ok=False):
    try:
        os.makedirs(path, mode)
    except OSError as e:
        if not exist_ok or e.errno != errno.EEXIST or not os.path.isdir(path):
            raise


def samefile(path1, path2):
    if hasattr(os.path, 'samefile'):
        return os.path.samefile(path1, path2)
    else:
        # This isn't entirely accurate, but it's close enough, and should only
        # be necessary for Windows with Python 2.x.
        return os.path.realpath(path1) == os.path.realpath(path2)
