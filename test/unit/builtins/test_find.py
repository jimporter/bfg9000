import mock
import os.path
from contextlib import contextmanager

from .. import *
from .common import BuiltinTest

from bfg9000.builtins import find, regenerate  # noqa


def mock_listdir(path):
    if path == '.':
        return ['file', 'dir']
    else:
        return ['file2']


def mock_isdir(path):
    return not os.path.basename(path).startswith('file')


@contextmanager
def mock_context():
    with mock.patch('os.listdir', mock_listdir) as a, \
         mock.patch('os.path.exists', return_value=True) as b, \
         mock.patch('os.path.isdir', mock_isdir) as c, \
         mock.patch('os.path.islink', return_value=False) as d:  # noqa
        yield a, b, c, d


class TestListdir(TestCase):
    def test_listdir(self):
        with mock_context():
            self.assertEqual(find._listdir('.'), (
                [('dir', './dir')],
                [('file', './file')],
            ))


class TestWalkFlat(TestCase):
    def test_exists(self):
        with mock_context():
            self.assertEqual(list(find._walk_flat('.')), [
                ('.', [('dir', './dir')], [('file', './file')]),
            ])

    def test_not_exists(self):
        with mock.patch('os.path.exists', return_value=False):
            self.assertEqual(list(find._walk_flat('.')), [])


class TestWalkRecursive(TestCase):
    def test_exists(self):
        with mock_context():
            self.assertEqual(list(find._walk_recursive('.')), [
                ('.', [('dir', './dir')], [('file', './file')]),
                ('./dir', [], [('file2', './dir/file2')])
            ])

    def test_not_exists(self):
        with mock.patch('os.path.exists', return_value=False):
            self.assertEqual(list(find._walk_recursive('.')),
                             [])


class TestFilterFromGlob(TestCase):
    def test_file(self):
        f = find._filter_from_glob('f', '*', None, None)
        self.assertEqual(f('foo', 'foo', 'f'), find.FindResult.include)
        self.assertEqual(f('foo', 'foo', 'd'), find.FindResult.exclude)

    def test_dir(self):
        f = find._filter_from_glob('d', '*', None, None)
        self.assertEqual(f('foo', 'foo', 'f'), find.FindResult.exclude)
        self.assertEqual(f('foo', 'foo', 'd'), find.FindResult.include)

    def test_either(self):
        f = find._filter_from_glob('*', '*', None, None)
        self.assertEqual(f('foo', 'foo', 'f'), find.FindResult.include)
        self.assertEqual(f('foo', 'foo', 'd'), find.FindResult.include)

    def test_match(self):
        f = find._filter_from_glob('*', '*.hpp', None, None)
        self.assertEqual(f('foo.hpp', 'foo.hpp', 'f'), find.FindResult.include)
        self.assertEqual(f('foo.cpp', 'foo.cpp', 'f'), find.FindResult.exclude)

    def test_extra(self):
        f = find._filter_from_glob('*', None, '*.hpp', None)
        self.assertEqual(f('foo.hpp', 'foo.hpp', 'f'), find.FindResult.not_now)
        self.assertEqual(f('foo.cpp', 'foo.cpp', 'f'), find.FindResult.exclude)

    def test_match_extra(self):
        f = find._filter_from_glob('*', '*.hpp', '*.?pp', None)
        self.assertEqual(f('foo.hpp', 'foo.hpp', 'f'), find.FindResult.include)
        self.assertEqual(f('foo.cpp', 'foo.cpp', 'f'), find.FindResult.not_now)
        self.assertEqual(f('foo.cxx', 'foo.cxx', 'f'), find.FindResult.exclude)

    def test_exclude(self):
        f = find._filter_from_glob('*', '*.?pp', None, '*.cpp')
        self.assertEqual(f('foo.hpp', 'foo.hpp', 'f'), find.FindResult.include)
        self.assertEqual(f('foo.cpp', 'foo.cpp', 'f'), find.FindResult.exclude)

    def test_match_extra_exclude(self):
        f = find._filter_from_glob('*', '*.c??', '*.?pp', '*.hpp')
        self.assertEqual(f('foo.hpp', 'foo.hpp', 'f'), find.FindResult.exclude)
        self.assertEqual(f('foo.cpp', 'foo.cpp', 'f'), find.FindResult.include)
        self.assertEqual(f('foo.ipp', 'foo.ipp', 'f'), find.FindResult.not_now)


class TestFind(TestCase):
    def test_default(self):
        with mock_context():
            self.assertEqual(find.find(),
                             ['.', './dir', './file', './dir/file2'])

    def test_file(self):
        with mock_context():
            self.assertEqual(find.find(type='f'), ['./file', './dir/file2'])

    def test_dir(self):
        with mock_context():
            self.assertEqual(find.find(type='d'), ['.', './dir'])

    def test_flat(self):
        with mock_context():
            self.assertEqual(find.find(flat=True),
                             ['.', './dir', './file'])


class TestFindFiles(BuiltinTest):
    def test_default(self):
        with mock_context():
            self.assertEqual(self.builtin_dict['find_files'](),
                             ['.', './dir', './file', './dir/file2'])

    def test_file(self):
        with mock_context():
            self.assertEqual(self.builtin_dict['find_files'](type='f'),
                             ['./file', './dir/file2'])

    def test_dir(self):
        with mock_context():
            self.assertEqual(self.builtin_dict['find_files'](type='d'),
                             ['.', './dir'])

    def test_flat(self):
        with mock_context():
            self.assertEqual(self.builtin_dict['find_files'](flat=True),
                             ['.', './dir', './file'])
