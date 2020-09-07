import ntpath
import posixpath

from .common import BuiltinTest

from bfg9000.backends.make import writer as make
from bfg9000.backends.ninja import writer as ninja
from bfg9000.builtins import default, file_types, tests  # noqa
from bfg9000.path import Path, Root
from bfg9000.platforms.posix import PosixPath
from bfg9000.platforms.windows import WindowsPath
from bfg9000.safe_str import jbos, literal, safe_str, shell_literal
from bfg9000.shell import posix as pshell, windows as wshell, shell_list


class TestTestInputs(BuiltinTest):
    def test_empty(self):
        self.assertEqual(bool(self.build['tests']), False)

    def test_filled(self):
        prog = file_types.Executable(Path('prog'), None)
        self.context['test'](prog)
        self.assertEqual(bool(self.build['tests']), True)


class TestTestCase(BuiltinTest):
    def test_basic(self):
        prog = file_types.Executable(Path('prog'), None)
        case = self.context['test'](prog)

        self.assertEqual(case.cmd, [prog])
        self.assertEqual(case.inputs, [])
        self.assertEqual(case.env, {})
        self.assertEqual(self.build['tests'].tests, [case])

    def test_creator(self):
        prog = file_types.Executable(Path('prog'), None)
        prog.creator = 'creator'
        case = self.context['test'](prog)

        self.assertEqual(case.cmd, [prog])
        self.assertEqual(case.inputs, [prog])
        self.assertEqual(case.env, {})
        self.assertEqual(self.build['tests'].tests, [case])

    def test_args(self):
        prog = file_types.Executable(Path('prog'), None)
        case = self.context['test']([prog, '--foo'])

        self.assertEqual(case.cmd, [prog, '--foo'])
        self.assertEqual(case.inputs, [])
        self.assertEqual(case.env, {})
        self.assertEqual(self.build['tests'].tests, [case])

    def test_driver(self):
        prog = file_types.Executable(Path('prog'), None)
        driver = self.context['test_driver'](prog)
        case = self.context['test'](prog, driver=driver)

        self.assertEqual(case.cmd, [prog])
        self.assertEqual(case.inputs, [])
        self.assertEqual(case.env, {})
        self.assertEqual(self.build['tests'].tests, [driver])
        self.assertEqual(driver.tests, [case])

    def test_environment(self):
        prog = file_types.Executable(Path('prog'), None)
        case = self.context['test'](prog, environment={'VAR': 'foo'})

        self.assertEqual(case.cmd, [prog])
        self.assertEqual(case.inputs, [])
        self.assertEqual(case.env, {'VAR': 'foo'})
        self.assertEqual(self.build['tests'].tests, [case])

    def test_invalid(self):
        prog = file_types.Executable(Path('prog'), None)
        driver = self.context['test_driver'](prog)
        with self.assertRaises(TypeError):
            self.context['test'](prog, driver=driver,
                                 environment={'VAR': 'foo'})


