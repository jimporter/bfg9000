from unittest import mock

from .common import BuiltinTestCase
from bfg9000 import file_types
from bfg9000.builtins import copy_file as _copy_file  # noqa: F401
from bfg9000.path import Path, Root


class TestCopyFile(BuiltinTestCase):
    def test_make_simple(self):
        expected = file_types.File(Path('file.txt'))
        result = self.context['copy_file'](file='file.txt')
        self.assertSameFile(result, expected)

        result = self.context['copy_file']('file.txt', 'src.txt')
        self.assertSameFile(result, expected)

        result = self.context['copy_file']('file.txt')
        self.assertSameFile(result, expected)

        src = self.context['generic_file']('file.txt')
        result = self.context['copy_file'](src)
        self.assertSameFile(result, expected)

    def test_make_no_name_or_file(self):
        self.assertRaises(TypeError, self.context['copy_file'])

    def test_make_directory(self):
        expected = file_types.File(Path('dir/file.txt'))
        copy_file = self.context['copy_file']

        result = copy_file('file.txt', directory='dir')
        self.assertSameFile(result, expected)

        src = self.context['generic_file']('file.txt')
        result = copy_file(src, directory='dir')
        self.assertSameFile(result, expected)

        result = copy_file('file.txt', directory='dir/')
        self.assertSameFile(result, expected)

        result = copy_file('file.txt', directory=Path('dir'))
        self.assertSameFile(result, expected)

        result = copy_file('dir1/file.txt', directory='dir2')
        self.assertSameFile(result,
                            file_types.File(Path('dir2/dir1/file.txt')))

        result = copy_file('copied.txt', 'file.txt', directory='dir')
        self.assertSameFile(result, file_types.File(Path('copied.txt')))

        self.assertRaises(ValueError, copy_file, file='file.txt',
                          directory=Path('dir', Root.srcdir))

    def test_make_submodule(self):
        with self.context.push_path(Path('dir/build.bfg', Root.srcdir)):
            copy_file = self.context['copy_file']
            File = file_types.File

            result = copy_file(file='file.txt')
            self.assertSameFile(result, File(Path('dir/file.txt')))
            result = copy_file(file='sub/file.txt')
            self.assertSameFile(result, File(Path('dir/sub/file.txt')))
            result = copy_file(file='../file.txt')
            self.assertSameFile(result, File(Path('file.txt')))

            result = copy_file('copied.txt', 'file.txt')
            self.assertSameFile(result, File(Path('dir/copied.txt')))
            result = copy_file('../copied.txt', 'file.txt')
            self.assertSameFile(result, File(Path('copied.txt')))

            result = copy_file(file='file.txt', directory='sub')
            self.assertSameFile(result, File(Path('dir/sub/file.txt')))
            result = copy_file(file='foo/file.txt', directory='sub')
            self.assertSameFile(result, File(Path('dir/sub/foo/file.txt')))
            result = copy_file(file='../file.txt', directory='sub')
            self.assertSameFile(result, File(Path('dir/sub/PAR/file.txt')))

            result = copy_file(file='file.txt', directory=Path('dir2'))
            self.assertSameFile(result, File(Path('dir2/dir/file.txt')))
            result = copy_file(file='sub/file.txt', directory=Path('dir2'))
            self.assertSameFile(result, File(Path('dir2/dir/sub/file.txt')))
            result = copy_file(file='../file.txt', directory=Path('dir2'))
            self.assertSameFile(result, File(Path('dir2/file.txt')))

            result = copy_file(file='file.txt', directory=Path('dir'))
            self.assertSameFile(result, File(Path('dir/dir/file.txt')))
            result = copy_file(file='sub/file.txt', directory=Path('dir'))
            self.assertSameFile(result, File(Path('dir/dir/sub/file.txt')))
            result = copy_file(file='../file.txt', directory=Path('dir'))
            self.assertSameFile(result, File(Path('dir/file.txt')))

    def test_extra_deps(self):
        dep = self.context['generic_file']('dep.txt')
        expected = file_types.File(Path('file.txt'))
        result = self.context['copy_file'](file='file.txt', extra_deps=[dep])
        self.assertSameFile(result, expected)
        self.assertEqual(result.creator.extra_deps, [dep])

    def test_invalid_mode(self):
        self.assertRaises(ValueError, self.context['copy_file'],
                          file='file.txt', mode='unknown')

    def test_description(self):
        result = self.context['copy_file'](
            file='file.txt', description='my description'
        )
        self.assertEqual(result.creator.description, 'my description')


class TestCopyFiles(BuiltinTestCase):
    def make_file_list(self, prefix=''):
        files = [file_types.File(Path(i, Root.builddir))
                 for i in [prefix + 'file1', prefix + 'file2']]
        src_files = [file_types.File(Path(i, Root.srcdir))
                     for i in [prefix + 'file1', prefix + 'file2']]

        file_list = self.context['copy_files'](src_files)
        return file_list, files, src_files

    def test_initialize(self):
        file_list, files, src_files = self.make_file_list()
        self.assertEqual(list(file_list), files)

    def test_getitem_index(self):
        file_list, files, src_files = self.make_file_list()
        self.assertEqual(file_list[0], files[0])

    def test_getitem_string(self):
        file_list, files, src_files = self.make_file_list()
        self.assertEqual(file_list['file1'], files[0])

    def test_getitem_string_submodule(self):
        file_list, files, src_files = self.make_file_list('dir/')
        self.assertEqual(file_list['dir/file1'], files[0])
        with self.context.push_path(Path('dir/build.bfg', Root.srcdir)):
            self.assertEqual(file_list['file1'], files[0])

    def test_getitem_path(self):
        file_list, files, src_files = self.make_file_list()
        self.assertEqual(file_list[src_files[0].path], files[0])

    def test_getitem_file(self):
        file_list, files, src_files = self.make_file_list()
        self.assertEqual(file_list[src_files[0]], files[0])

    def test_getitem_not_found(self):
        file_list, files, src_files = self.make_file_list()
        self.assertRaises(IndexError, lambda: file_list[2])
        self.assertRaises(IndexError, lambda: file_list['file3'])
        self.assertRaises(IndexError, lambda: file_list[Path(
            'file3', Root.srcdir
        )])


