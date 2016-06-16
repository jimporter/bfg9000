import json
import os
import warnings
from packaging.version import LegacyVersion
from six import iteritems

from .backends import list_backends
from .path import InstallRoot, Path, Root
from . import platforms
from . import tools


class EnvVersionError(RuntimeError):
    pass


class Environment(object):
    version = 7
    envfile = '.bfg_environ'

    def __new__(cls, *args, **kwargs):
        env = object.__new__(cls)
        env.__builders = {}
        env.__tools = {}
        return env

    def __init__(self, bfgdir, backend, backend_version, srcdir, builddir,
                 install_dirs):
        self.bfgdir = bfgdir
        self.backend = backend
        self.backend_version = backend_version

        self.srcdir = srcdir
        self.builddir = builddir
        self.install_dirs = install_dirs

        self.variables = dict(os.environ)
        self.platform = platforms.platform_info()

    @property
    def path_roots(self):
        return {
            Root.srcdir: self.srcdir,
            Root.builddir: self.builddir
        }

    def getvar(self, key, default=None):
        return self.variables.get(key, default)

    def builder(self, lang):
        if lang not in self.__builders:
            self.__builders[lang] = tools.get_builder(lang, self)
        return self.__builders[lang]

    def compiler(self, lang):
        warnings.warn('env.compiler(lang) is deprecated; please use ' +
                      'env.builder(lang).compiler instead', DeprecationWarning)
        return self.builder(lang).compiler

    def linker(self, lang, mode):
        warnings.warn('env.linker(lang, mode) is deprecated; please use ' +
                      'env.builder(lang).linker(mode) instead',
                      DeprecationWarning)
        return self.builder(lang).linker(mode)

    def tool(self, name):
        if name not in self.__tools:
            self.__tools[name] = tools.get_tool(name, self)
        return self.__tools[name]

    def save(self, path):
        with open(os.path.join(path, self.envfile), 'w') as out:
            json.dump({
                'version': self.version,
                'data': {
                    'bfgdir': self.bfgdir.to_json(),
                    'platform': self.platform.name,
                    'backend': self.backend,
                    'backend_version': str(self.backend_version),
                    'variables': self.variables,
                    'srcdir': self.srcdir.to_json(),
                    'builddir': self.builddir.to_json(),
                    'install_dirs': {
                        k.name: v.to_json() for k, v in
                        iteritems(self.install_dirs)
                    },
                }
            }, out)

    @classmethod
    def load(cls, path):
        with open(os.path.join(path, cls.envfile)) as inp:
            state = json.load(inp)
            version, data = state['version'], state['data']
        if version > cls.version:
            raise EnvVersionError('saved version exceeds expected version')

        # Upgrade from older versions of the Environment if necessary.

        # v5 converts srcdir and builddir to Path objects internally.
        if version < 5:
            for i in ('srcdir', 'builddir'):
                data[i] = Path(data[i]).to_json()

        # v6 adds persistence for the backend's version and converts bfgpath to
        # a Path object internally.
        if version < 6:
            backend = list_backends()[data['backend']]
            data['backend_version'] = str(backend.version())
            data['bfgpath'] = Path(data['bfgpath']).to_json()

        # v7 replaces bfgpath with bfgdir.
        if version < 7:
            bfgdir = Path.from_json(data['bfgpath']).parent()
            data['bfgdir'] = bfgdir.to_json()
            del data['bfgpath']

        # Now that we've upgraded, initialize the Environment object.
        env = Environment.__new__(Environment)

        for i in ['backend', 'variables']:
            setattr(env, i, data[i])

        setattr(env, 'backend_version', LegacyVersion(data['backend_version']))

        for i in ('bfgdir', 'srcdir', 'builddir'):
            setattr(env, i, Path.from_json(data[i]))

        env.platform = platforms.platform_info(data['platform'])
        env.install_dirs = {
            InstallRoot[k]: Path.from_json(v) for k, v in
            iteritems(data['install_dirs'])
        }

        return env
