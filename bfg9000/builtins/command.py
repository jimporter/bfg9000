from itertools import chain, repeat
from six.moves import cStringIO as StringIO

from . import builtin
from .file_types import source_file
from .. import safe_str
from ..backends.make import writer as make
from ..backends.ninja import writer as ninja
from ..build_inputs import Edge
from ..file_types import File, Phony
from ..iterutils import isiterable, listify
from ..path import Path, Root
from ..shell import posix as pshell


class BaseCommand(Edge):
    def __init__(self, build, name, outputs, cmd=None, cmds=None,
                 environment=None, extra_deps=None):
        if (cmd is None) == (cmds is None):
            raise ValueError('exactly one of "cmd" or "cmds" must be ' +
                             'specified')
        elif cmds is None:
            cmds = [cmd]

        self.name = name
        self.cmds = cmds
        self.env = environment or {}
        Edge.__init__(self, build, outputs, extra_deps=extra_deps)


class Command(BaseCommand):
    def __init__(self, build, name, **kwargs):
        BaseCommand.__init__(self, build, name, Phony(name), **kwargs)


@builtin.globals('build_inputs')
def command(build, name, **kwargs):
    return Command(build, name, **kwargs).public_output


class BuildStep(BaseCommand):
    def __init__(self, build, name, **kwargs):
        name = listify(name)
        project_name = name[0]

        type = kwargs.pop('type', source_file)
        if not isiterable(type):
            type = repeat(type, len(name))

        type_args = kwargs.pop('args', None)
        if type_args is None:
            type_args = repeat([], len(name))

        type_kwargs = kwargs.pop('kwargs', None)
        if type_kwargs is None:
            type_kwargs = repeat({}, len(name))

        outputs = [self._make_outputs(*i) for i in
                   zip(name, type, type_args, type_kwargs)]

        BaseCommand.__init__(self, build, project_name, outputs, **kwargs)

    @staticmethod
    def _make_outputs(name, type, args, kwargs):
        f = getattr(type, 'type', type)
        result = f(Path(name, Root.builddir), *args, **kwargs)
        if not isinstance(result, File):
            raise ValueError('expected a function returning a file')
        return result


@builtin.globals('build_inputs')
def build_step(build, name, **kwargs):
    return BuildStep(build, name, **kwargs).public_output


@make.rule_handler(Command, BuildStep)
def make_command(rule, build_inputs, buildfile, env):
    # Join all the commands onto one line so that users can use 'cd' and such.
    out = make.Writer(StringIO())
    env_vars = pshell.global_env(rule.env)

    for line in pshell.join_commands(chain(env_vars, rule.cmds)):
        out.write_shell(line)

    buildfile.rule(
        target=rule.output,
        deps=rule.extra_deps,
        recipe=[safe_str.escaped_str(out.stream.getvalue())],
        phony=isinstance(rule, Command)
    )


@ninja.rule_handler(Command, BuildStep)
def ninja_command(rule, build_inputs, buildfile, env):
    ninja.command_build(
        buildfile, env,
        output=rule.output,
        inputs=rule.extra_deps,
        commands=rule.cmds,
        environ=rule.env,
        console=isinstance(rule, Command)
    )


try:
    from ..backends.msbuild import writer as msbuild

    @msbuild.rule_handler(Command, BuildStep)
    def msbuild_command(rule, build_inputs, solution, env):
        # XXX: Support environment variables
        project = msbuild.ExecProject(
            env, name=rule.name,
            commands=rule.cmds,
            dependencies=solution.dependencies(rule.extra_deps),
        )
        solution[rule.output[0]] = project
except:
    pass
