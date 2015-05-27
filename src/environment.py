import os.path

import platforms
from builders import ar
from builders import cc
from builders import msvc

class Environment(object):
    def __init__(self, bfgpath, srcdir, builddir, backend, install_prefix):
        self.bfgpath = bfgpath
        self.srcdir = srcdir
        self.builddir = builddir
        self.backend = backend
        self.install_prefix = install_prefix

        self.platform = platforms.platform_info(platforms.platform_name())

        # TODO: Come up with a more flexible way to initialize the compilers and
        # linkers for each language.
        if self.platform.name == 'Windows':
            compiler = msvc.MSVCCompiler(self.platform)
            exelinker = msvc.MSVCLinker(self.platform, 'executable')
            liblinker = msvc.MSVCLinker(self.platform, 'static_library')
            dlllinker = msvc.MSVCLinker(self.platform, 'shared_library')
            self._compilers = {
                'c'  : compiler,
                'c++': compiler,
            }
            self._linkers = {
                'executable': {
                    'c'  : exelinker,
                    'c++': exelinker,
                },
                'static_library': {
                    'c'  : liblinker,
                    'c++': liblinker,
                },
                'shared_library': {
                    'c'  : dlllinker,
                    'c++': dlllinker,
                },
            }
        else:
            self._compilers = {
                'c'  : cc.CcCompiler(self.platform),
                'c++': cc.CxxCompiler(self.platform),
            }
            self._linkers = {
                'executable': {
                    'c'  : cc.CcLinker(self.platform, 'executable'),
                    'c++': cc.CxxLinker(self.platform, 'executable'),
                },
                'static_library': {
                    'c'  : ar.ArLinker(self.platform),
                    'c++': ar.ArLinker(self.platform),
                },
                'shared_library': {
                    'c'  : cc.CcLinker(self.platform, 'shared_library'),
                    'c++': cc.CxxLinker(self.platform, 'shared_library'),
                },
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
