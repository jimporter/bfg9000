from itertools import chain, repeat
from six.moves import cStringIO as StringIO

from .file_types import source_file
from .hooks import builtin
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
        Edge.__init__(self, build, outputs, extra_deps)


class Command(BaseCommand):
    def __init__(self, build, name, *args, **kwargs):
        BaseCommand.__init__(self, build, name, Phony(name), *args, **kwargs)


@builtin.globals('build_inputs')
def command(build, *args, **kwargs):
    return Command(build, *args, **kwargs).public_output


class BuildStep(BaseCommand):
    def __init__(self, build, name, cmd=None, cmds=None, environment=None,
                 type=source_file, args=None, kwargs=None, extra_deps=None):
        name = listify(name)
        project_name = name[0]
        if not isiterable(type):
            type = repeat(type, len(name))
        if args is None:
            args = repeat([], len(name))
        if kwargs is None:
            kwargs = repeat({}, len(name))

        outputs = [self._make_outputs(*i) for i in
                   zip(name, type, args, kwargs)]

        BaseCommand.__init__(self, build, project_name, outputs, cmd, cmds,
                             environment, extra_deps)

    @staticmethod
    def _make_outputs(name, type, args, kwargs):
        f = getattr(type, 'type', type)
        result = f(Path(name, Root.builddir), *args, **kwargs)
        if not isinstance(result, File):
            raise ValueError('expected a function returning a file')
        return result


@builtin.globals('build_inputs')
def build_step(build, *args, **kwargs):
    return BuildStep(build, *args, **kwargs).public_output


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
