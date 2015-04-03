import os.path

import toolchains.cc
from node import Node

class Environment(object):
    def __init__(self, srcdir, builddir):
        self.srcdir = srcdir
        self.builddir = builddir
        self._compilers = {
            'c'  : toolchains.cc.CcCompiler(),
            'c++': toolchains.cc.CxxCompiler(),
        }

    # TODO: This shouldn't be set here, since Environment should be reentrant
    def set_srcdir_var(self, var):
        self._srcdir_var = var

    def compiler(self, lang):
        if isinstance(lang, basestring):
            return self._compilers[lang]

        # TODO: Be more intelligent about this when we support more languages
        lang = set(lang)
        if 'c++' in lang:
            return self._compilers['c++']
        return self._compilers['c']

    # TODO: This still needs some improvement to be more flexible
    def target_name(self, target):
        if type(target).__name__ == 'Library':
            return os.path.join(
                os.path.dirname(target.name),
                'lib{}.so'.format(os.path.basename(target.name))
            )
        elif type(target).__name__ == 'ObjectFile':
            return '{}.o'.format(target.name)
        else:
            return target.name

    def target_path(self, target, srcdir=None):
        if srcdir is None:
            srcdir = self._srcdir_var or self.srcdir
        name = self.target_name(target)
        return os.path.join(str(srcdir), name) if target.is_source else name