class TestTestDriver(BuiltinTest):
    def test_basic(self):
        prog = file_types.Executable(Path('prog'), None)
        driver = self.context['test_driver'](prog)

        self.assertEqual(driver.cmd, [prog])
        self.assertEqual(driver.inputs, [])
        self.assertEqual(driver.env, {})
        self.assertEqual(driver.tests, [])
        self.assertEqual(driver.wrap_children, False)
        self.assertEqual(self.build['tests'].tests, [driver])

    def test_case(self):
        prog = file_types.Executable(Path('prog'), None)
        driver = self.context['test_driver'](prog)
        case = self.context['test'](prog, driver=driver)

        self.assertEqual(driver.cmd, [prog])
        self.assertEqual(driver.inputs, [])
        self.assertEqual(driver.env, {})
        self.assertEqual(driver.tests, [case])
        self.assertEqual(driver.wrap_children, False)
        self.assertEqual(self.build['tests'].tests, [driver])

    def test_creator(self):
        prog = file_types.Executable(Path('prog'), None)
        prog.creator = 'creator'
        driver = self.context['test_driver'](prog)
        case = self.context['test'](prog, driver=driver)

        self.assertEqual(driver.cmd, [prog])
        self.assertEqual(driver.inputs, [prog])
        self.assertEqual(driver.env, {})
        self.assertEqual(driver.tests, [case])
        self.assertEqual(driver.wrap_children, False)
        self.assertEqual(self.build['tests'].tests, [driver])

    def test_args(self):
        prog = file_types.Executable(Path('prog'), None)
        driver = self.context['test_driver']([prog, '--foo'])
        case = self.context['test'](prog, driver=driver)

        self.assertEqual(driver.cmd, [prog, '--foo'])
        self.assertEqual(driver.inputs, [])
        self.assertEqual(driver.env, {})
        self.assertEqual(driver.tests, [case])
        self.assertEqual(driver.wrap_children, False)
        self.assertEqual(self.build['tests'].tests, [driver])

    def test_parent(self):
        prog = file_types.Executable(Path('prog'), None)
        parent = self.context['test_driver'](prog)
        driver = self.context['test_driver'](prog, parent=parent)
        case = self.context['test'](prog, driver=driver)

        self.assertEqual(driver.cmd, [prog])
        self.assertEqual(driver.inputs, [])
        self.assertEqual(driver.env, {})
        self.assertEqual(driver.tests, [case])
        self.assertEqual(driver.wrap_children, False)
        self.assertEqual(self.build['tests'].tests, [parent])
        self.assertEqual(parent.tests, [driver])

    def test_environment(self):
        prog = file_types.Executable(Path('prog'), None)
        driver = self.context['test_driver'](
            prog, environment={'VAR': 'foo'}
        )
        case = self.context['test'](prog, driver=driver)

        self.assertEqual(driver.cmd, [prog])
        self.assertEqual(driver.inputs, [])
        self.assertEqual(driver.env, {'VAR': 'foo'})
        self.assertEqual(driver.tests, [case])
        self.assertEqual(driver.wrap_children, False)
        self.assertEqual(self.build['tests'].tests, [driver])

    def test_wrap_children(self):
        prog = file_types.Executable(Path('prog'), None)
        driver = self.context['test_driver'](prog, wrap_children=True)
        case = self.context['test'](prog, driver=driver)

        self.assertEqual(driver.cmd, [prog])
        self.assertEqual(driver.inputs, [])
        self.assertEqual(driver.env, {})
        self.assertEqual(driver.tests, [case])
        self.assertEqual(driver.wrap_children, True)
        self.assertEqual(self.build['tests'].tests, [driver])

    def test_invalid(self):
        prog = file_types.Executable(Path('prog'), None)
        parent = self.context['test_driver'](prog)
        with self.assertRaises(TypeError):
            self.context['test_driver'](prog, parent=parent,
                                        environment={'VAR': 'foo'})


class TestTestDeps(BuiltinTest):
    def test_empty(self):
        self.assertEqual(self.build['tests'].extra_deps, [])

    def test_single(self):
        prog = file_types.Executable(Path('prog'), None)
        self.context['test_deps'](prog)
        self.assertEqual(self.build['tests'].extra_deps, [prog])

    def test_multiple(self):
        foo = file_types.Executable(Path('foo'), None)
        bar = file_types.Executable(Path('bar'), None)
        self.context['test_deps'](foo, bar)
        self.assertEqual(self.build['tests'].extra_deps, [foo, bar])

    def test_none(self):
        with self.assertRaises(ValueError):
            self.context['test_deps']()


