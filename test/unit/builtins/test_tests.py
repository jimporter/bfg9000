import os.path

from .common import BuiltinTest

from bfg9000.backends.ninja import writer as ninja
from bfg9000.builtins import default, file_types, tests  # noqa
from bfg9000.path import Path
from bfg9000.safe_str import jbos, literal, shell_literal
from bfg9000.shell import posix as pshell, shell_list


def p(path):
    return os.path.join('.', path)


class TestTestInputs(BuiltinTest):
    def test_empty(self):
        self.assertEqual(bool(self.build['tests']), False)

    def test_filled(self):
        prog = file_types.Executable(Path('prog'), None)
        self.builtin_dict['test'](prog)
        self.assertEqual(bool(self.build['tests']), True)


class TestTestCase(BuiltinTest):
    def test_basic(self):
        prog = file_types.Executable(Path('prog'), None)
        case = self.builtin_dict['test'](prog)

        self.assertEqual(case.cmd, [prog])
        self.assertEqual(case.inputs, [])
        self.assertEqual(case.env, {})
        self.assertEqual(self.build['tests'].tests, [case])

    def test_creator(self):
        prog = file_types.Executable(Path('prog'), None)
        prog.creator = 'creator'
        case = self.builtin_dict['test'](prog)

        self.assertEqual(case.cmd, [prog])
        self.assertEqual(case.inputs, [prog])
        self.assertEqual(case.env, {})
        self.assertEqual(self.build['tests'].tests, [case])

    def test_args(self):
        prog = file_types.Executable(Path('prog'), None)
        case = self.builtin_dict['test']([prog, '--foo'])

        self.assertEqual(case.cmd, [prog, '--foo'])
        self.assertEqual(case.inputs, [])
        self.assertEqual(case.env, {})
        self.assertEqual(self.build['tests'].tests, [case])

    def test_driver(self):
        prog = file_types.Executable(Path('prog'), None)
        driver = self.builtin_dict['test_driver'](prog)
        case = self.builtin_dict['test'](prog, driver=driver)

        self.assertEqual(case.cmd, [prog])
        self.assertEqual(case.inputs, [])
        self.assertEqual(case.env, {})
        self.assertEqual(self.build['tests'].tests, [driver])
        self.assertEqual(driver.tests, [case])

    def test_environment(self):
        prog = file_types.Executable(Path('prog'), None)
        case = self.builtin_dict['test'](prog, environment={'VAR': 'foo'})

        self.assertEqual(case.cmd, [prog])
        self.assertEqual(case.inputs, [])
        self.assertEqual(case.env, {'VAR': 'foo'})
        self.assertEqual(self.build['tests'].tests, [case])

    def test_invalid(self):
        prog = file_types.Executable(Path('prog'), None)
        driver = self.builtin_dict['test_driver'](prog)
        with self.assertRaises(TypeError):
            self.builtin_dict['test'](prog, driver=driver,
                                      environment={'VAR': 'foo'})


class TestTestDriver(BuiltinTest):
    def test_basic(self):
        prog = file_types.Executable(Path('prog'), None)
        driver = self.builtin_dict['test_driver'](prog)

        self.assertEqual(driver.cmd, [prog])
        self.assertEqual(driver.inputs, [])
        self.assertEqual(driver.env, {})
        self.assertEqual(driver.tests, [])
        self.assertEqual(driver.wrap_children, False)
        self.assertEqual(self.build['tests'].tests, [driver])

    def test_case(self):
        prog = file_types.Executable(Path('prog'), None)
        driver = self.builtin_dict['test_driver'](prog)
        case = self.builtin_dict['test'](prog, driver=driver)

        self.assertEqual(driver.cmd, [prog])
        self.assertEqual(driver.inputs, [])
        self.assertEqual(driver.env, {})
        self.assertEqual(driver.tests, [case])
        self.assertEqual(driver.wrap_children, False)
        self.assertEqual(self.build['tests'].tests, [driver])

    def test_creator(self):
        prog = file_types.Executable(Path('prog'), None)
        prog.creator = 'creator'
        driver = self.builtin_dict['test_driver'](prog)
        case = self.builtin_dict['test'](prog, driver=driver)

        self.assertEqual(driver.cmd, [prog])
        self.assertEqual(driver.inputs, [prog])
        self.assertEqual(driver.env, {})
        self.assertEqual(driver.tests, [case])
        self.assertEqual(driver.wrap_children, False)
        self.assertEqual(self.build['tests'].tests, [driver])

    def test_args(self):
        prog = file_types.Executable(Path('prog'), None)
        driver = self.builtin_dict['test_driver']([prog, '--foo'])
        case = self.builtin_dict['test'](prog, driver=driver)

        self.assertEqual(driver.cmd, [prog, '--foo'])
        self.assertEqual(driver.inputs, [])
        self.assertEqual(driver.env, {})
        self.assertEqual(driver.tests, [case])
        self.assertEqual(driver.wrap_children, False)
        self.assertEqual(self.build['tests'].tests, [driver])

    def test_parent(self):
        prog = file_types.Executable(Path('prog'), None)
        parent = self.builtin_dict['test_driver'](prog)
        driver = self.builtin_dict['test_driver'](prog, parent=parent)
        case = self.builtin_dict['test'](prog, driver=driver)

        self.assertEqual(driver.cmd, [prog])
        self.assertEqual(driver.inputs, [])
        self.assertEqual(driver.env, {})
        self.assertEqual(driver.tests, [case])
        self.assertEqual(driver.wrap_children, False)
        self.assertEqual(self.build['tests'].tests, [parent])
        self.assertEqual(parent.tests, [driver])

    def test_environment(self):
        prog = file_types.Executable(Path('prog'), None)
        driver = self.builtin_dict['test_driver'](
            prog, environment={'VAR': 'foo'}
        )
        case = self.builtin_dict['test'](prog, driver=driver)

        self.assertEqual(driver.cmd, [prog])
        self.assertEqual(driver.inputs, [])
        self.assertEqual(driver.env, {'VAR': 'foo'})
        self.assertEqual(driver.tests, [case])
        self.assertEqual(driver.wrap_children, False)
        self.assertEqual(self.build['tests'].tests, [driver])

    def test_wrap_children(self):
        prog = file_types.Executable(Path('prog'), None)
        driver = self.builtin_dict['test_driver'](prog, wrap_children=True)
        case = self.builtin_dict['test'](prog, driver=driver)

        self.assertEqual(driver.cmd, [prog])
        self.assertEqual(driver.inputs, [])
        self.assertEqual(driver.env, {})
        self.assertEqual(driver.tests, [case])
        self.assertEqual(driver.wrap_children, True)
        self.assertEqual(self.build['tests'].tests, [driver])

    def test_invalid(self):
        prog = file_types.Executable(Path('prog'), None)
        parent = self.builtin_dict['test_driver'](prog)
        with self.assertRaises(TypeError):
            self.builtin_dict['test_driver'](prog, parent=parent,
                                             environment={'VAR': 'foo'})


