import os.path
from collections import namedtuple

from . import safe_str

class real_path(safe_str.safe_string):
    def __init__(self, base, path):
        self.base = base
        self.raw_path = os.path.normpath(path) if path else ''

    def path(self, variables, executable=False):
        if self.base in variables:
            suffix = os.path.sep + self.raw_path if self.raw_path else ''
            return variables[self.base] + suffix
        elif executable:
            return os.path.join('.', self.raw_path)
        else:
            return self.raw_path or '.'

    def __str__(self):
        raise NotImplementedError()

    def __repr__(self):
        return '`$({base}){path}`'.format(base=self.base, path=self.path(True))

    def _safe_str(self):
        return self

    def __cmp__(self, rhs):
        if not isinstance(rhs, real_path):
            return NotImplemented
        return cmp(self.base, rhs.base) or cmp(self.raw_path, rhs.raw_path)

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

    def __init__(self, path, source=builddir, install_base=basedir):
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
            return real_path('builddir', self.path)

    def install_path(self):
        if self.source == Path.srcdir:
            path = os.path.basename(self.path)
        else:
            path = self.path
        return real_path('prefix', os.path.join(self.install_base, path))

    # XXX: It might make sense to remove this if/when we support changing
    # bindir, libdir, etc. At that point, we might have to mandate absolute
    # paths for rpath.
    def relpath(self, start):
        if os.path.isabs(self.path):
            return self.path
        else:
            if self.source != start.source:
                raise ValueError('source mismatch')
            return os.path.relpath(self.path or '.', start.path or '.')

    def _safe_str(self):
        return self.local_path()

    def __str__(self):
        raise NotImplementedError()

    def __repr__(self):
        return repr(self.local_path())

    def __hash__(self):
        return hash(self.path)

    def __eq__(self, rhs):
        return (self.source == rhs.source and
                self.install_base == rhs.install_base and
                self.path == rhs.path)

    def __nonzero__(self):
        return self.source != Path.builddir or bool(self.path)
