import json
import os
from packaging.version import Version
from six import iteritems, string_types
from six.moves import reduce

from .backends import get_backends
from .iterutils import intersect, isiterable, iterate
from .languages import lang_link
from .path import Path, InstallRoot
from . import platforms
from . import tools


class EnvVersionError(RuntimeError):
    pass


class Environment(object):
    version = 6
    envfile = '.bfg_environ'

    def __new__(cls, *args, **kwargs):
        env = object.__new__(cls)
        env.__builders = {}
        env.__tools = {}
        return env

    def __init__(self, bfgpath, backend, backend_version, srcdir, builddir,
                 install_dirs):
        self.bfgpath = bfgpath
        self.backend = backend
        self.backend_version = backend_version

        self.srcdir = srcdir
        self.builddir = builddir
        self.install_dirs = install_dirs

        self.variables = dict(os.environ)
        self.platform = platforms.platform_info()

    def getvar(self, key, default=None):
        return self.variables.get(key, default)

    def builder(self, lang):
        if isiterable(lang):
            langs = reduce(
                intersect, (lang_link[i] for i in iterate(lang) if i)
            )
            if len(langs) == 0:
                raise ValueError('unable to find a valid linker')
            lang = langs[0]

        if lang not in self.__builders:
            self.__builders[lang] = tools.get_builder(lang, self)
        return self.__builders[lang]

    def compiler(self, lang):
        if not isinstance(lang, string_types):
            raise TypeError('only one lang supported')
        return self.builder(lang).compiler

    def linker(self, lang, mode):
        return self.builder(lang).linkers[mode]

    def tool(self, name):
        if name not in self.__tools:
            self.__tools[name] = tools.get_tool(name, self)
        return self.__tools[name]

    def save(self, path):
        with open(os.path.join(path, self.envfile), 'w') as out:
            json.dump({
                'version': self.version,
                'data': {
                    'bfgpath': self.bfgpath.to_json(),
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

        env = Environment.__new__(Environment)

        for i in ['backend', 'variables']:
            setattr(env, i, data[i])

        if version <= 5:
            backend_version = get_backends()[data['backend']].version()
        else:
            backend_version = Version(data['backend_version'])
        setattr(env, 'backend_version', backend_version)

        for i in ['bfgpath', 'srcdir', 'builddir']:
            if version <= 4 or (version <= 5 and i == 'bfgpath'):
                setattr(env, i, Path(data[i]))
            else:
                setattr(env, i, Path.from_json(data[i]))

        env.platform = platforms.platform_info(data['platform'])
        env.install_dirs = {
            InstallRoot[k]: Path.from_json(v) for k, v in
            iteritems(data['install_dirs'])
        }

        return env
