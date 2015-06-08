import os.path
from collections import namedtuple

from . import safe_str

class real_path(safe_str.safe_string):
    def __init__(self, base, path):
        self.base = base
        self.path = path

    def __str__(self):
        raise NotImplementedError()

    def __repr__(self):
        return '`$({base}){sep}{path}`'.format(
            base=self.base, sep=os.sep, path=self.path
        )

    def _safe_str(self):
        return self

    def __cmp__(self, rhs):
        if not isinstance(rhs, real_path):
            return NotImplemented
        return cmp(self.base, rhs.base) or cmp(self.path, rhs.path)

    def __add__(self, rhs):
        return safe_str.jbos(self, rhs)

    def __radd__(self, lhs):
        return safe_str.jbos(lhs, self)

class Path(object):
    srcdir = 1
    builddir = 2

    # TODO: Allow these to be set by the user. Then, just keep track of which
    # dir and build it up appropriately somehow in the backend.
    basedir = ''
    bindir = 'bin'
    libdir = 'lib'
    includedir = 'include'

    def __init__(self, path, source, install_base):
        self.path = path
        self.source = source
        self.install_base = install_base

    def parent(self):
        if not self.path:
            raise ValueError('already at root')
        return Path(os.path.dirname(self.path), self.source, self.install_base)

    def append(self, path):
        return Path(os.path.join(self.path, path), self.source,
                    self.install_base)

    def addext(self, ext):
        return Path(self.path + ext, self.source, self.install_base)

    def basename(self):
        return os.path.basename(self.path)

    def local_path(self):
        if self.source == Path.srcdir:
            return real_path('srcdir', self.path)
        else:
            path = self.install_base
            if self.path:
                path = os.path.join(path, self.path)
            return real_path('builddir', path)

    def install_path(self):
        if self.source == Path.srcdir:
            path = os.path.basename(self.path)
        else:
            path = self.path
        return real_path('prefix', os.path.join(self.install_base, path))

    def _safe_str(self):
        return self.local_path()

    def __str__(self):
        raise NotImplementedError

    def __repr__(self):
        return repr(self.local_path())

    def __hash__(self):
        return hash(self.path)

    def __eq__(self, rhs):
        return (self.source == rhs.source and
                self.install_base == rhs.install_base and
                self.path == rhs.path)

    def __nonzero__(self):
        return (self.source != Path.builddir or
                self.install_base != Path.basedir or
                bool(self.path))
