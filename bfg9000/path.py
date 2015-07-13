import os.path
from collections import namedtuple

from . import safe_str

class Path(safe_str.safe_string):
    srcdir = 'srcdir'
    builddir = 'builddir'
    prefix = 'prefix'
    absolute = 'absolute'

    # TODO: Allow these to be set by the user. Then, just keep track of which
    # dir and build it up appropriately somehow in the backend.
    basedir = ''
    bindir = 'bin'
    libdir = 'lib'
    includedir = 'include'

    def __init__(self, path, source=builddir):
        self.raw_path = os.path.normpath(path)
        if self.raw_path == '.':
            self.raw_path = ''

        if os.path.isabs(path):
            self.base = self.absolute
        elif source == self.absolute:
            raise ValueError("'{}' is not absolute".format(path))
        else:
            self.base = source

    def realize(self, variables, executable=False):
        base = variables[self.base] if self.base != self.absolute else None
        if base is not None:
            return base + (os.path.sep + self.raw_path if self.raw_path else '')
        elif executable and os.path.sep not in self.raw_path:
            return os.path.join('.', self.raw_path)
        else:
            return self.raw_path or '.'

    def parent(self):
        if not self.raw_path:
            raise ValueError('already at root')
        return Path(os.path.dirname(self.raw_path), self.base)

    def append(self, path):
        return Path(os.path.join(self.raw_path, path), self.base)

    def addext(self, ext):
        return Path(self.raw_path + ext, self.base)

    def basename(self):
        return os.path.basename(self.raw_path)

    # XXX: It might make sense to remove this if/when we support changing
    # bindir, libdir, etc. At that point, we might have to mandate absolute
    # paths for rpath.
    def relpath(self, start):
        if os.path.isabs(self.raw_path):
            return self.raw_path
        else:
            if self.base != start.base:
                raise ValueError('source mismatch')
            return os.path.relpath(self.raw_path or '.', start.raw_path or '.')

    def __str__(self):
        raise NotImplementedError()

    def __repr__(self):
        variables = {
            self.srcdir: '$(srcdir)',
            self.builddir: '$(builddir)',
            self.prefix: '$(prefix)',
        }
        return '`{}`'.format(self.realize(variables))

    def __hash__(self):
        return hash(self.raw_path)

    def __eq__(self, rhs):
        return self.base == rhs.base and self.raw_path == rhs.raw_path

    def __nonzero__(self):
        return self.base != Path.builddir or bool(self.raw_path)

    def __add__(self, rhs):
        return safe_str.jbos(self, rhs)

    def __radd__(self, lhs):
        return safe_str.jbos(lhs, self)

def install_path(path, install_root):
    if path.base == Path.srcdir:
        suffix = os.path.basename(path.raw_path)
    else:
        suffix = path.raw_path
    return Path(os.path.join(install_root, suffix), Path.prefix)
