import os.path

from node import Node

class Environment(object):
    def __init__(self, srcdir, builddir):
        self.srcdir = srcdir
        self.builddir = builddir

    def set_srcdir_var(self, var):
        self._srcdir_var = var

    # TODO: This still needs some improvement to be more flexible
    def target_name(self, target):
        if type(target).__name__ == 'Library':
            return 'lib{}.so'.format(target.name)
        elif type(target).__name__ == 'ObjectFile':
            return '{}.o'.format(target.name)
        else:
            return target.name

    def target_path(self, target, srcdir=None):
        if srcdir is None:
            srcdir = self._srcdir_var or self.srcdir
        name = self.target_name(target)
        return os.path.join(str(srcdir), name) if target.is_source else name