class TestBuildCommandsBase(BuiltinTest):
    path_vars = {
        Root.builddir: None,
    }

    def make_basic(self):
        test_exe = file_types.Executable(self.Path('test'), None)
        self.context['test'](test_exe)
        return test_exe

    def make_extras(self):
        test_exe = file_types.Executable(self.Path('test'), None)
        test_exe.creator = 'creator'
        self.context['test']([test_exe, '--foo'],
                             environment={'VAR': 'value'})
        return test_exe

    def make_empty_driver(self):
        driver_exe = file_types.Executable(self.Path('driver'), None)
        self.context['test_driver'](driver_exe)
        return driver_exe

    def make_driver(self):
        driver_exe = file_types.Executable(self.Path('driver'), None)
        driver_exe.creator = 'creator'
        driver = self.context['test_driver'](driver_exe)

        test_exe = file_types.Executable(self.Path('test'), None)
        test_exe.creator = 'creator'
        self.context['test'](test_exe, driver=driver)
        return driver_exe, test_exe

    def make_complex(self):
        test_exe = file_types.Executable(self.Path('test'), None)
        test_exe.creator = 'creator'
        self.context['test'](test_exe)

        driver_exe = file_types.Executable(self.Path('driver'), None)
        driver = self.context['test_driver'](driver_exe)

        mid_driver_exe = file_types.Executable(self.Path('mid_driver'), None)
        mid_driver = self.context['test_driver'](mid_driver_exe, parent=driver)
        mid_test_exe = file_types.Executable(self.Path('mid_test'), None)
        mid_test_exe.creator = 'creator'
        self.context['test'](mid_test_exe, driver=mid_driver)

        inner_driver_exe = file_types.Executable(self.Path('inner_driver'),
                                                 None)
        inner_driver = self.context['test_driver'](inner_driver_exe,
                                                   parent=mid_driver)
        inner_test_exe = file_types.Executable(self.Path('inner_test'), None)
        inner_test_exe.creator = 'creator'
        self.context['test']([inner_test_exe, '--foo'], driver=inner_driver)

        return (test_exe, driver_exe, mid_driver_exe, mid_test_exe,
                inner_driver_exe, inner_test_exe)


class TestBuildCommandsPosixNinja(TestBuildCommandsBase):
    Path = PosixPath

    @staticmethod
    def execpath(path):
        return posixpath.join('.', path)

    def _build_commands(self):
        return tests._build_commands(
            self.build['tests'].tests,
            lambda x: ninja.Writer(x, self.path_vars, pshell),
            pshell.local_env
        )

    def test_basic(self):
        test_exe = self.make_basic()

        cmd, deps = self._build_commands()
        self.assertEqual(cmd, [[test_exe]])
        self.assertEqual(deps, [])

    def test_extras(self):
        test_exe = self.make_extras()

        cmd, deps = self._build_commands()
        self.assertEqual(cmd, [shell_list([
            jbos('VAR', shell_literal('='), 'value'), test_exe, '--foo'
        ])])
        self.assertEqual(deps, [test_exe])

    def test_empty_driver(self):
        driver_exe = self.make_empty_driver()

        cmd, deps = self._build_commands()
        self.assertEqual(cmd, [[driver_exe]])
        self.assertEqual(deps, [])

    def test_driver(self):
        driver_exe, test_exe = self.make_driver()

        cmd, deps = self._build_commands()
        self.assertEqual(cmd, [[driver_exe, literal(self.execpath('test'))]])
        self.assertEqual(deps, [driver_exe, test_exe])

    def test_complex(self):
        p = self.execpath
        (test_exe, driver_exe, mid_driver_exe, mid_test_exe, inner_driver_exe,
         inner_test_exe) = self.make_complex()

        cmd, deps = self._build_commands()
        self.assertEqual(deps, [test_exe, mid_test_exe, inner_test_exe])

        self.assertEqual(cmd, [
            [test_exe],
            [driver_exe, literal(
                "'" + p('mid_driver') + ' ' + p('mid_test') + r" '\''" +
                p('inner_driver') + r" '\''\'\'''\''" + p('inner_test') +
                ' --foo' + r"'\''\'\'"
            )],
        ])

        arg = pshell.split(cmd[1][1].string, escapes=True)
        self.assertEqual(arg, [
            p('mid_driver') + ' ' + p('mid_test') + " '" + p('inner_driver') +
            r" '\''" + p('inner_test') + ' --foo' + r"'\'"
        ])

        arg = pshell.split(arg[0], escapes=True)
        self.assertEqual(arg, [
            p('mid_driver'),
            p('mid_test'),
            p('inner_driver') + " '" + p('inner_test') + ' --foo' + "'"
        ])

        arg = pshell.split(arg[2], escapes=True)
        self.assertEqual(arg, [
            p('inner_driver'),
            p('inner_test') + ' --foo'
        ])


