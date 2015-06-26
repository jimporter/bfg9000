import json
import os.path

from . import platforms
from .builders import ar
from .builders import cc
from .builders import msvc

class Environment(object):
    version = 1
    envfile = '.bfg_environ'

    def __init__(self, bfgpath, srcdir, builddir, backend, install_prefix,
                 variables):
        self.bfgpath = bfgpath
        self.scanpath = os.path.join(os.path.dirname(bfgpath), 'arachnotron')

        self.srcdir = srcdir
        self.builddir = builddir
        self.backend = backend
        self.install_prefix = install_prefix

        self.variables = variables

        self.platform = platforms.platform_info(platforms.platform_name())

        # TODO: Come up with a more flexible way to initialize the compilers and
        # linkers for each language.
        if self.platform.name == 'windows':
            compiler = msvc.MSVCCompiler(self)
            exe_linker = msvc.MSVCLinker(self, 'executable')
            lib_linker = msvc.MSVCStaticLinker(self)
            dll_linker = msvc.MSVCLinker(self, 'shared_library')
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
            ar_linker = ar.ArLinker(self)
            self._compilers = {
                'c'  : cc.CcCompiler(self),
                'c++': cc.CxxCompiler(self),
            }
            self._linkers = {
                'executable': {
                    'c'  : cc.CcLinker(self, 'executable'),
                    'c++': cc.CxxLinker(self, 'executable'),
                },
                'static_library': {
                    'c'  : ar_linker,
                    'c++': ar_linker,
                },
                'shared_library': {
                    'c'  : cc.CcLinker(self, 'shared_library'),
                    'c++': cc.CxxLinker(self, 'shared_library'),
                },
            }

    def getvar(self, key, default=None):
        return self.variables.get(key, default)

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
        with open(os.path.join(path, self.envfile), 'w') as out:
            json.dump({
                'version': self.version,
                'data': {
                    'bfgpath': self.bfgpath,
                    'srcdir': self.srcdir,
                    'builddir': self.builddir,
                    'backend': self.backend,
                    'install_prefix': self.install_prefix,
                    'variables': self.variables,
                }
            }, out)

    @classmethod
    def load(cls, path):
        with open(os.path.join(path, cls.envfile)) as inp:
            data = json.load(inp)
        if data['version'] > cls.version:
            raise ValueError('saved version exceeds expected version')
        return Environment(**data['data'])
