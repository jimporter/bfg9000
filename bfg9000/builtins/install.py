import warnings
from itertools import chain
from six import itervalues
from six.moves import filter as ifilter

from . import builtin
from .. import path
from ..backends.make import writer as make
from ..backends.ninja import writer as ninja
from ..build_inputs import build_input
from ..file_types import Directory, File


@build_input('install')
class InstallOutputs(object):
    def __init__(self, build_inputs, env):
        self._outputs = []

    def add(self, item):
        for i in item.all:
            if i not in self._outputs:
                if not isinstance(i, File):
                    raise TypeError('expected a file or directory')
                if i.external:
                    raise ValueError('external files are not installable')

                self._outputs.append(i)

            for j in i.install_deps:
                self.add(j)

    def __nonzero__(self):
        return self.__bool__()

    def __bool__(self):
        return bool(self._outputs)

    def __iter__(self):
        return iter(self._outputs)


def _can_install(env):
    return all(i is not None for i in itervalues(env.install_dirs))


@builtin.globals('builtins', 'build_inputs', 'env')
def install(builtins, build, env, *args):
    if len(args) == 0:
        raise ValueError('expected at least one argument')

    can_install = _can_install(env)
    if not can_install:
        warnings.warn('unset installation directories; installation of this ' +
                      'build disabled')

    for i in args:
        if can_install:
            build['install'].add(i)
        builtins['default'](i)


def _install_commands(backend, build_inputs, buildfile, env):
    install_outputs = build_inputs['install']
    if not install_outputs:
        return None

    doppel = env.tool('doppel')

    def doppel_cmd(kind):
        cmd = backend.cmd_var(doppel, buildfile)
        name = cmd.name

        if kind != 'program':
            kind = 'data'
            cmd = [cmd] + doppel.data_args

        cmdname = '{name}_{kind}'.format(name=name, kind=kind)
        return buildfile.variable(cmdname, cmd, backend.Section.command, True)

    def install_line(output):
        cmd = doppel_cmd(output.install_kind)
        if isinstance(output, Directory):
            if output.files is not None:
                src = [i.path.relpath(output.path) for i in output.files]
                dst = path.install_path(output.path, output.install_root,
                                        directory=True)
                return doppel(cmd, 'into', src, dst, directory=output.path)

            warnings.warn(
                ('installed directory {!r} has no matching files; did you ' +
                 'forget to set `include`?').format(output.path)
            )

        src = output.path
        dst = path.install_path(src, output.install_root)
        return doppel(cmd, 'onto', src, dst)

    def post_install(output):
        if output.post_install:
            line = output.post_install
            line[0] = backend.cmd_var(line[0], buildfile)
            return line

    return list(chain(
        (install_line(i) for i in install_outputs),
        ifilter(None, (post_install(i) for i in install_outputs))
    ))


@make.post_rule
def make_install_rule(build_inputs, buildfile, env):
    recipe = _install_commands(make, build_inputs, buildfile, env)
    if recipe:
        buildfile.rule(
            target='install',
            deps='all',
            recipe=recipe,
            phony=True
        )


@ninja.post_rule
def ninja_install_rule(build_inputs, buildfile, env):
    commands = _install_commands(ninja, build_inputs, buildfile, env)
    if commands:
        ninja.command_build(
            buildfile, env,
            output='install',
            inputs=['all'],
            commands=commands
        )
