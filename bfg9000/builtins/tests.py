from functools import partial
from six.moves import cStringIO as StringIO

from . import builtin
from .. import safe_str
from .. import shell
from .packages import SystemExecutable
from ..backends.make import writer as make
from ..backends.ninja import writer as ninja
from ..build_inputs import build_input
from ..file_types import Executable, File, objectify, sourcify
from ..shell import posix as pshell


@build_input('tests')
class TestInputs(object):
    def __init__(self):
        self.tests = []
        self.targets = []
        self.extra_deps = []

    def __nonzero__(self):
        return bool(self.tests)


class TestCase(object):
    def __init__(self, target, options, env):
        self.target = target
        self.options = options
        self.env = env


class TestDriver(object):
    def __init__(self, target, options, env):
        self.target = target
        self.options = options
        self.env = env
        self.tests = []


@builtin.globals('build_inputs')
def test(build, test, options=None, environment=None, driver=None):
    if driver and environment:
        raise TypeError('only one of "driver" and "environment" may be ' +
                        'specified')

    test = sourcify(test, File)
    build['tests'].targets.append(test)
    build['defaults'].remove(test)

    case = TestCase(test, pshell.listify(options), environment or {})
    (driver or build['tests']).tests.append(case)
    return case


@builtin.globals('builtins', 'build_inputs', 'env')
def test_driver(builtins, build, env, driver, options=None, environment=None,
                parent=None):
    if parent and environment:
        raise TypeError('only one of "parent" and "environment" may be ' +
                        'specified')

    driver = objectify(driver, Executable, builtins['system_executable'])
    result = TestDriver(driver, pshell.listify(options), environment or {})
    (parent or build['tests']).tests.append(result)
    return result


@builtin.globals('build_inputs')
def test_deps(build, *args):
    if len(args) == 0:
        raise ValueError('expected at least one argument')
    build['tests'].extra_deps.extend(args)


def _build_commands(tests, writer, local_env, collapse=False):
    def command(test, args=None):
        env_vars = local_env(test.env)
        subcmd = env_vars + [test.target] + test.options + (args or [])

        if collapse:
            out = writer(StringIO())
            out.write_shell(subcmd)
            s = out.stream.getvalue()
            if len(subcmd) > 1:
                s = shell.quote(s)
            return safe_str.escaped_str(s)
        return subcmd

    cmd, deps = [], []
    for i in tests:
        if type(i) == TestDriver:
            args, moredeps = _build_commands(i.tests, writer, local_env, True)
            if type(i.target) != SystemExecutable:
                deps.append(i.target)
            deps.extend(moredeps)
            cmd.append(command(i, args))
        else:
            cmd.append(command(i))
    return cmd, deps


@make.post_rule
def make_test_rule(build_inputs, buildfile, env):
    tests = build_inputs['tests']
    if not tests:
        return

    deps = []
    if tests.targets:
        buildfile.rule(
            target='tests',
            deps=tests.targets,
            phony=True
        )
        deps.append('tests')
    deps.extend(tests.extra_deps)

    try:
        local_env = shell.local_env
    except AttributeError:
        setenv = env.tool('setenv')
        local_env = partial(setenv, make.cmd_var(setenv, buildfile))

    recipe, moredeps = _build_commands(tests.tests, make.Writer, local_env)
    buildfile.rule(
        target='test',
        deps=deps + moredeps,
        recipe=recipe,
        phony=True
    )


@ninja.post_rule
def ninja_test_rule(build_inputs, buildfile, env):
    tests = build_inputs['tests']
    if not tests:
        return

    deps = []
    if tests.targets:
        buildfile.build(
            output='tests',
            rule='phony',
            inputs=tests.targets
        )
        deps.append('tests')
    deps.extend(tests.extra_deps)

    try:
        local_env = shell.local_env
    except AttributeError:
        setenv = env.tool('setenv')
        local_env = partial(setenv, ninja.cmd_var(setenv, buildfile))

    commands, moredeps = _build_commands(tests.tests, ninja.Writer, local_env)
    ninja.command_build(
        buildfile, env,
        output='test',
        inputs=deps + moredeps,
        commands=commands,
    )
