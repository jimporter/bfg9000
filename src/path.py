import os.path
from collections import namedtuple

VarPath = namedtuple('VarPath', ['base', 'path'])

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
            raise RuntimeError('already at root')
        return Path(os.path.dirname(self.path), self.source, self.install_base)

    def append(self, path):
        return Path(os.path.join(self.path, path), self.source,
                    self.install_base)

    def subext(self, ext):
        # TODO: Is there a better way to do this?
        return Path(os.path.splitext(self.path)[0] + ext, self.source,
                    self.install_base)

    def local_path(self):
        if self.source == Path.srcdir:
            return VarPath('srcdir', self.path)
        elif self.path:
            return VarPath(None, os.path.join(self.install_base, self.path))
        else:
            return VarPath(None, self.install_base)

    def install_path(self):
        if self.source == Path.srcdir:
            path = os.path.basename(self.path)
        else:
            path = self.path
        return VarPath('prefix', os.path.join(self.install_base, path))

    def __repr__(self):
        if self.source == Path.srcdir:
            return repr(os.path.join('$(srcdir)', self.path))
        elif self.path:
            return repr(os.path.join(self.install_base, self.path))
        else:
            return repr(self.install_base)

    def __hash__(self):
        return hash(self.path)

    def __eq__(self, rhs):
        return (self.source == rhs.source and
                self.install_base == rhs.install_base and
                self.path == rhs.path)

    def __nonzero__(self):
        return (self.source != Path.srcdir or
                self.install_base != Path.basedir or
                bool(self.path))
