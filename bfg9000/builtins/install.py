from itertools import chain
from six.moves import filter as ifilter

from .hooks import builtin
from .. import path
from ..backends.make import writer as make
from ..backends.ninja import writer as ninja
from ..build_inputs import build_input
from ..file_types import Directory


@build_input('install')
class InstallTargets(object):
    def __init__(self):
        self.files = []
        self.dirs = []

    def add(self, item, explicit=True):
        group = self.dirs if isinstance(item, Directory) else self.files
        if item not in group:
            group.append(item)

        for i in item.runtime_deps:
            self.add(i, explicit=False)
        if explicit:
            for i in item.install_deps:
                self.add(i, explicit=False)

    def __nonzero__(self):
        return bool(self.files or self.dirs)


@builtin.globals('builtins', 'build_inputs')
def install(builtins, build, *args):
    if len(args) == 0:
        raise ValueError('expected at least one argument')
    for i in args:
        builtins['default'](i)
        build['install'].add(i)


def _install_commands(backend, build_inputs, buildfile, env):
    install_targets = build_inputs['install']
    if not install_targets:
        return None

    install = env.tool('install')
    mkdir_p = env.tool('mkdir_p')

    def install_line(file):
        kind = file.install_kind
        cmd = backend.cmd_var(install, buildfile)

        if kind != 'program':
            kind = 'data'
            cmd = [cmd] + install.data_args
        cmdname = 'install_' + kind
        if backend == make:
            cmdname = cmdname.upper()

        cmd = buildfile.variable(cmdname, cmd, backend.Section.command, True)
        src = file.path
        dst = path.install_path(file.path, file.install_root)
        return install(cmd, src, dst)

    def mkdir_line(dir):
        src = dir.path
        dst = path.install_path(dir.path.parent(), dir.install_root)
        return mkdir_p.copy(backend.cmd_var(mkdir_p, buildfile), src, dst)

    def post_install(file):
        if file.post_install:
            line = file.post_install
            line[0] = backend.cmd_var(line[0], buildfile)
            return line

    return list(chain(
        (install_line(i) for i in install_targets.files),
        (mkdir_line(i) for i in install_targets.dirs),
        ifilter(None, (post_install(i) for i in install_targets.files))
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
