from unittest import mock

from .. import *

from bfg9000 import tools
from bfg9000.build_inputs import Regenerating
from bfg9000.builtins import builtin, toolchain  # noqa: F401
from bfg9000.path import InstallRoot

tools.init()


def mock_which(*args, **kwargs):
    return ['command']


def mock_bad_which(*args, **kwargs):
    raise FileNotFoundError()


class TestToolchain(TestCase):
    def setUp(self):
        self.env = make_env(clear_variables=True)
        self.context = builtin.ToolchainContext(self.env)

    def test_builtins(self):
        safe = ['abs', 'int', 'str']
        unsafe = ['file', '__import__', 'input', 'open', 'raw_input',
                  'reload']

        for i in safe:
            self.assertTrue(i in self.context)
        for i in unsafe:
            self.assertFalse(i in self.context)

    def test_environ(self):
        self.context['environ']['NAME'] = 'value'
        self.assertEqual(self.context['environ'], {'NAME': 'value'})

    def test_srcdir(self):
        self.assertEqual(self.context['srcdir'], self.env.srcdir)
        self.assertIsNot(self.context['srcdir'], self.env.srcdir)

    def test_target_platform(self):
        self.context['target_platform']('winnt')
        self.assertEqual(self.env.target_platform.name, 'winnt')

    def test_which(self):
        which = self.context['which']
        with mock.patch('bfg9000.shell.which', mock_which):
            self.assertEqual(which('foo'), 'command')
            self.assertEqual(which(['foo', 'bar']), 'command')

        with mock.patch('bfg9000.shell.which', mock_bad_which):
            self.assertRaises(FileNotFoundError, which, 'foo')
            self.assertRaises(FileNotFoundError, which, ['foo', 'bar'])

            self.assertEqual(which('foo', strict=False), 'foo')
            self.assertEqual(which(['foo', 'bar'], strict=False), 'foo')
            self.assertEqual(which([['foo', 'bar']], strict=False), 'foo bar')

    def test_compiler(self):
        compiler = self.context['compiler']
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

            with self.assertRaises(FileNotFoundError):
                compiler('foo', 'c++', strict=True)
            with self.assertRaises(FileNotFoundError):
                compiler(['foo', 'bar'], 'c++', strict=True)

    def test_compile_options(self):
        compile_options = self.context['compile_options']
        compile_options('foo', 'c++')
        self.assertEqual(self.env.variables, {'CXXFLAGS': 'foo'})

        compile_options(['foo', 'bar'], 'c++')
        self.assertEqual(self.env.variables, {'CXXFLAGS': 'foo bar'})

    def test_runner(self):
        runner = self.context['runner']
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

            with self.assertRaises(FileNotFoundError):
                runner('foo', 'java', strict=True)
            with self.assertRaises(FileNotFoundError):
                runner(['foo', 'bar'], 'java', strict=True)

    def test_dynamic_linker(self):
        linker = self.context['linker']
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

            with self.assertRaises(FileNotFoundError):
                linker('foo', 'native', strict=True)
            with self.assertRaises(FileNotFoundError):
                linker(['foo', 'bar'], 'native', strict=True)

    def test_static_linker(self):
        linker = self.context['linker']
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

            with self.assertRaises(FileNotFoundError):
                linker('foo', 'native', 'static', strict=True)
            with self.assertRaises(FileNotFoundError):
                linker(['foo', 'bar'], 'native', 'static', strict=True)

    def test_link_options(self):
        link_options = self.context['link_options']

        link_options('foo')
        self.assertEqual(self.env.variables, {'LDFLAGS': 'foo'})

        link_options('foo', 'native')
        self.assertEqual(self.env.variables, {'LDFLAGS': 'foo'})

        link_options(['foo', 'bar'])
        self.assertEqual(self.env.variables, {'LDFLAGS': 'foo bar'})

        link_options(['foo', 'bar'], 'native')
        self.assertEqual(self.env.variables, {'LDFLAGS': 'foo bar'})

    def test_lib_options(self):
        lib_options = self.context['lib_options']

        lib_options('foo')
        self.assertEqual(self.env.variables, {'LDLIBS': 'foo'})

        lib_options('foo', 'native')
        self.assertEqual(self.env.variables, {'LDLIBS': 'foo'})

        lib_options(['foo', 'bar'])
        self.assertEqual(self.env.variables, {'LDLIBS': 'foo bar'})

        lib_options(['foo', 'bar'], 'native')
        self.assertEqual(self.env.variables, {'LDLIBS': 'foo bar'})

    def test_install_dirs(self):
        self.context['install_dirs'](prefix='/prefix', bindir='/bin/dir')

        self.assertEqual(self.env.install_dirs[InstallRoot.prefix],
                         Path('/prefix'))
        self.assertEqual(self.env.install_dirs[InstallRoot.bindir],
                         Path('/bin/dir'))

    def test_install_dirs_reload(self):
        self.context = builtin.ToolchainContext(self.env, Regenerating.true)

        prefix = self.env.install_dirs[InstallRoot.prefix]
        bindir = self.env.install_dirs[InstallRoot.bindir]
        self.context['install_dirs'](prefix='/bad', bindir='/bad/bin')

        self.assertEqual(self.env.install_dirs[InstallRoot.prefix], prefix)
        self.assertEqual(self.env.install_dirs[InstallRoot.bindir], bindir)
