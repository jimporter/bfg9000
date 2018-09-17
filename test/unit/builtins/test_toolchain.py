import mock
import os
import unittest

from bfg9000.build import Toolchain
from bfg9000.builtins import toolchain


def mock_which(*args, **kwargs):
    return ['command']


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

    def test_compiler(self):
        environ = {}
        with mock.patch('bfg9000.shell.which', mock_which), \
             mock.patch('os.environ', environ):  # noqa
            toolchain.compiler('c++', 'foo')
            self.assertEqual(environ, {'CXX': 'command'})

            toolchain.compiler('c++', ['foo', 'bar'])
            self.assertEqual(environ, {'CXX': 'command'})

    def test_compile_options(self):
        environ = {}
        with mock.patch('os.environ', environ):
            toolchain.compile_options('c++', 'foo')
            self.assertEqual(environ, {'CXXFLAGS': 'foo'})

            toolchain.compile_options('c++', ['foo', 'bar'])
            self.assertEqual(environ, {'CXXFLAGS': 'foo bar'})

    def test_runner(self):
        environ = {}
        with mock.patch('bfg9000.shell.which', mock_which), \
             mock.patch('os.environ', environ):  # noqa
            toolchain.runner('java', 'foo')
            self.assertEqual(environ, {'JAVACMD': 'command'})

            toolchain.runner('java', ['foo', 'bar'])
            self.assertEqual(environ, {'JAVACMD': 'command'})
