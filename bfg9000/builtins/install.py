from itertools import chain
from six.moves import filter as ifilter

from .hooks import builtin
from .. import path
from ..backends.make import writer as make
from ..backends.ninja import writer as ninja
from ..build_inputs import build_input
from ..file_types import Directory, File


@build_input('install')
class InstallOutputs(object):
    def __init__(self, build_inputs, env):
        self._outputs = []

    def add(self, item, explicit=True):
        if item not in self._outputs:
            self._outputs.append(item)

        for i in item.runtime_deps:
            self.add(i, explicit=False)
        if explicit:
            for i in item.install_deps:
                self.add(i, explicit=False)

    def __nonzero__(self):
        return bool(self._outputs)

    def __iter__(self):
        return iter(self._outputs)


@builtin.globals('builtins', 'build_inputs')
def install(builtins, build, *args):
    if len(args) == 0:
        raise ValueError('expected at least one argument')
    for i in args:
        if not isinstance(i, File):
            raise TypeError('expected a file or directory')
        if i.external:
            raise ValueError('external files are not installable')

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
            src = [i.path.relpath(output.path) for i in output.files]
            dst = path.install_path(output.path.parent(), output.install_root)
            return doppel.copy_into(cmd, src, dst, directory=output.path)
        else:
            src = output.path
            dst = path.install_path(src, output.install_root)
            return doppel.copy_onto(cmd, src, dst)

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
