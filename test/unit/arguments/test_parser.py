import mock
import unittest

from bfg9000 import path
from bfg9000.arguments import parser


class TestDirectory(unittest.TestCase):
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


class TestFile(unittest.TestCase):
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
