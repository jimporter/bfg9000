import mock
import unittest

from ... import make_env

from bfg9000 import tools
from bfg9000.builtins import builtin, toolchain
from bfg9000.path import abspath, InstallRoot

tools.init()


def mock_which(*args, **kwargs):
    return ['command']


def mock_bad_which(*args, **kwargs):
    raise IOError()


class TestToolchain(unittest.TestCase):
    def setUp(self):
        self.env = make_env(clear_variables=True)
        self.builtin_dict = builtin.toolchain.bind(
            env=self.env
        )

    def test_builtins(self):
        builtins = toolchain.builtins()
        safe = ['abs', 'int', 'str']
        unsafe = ['file', '__import__', 'input', 'open', 'raw_input',
                  'reload']

        for i in safe:
            self.assertTrue(i in builtins)
        for i in unsafe:
            self.assertFalse(i in builtins)

    def test_environ(self):
        self.builtin_dict['environ']['NAME'] = 'value'
        self.assertEqual(self.builtin_dict['environ'], {'NAME': 'value'})

    def test_target_platform(self):
        self.builtin_dict['target_platform']('winnt')
        self.assertEqual(self.env.target_platform.name, 'winnt')

    def test_which(self):
        which = self.builtin_dict['which']
        with mock.patch('bfg9000.shell.which', mock_which):
            self.assertEqual(which('foo'), 'command')
            self.assertEqual(which(['foo', 'bar']), 'command')

        with mock.patch('bfg9000.shell.which', mock_bad_which):
            self.assertRaises(IOError, which, 'foo')
            self.assertRaises(IOError, which, ['foo', 'bar'])

            self.assertEqual(which('foo', strict=False), 'foo')
            self.assertEqual(which(['foo', 'bar'], strict=False), 'foo')
            self.assertEqual(which([['foo', 'bar']], strict=False), 'foo bar')

    def test_compiler(self):
        compiler = self.builtin_dict['compiler']
        with mock.patch('bfg9000.shell.which', mock_which):
            compiler('foo', 'c++')
            self.assertEqual(self.env.variables, {'CXX': 'command'})
            compiler(['foo', 'bar'], 'c++')
            self.assertEqual(self.env.variables, {'CXX': 'command'})

            compiler('foo', 'c++', strict=True)
            self.assertEqual(self.env.variables, {'CXX': 'command'})
            compiler(['foo', 'bar'], 'c++', strict=True)
            self.assertEqual(self.env.variables, {'CXX': 'command'})

        with mock.patch('bfg9000.shell.which', mock_bad_which):
            compiler('foo', 'c++')
            self.assertEqual(self.env.variables, {'CXX': 'foo'})
            compiler(['foo', 'bar'], 'c++')
            self.assertEqual(self.env.variables, {'CXX': 'foo'})

            self.assertRaises(IOError, compiler, 'foo', 'c++', strict=True)
            self.assertRaises(IOError, compiler, ['foo', 'bar'], 'c++',
                              strict=True)

    def test_compile_options(self):
        compile_options = self.builtin_dict['compile_options']
        compile_options('foo', 'c++')
        self.assertEqual(self.env.variables, {'CXXFLAGS': 'foo'})

        compile_options(['foo', 'bar'], 'c++')
        self.assertEqual(self.env.variables, {'CXXFLAGS': 'foo bar'})

    def test_runner(self):
        runner = self.builtin_dict['runner']
        with mock.patch('bfg9000.shell.which', mock_which):
            runner('foo', 'java')
            self.assertEqual(self.env.variables, {'JAVACMD': 'command'})
            runner(['foo', 'bar'], 'java')
            self.assertEqual(self.env.variables, {'JAVACMD': 'command'})

            runner('foo', 'java', strict=True)
            self.assertEqual(self.env.variables, {'JAVACMD': 'command'})
            runner(['foo', 'bar'], 'java', strict=True)
            self.assertEqual(self.env.variables, {'JAVACMD': 'command'})

        with mock.patch('bfg9000.shell.which', mock_bad_which):
            runner('foo', 'java')
            self.assertEqual(self.env.variables, {'JAVACMD': 'foo'})
            runner(['foo', 'bar'], 'java')
            self.assertEqual(self.env.variables, {'JAVACMD': 'foo'})

            self.assertRaises(IOError, runner, 'foo', 'java', strict=True)
            self.assertRaises(IOError, runner, ['foo', 'bar'], 'java',
                              strict=True)

    def test_dynamic_linker(self):
        linker = self.builtin_dict['linker']
        with mock.patch('bfg9000.shell.which', mock_which):
            linker('foo')
            self.assertEqual(self.env.variables, {'LD': 'command'})
            linker(['foo', 'bar'])
            self.assertEqual(self.env.variables, {'LD': 'command'})

            linker('foo', 'native')
            self.assertEqual(self.env.variables, {'LD': 'command'})
            linker(['foo', 'bar'], 'native')
            self.assertEqual(self.env.variables, {'LD': 'command'})

            linker('foo', 'native', strict=True)
            self.assertEqual(self.env.variables, {'LD': 'command'})
            linker(['foo', 'bar'], 'native', strict=True)
            self.assertEqual(self.env.variables, {'LD': 'command'})

        with mock.patch('bfg9000.shell.which', mock_bad_which):
            linker('foo', 'native')
            self.assertEqual(self.env.variables, {'LD': 'foo'})
            linker(['foo', 'bar'], 'native')
            self.assertEqual(self.env.variables, {'LD': 'foo'})

            self.assertRaises(IOError, linker, 'foo', 'native', strict=True)
            self.assertRaises(IOError, linker, ['foo', 'bar'], 'native',
                              strict=True)

    def test_static_linker(self):
        linker = self.builtin_dict['linker']
        with mock.patch('bfg9000.shell.which', mock_which):
            linker('foo', mode='static')
            self.assertEqual(self.env.variables, {'AR': 'command'})
            linker(['foo', 'bar'], mode='static')
            self.assertEqual(self.env.variables, {'AR': 'command'})

            linker('foo', 'native', 'static')
            self.assertEqual(self.env.variables, {'AR': 'command'})
            linker(['foo', 'bar'], 'native', 'static')
            self.assertEqual(self.env.variables, {'AR': 'command'})

            linker('foo', 'native', 'static', strict=True)
            self.assertEqual(self.env.variables, {'AR': 'command'})
            linker(['foo', 'bar'], 'native', 'static', strict=True)
            self.assertEqual(self.env.variables, {'AR': 'command'})

        with mock.patch('bfg9000.shell.which', mock_bad_which):
            linker('foo', 'native', 'static')
            self.assertEqual(self.env.variables, {'AR': 'foo'})
            linker(['foo', 'bar'], 'native', 'static')
            self.assertEqual(self.env.variables, {'AR': 'foo'})

            self.assertRaises(IOError, linker, 'foo', 'native', 'static',
                              strict=True)
            self.assertRaises(IOError, linker, ['foo', 'bar'], 'native',
                              'static', strict=True)

    def test_link_options(self):
        link_options = self.builtin_dict['link_options']

        link_options('foo')
        self.assertEqual(self.env.variables, {'LDFLAGS': 'foo'})

        link_options('foo', 'native')
        self.assertEqual(self.env.variables, {'LDFLAGS': 'foo'})

        link_options(['foo', 'bar'])
        self.assertEqual(self.env.variables, {'LDFLAGS': 'foo bar'})

        link_options(['foo', 'bar'], 'native')
        self.assertEqual(self.env.variables, {'LDFLAGS': 'foo bar'})

    def test_lib_options(self):
        lib_options = self.builtin_dict['lib_options']

        lib_options('foo')
        self.assertEqual(self.env.variables, {'LDLIBS': 'foo'})

        lib_options('foo', 'native')
        self.assertEqual(self.env.variables, {'LDLIBS': 'foo'})

        lib_options(['foo', 'bar'])
        self.assertEqual(self.env.variables, {'LDLIBS': 'foo bar'})

        lib_options(['foo', 'bar'], 'native')
        self.assertEqual(self.env.variables, {'LDLIBS': 'foo bar'})

    def test_install_dirs(self):
        self.builtin_dict['install_dirs'](prefix='/prefix', bindir='/bin/dir')

        self.assertEqual(self.env.install_dirs[InstallRoot.prefix],
                         abspath('/prefix'))
        self.assertEqual(self.env.install_dirs[InstallRoot.bindir],
                         abspath('/bin/dir'))
