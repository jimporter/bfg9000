from io import StringIO

from . import builtin
from .. import safe_str
from .. import shell
from ..backends.make import writer as make
from ..backends.ninja import writer as ninja
from ..build_inputs import build_input
from ..file_types import Node
from ..iterutils import first, iterate
from ..shell import posix as pshell


@build_input('tests')
class TestInputs:
    def __init__(self, build_inputs, env):
        self.tests = []
        self.extra_deps = []

    def __bool__(self):
        return bool(self.tests)


class Test:
    def __init__(self, context, cmd, environment, driver):
        # Ensure that bare Node objects are treated as a list of args instead
        # of a literal command line (the former has shell-characters escaped).
        if isinstance(cmd, Node):
            cmd = [cmd]
        wrap = not driver or driver.wrap_children
        self.cmd = context.env.run_arguments(cmd) if wrap else cmd

        self.inputs = [i for i in iterate(cmd)
                       if isinstance(i, Node) and i.creator]
        self.env = environment

        primary = first(cmd)
        if isinstance(primary, Node) and primary.creator:
            context.build['defaults'].remove(primary)
        (driver or context.build['tests']).tests.append(self)


class TestCase(Test):
    def __init__(self, context, cmd, environment={}, driver=None):
        if driver and environment:
            raise TypeError(
                "only one of 'driver' and 'environment' may be specified"
            )
        super().__init__(context, cmd, environment, driver)


class TestDriver(Test):
    def __init__(self, context, cmd, environment={}, parent=None,
                 wrap_children=False):
        if parent and environment:
            raise TypeError(
                "only one of 'parent' and 'environment' may be specified"
            )

        super().__init__(context, cmd, environment, parent)
        self.tests = []
        self.wrap_children = wrap_children


@builtin.function()
def test(context, cmd, **kwargs):
    return TestCase(context, cmd, **kwargs)


@builtin.function()
def test_driver(context, cmd, **kwargs):
    return TestDriver(context, cmd, **kwargs)


@builtin.function()
def test_deps(context, *args):
    if len(args) == 0:
        raise ValueError('expected at least one argument')
    context.build['tests'].extra_deps.extend(args)


def _build_commands(tests, writer, local_env, collapse=False):
    def command(test, args=[]):
        subcmd = local_env(test.env, test.cmd) + args

        if collapse:
            out = writer(StringIO())
            out.write_shell(subcmd)
            s = out.stream.getvalue()
            if len(subcmd) > 1:
                s = out.quote(s)
            return safe_str.literal(s)
        return subcmd

    cmd, deps = [], []
    for i in tests:
        deps.extend(i.inputs)
        if isinstance(i, TestDriver):
            args, more_deps = _build_commands(i.tests, writer, local_env, True)
            cmd.append(command(i, args))
            deps.extend(more_deps)
        else:
            cmd.append(command(i))
    return cmd, deps


@make.post_rule
def make_test_rule(build_inputs, buildfile, env):
    tests = build_inputs['tests']
    if not tests:
        return

    recipe, deps = _build_commands(tests.tests, buildfile.writer,
                                   pshell.local_env)

    buildfile.rule(
        target='tests',
        deps=deps + tests.extra_deps,
        phony=True
    )
    buildfile.rule(
        target='test',
        deps='tests',
        recipe=recipe,
        phony=True
    )


@ninja.post_rule
def ninja_test_rule(build_inputs, buildfile, env):
    tests = build_inputs['tests']
    if not tests:
        return

    try:
        local_env = shell.local_env
    except AttributeError:
        local_env = env.tool('setenv')

    commands, deps = _build_commands(tests.tests, buildfile.writer, local_env)

    buildfile.build(
        output='tests',
        rule='phony',
        inputs=deps + tests.extra_deps
    )
    ninja.command_build(
        buildfile, env,
        output='test',
        inputs='tests',
        command=shell.join_lines(commands),
        console=True, phony=True
    )
