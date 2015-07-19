import json
import os

from .path import Path
from . import platforms
from .tools import ar, cc, msvc

class EnvVersionError(RuntimeError):
    pass

class Environment(object):
    version = 4
    envfile = '.bfg_environ'

    def __init__(self, bfgpath, backend, srcdir, builddir, install_dirs):
        self.bfgpath = bfgpath
        self.backend = backend

        self.srcdir = srcdir
        self.builddir = builddir
        self.install_dirs = install_dirs

        self.variables = dict(os.environ)
        self.platform = platforms.platform_info()
        self.__init_compilers()

    def __init_compilers(self):
        # TODO: Come up with a more flexible way to initialize the compilers and
        # linkers for each language.
        if self.platform.name == 'windows':
            compiler = msvc.MSVCCompiler(self)
            exe_linker = msvc.MSVCLinker(self, 'executable')
            lib_linker = msvc.MSVCStaticLinker(self)
            dll_linker = msvc.MSVCLinker(self, 'shared_library')
            self.__compilers = {
                'c'  : compiler,
                'c++': compiler,
            }
            self.__linkers = {
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
            self.__compilers = {
                'c'  : cc.CcCompiler(self),
                'c++': cc.CxxCompiler(self),
            }
            self.__linkers = {
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

    @property
    def depfixer(self):
        return os.path.join(os.path.dirname(self.bfgpath), 'depfixer')

    def getvar(self, key, default=None):
        return self.variables.get(key, default)

    @property
    def bin_dirs(self):
        return self.getvar('PATH', os.defpath).split(os.pathsep)

    @property
    def bin_exts(self):
        # XXX: Create something to manage host-platform stuff like this?
        # (`platforms.Platform` is for targets.)
        plat = platforms.platform_name()
        if plat == 'windows' or plat == 'cygwin':
            return self.getvar('PATHEXT', '').split(os.pathsep)
        else:
            return ['']

    @property
    def lib_dirs(self):
        paths = self.getvar('LIBRARY_PATH')
        paths = paths.split(os.pathsep) if paths else []
        return paths + self.platform.lib_dirs

    def compiler(self, lang):
        return self.__compilers[lang]

    def linker(self, lang, mode):
        if isinstance(lang, basestring):
            return self.__linkers[mode][lang]

        if not isinstance(lang, set):
            lang = set(lang)
        # TODO: Be more intelligent about this when we support more languages
        if 'c++' in lang:
            return self.__linkers[mode]['c++']
        return self.__linkers[mode]['c']

    def save(self, path):
        with open(os.path.join(path, self.envfile), 'w') as out:
            json.dump({
                'version': self.version,
                'data': {
                    'bfgpath': self.bfgpath,
                    'backend': self.backend,
                    'srcdir': self.srcdir,
                    'builddir': self.builddir,
                    'install_dirs': {
                        k: (v.raw_path, v.base) for k, v in
                        self.install_dirs.iteritems()
                    },
                    'platform': self.platform.name,
                    'variables': self.variables,
                }
            }, out)

    @classmethod
    def load(cls, path):
        with open(os.path.join(path, cls.envfile)) as inp:
            state = json.load(inp)
        if state['version'] > cls.version:
            raise EnvVersionError('saved version exceeds expected version')

        if state['version'] == 1:
            state['data']['platform'] = platforms.platform_name()

        platform = state['data']['platform'] = platforms.platform_info(
            state['data']['platform']
        )

        if state['version'] <= 3:
            prefix = state['data'].pop('install_prefix')
            state['data'][Path.prefix] = Path(prefix, Path.absolute)
            for i in ['bindir', 'libdir', 'includedir']:
                state['data']['install_dirs'][i] = platform.install_paths[i]
        else:
            install_dirs = state['data']['install_dirs']
            for k, v in install_dirs.iteritems():
                install_dirs[k] = Path(*v)

        env = Environment.__new__(Environment)
        for k, v in state['data'].iteritems():
            setattr(env, k, v)
        env.__init_compilers()
        return env
