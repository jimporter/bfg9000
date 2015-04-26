import os.path

import toolchains.ar
import toolchains.cc

class Environment(object):
    def __init__(self, srcdir, builddir, install_prefix):
        self.srcdir = srcdir
        self.builddir = builddir
        self.install_prefix = install_prefix

        self._compilers = {
            'c'  : toolchains.cc.CcCompiler(),
            'c++': toolchains.cc.CxxCompiler(),
        }
        self._linkers = {
            'executable': {
                'c'  : toolchains.cc.CcLinker('executable'),
                'c++': toolchains.cc.CxxLinker('executable'),
            },
            'shared_library': {
                'c'  : toolchains.cc.CcLinker('shared_library'),
                'c++': toolchains.cc.CxxLinker('shared_library'),
            },
            'static_library': {
                'c'  : toolchains.ar.ArLinker(),
                'c++': toolchains.ar.ArLinker(),
            }
        }

    def compiler(self, lang):
        return self._compilers[lang]

    def linker(self, lang, mode):
        if isinstance(lang, basestring):
            return self._linkers[mode][lang]

        if not isinstance(lang, set):
            lang = set(lang)
        # TODO: Be more intelligent about this when we support more languages
        if 'c++' in lang:
            return self._linkers[mode]['c++']
        return self._linkers[mode]['c']
