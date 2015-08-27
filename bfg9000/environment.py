import json
import os

from .path import Path, InstallRoot
from . import platforms
from . import tools

class EnvVersionError(RuntimeError):
    pass

class Environment(object):
    version = 4
    envfile = '.bfg_environ'

    def __new__(cls, *args, **kwargs):
        env = object.__new__(cls, *args, **kwargs)
        env.__builders = {}
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
        if lang not in self.__builders:
            self.__builders[lang] = tools.get_builder(lang, self)
        return self.__builders[lang].compiler

    def linker(self, lang, mode):
        # TODO: Be more intelligent about this when we support more languages.
        if not isinstance(lang, basestring):
            if 'c++' in lang:
                lang = 'c++'

        if lang not in self.__builders:
            self.__builders[lang] = tools.get_builder(lang, self)
        return self.__builders[lang].linkers[mode]

    def tool(self, name):
        if name not in self.__tools:
            self.__tools[name] = tools.get_tool(name, self)
        return self.__tools[name]

    def save(self, path):
        with open(os.path.join(path, self.envfile), 'w') as out:
            json.dump({
                'version': self.version,
                'data': {
                    'bfgpath': self.bfgpath,
                    'platform': self.platform.name,
                    'backend': self.backend,
                    'variables': self.variables,
                    'srcdir': self.srcdir,
                    'builddir': self.builddir,
                    'install_dirs': {
                        k.name: v.to_json() for k, v in
                        self.install_dirs.iteritems()
                    },
                }
            }, out)

    @classmethod
    def load(cls, path):
        with open(os.path.join(path, cls.envfile)) as inp:
            state = json.load(inp)
        if state['version'] > cls.version:
            raise EnvVersionError('saved version exceeds expected version')

        env = Environment.__new__(Environment)

        for i in ['bfgpath', 'backend', 'variables', 'srcdir', 'builddir']:
            setattr(env, i, state['data'][i])

        env.platform = platforms.platform_info(state['data']['platform'])
        env.install_dirs = {
            InstallRoot[k]: Path.from_json(v) for k, v in
            state['data']['install_dirs'].iteritems()
        }

        return env
