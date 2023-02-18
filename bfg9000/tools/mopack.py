import json
import os
import re
import yaml

from . import tool
from .common import SimpleCommand
from .. import shell
from ..exceptions import PackageResolutionError
from ..iterutils import iterate
from ..packages import Framework
from ..path import Path, Root
from ..safe_str import safe_format

_bad_dependency_ex = re.compile(r'[,[\]]')


@tool('mopack')
class Mopack(SimpleCommand):
    metadata_file = Path('mopack/mopack.json')

    def __init__(self, env):
        super().__init__(env, name='mopack', env_var='MOPACK',
                         default='mopack')

    @staticmethod
    def _dir_arg(directory):
        return ['--directory', directory] if directory else []

    @staticmethod
    def _dependency(package, submodules):
        def check(s):
            if not s or _bad_dependency_ex.search(s):
                raise ValueError('invalid dependency')
            return s

        submodules_str = ','.join(check(i) for i in iterate(submodules))
        if submodules_str:
            return '{}[{}]'.format(check(package), submodules_str)
        return check(package)

    def _call_resolve(self, cmd, config, *, flags=None, directory=None):
        result = cmd + ['resolve'] + self._dir_arg(directory)
        for k, v in self.env.install_dirs.items():
            if v is not None and v.root == Root.absolute:
                result.append(safe_format('-d{}={}', k.name, v))

        result.extend(iterate(flags))
        result.append('--')
        result.extend(iterate(config))
        return result

    def _call_usage(self, cmd, name, submodules=None, *, directory=None):
        return (cmd + ['usage'] + self._dir_arg(directory) +
                ['--json', self._dependency(name, iterate(submodules))])

    def _call_deploy(self, cmd, *, directory=None):
        return cmd + ['deploy'] + self._dir_arg(directory)

    def _call_clean(self, cmd, *, directory=None):
        return cmd + ['clean'] + self._dir_arg(directory)

    def _call_list_files(self, cmd, *, directory=None):
        return cmd + ['list-files'] + self._dir_arg(directory) + ['--json']

    def _call(self, cmd, subcmd, *args, **kwargs):
        try:
            return getattr(self, '_call_' + subcmd)(cmd, *args, **kwargs)
        except AttributeError:
            raise TypeError('unknown subcommand {!r}'.format(subcmd))

    def run(self, subcmd, *args, **kwargs):
        result = super().run(subcmd, *args, **kwargs)
        if subcmd in ['usage', 'list_files']:
            return json.loads(result.strip())
        return result


def get_usage(env, name, submodules=None, include_path=None, lib_path=None,
              lib_names=None):
    extra_env = {}
    if include_path:
        extra_env['MOPACK_INCLUDE_PATH'] = shell.join_paths(
            i.string() for i in include_path
        )
    if lib_path:
        extra_env['MOPACK_LIB_PATH'] = shell.join_paths(
            i.string() for i in lib_path
        )
    if lib_names:
        extra_env['MOPACK_LIB_NAMES'] = shell.join_paths(lib_names)

    try:
        return env.tool('mopack').run('usage', name, submodules,
                                      directory=env.builddir,
                                      extra_env=extra_env)
    except (OSError, shell.CalledProcessError) as e:
        stdout = getattr(e, 'stdout', None)
        msg = ((stdout and json.loads(stdout.strip()).get('error')) or
               'unable to resolve package {!r}'.format(name))
        raise PackageResolutionError(msg)


def to_frameworks(libs):
    def convert(lib):
        if isinstance(lib, dict):
            if lib['type'] == 'framework':
                return Framework(lib['name'])
            raise ValueError('unknown type {!r}'.format(lib['type']))
        return lib

    return [convert(i) for i in libs]


def _dump_yaml(data):
    # `sort_keys` only works on newer versions of PyYAML, so don't worry too
    # much if we can't use it.
    try:
        return yaml.dump(data, sort_keys=False)
    except TypeError:  # pragma: no cover
        return yaml.dump(data)


def make_options_yml(env):
    options = {}
    if env.target_platform != env.host_platform:
        options['target_platform'] = env.target_platform.name
    if env.variables.changes:
        options['env'] = env.variables.changes
    if env.toolchain.path:
        options['builders'] = {'bfg9000': {
            'toolchain': env.toolchain.path.string()
        }}

    path = Path('mopack-options.yml')
    if options:
        with open(path.string(env.base_dirs), 'w') as f:
            print(_dump_yaml({'options': options}), file=f)
        return path
    else:
        try:
            os.remove(path.string(env.base_dirs))
        except FileNotFoundError:
            pass
