import warnings
from itertools import repeat

from . import builtin
from .. import shell
from ..backends.make import writer as make
from ..backends.ninja import writer as ninja
from ..build_inputs import Edge
from ..file_types import File, Node, Phony
from ..iterutils import isiterable, iterate, listify
from ..path import Path, Root
from ..shell import posix as pshell


class BaseCommand(Edge):
    def __init__(self, build, env, name, outputs, cmd=None, cmds=None,
                 environment=None, extra_deps=None, description=None):
        if (cmd is None) == (cmds is None):
            raise ValueError('exactly one of "cmd" or "cmds" must be ' +
                             'specified')
        elif cmds is None:
            cmds = [cmd]

        inputs = [i for line in cmds for i in iterate(line)
                  if isinstance(i, Node) and i.creator]
        cmds = [env.run_arguments(line) for line in cmds]

        self.name = name
        self.cmds = cmds
        self.inputs = inputs
        self.env = environment or {}
        Edge.__init__(self, build, outputs, extra_deps=extra_deps,
                      description=description)


class Command(BaseCommand):
    phony = True
    console = True

    def __init__(self, build, env, name, **kwargs):
        BaseCommand.__init__(self, build, env, name, Phony(name), **kwargs)


@builtin.function('build_inputs', 'env')
def command(build, env, name, **kwargs):
    return Command(build, env, name, **kwargs).public_output


class BuildStep(BaseCommand):
    console = False
    msbuild_output = True

    def __init__(self, build, builtins, env, name, type=None, args=None,
                 kwargs=None, always_outdated=False, **fwd_kwargs):
        self.phony = always_outdated

        name = listify(name)
        project_name = name[0]

        if type is None:
            type = builtins['auto_file']
        if not isiterable(type):
            type = repeat(type, len(name))

        if args is None:
            args = repeat([], len(name))
        else:  # pragma: no cover
            # TODO: remove this after 0.5 is released.
            warnings.warn('"args" is deprecated; use "type" instead ' +
                          '(e.g. with a lambda)')

        if kwargs is None:
            kwargs = repeat({}, len(name))
        else:  # pragma: no cover
            # TODO: remove this after 0.5 is released.
            warnings.warn('"kwargs" is deprecated; use "type" instead ' +
                          '(e.g. with a lambda)')

        outputs = [self._make_outputs(*i) for i in
                   zip(name, type, args, kwargs)]

        desc = fwd_kwargs.pop('description', 'build => ' + ' '.join(name))
        BaseCommand.__init__(self, build, env, project_name, outputs,
                             description=desc, **fwd_kwargs)

    @staticmethod
    def _make_outputs(name, type, args, kwargs):
        result = type(Path(name, Root.builddir), *args, **kwargs)
        if not isinstance(result, File):
            raise ValueError('expected a function returning a file')
        return result


@builtin.function('build_inputs', 'builtins', 'env')
def build_step(build, builtins, env, name, **kwargs):
    return BuildStep(build, builtins, env, name, **kwargs).public_output


@make.rule_handler(Command, BuildStep)
def make_command(rule, build_inputs, buildfile, env):
    # Join all the commands onto one line so that users can use 'cd' and such.
    make.multitarget_rule(
        buildfile,
        targets=rule.output,
        deps=rule.inputs + rule.extra_deps,
        order_only=(make.directory_deps(rule.output) if
                    isinstance(rule, BuildStep) else []),
        recipe=[pshell.global_env(rule.env, rule.cmds)],
        phony=rule.phony
    )


@ninja.rule_handler(Command, BuildStep)
def ninja_command(rule, build_inputs, buildfile, env):
    ninja.command_build(
        buildfile, env,
        output=rule.output,
        inputs=rule.inputs + rule.extra_deps,
        command=shell.global_env(rule.env, rule.cmds),
        console=rule.console,
        phony=rule.phony,
        description=rule.description
    )


try:
    from ..backends.msbuild import writer as msbuild

    @msbuild.rule_handler(Command, BuildStep)
    def msbuild_command(rule, build_inputs, solution, env):
        project = msbuild.ExecProject(
            env, name=rule.name,
            commands=[shell.global_env(rule.env, rule.cmds)],
            dependencies=solution.dependencies(rule.extra_deps),
        )
        solution[rule.output[0]] = project
except ImportError:
    pass
