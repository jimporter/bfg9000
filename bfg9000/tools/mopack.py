import json
import os
import re
import yaml

from . import tool
from .common import SimpleCommand
from .. import shell
from ..exceptions import PackageResolutionError
from ..iterutils import iterate
from ..objutils import memoize_method
from ..path import Path, Root
from ..safe_str import safe_format
from ..shell import join_paths as jp

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

        if submodules_str := ','.join(check(i) for i in iterate(submodules)):
            return '{}[{}]'.format(check(package), submodules_str)
        return check(package)

    @memoize_method
    def _toolchain_env(self):
        # TODO: We really shouldn't assume that mopack just wants the C
        # builder's configuration. Better would be to examine the default
        # language from the `projet` call, but that requires some thought about
        # how to defer `mopack resolve` until after we call that function...
        pkg = self.env.builder('c').packages
        return {
            'MOPACK_INCLUDE_PATH': jp(i.string() for i in pkg.include_dirs),
            'MOPACK_LIB_PATH': jp(i.string() for i in pkg.lib_dirs),
            'MOPACK_LIB_NAMES': jp(pkg.lib_names),
            'MOPACK_AUTO_LINK': str(pkg.builder.auto_link).lower(),
        }

    def _call_resolve(self, cmd, config, *, flags=None, directory=None,
                      verbose=False):
        result = cmd
        if verbose:
            result.append('--verbose')
        result.append('resolve')
        result.extend(self._dir_arg(directory))

        for k, v in self.env.install_dirs.items():
            if v is not None and v.root == Root.absolute:
                result.append(safe_format('-d{}={}', k.name, v))

        result.extend(iterate(flags))
        result.append('--')
        result.extend(iterate(config))
        return result

    def _call_linkage(self, cmd, name, submodules=None, *, directory=None):
        return (cmd + ['linkage'] + self._dir_arg(directory) +
                ['--json', self._dependency(name, iterate(submodules))])

    def _call_deploy(self, cmd, *, directory=None):
        return cmd + ['deploy'] + self._dir_arg(directory)

    def _call_clean(self, cmd, *, directory=None):
        return cmd + ['clean'] + self._dir_arg(directory)

    def _call_list_files(self, cmd, *, directory=None):
        return cmd + ['list-files'] + self._dir_arg(directory) + ['--json']

    def _call(self, cmd, subcmd, *args, **kwargs):
        self._toolchain_env()
        try:
            return getattr(self, '_call_' + subcmd)(cmd, *args, **kwargs)
        except AttributeError:
            raise TypeError('unknown subcommand {!r}'.format(subcmd))

    def run(self, subcmd, *args, extra_env=None, **kwargs):
        if extra_env is None:
            extra_env = self._toolchain_env()
        else:
            extra_env = {**extra_env, **self._toolchain_env()}

        result = super().run(subcmd, *args, extra_env=extra_env, **kwargs)
        if subcmd in ['linkage', 'list_files']:
            return json.loads(result.strip())
        return result


def get_linkage(env, name, submodules=None):
    try:
        kwargs = {'stderr': shell.Mode.normal} if env.verbose else {}
        return env.tool('mopack').run('linkage', name, submodules,
                                      directory=env.builddir, **kwargs)
    except (OSError, shell.CalledProcessError) as e:
        stdout = getattr(e, 'stdout', None)
        msg = ((stdout and json.loads(stdout.strip()).get('error')) or
               'unable to resolve package {!r}'.format(name))
        raise PackageResolutionError(msg)


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
