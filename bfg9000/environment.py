import os.path
import pickle

from . import platforms
from .builders import ar
from .builders import cc
from .builders import msvc

envfile = '.bfg_environ'

class Environment(object):
    def __init__(self, bfgpath, srcdir, builddir, backend, install_prefix):
        self.bfgpath = bfgpath
        self.scanpath = os.path.join(os.path.dirname(bfgpath), 'arachnotron')

        self.srcdir = srcdir
        self.builddir = builddir
        self.backend = backend
        self.install_prefix = install_prefix

        self.platform = platforms.platform_info(platforms.platform_name())

        # TODO: Come up with a more flexible way to initialize the compilers and
        # linkers for each language.
        if self.platform.name == 'windows':
            compiler = msvc.MSVCCompiler(self.platform)
            exe_linker = msvc.MSVCLinker(self.platform, 'executable')
            lib_linker = msvc.MSVCStaticLinker(self.platform)
            dll_linker = msvc.MSVCLinker(self.platform, 'shared_library')
            self._compilers = {
                'c'  : compiler,
                'c++': compiler,
            }
            self._linkers = {
                'executable': {
                    'c'  : exe_linker,
                    'c++': exe_linker,
                },
                'static_library': {
                    'c'  : lib_linker,
                    'c++': lib_linker,
                },
                'shared_library': {
                    'c'  : dll_linker,
                    'c++': dll_linker,
                },
            }
        else:
            ar_linker = ar.ArLinker(self.platform)
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
                    'c'  : ar_linker,
                    'c++': ar_linker,
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

    def save(self, path):
        with open(os.path.join(path, envfile), 'w') as out:
            pickle.dump(self, out, protocol=2)

    @staticmethod
    def load(path):
        with open(os.path.join(path, envfile)) as inp:
            return pickle.load(inp)