class TestTestDeps(BuiltinTest):
    def test_empty(self):
        self.assertEqual(self.build['tests'].extra_deps, [])

    def test_single(self):
        prog = file_types.Executable(Path('prog'), None)
        self.builtin_dict['test_deps'](prog)
        self.assertEqual(self.build['tests'].extra_deps, [prog])

    def test_multiple(self):
        foo = file_types.Executable(Path('foo'), None)
        bar = file_types.Executable(Path('bar'), None)
        self.builtin_dict['test_deps'](foo, bar)
        self.assertEqual(self.build['tests'].extra_deps, [foo, bar])

    def test_none(self):
        with self.assertRaises(ValueError):
            self.builtin_dict['test_deps']()


class TestBuildCommands(BuiltinTest):
    def _build_commands(self):
        return tests._build_commands(
            self.build['tests'].tests, ninja.Writer, pshell, pshell.local_env
        )

    def test_basic(self):
        test_exe = file_types.Executable(Path('test'), None)
        self.builtin_dict['test'](test_exe)

        cmd, deps = self._build_commands()
        self.assertEqual(cmd, [[test_exe]])
        self.assertEqual(deps, [])

    def test_extras(self):
        test_exe = file_types.Executable(Path('test'), None)
        test_exe.creator = 'creator'
        self.builtin_dict['test']([test_exe, '--foo'],
                                  environment={'VAR': 'value'})

        cmd, deps = self._build_commands()
        self.assertEqual(cmd, [shell_list([
            jbos('VAR', shell_literal('='), 'value'), test_exe, '--foo'
        ])])
        self.assertEqual(deps, [test_exe])

    def test_empty_driver(self):
        driver_exe = file_types.Executable(Path('driver'), None)
        self.builtin_dict['test_driver'](driver_exe)

        cmd, deps = self._build_commands()
        self.assertEqual(cmd, [[driver_exe]])
        self.assertEqual(deps, [])

    def test_driver(self):
        driver_exe = file_types.Executable(Path('driver'), None)
        driver_exe.creator = 'creator'
        driver = self.builtin_dict['test_driver'](driver_exe)

        test_exe = file_types.Executable(Path('test'), None)
        test_exe.creator = 'creator'
        self.builtin_dict['test'](test_exe, driver=driver)

        cmd, deps = self._build_commands()
        self.assertEqual(cmd, [[driver_exe, literal(p('test'))]])
        self.assertEqual(deps, [driver_exe, test_exe])

    def test_complex(self):
        test_exe = file_types.Executable(Path('test'), None)
        test_exe.creator = 'creator'
        self.builtin_dict['test'](test_exe)

        driver_exe = file_types.Executable(Path('driver'), None)
        driver = self.builtin_dict['test_driver'](driver_exe)

        mid_driver_exe = file_types.Executable(Path('mid_driver'), None)
        mid_driver = self.builtin_dict['test_driver'](mid_driver_exe,
                                                      parent=driver)
        mid_test_exe = file_types.Executable(Path('mid_test'), None)
        mid_test_exe.creator = 'creator'
        self.builtin_dict['test'](mid_test_exe, driver=mid_driver)

        inner_driver_exe = file_types.Executable(Path('inner_driver'), None)
        inner_driver = self.builtin_dict['test_driver'](inner_driver_exe,
                                                        parent=mid_driver)
        inner_test_exe = file_types.Executable(Path('inner_test'), None)
        inner_test_exe.creator = 'creator'
        self.builtin_dict['test']([inner_test_exe, '--foo'],
                                  driver=inner_driver)

        cmd, deps = self._build_commands()
        some_quotes = "'\"'\"'"
        many_quotes = "'\"'\"'\"'\"'\"'\"'\"'\"'"
        self.assertEqual(cmd, [
            [test_exe],
            [driver_exe, literal(
                "'" + p('mid_driver') + ' ' + p('mid_test') + ' ' +
                some_quotes + p('inner_driver') + ' ' + many_quotes +
                p('inner_test') + ' --foo' + many_quotes + some_quotes + "'"
            )],
        ])
        self.assertEqual(deps, [test_exe, mid_test_exe, inner_test_exe])
