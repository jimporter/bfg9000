from itertools import chain
from six.moves import cStringIO as StringIO

from .hooks import builtin
from .. import safe_str
from ..backends.make import writer as make
from ..backends.ninja import writer as ninja
from ..build_inputs import Edge
from ..file_types import Phony
from ..shell import posix as pshell


class Command(Edge):
    def __init__(self, build, name, cmd=None, cmds=None, environment=None,
                 extra_deps=None):
        if (cmd is None) == (cmds is None):
            raise ValueError('exactly one of "cmd" or "cmds" must be ' +
                             'specified')
        elif cmds is None:
            cmds = [cmd]

        self.cmds = cmds
        self.env = environment or {}
        Edge.__init__(self, build, Phony(name), extra_deps)


@builtin.globals('build_inputs')
def command(build, *args, **kwargs):
    return Command(build, *args, **kwargs).public_output


@make.rule_handler(Command)
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
        phony=True
    )


@ninja.rule_handler(Command)
def ninja_command(rule, build_inputs, buildfile, env):
    ninja.command_build(
        buildfile, env,
        output=rule.output,
        inputs=rule.extra_deps,
        commands=rule.cmds,
        environ=rule.env
    )

try:
    from ..backends.msbuild import writer as msbuild

    @msbuild.rule_handler(Command)
    def msbuild_command(rule, build_inputs, solution, env):
        # XXX: Support environment variables
        project = msbuild.ExecProject(
            name=rule.output.path,
            version=env.getvar('VISUALSTUDIOVERSION'),
            platform=env.getvar('PLATFORM'),
            srcdir=env.srcdir.string(),
            commands=rule.cmds,
            dependencies=solution.dependencies(rule.extra_deps),
        )
        solution[rule.output] = project
except:
    pass