class TestManPage(BuiltinTestCase):
    def test_identity(self):
        expected = file_types.ManPage(Path('myprogram.1', Root.srcdir), '1')
        self.assertIs(self.context['man_page'](expected, compress=False),
                      expected)

    def test_compress(self):
        expected = file_types.ManPage(Path('myprogram.1.gz'), '1')
        result = self.context['man_page']('myprogram.1', compress=True)
        self.assertSameFile(result, expected)

        man_page = file_types.ManPage(Path('myprogram.1', Root.srcdir), '1')
        result = self.context['man_page'](man_page, compress=True)
        self.assertSameFile(result, expected)

        expected = file_types.ManPage(Path('myprogram.1s.gz'), '1')
        result = self.context['man_page']('myprogram.1s', compress=True)
        self.assertSameFile(result, expected)

        expected = file_types.ManPage(Path('myprogram.1.gz'), '2')
        result = self.context['man_page']('myprogram.1', level='2',
                                          compress=True)
        self.assertSameFile(result, expected)

    def test_no_compress(self):
        expected = file_types.ManPage(Path('myprogram.1', Root.srcdir), '1')
        result = self.context['man_page']('myprogram.1', compress=False)
        self.assertSameFile(result, expected)

        expected = file_types.ManPage(Path('myprogram.1s', Root.srcdir), '1')
        result = self.context['man_page']('myprogram.1s', compress=False)
        self.assertSameFile(result, expected)

        expected = file_types.ManPage(Path('myprogram.1', Root.srcdir), '2')
        result = self.context['man_page']('myprogram.1', level='2',
                                          compress=False)
        self.assertSameFile(result, expected)

    def test_auto_compress_enabled(self):
        with mock.patch('bfg9000.shell.which', return_value=['command']):
            self.env.tool('gzip')

        expected = file_types.ManPage(Path('myprogram.1.gz'), '1')
        result = self.context['man_page']('myprogram.1')
        self.assertSameFile(result, expected)

    def test_auto_compress_disabled(self):
        with mock.patch('bfg9000.shell.which',
                        side_effect=FileNotFoundError()), \
             mock.patch('warnings.warn'):
            self.env.tool('gzip')

        expected = file_types.ManPage(Path('myprogram.1', Root.srcdir), '1')
        result = self.context['man_page']('myprogram.1')
        self.assertSameFile(result, expected)

    def test_invalid(self):
        with self.assertRaises(ValueError):
            self.context['man_page']('myprogram.foo')

        man_page = file_types.ManPage(Path('myprogram.1', Root.srcdir), '1')
        with self.assertRaises(TypeError):
            self.context['man_page'](man_page, level='2')


class TestMakeBackend(BuiltinTestCase):
    def test_simple(self):
        makefile = mock.Mock()
        src = self.context['generic_file']('file.txt')

        result = self.context['copy_file'](file=src)
        _copy_file.make_copy_file(result.creator, self.build, makefile,
                                  self.env)
        makefile.rule.assert_called_once_with(
            target=[result], deps=[src], order_only=[], recipe=mock.ANY
        )

    def test_dir_sentinel(self):
        makefile = mock.Mock()
        src = self.context['generic_file']('dir/file.txt')

        result = self.context['copy_file'](file=src)
        _copy_file.make_copy_file(result.creator, self.build, makefile,
                                  self.env)
        makefile.rule.assert_called_once_with(
            target=[result], deps=[src], order_only=[Path('dir/.dir')],
            recipe=mock.ANY
        )

    def test_extra_deps(self):
        makefile = mock.Mock()
        dep = self.context['generic_file']('dep.txt')
        src = self.context['generic_file']('file.txt')

        result = self.context['copy_file'](file=src, extra_deps=dep)
        _copy_file.make_copy_file(result.creator, self.build, makefile,
                                  self.env)
        makefile.rule.assert_called_once_with(
            target=[result], deps=[src, dep], order_only=[],
            recipe=mock.ANY
        )


class TestNinjaBackend(BuiltinTestCase):
    def test_simple(self):
        ninjafile = mock.Mock()
        src = self.context['generic_file']('file.txt')

        result = self.context['copy_file'](file=src)
        _copy_file.ninja_copy_file(result.creator, self.build, ninjafile,
                                   self.env)
        ninjafile.build.assert_called_once_with(
            output=[result], rule='cp', inputs=src, implicit=[],
            variables={}
        )

    def test_extra_deps(self):
        ninjafile = mock.Mock()
        dep = self.context['generic_file']('dep.txt')
        src = self.context['generic_file']('file.txt')

        result = self.context['copy_file'](file=src, extra_deps=dep)
        _copy_file.ninja_copy_file(result.creator, self.build, ninjafile,
                                   self.env)
        ninjafile.build.assert_called_once_with(
            output=[result], rule='cp', inputs=src, implicit=[dep],
            variables={}
        )
