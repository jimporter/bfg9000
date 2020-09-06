import json
import os
import platform
from collections import namedtuple

from . import platforms
from . import tools
from . import shell
from .backends import list_backends
from .file_types import Executable, Node
from .iterutils import first, isiterable, listify
from .path import InstallRoot, Path, Root
from .tools.common import Command
from .versioning import Version

LibraryMode = namedtuple('LibraryMode', ['shared', 'static'])


def try_to_json(value):
    return value.to_json() if value is not None else None


def try_from_json(type, value):
    return type.from_json(value) if value is not None else None


def try_as_directory(path):
    return path.as_directory() if path is not None else None


class EnvVersionError(RuntimeError):
    pass


class EnvVarDict(dict):
    def __setitem__(self, key, value):
        if ( not isinstance(key, str) or
             not isinstance(value, str) ):  # pragma: no cover
            raise TypeError('expected a string')
        super().__setitem__(key, value)


class Toolchain:
    def __init__(self, path=None):
        self.path = path

    def to_json(self):
        return {
            'path': try_to_json(self.path),
        }

    @classmethod
    def from_json(cls, data):
        return cls(
            path=try_from_json(Path, data['path']),
        )


class Environment:
    version = 14
    envfile = '.bfg_environ'

    Mode = shell.Mode

    def __new__(cls, *args, **kwargs):
        env = object.__new__(cls)
        tools.init()
        env.__builders = {}
        env.__tools = {}
        return env

    def __init__(self, bfgdir, backend, backend_version, srcdir, builddir):
        self.bfgdir = bfgdir.as_directory()
        self.backend = backend
        self.backend_version = backend_version

        self.host_platform = platforms.host.platform_info()
        self.target_platform = platforms.target.platform_info()

        self.srcdir = srcdir.as_directory()
        self.builddir = try_as_directory(builddir)
        self.install_dirs = {}
        self.toolchain = Toolchain()

        self.initial_variables = dict(os.environ)
        self.init_variables()

    def finalize(self, install_dirs, library_mode, extra_args=None):
        # Fill in any install dirs that aren't already set (e.g. by a
        # toolchain file) with defaults from the target platform, but skip
        # absolute paths if this is a cross-compilation build.
        for k, v in self.target_platform.install_dirs.items():
            if self.install_dirs.get(k):
                continue
            elif self.is_cross and v and v.root == Root.absolute:
                self.install_dirs[k] = None
            else:
                self.install_dirs[k] = try_as_directory(v)

        for k, v in install_dirs.items():
            if v:
                self.install_dirs[k] = v.as_directory()

        self.library_mode = LibraryMode(*library_mode)
        self.extra_args = extra_args

    def init_variables(self):
        self.variables = EnvVarDict(self.initial_variables)

    @property
    def is_cross(self):
        return self.host_platform != self.target_platform

    @property
    def base_dirs(self):
        dirs = {
            Root.srcdir: self.srcdir,
            Root.builddir: self.builddir
        }
        dirs.update(self.install_dirs)
        return dirs

    @property
    def supports_destdir(self):
        return all(i and (i.root != Root.absolute or not i.has_drive())
                   for i in self.install_dirs.values())

    def getvar(self, key, default=None):
        return self.variables.get(key, default)

    def builder(self, lang):
        if lang not in self.__builders:
            self.__builders[lang] = tools.get_builder(self, lang)
        return self.__builders[lang]

    def tool(self, name):
        if name not in self.__tools:
            self.__tools[name] = tools.get_tool(self, name)
        return self.__tools[name]

    def _runner(self, lang):
        try:
            return self.builder(lang).runner
        except tools.ToolNotFoundError:
            try:
                return self.tool(tools.get_tool_runner(lang))
            except tools.ToolNotFoundError:
                return None

    def run_arguments(self, args, lang=None):
        if isinstance(args, Node):
            args = [args]
        elif isiterable(args):
            args = listify(args)
        else:
            return args

        if len(args) == 0 or not isinstance(args[0], Node):
            return args

        if lang is None:
            lang = first(getattr(args[0], 'lang', None), default=None)
        runner = self._runner(lang)
        if runner:
            return runner.run_arguments(args[0]) + args[1:]

        if not isinstance(args[0], Executable):
            raise TypeError('expected an executable for {} to run'
                            .format(lang))
        return args

    def execute(self, args, *, env=None, extra_env=None, **kwargs):
        if env is None:
            env = self.variables
        if extra_env:
            env = env.copy()
            env.update(extra_env)

        if not kwargs.get('shell', False):
            args = Command.convert_args(args, lambda x: x.command)

        return shell.execute(args, env=env, base_dirs=self.base_dirs,
                             **kwargs)

    def run(self, args, lang=None, *posargs, **kwargs):
        return self.execute(self.run_arguments(args, lang), *posargs, **kwargs)

    def save(self, path):
        with open(os.path.join(path, self.envfile), 'w') as out:
            json.dump({
                'version': self.version,
                'data': {
                    'bfgdir': self.bfgdir.to_json(),
                    'backend': self.backend,
                    'backend_version': str(self.backend_version),

                    'host_platform': self.host_platform.to_json(),
                    'target_platform': self.target_platform.to_json(),

                    'srcdir': self.srcdir.to_json(),
                    'builddir': self.builddir.to_json(),
                    'install_dirs': {
                        k.name: try_to_json(v)
                        for k, v in self.install_dirs.items()
                    },
                    'toolchain': self.toolchain.to_json(),

                    'library_mode': self.library_mode,
                    'extra_args': self.extra_args,

                    'initial_variables': self.initial_variables,
                    'variables': self.variables,
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
            bfgdir = Path.from_json(data['bfgpath'] + (False,)).parent()
            data['bfgdir'] = bfgdir.to_json()
            del data['bfgpath']

        # v8 adds support for user-defined command-line arguments.
        if version < 8:
            data['extra_args'] = []

        # v9 adds options for choosing the mode to build libraries in.
        if version < 9:
            data['library_mode'] = [True, False]

        # v10 adds exec_prefix to install_dirs.
        if version < 10:
            data['install_dirs']['exec_prefix'] = ['', 'prefix']
            for i in ('bindir', 'libdir'):
                if data['install_dirs'][i][1] == 'prefix':
                    data['install_dirs'][i][1] = 'exec_prefix'

        # v11 adds $(DESTDIR) support to Path objects.
        if version < 11:
            for i in ('bfgdir', 'srcdir', 'builddir'):
                data[i] += (False,)
            for i in data['install_dirs']:
                data['install_dirs'][i] += (False,)

        # v12 splits platform into host_platform and target_platform.
        if version < 12:
            platform_name = data.pop('platform')
            data['host_platform'] = data['target_platform'] = platform_name

        # v13 adds initial_variables and toolchain.
        if version < 13:
            data['initial_variables'] = data['variables']
            data['toolchain'] = {'path': None}

        # v14 adds architecture to platform objects.
        if version < 14:
            for i in ('host_platform', 'target_platform'):
                genus, species = platforms.platform_tuple(data[i])
                data[i] = {'genus': genus, 'species': species,
                           'arch': platform.machine()}

        # Now that we've upgraded, initialize the Environment object.
        env = Environment.__new__(Environment)

        env.host_platform = platforms.host.from_json(data['host_platform'])
        env.target_platform = platforms.target.from_json(
            data['target_platform']
        )

        for i in ('backend', 'extra_args', 'initial_variables', 'variables'):
            setattr(env, i, data[i])

        for i in ('bfgdir', 'srcdir', 'builddir'):
            setattr(env, i, Path.from_json(data[i]).as_directory())

        env.backend_version = Version(data['backend_version'])
        env.install_dirs = {
            InstallRoot[k]: Path.from_json(v).as_directory() if v else None
            for k, v in data['install_dirs'].items()
        }
        env.toolchain = Toolchain.from_json(data['toolchain'])
        env.library_mode = LibraryMode(*data['library_mode'])

        return env
