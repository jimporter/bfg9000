import argparse
import mock

from .. import *

from bfg9000 import path
from bfg9000.arguments import parser


class TestDirectory(TestCase):
    def test_existent(self):
        with mock.patch('bfg9000.path.exists', return_value=True), \
             mock.patch('bfg9000.path.isdir', return_value=True):  # noqa
            self.assertEqual(parser.Directory()('foo'), path.abspath('foo'))
            self.assertEqual(parser.Directory(True)('foo'),
                             path.abspath('foo'))

    def test_not_dir(self):
        with mock.patch('bfg9000.path.exists', return_value=True), \
             mock.patch('bfg9000.path.isdir', return_value=False):  # noqa
            with self.assertRaises(parser.ArgumentTypeError):
                parser.Directory()('foo')
            with self.assertRaises(parser.ArgumentTypeError):
                parser.Directory(True)('foo')

    def test_nonexistent(self):
        with mock.patch('bfg9000.path.exists', return_value=False):
            self.assertEqual(parser.Directory()('foo'), path.abspath('foo'))
            with self.assertRaises(parser.ArgumentTypeError):
                parser.Directory(True)('foo')


class TestFile(TestCase):
    def test_existent(self):
        with mock.patch('bfg9000.path.exists', return_value=True), \
             mock.patch('bfg9000.path.isfile', return_value=True):  # noqa
            self.assertEqual(parser.File()('foo'), path.abspath('foo'))
            self.assertEqual(parser.File(True)('foo'),
                             path.abspath('foo'))

    def test_not_dir(self):
        with mock.patch('bfg9000.path.exists', return_value=True), \
             mock.patch('bfg9000.path.isfile', return_value=False):  # noqa
            with self.assertRaises(parser.ArgumentTypeError):
                parser.File()('foo')
            with self.assertRaises(parser.ArgumentTypeError):
                parser.File(True)('foo')

    def test_nonexistent(self):
        with mock.patch('bfg9000.path.exists', return_value=False):
            self.assertEqual(parser.File()('foo'), path.abspath('foo'))
            with self.assertRaises(parser.ArgumentTypeError):
                parser.File(True)('foo')


class TestAddUserArgument(TestCase):
    def test_parse(self):
        p = argparse.ArgumentParser()
        p.usage = 'parse'

        parser.add_user_argument(p, '--foo', action='store_true')
        self.assertEqual(p.parse_args(['--foo']), argparse.Namespace(foo=True))
        self.assertEqual(p.parse_args(['--x-foo']),
                         argparse.Namespace(foo=True))

    def test_help(self):
        p = argparse.ArgumentParser()
        p.usage = 'help'

        parser.add_user_argument(p, '--foo', action='store_true')
        self.assertEqual(p.parse_args(['--foo']), argparse.Namespace(foo=True))
        self.assertEqual(p.parse_known_args(['--x-foo']),
                         (argparse.Namespace(foo=False), ['--x-foo']))

    def test_invalid(self):
        add_user_argument = parser.add_user_argument
        p = argparse.ArgumentParser()
        p.usage = 'parse'

        self.assertRaises(ValueError, add_user_argument, p, '-f')
        self.assertRaises(ValueError, add_user_argument, p, 'foo')
        self.assertRaises(ValueError, add_user_argument, p, '--foo', '-f')
        self.assertRaises(ValueError, add_user_argument, p, '--x-foo')
