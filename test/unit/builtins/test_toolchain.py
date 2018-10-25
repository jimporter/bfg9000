import mock
import os
import unittest

from bfg9000 import tools
from bfg9000.build import Toolchain
from bfg9000.builtins import toolchain

tools.init()


def mock_which(*args, **kwargs):
    return ['command']


def mock_bad_which(*args, **kwargs):
    raise IOError()


class TestToolchain(unittest.TestCase):
    def setUp(self):
        self.toolchain = Toolchain()

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
        self.assertEqual(toolchain.environ(), os.environ)

    def test_target_platform(self):
        toolchain.target_platform(self.toolchain, 'windows')
        self.assertEqual(self.toolchain.target_platform, 'windows')

    def test_which(self):
        with mock.patch('bfg9000.shell.which', mock_which):
            self.assertEqual(toolchain.which('foo'), 'command')
            self.assertEqual(toolchain.which(['foo', 'bar']), 'command')

        with mock.patch('bfg9000.shell.which', mock_bad_which):
            self.assertRaises(IOError, toolchain.which, 'foo')
            self.assertRaises(IOError, toolchain.which, ['foo', 'bar'])

            self.assertEqual(toolchain.which('foo', strict=False), 'foo')
            self.assertEqual(toolchain.which(['foo', 'bar'], strict=False),
                             'foo')
            self.assertEqual(toolchain.which([['foo', 'bar']], strict=False),
                             'foo bar')

    def test_compiler(self):
        environ = {}
        with mock.patch('os.environ', environ):
            with mock.patch('bfg9000.shell.which', mock_which):
                toolchain.compiler('foo', 'c++')
                self.assertEqual(environ, {'CXX': 'command'})
                toolchain.compiler(['foo', 'bar'], 'c++')
                self.assertEqual(environ, {'CXX': 'command'})

                toolchain.compiler('foo', 'c++', strict=True)
                self.assertEqual(environ, {'CXX': 'command'})
                toolchain.compiler(['foo', 'bar'], 'c++', strict=True)
                self.assertEqual(environ, {'CXX': 'command'})

            with mock.patch('bfg9000.shell.which', mock_bad_which):
                toolchain.compiler('foo', 'c++')
                self.assertEqual(environ, {'CXX': 'foo'})
                toolchain.compiler(['foo', 'bar'], 'c++')
                self.assertEqual(environ, {'CXX': 'foo'})

                self.assertRaises(IOError, toolchain.compiler, 'foo', 'c++',
                                  strict=True)
                self.assertRaises(IOError, toolchain.compiler, ['foo', 'bar'],
                                  'c++', strict=True)

    def test_compile_options(self):
        environ = {}
        with mock.patch('os.environ', environ):
            toolchain.compile_options('foo', 'c++')
            self.assertEqual(environ, {'CXXFLAGS': 'foo'})

            toolchain.compile_options(['foo', 'bar'], 'c++')
            self.assertEqual(environ, {'CXXFLAGS': 'foo bar'})

    def test_runner(self):
        environ = {}
        with mock.patch('os.environ', environ):
            with mock.patch('bfg9000.shell.which', mock_which):
                toolchain.runner('foo', 'java')
                self.assertEqual(environ, {'JAVACMD': 'command'})
                toolchain.runner(['foo', 'bar'], 'java')
                self.assertEqual(environ, {'JAVACMD': 'command'})

                toolchain.runner('foo', 'java', strict=True)
                self.assertEqual(environ, {'JAVACMD': 'command'})
                toolchain.runner(['foo', 'bar'], 'java', strict=True)
                self.assertEqual(environ, {'JAVACMD': 'command'})

            with mock.patch('bfg9000.shell.which', mock_bad_which):
                toolchain.runner('foo', 'java')
                self.assertEqual(environ, {'JAVACMD': 'foo'})
                toolchain.runner(['foo', 'bar'], 'java')
                self.assertEqual(environ, {'JAVACMD': 'foo'})

                self.assertRaises(IOError, toolchain.runner, 'foo', 'java',
                                  strict=True)
                self.assertRaises(IOError, toolchain.runner, ['foo', 'bar'],
                                  'java', strict=True)

    def test_dynamic_linker(self):
        environ = {}
        with mock.patch('os.environ', environ):
            with mock.patch('bfg9000.shell.which', mock_which):
                toolchain.linker('foo')
                self.assertEqual(environ, {'LD': 'command'})
                toolchain.linker(['foo', 'bar'])
                self.assertEqual(environ, {'LD': 'command'})

                toolchain.linker('foo', 'native')
                self.assertEqual(environ, {'LD': 'command'})
                toolchain.linker(['foo', 'bar'], 'native')
                self.assertEqual(environ, {'LD': 'command'})

                toolchain.linker('foo', 'native', strict=True)
                self.assertEqual(environ, {'LD': 'command'})
                toolchain.linker(['foo', 'bar'], 'native', strict=True)
                self.assertEqual(environ, {'LD': 'command'})

            with mock.patch('bfg9000.shell.which', mock_bad_which):
                toolchain.linker('foo', 'native')
                self.assertEqual(environ, {'LD': 'foo'})
                toolchain.linker(['foo', 'bar'], 'native')
                self.assertEqual(environ, {'LD': 'foo'})

                self.assertRaises(IOError, toolchain.linker, 'foo', 'native',
                                  strict=True)
                self.assertRaises(IOError, toolchain.linker, ['foo', 'bar'],
                                  'native', strict=True)

    def test_static_linker(self):
        environ = {}
        with mock.patch('os.environ', environ):
            with mock.patch('bfg9000.shell.which', mock_which):
                toolchain.linker('foo', mode='static')
                self.assertEqual(environ, {'AR': 'command'})
                toolchain.linker(['foo', 'bar'], mode='static')
                self.assertEqual(environ, {'AR': 'command'})

                toolchain.linker('foo', 'native', 'static')
                self.assertEqual(environ, {'AR': 'command'})
                toolchain.linker(['foo', 'bar'], 'native', 'static')
                self.assertEqual(environ, {'AR': 'command'})

                toolchain.linker('foo', 'native', 'static', strict=True)
                self.assertEqual(environ, {'AR': 'command'})
                toolchain.linker(['foo', 'bar'], 'native', 'static',
                                 strict=True)
                self.assertEqual(environ, {'AR': 'command'})

            with mock.patch('bfg9000.shell.which', mock_bad_which):
                toolchain.linker('foo', 'native', 'static')
                self.assertEqual(environ, {'AR': 'foo'})
                toolchain.linker(['foo', 'bar'], 'native', 'static')
                self.assertEqual(environ, {'AR': 'foo'})

                self.assertRaises(IOError, toolchain.linker, 'foo', 'native',
                                  'static', strict=True)
                self.assertRaises(IOError, toolchain.linker, ['foo', 'bar'],
                                  'native', 'static', strict=True)

    def test_link_options(self):
        environ = {}
        with mock.patch('os.environ', environ):
            toolchain.link_options('foo')
            self.assertEqual(environ, {'LDFLAGS': 'foo'})

            toolchain.link_options('foo', 'native')
            self.assertEqual(environ, {'LDFLAGS': 'foo'})

            toolchain.link_options(['foo', 'bar'])
            self.assertEqual(environ, {'LDFLAGS': 'foo bar'})

            toolchain.link_options(['foo', 'bar'], 'native')
            self.assertEqual(environ, {'LDFLAGS': 'foo bar'})

    def test_lib_options(self):
        environ = {}
        with mock.patch('os.environ', environ):
            toolchain.lib_options('foo')
            self.assertEqual(environ, {'LDLIBS': 'foo'})

            toolchain.lib_options('foo', 'native')
            self.assertEqual(environ, {'LDLIBS': 'foo'})

            toolchain.lib_options(['foo', 'bar'])
            self.assertEqual(environ, {'LDLIBS': 'foo bar'})

            toolchain.lib_options(['foo', 'bar'], 'native')
            self.assertEqual(environ, {'LDLIBS': 'foo bar'})
