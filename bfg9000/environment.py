import json
import os

from .path import Path, InstallRoot
from . import platforms
from .tools import ar, cc, msvc, install, mkdir_p, patchelf

class EnvVersionError(RuntimeError):
    pass

class Environment(object):
    version = 4
    envfile = '.bfg_environ'

    def __new__(cls, *args, **kwargs):
        env = object.__new__(cls, *args, **kwargs)
        env.__compilers = {}
        env.__linkers = {
            'executable': {},
            'static_library': {},
            'shared_library': {}
        }
        env.__tools = {}
        return env

    def __init__(self, bfgpath, backend, srcdir, builddir, install_dirs):
        self.bfgpath = bfgpath
        self.backend = backend

        self.srcdir = srcdir
        self.builddir = builddir
        self.install_dirs = install_dirs

        self.variables = dict(os.environ)
        self.platform = platforms.platform_info()

    def __load_compiler(self, lang):
        # TODO: Come up with a more flexible way to initialize the compilers and
        # linkers for each language.
        if lang not in ['c', 'c++']:
            raise ValueError('unknown language "{}"'.format(lang))

        if self.platform.name == 'windows':
            self.__compilers[lang] = msvc.MSVCCompiler(self)
            for mode in ['executable', 'shared_library']:
                self.__linkers[mode][lang] = msvc.MSVCLinker(self, mode)
            self.__linkers['static_library'][lang] = msvc.MSVCStaticLinker(self)
        else:
            if lang == 'c':
                self.__compilers[lang] = cc.CcCompiler(self)
                linker = cc.CcLinker
            else: # lang == 'c++'
                self.__compilers[lang] = cc.CxxCompiler(self)
                linker = cc.CxxLinker
            for mode in ['executable', 'shared_library']:
                self.__linkers[mode][lang] = linker(self, mode)
            self.__linkers['static_library'][lang] = ar.ArLinker(self)

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
        if lang not in self.__compilers:
            self.__load_compiler(lang)
        return self.__compilers[lang]

    def linker(self, lang, mode):
        # TODO: Be more intelligent about this when we support more languages.
        if not isinstance(lang, basestring):
            if 'c++' in lang:
                lang = 'c++'

        if lang not in self.__linkers[mode]:
            self.__load_compiler(lang)
        return self.__linkers[mode][lang]

    def tool(self, name):
        if name not in self.__tools:
            if name == 'install':
                self.__tools[name] = install.Install(self)
            elif name == 'patchelf':
                # XXX: Only do this on Linux?
                self.__tools[name] = patchelf.PatchElf(self)
            elif name == 'mkdir_p':
                self.__tools[name] = mkdir_p.MkdirP(self)
            else:
                raise ValueError('unknown tool "{}"'.format(name))
        return self.__tools[name]

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
                        k.name: v.to_json() for k, v in
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
            state['data'][InstallRoot.prefix] = Path(prefix)
            for i in [InstallRoot.bindir, InstallRoot.libdir,
                      InstallRoot.includedir]:
                state['data']['install_dirs'][i] = platform.install_paths[i]
        else:
            state['data']['install_dirs'] = {
                InstallRoot[k]: Path.from_json(v) for k, v in
                state['data']['install_dirs'].iteritems()
            }

        env = Environment.__new__(Environment)
        for k, v in state['data'].iteritems():
            setattr(env, k, v)
        return env
