import os
from contextlib import contextmanager
from unittest import mock

from .. import *
from .common import BuiltinTest

from bfg9000.builtins import find, regenerate  # noqa
from bfg9000.file_types import Directory, File, HeaderDirectory, SourceFile
from bfg9000.path import Path, Root
from bfg9000.platforms import known_platforms

path_vars = {
    Root.srcdir: None,
    Root.builddir: None,
}


def srcpath(p):
    return Path(p, Root.srcdir)


def mock_listdir(path):
    if os.path.basename(path) == 'dir':
        return ['file2.txt']
    return ['file.cpp', 'dir']


def mock_isdir(path, variables=None):
    return not path.basename().startswith('file')


@contextmanager
def mock_context():
    find = 'bfg9000.builtins.find'
    with mock.patch('os.listdir', mock_listdir) as a, \
         mock.patch(find + '.exists', return_value=True) as b, \
         mock.patch(find + '.isdir', mock_isdir) as c, \
         mock.patch(find + '.islink', return_value=False) as d:  # noqa
        yield a, b, c, d


class TestListdir(TestCase):
    def test_listdir(self):
        with mock_context():
            self.assertEqual(find._listdir(Path('.'), path_vars), (
                [Path('dir')], [Path('file.cpp')],
            ))

    def test_not_found(self):
        def mock_listdir(path):
            raise OSError()

        with mock.patch('os.listdir', mock_listdir):
            self.assertEqual(find._listdir(Path('.'), path_vars), ([], []))


class TestWalkFlat(TestCase):
    def test_exists(self):
        with mock_context():
            self.assertEqual(list(find._walk_flat(Path('.'), path_vars)), [
                (Path('.'), [Path('dir')], [Path('file.cpp')]),
            ])

    def test_not_exists(self):
        with mock.patch('bfg9000.builtins.find.exists', return_value=False):
            self.assertEqual(list(find._walk_flat(Path('.'), path_vars)), [])


class TestWalkRecursive(TestCase):
    def test_exists(self):
        with mock_context():
            self.assertEqual(
                list(find._walk_recursive(Path('.'), path_vars)),
                [ (Path('.'), [Path('dir')], [Path('file.cpp')]),
                  (Path('dir'), [], [Path('dir/file2.txt')]) ]
            )

    def test_not_exists(self):
        with mock.patch('bfg9000.builtins.find.exists', return_value=False):
            self.assertEqual(list(find._walk_recursive(Path('.'), path_vars)),
                             [])

    def test_link(self):
        def mock_islink(path, variables=None):
            return path.basename() == 'dir'

        with mock.patch('os.listdir', mock_listdir), \
             mock.patch('bfg9000.builtins.find.exists', return_value=True), \
             mock.patch('bfg9000.builtins.find.isdir', mock_isdir), \
             mock.patch('bfg9000.builtins.find.islink', mock_islink):  # noqa
            self.assertEqual(
                list(find._walk_recursive(Path('.'), path_vars)),
                [ (Path('.'), [Path('dir')], [Path('file.cpp')]) ]
            )


class TestMakeFilterFromGlob(TestCase):
    def test_file(self):
        f = find._make_filter_from_glob('f', '*', None, None)
        self.assertEqual(f(Path('foo'), 'f'), find.FindResult.include)
        self.assertEqual(f(Path('foo'), 'd'), find.FindResult.exclude)

    def test_dir(self):
        f = find._make_filter_from_glob('d', '*', None, None)
        self.assertEqual(f(Path('foo'), 'f'), find.FindResult.exclude)
        self.assertEqual(f(Path('foo'), 'd'), find.FindResult.include)

    def test_either(self):
        f = find._make_filter_from_glob('*', '*', None, None)
        self.assertEqual(f(Path('foo'), 'f'), find.FindResult.include)
        self.assertEqual(f(Path('foo'), 'd'), find.FindResult.include)

    def test_match(self):
        f = find._make_filter_from_glob('*', '*.hpp', None, None)
        self.assertEqual(f(Path('foo.hpp'), 'f'), find.FindResult.include)
        self.assertEqual(f(Path('foo.cpp'), 'f'), find.FindResult.exclude)

    def test_extra(self):
        f = find._make_filter_from_glob('*', None, '*.hpp', None)
        self.assertEqual(f(Path('foo.hpp'), 'f'), find.FindResult.not_now)
        self.assertEqual(f(Path('foo.cpp'), 'f'), find.FindResult.exclude)

    def test_match_extra(self):
        f = find._make_filter_from_glob('*', '*.hpp', '*.?pp', None)
        self.assertEqual(f(Path('foo.hpp'), 'f'), find.FindResult.include)
        self.assertEqual(f(Path('foo.cpp'), 'f'), find.FindResult.not_now)
        self.assertEqual(f(Path('foo.cxx'), 'f'), find.FindResult.exclude)

    def test_exclude(self):
        f = find._make_filter_from_glob('*', '*.?pp', None, '*.cpp')
        self.assertEqual(f(Path('foo.hpp'), 'f'), find.FindResult.include)
        self.assertEqual(f(Path('foo.cpp'), 'f'), find.FindResult.exclude)

    def test_match_extra_exclude(self):
        f = find._make_filter_from_glob('*', '*.c??', '*.?pp', '*.hpp')
        self.assertEqual(f(Path('foo.hpp'), 'f'), find.FindResult.exclude)
        self.assertEqual(f(Path('foo.cpp'), 'f'), find.FindResult.include)
        self.assertEqual(f(Path('foo.ipp'), 'f'), find.FindResult.not_now)


