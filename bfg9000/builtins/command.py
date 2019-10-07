import warnings
from itertools import chain, repeat
from six.moves import filter as ifilter

from . import builtin
from .. import shell
from ..backends.make import writer as make
from ..backends.ninja import writer as ninja
from ..build_inputs import Edge
from ..file_types import File, Node, Phony
from ..iterutils import isiterable, iterate, listify
from ..objutils import convert_each
from ..path import Path, Root
from ..safe_str import jbos, safe_str, safe_string
from ..shell import posix as pshell


class Placeholder(safe_string):
    def __init__(self, field, key=slice(None)):
        self._field = field
        self._key = key

    def __getitem__(self, key):
        if self._key != slice(None):
            raise TypeError('{!r} object has already been indexed'
                            .format(type(self).__name__))
        return Placeholder(self._field, key)

    def expand(self, rule):
        data = getattr(rule, self._field)
        if isinstance(self._key, slice):
            return data[self._key]
        else:
            return [data[self._key]]

    @classmethod
    def expand_word(cls, word, rule):
        if isinstance(word, cls):
            return word.expand(rule)
        elif isinstance(word, jbos):
            placeholders = list(ifilter(lambda i: isinstance(i[1], cls),
                                        enumerate(word.bits)))
            if len(placeholders) > 1:
                raise ValueError('only one placeholder per word permitted')
            elif len(placeholders) == 1:
                index, bit = placeholders[0]
                expanded = bit.expand(rule)
                pre, post = word.bits[:index], word.bits[index + 1:]
                return [jbos(*(pre + (safe_str(i),) + post)) for i in expanded]
        return [word]


Input = Placeholder('files')
Output = Placeholder('output')


class BaseCommand(Edge):
    def __init__(self, build, env, name, outputs, cmds, files,
                 environment=None, phony=False, extra_deps=None,
                 description=None):
        self.name = name
        self.files = files
        self.phony = phony

        implicit = [i for line in cmds for i in iterate(line)
                    if isinstance(i, Node) and (i.creator or not phony)]
        implicit.extend(iterate(extra_deps))

        Edge.__init__(self, build, outputs, extra_deps=implicit,
                      description=description)

        # Do this after Edge.__init__ so that self.output is set for our
        # placeholders.
        self.cmds = [env.run_arguments(self._expand_cmd(line))
                     for line in cmds]
        self.env = environment or {}

    @staticmethod
    def convert_args(builtins, kwargs):
        cmd = kwargs.pop('cmd', None)
        cmds = kwargs.pop('cmds', None)
        if (cmd is None) == (cmds is None):
            raise ValueError('exactly one of "cmd" or "cmds" must be ' +
                             'specified')
        kwargs['cmds'] = [cmd] if cmds is None else cmds

        convert_each(kwargs, 'files', builtins['auto_file'])
        return kwargs

    def _expand_cmd(self, cmd):
        if not isiterable(cmd):
            expanded = Placeholder.expand_word(cmd, self)
            if len(expanded) > 1:
                raise ValueError('placeholder can only expand to one item ' +
                                 'when used in a string command line')
            return expanded[0]
        return list(chain.from_iterable(
            Placeholder.expand_word(i, self) for i in cmd)
        )


class Command(BaseCommand):
    console = True

    def __init__(self, build, env, name, **kwargs):
        BaseCommand.__init__(self, build, env, name, Phony(name), phony=True,
                             **kwargs)


@builtin.function('build_inputs', 'builtins', 'env')
def command(build, builtins, env, name, **kwargs):
    kwargs = Command.convert_args(builtins, kwargs)
    return Command(build, env, name, **kwargs).public_output


command.input = Input


class BuildStep(BaseCommand):
    console = False
    msbuild_output = True

    def __init__(self, build, env, name, type=None, args=None, kwargs=None,
                 always_outdated=False, **fwd_kwargs):
        name = listify(name)
        project_name = name[0]

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
                             phony=always_outdated, description=desc,
                             **fwd_kwargs)

    @staticmethod
    def convert_args(builtins, kwargs):
        if kwargs.get('type') is None:
            kwargs['type'] = builtins['auto_file']
        return BaseCommand.convert_args(builtins, kwargs)

    @staticmethod
    def _make_outputs(name, type, args, kwargs):
        result = type(Path(name, Root.builddir), *args, **kwargs)
        if not isinstance(result, File):
            raise ValueError('expected a function returning a file')
        return result


@builtin.function('build_inputs', 'builtins', 'env')
def build_step(build, builtins, env, name, **kwargs):
    kwargs = BuildStep.convert_args(builtins, kwargs)
    return BuildStep(build, env, name, **kwargs).public_output


build_step.input = Input
build_step.output = Output


@make.rule_handler(Command, BuildStep)
def make_command(rule, build_inputs, buildfile, env):
    # Join all the commands onto one line so that users can use 'cd' and such.
    make.multitarget_rule(
        buildfile,
        targets=rule.output,
        deps=rule.files + rule.extra_deps,
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
        inputs=rule.files,
        implicit=rule.extra_deps,
        command=shell.global_env(rule.env, rule.cmds),
        console=rule.console,
        phony=rule.phony,
        description=rule.description
    )


try:
    from ..backends.msbuild import writer as msbuild

    @msbuild.rule_handler(Command, BuildStep)
    def msbuild_command(rule, build_inputs, solution, env):
        command = msbuild.CommandProject.convert_command(shell.global_env(
            rule.env, rule.cmds
        ))
        project = msbuild.CommandProject(
            env, name=rule.name,
            commands=[msbuild.CommandProject.task(
                'Exec', Command=command, WorkingDirectory='$(OutDir)'
            )],
            dependencies=solution.dependencies(rule.extra_deps),
        )
        solution[rule.output[0]] = project
except ImportError:  # pragma: no cover
    pass