class TestBuildCommandsWindowsNinja(TestBuildCommandsBase):
    Path = WindowsPath

    @staticmethod
    def execpath(path):
        return ntpath.join('.', path)

    def _build_commands(self):
        def mock_local_env(env, line):
            if env:
                eq = shell_literal('=')
                env_vars = [jbos(safe_str(name), eq, safe_str(value))
                            for name, value in env.items()]
            else:
                env_vars = []
            return env_vars + wshell.escape_line(line, listify=True)

        return tests._build_commands(
            self.build['tests'].tests,
            lambda x: ninja.Writer(x, self.path_vars, wshell),
            mock_local_env
        )

    def test_basic(self):
        test_exe = self.make_basic()

        cmd, deps = self._build_commands()
        self.assertEqual(cmd, [[test_exe]])
        self.assertEqual(deps, [])

    def test_extras(self):
        test_exe = self.make_extras()

        cmd, deps = self._build_commands()
        self.assertEqual(cmd, [[
            jbos('VAR', shell_literal('='), 'value'), test_exe, '--foo'
        ]])
        self.assertEqual(deps, [test_exe])

    def test_empty_driver(self):
        driver_exe = self.make_empty_driver()

        cmd, deps = self._build_commands()
        self.assertEqual(cmd, [[driver_exe]])
        self.assertEqual(deps, [])

    def test_driver(self):
        driver_exe, test_exe = self.make_driver()

        cmd, deps = self._build_commands()
        self.assertEqual(cmd, [[driver_exe, literal(self.execpath('test'))]])
        self.assertEqual(deps, [driver_exe, test_exe])

    def test_complex(self):
        p = self.execpath
        (test_exe, driver_exe, mid_driver_exe, mid_test_exe, inner_driver_exe,
         inner_test_exe) = self.make_complex()

        cmd, deps = self._build_commands()
        self.assertEqual(deps, [test_exe, mid_test_exe, inner_test_exe])

        self.assertEqual(cmd, [
            [test_exe],
            [driver_exe, literal(
                '"' + p('mid_driver') + ' ' + p('mid_test') + r' \"' +
                p('inner_driver') + r' \\\"' + p('inner_test') +
                ' --foo' + r'\\\"\""'
            )],
        ])

        arg = wshell.split(cmd[1][1].string)
        self.assertEqual(arg, [
            p('mid_driver') + ' ' + p('mid_test') + ' "' + p('inner_driver') +
            r' \"' + p('inner_test') + ' --foo' + r'\""'
        ])

        arg = wshell.split(arg[0])
        self.assertEqual(arg, [
            p('mid_driver'),
            p('mid_test'),
            p('inner_driver') + ' "' + p('inner_test') + ' --foo' + '"'
        ])

        arg = wshell.split(arg[2])
        self.assertEqual(arg, [
            p('inner_driver'),
            p('inner_test') + ' --foo'
        ])


class TestBuildCommandsPosixMake(TestBuildCommandsPosixNinja):
    def _build_commands(self):
        return tests._build_commands(
            self.build['tests'].tests,
            lambda x: make.Writer(x, self.path_vars),
            pshell.local_env
        )