class TestFilterByPlatform(BuiltinTest):
    def setUp(self):
        super().setUp()
        self.filter = self.context['filter_by_platform']

    def test_normal(self):
        self.assertEqual(self.filter(Path('file.txt'), 'f'),
                         find.FindResult.include)

    def do_test_platform(self, platform, result):
        paths = [
            Path('{}/file.txt'.format(platform)),
            Path('dir/{}/file.txt'.format(platform)),
            Path('file_{}.txt'.format(platform)),
            Path('dir_{}/file.txt'.format(platform)),
        ]
        for p in paths:
            self.assertEqual(self.filter(p, 'f'), result, repr(p))

    def test_current_platform(self):
        self.do_test_platform(self.env.target_platform.genus,
                              find.FindResult.include)
        self.do_test_platform(self.env.target_platform.family,
                              find.FindResult.include)

    def test_non_current_platform(self):
        my_plat = {self.env.target_platform.genus,
                   self.env.target_platform.family}
        for i in known_platforms:
            if i not in my_plat:
                self.do_test_platform(i, find.FindResult.not_now)


class TestFind(BuiltinTest):
    def test_default(self):
        with mock_context():
            self.assertEqual(find.find(self.env), [
                srcpath('.'), srcpath('dir'), srcpath('file.cpp'),
                srcpath('dir/file2.txt')
            ])

    def test_file(self):
        with mock_context():
            self.assertEqual(find.find(self.env, type='f'), [
                srcpath('file.cpp'), srcpath('dir/file2.txt')
            ])

    def test_dir(self):
        with mock_context():
            self.assertEqual(find.find(self.env, type='d'), [
                srcpath('.'), srcpath('dir')
            ])

    def test_flat(self):
        with mock_context():
            self.assertEqual(find.find(self.env, flat=True), [
                srcpath('.'), srcpath('dir'), srcpath('file.cpp')
            ])


