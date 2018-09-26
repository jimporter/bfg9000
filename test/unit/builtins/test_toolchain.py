import mock
import os
import unittest

from bfg9000.build import Toolchain
from bfg9000.builtins import toolchain


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