class TestFindFiles(BuiltinTest):
    def setUp(self):
        super().setUp()
        self.find = self.context['find_files']

    def assertFound(self, result, expected, dist=None):
        if dist is None:
            dist = [self.bfgfile] + expected
        self.assertEqual(result, expected)
        self.assertEqual(list(self.build.sources()), dist)

    def test_default(self):
        expected = [
            Directory(srcpath('.')),
            Directory(srcpath('dir')),
            SourceFile(srcpath('file.cpp'), 'c++'),
            File(srcpath('dir/file2.txt'))
        ]
        with mock_context():
            self.assertFound(self.find(), expected)
            self.assertEqual(self.build['find_dirs'], {
                srcpath('.'), srcpath('dir')
            })

    def test_str_path(self):
        expected = [
            Directory(srcpath('dir')),
            File(srcpath('dir/file2.txt'))
        ]
        with mock_context():
            self.assertFound(self.find('dir'), expected)

    def test_path_object(self):
        expected = [
            Directory(srcpath('dir')),
            File(srcpath('dir/file2.txt'))
        ]
        with mock_context():
            self.assertFound(self.find(srcpath('dir')), expected)

    def test_submodule(self):
        with self.context.push_path(Path('dir/build.bfg', Root.srcdir)), \
             mock_context():  # noqa
            expected = [
                Directory(srcpath('dir')),
                File(srcpath('dir/file2.txt'))
            ]
            self.assertFound(self.find('.'), expected)

    def test_submodule_parent(self):
        with self.context.push_path(Path('dir/build.bfg', Root.srcdir)), \
             mock_context():  # noqa
            expected = [
                Directory(srcpath('.')),
                Directory(srcpath('dir')),
                SourceFile(srcpath('file.cpp'), 'c++'),
                File(srcpath('dir/file2.txt'))
            ]
            self.assertFound(self.find('..'), expected)

    def test_submodule_path_object(self):
        with self.context.push_path(Path('dir/build.bfg', Root.srcdir)), \
             mock_context():  # noqa
            expected = [
                Directory(srcpath('.')),
                Directory(srcpath('dir')),
                SourceFile(srcpath('file.cpp'), 'c++'),
                File(srcpath('dir/file2.txt'))
            ]
            self.assertFound(self.find(srcpath('.')), expected)

    def test_name(self):
        expected = [
            SourceFile(srcpath('file.cpp'), 'c++'),
            File(srcpath('dir/file2.txt'))
        ]
        with mock_context():
            self.assertFound(self.find('.', 'file*'), expected)

    def test_type_file(self):
        expected = [
            SourceFile(srcpath('file.cpp'), 'c++'),
            File(srcpath('dir/file2.txt'))
        ]
        with mock_context():
            self.assertFound(self.find(type='f'), expected)

    def test_type_dir(self):
        expected = [
            Directory(srcpath('.')),
            Directory(srcpath('dir'))
        ]
        with mock_context():
            self.assertFound(self.find(type='d'), expected)

    def test_extra(self):
        expected = [SourceFile(srcpath('file.cpp'), 'c++')]
        dist = [self.bfgfile] + expected + [File(srcpath('dir/file2.txt'))]
        with mock_context():
            self.assertFound(self.find('.', '*.cpp', extra='*.txt'),
                             expected, dist)

    def test_exclude(self):
        expected = [SourceFile(srcpath('file.cpp'), 'c++')]
        with mock_context():
            self.assertFound(self.find('.', 'file*', exclude='*.txt'),
                             expected)

    def test_flat(self):
        expected = [
            Directory(srcpath('.')), Directory(srcpath('dir')),
            SourceFile(srcpath('file.cpp'), 'c++')
        ]
        with mock_context():
            self.assertFound(self.find(flat=True), expected)

    def test_filter(self):
        def my_filter(path, type):
            if path.basename() == 'dir':
                return find.FindResult.not_now
            elif path.ext() == '.cpp':
                return find.FindResult.include
            else:
                return find.FindResult.exclude

        expected = [SourceFile(srcpath('file.cpp'), 'c++')]
        with mock_context():
            self.assertFound(self.find(filter=my_filter), expected, [
                self.bfgfile, Directory(srcpath('dir'))
            ] + expected)

    def test_combine_filters(self):
        def my_filter(path, type):
            return (find.FindResult.include if type == 'f' else
                    find.FindResult.exclude)

        expected = [SourceFile(srcpath('file.cpp'), 'c++')]
        with mock_context():
            self.assertFound(self.find(name='*.cpp', filter=my_filter),
                             expected)

    def test_file_types(self):
        expected = [
            HeaderDirectory(srcpath('.')),
            HeaderDirectory(srcpath('dir')),
            File(srcpath('file.cpp')),
            File(srcpath('dir/file2.txt'))
        ]
        f = self.context['generic_file']
        d = self.context['header_directory']
        with mock_context():
            self.assertFound(self.find(file_type=f, dir_type=d), expected)
            self.assertEqual(self.build['find_dirs'], {
                srcpath('.'), srcpath('dir')
            })

    def test_dist(self):
        expected = [
            Directory(srcpath('.')),
            Directory(srcpath('dir')),
            SourceFile(srcpath('file.cpp'), 'c++'),
            File(srcpath('dir/file2.txt'))
        ]
        with mock_context():
            self.assertFound(self.find(dist=False), expected, [self.bfgfile])

    def test_cache(self):
        expected = [
            Directory(srcpath('.')),
            Directory(srcpath('dir')),
            SourceFile(srcpath('file.cpp'), 'c++'),
            File(srcpath('dir/file2.txt'))
        ]
        with mock_context():
            self.assertFound(self.find(cache=False), expected)
            self.assertEqual(self.build['find_dirs'], set())


class TestFindPaths(TestFindFiles):
    def setUp(self):
        super().setUp()
        self.find = self.context['find_paths']

    def assertFound(self, result, expected, dist=None):
        if dist is None:
            dist = [self.bfgfile] + expected
        self.assertEqual(result, [i.path for i in expected])
        self.assertEqual(list(self.build.sources()), dist)
