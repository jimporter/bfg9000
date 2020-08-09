from unittest import mock

from .common import AttrDict, BuiltinTest

from bfg9000.builtins import regenerate  # noqa
from bfg9000.builtins.file_types import FileList, static_file
from bfg9000.file_types import *
from bfg9000.path import Path, Root


def srcpath(p):
    return Path(p, Root.srcdir)


class TestStaticFile(BuiltinTest):
    def test_basic(self):
        expected = File(srcpath('file.txt'))
        self.assertSameFile(static_file(self.context, File, 'file.txt'),
                            expected)
        self.assertEqual(list(self.build.sources()), [self.bfgfile, expected])

    def test_path(self):
        p = srcpath('file.txt')
        expected = File(p)
        self.assertSameFile(static_file(self.context, File, p), expected)
        self.assertEqual(list(self.build.sources()), [self.bfgfile, expected])

    def test_builddir_path(self):
        p = Path('file.txt', Root.builddir)
        expected = File(p)
        self.assertSameFile(static_file(self.context, File, p), expected)
        self.assertEqual(list(self.build.sources()), [self.bfgfile])

    def test_submodule(self):
        with self.context.push_path(Path('dir/build.bfg', Root.srcdir)):
            expected = File(srcpath('dir/file.txt'))
            self.assertSameFile(static_file(self.context, File, 'file.txt'),
                                expected)
            self.assertEqual(list(self.build.sources()),
                             [self.bfgfile, expected])

    def test_no_dist(self):
        p = srcpath('file.txt')
        expected = File(p)
        self.assertSameFile(static_file(self.context, File, p, dist=False),
                            expected)
        self.assertEqual(list(self.build.sources()), [self.bfgfile])

    def test_params_default(self):
        expected = SourceFile(srcpath('file.txt'), 'c')
        self.assertSameFile(static_file(
            self.context, SourceFile, 'file.txt', params=[('lang', 'c')]
        ), expected)
        self.assertEqual(list(self.build.sources()), [self.bfgfile, expected])

    def test_params_custom(self):
        expected = SourceFile(srcpath('file.txt'), 'c++')
        self.assertSameFile(static_file(
            self.context, SourceFile, 'file.txt', params=[('lang', 'c')],
            kwargs={'lang': 'c++'}
        ), expected)
        self.assertEqual(list(self.build.sources()), [self.bfgfile, expected])

    def test_extra_kwargs(self):
        self.assertRaises(TypeError, static_file, self.context,
                          SourceFile, 'file.txt', params=[('lang', 'c')],
                          kwargs={'lang': 'c++', 'extra': 'value'})
        self.assertEqual(list(self.build.sources()), [self.bfgfile])


class TestFileList(BuiltinTest):
    def make_file_list(self, *args):
        def make_file(src, format=None):
            obj = ObjectFile(src.path.stripext('.o').reroot(), format,
                             src.lang)
            obj.creator = AttrDict(file=src)
            return obj

        files = [SourceFile(srcpath(i), 'c++') for i in args]
        return FileList(self.context, make_file, files, format='elf')

    def test_len(self):
        self.assertEqual(len(self.make_file_list()), 0)
        self.assertEqual(len(self.make_file_list('foo.cpp', 'bar.cpp')), 2)

    def test_index_int(self):
        f = self.make_file_list('foo.cpp', 'bar.cpp')
        self.assertSameFile(f[0], ObjectFile(Path('foo.o'), 'elf', 'c++'))

    def test_index_str(self):
        f = self.make_file_list('foo.cpp', 'bar.cpp')
        self.assertSameFile(f['foo.cpp'],
                            ObjectFile(Path('foo.o'), 'elf', 'c++'))

    def test_index_path(self):
        f = self.make_file_list('foo.cpp', 'bar.cpp')
        self.assertSameFile(f[srcpath('foo.cpp')],
                            ObjectFile(Path('foo.o'), 'elf', 'c++'))

    def test_index_file(self):
        f = self.make_file_list('foo.cpp', 'bar.cpp')
        src = SourceFile(srcpath('foo.cpp'), 'c++')
        self.assertEqual(f[src], ObjectFile(Path('foo.o'), 'elf', 'c++'))

    def test_submodule(self):
        f = self.make_file_list('dir/foo.cpp', 'dir/bar.cpp')
        obj = ObjectFile(Path('dir/foo.o'), 'elf', 'c++')
        with self.context.push_path(Path('dir/build.bfg', Root.srcdir)):
            self.assertSameFile(f['foo.cpp'], obj)
        self.assertSameFile(f['dir/foo.cpp'], obj)


class TestAutoFile(BuiltinTest):
    def test_identity(self):
        expected = File(srcpath('file.txt'))
        self.assertIs(self.context['auto_file'](expected), expected)
        self.assertEqual(list(self.build.sources()), [self.bfgfile])

    def test_source_file(self):
        expected = SourceFile(srcpath('file.cpp'), 'c++')
        self.assertSameFile(self.context['auto_file']('file.cpp'),
                            expected)
        self.assertEqual(list(self.build.sources()), [self.bfgfile, expected])

    def test_header_file(self):
        expected = HeaderFile(srcpath('file.hpp'), 'c++')
        self.assertSameFile(self.context['auto_file']('file.hpp'),
                            expected)
        self.assertEqual(list(self.build.sources()), [self.bfgfile, expected])

    def test_other_file(self):
        expected = File(srcpath('file.txt'))
        self.assertSameFile(self.context['auto_file']('file.txt'),
                            expected)
        self.assertEqual(list(self.build.sources()), [self.bfgfile, expected])

    def test_directory(self):
        expected = Directory(srcpath('directory/'))
        self.assertSameFile(self.context['auto_file']('directory/'),
                            expected)
        self.assertEqual(list(self.build.sources()), [self.bfgfile, expected])

    def test_header_directory(self):
        expected = HeaderDirectory(srcpath('directory/'), 'c++')
        self.assertSameFile(self.context['auto_file']('directory/', 'c++'),
                            expected)
        self.assertEqual(list(self.build.sources()), [self.bfgfile, expected])

    def test_auxext(self):
        expected = HeaderFile(srcpath('file.h'), 'c++')
        self.assertSameFile(self.context['auto_file']('file.h', 'c++'),
                            expected)
        self.assertEqual(list(self.build.sources()), [self.bfgfile, expected])

    def test_src_lang(self):
        expected_src = SourceFile(srcpath('file.cpp'), 'qtmoc')
        self.assertSameFile(self.context['auto_file']('file.cpp', 'qtmoc'),
                            expected_src)

        expected_hdr = HeaderFile(srcpath('file.hpp'), 'qtmoc')
        self.assertSameFile(self.context['auto_file']('file.hpp', 'qtmoc'),
                            expected_hdr)
        self.assertEqual(list(self.build.sources()), [
            self.bfgfile, expected_src, expected_hdr,
        ])

    def test_unknown_ext(self):
        expected = SourceFile(srcpath('file.goofy'), 'c++')
        self.assertSameFile(self.context['auto_file']('file.goofy', 'c++'),
                            expected)
        self.assertEqual(list(self.build.sources()), [self.bfgfile, expected])

    def test_unknown_lang(self):
        expected = SourceFile(srcpath('file.goofy'), 'goofy')
        self.assertSameFile(self.context['auto_file']('file.goofy', 'goofy'),
                            expected)
        self.assertEqual(list(self.build.sources()), [self.bfgfile, expected])

    def test_submodule(self):
        with self.context.push_path(Path('dir/build.bfg', Root.srcdir)):
            expected = SourceFile(srcpath('file.cpp'), 'c++')
            self.assertIs(self.context['auto_file'](expected), expected)
            self.assertEqual(list(self.build.sources()), [self.bfgfile])

            expected = SourceFile(srcpath('dir/file.cpp'), 'c++')
            self.assertSameFile(self.context['auto_file']('file.cpp'),
                                expected)
            self.assertEqual(list(self.build.sources()),
                             [self.bfgfile, expected])


class TestGenericFile(BuiltinTest):
    type = File
    args = ()
    fn = 'generic_file'
    filename = 'file.txt'

    def test_identity(self):
        expected = self.type(srcpath(self.filename), *self.args)
        self.assertIs(self.context[self.fn](expected), expected)
        self.assertEqual(list(self.build.sources()), [self.bfgfile])

    def test_basic(self):
        expected = self.type(srcpath(self.filename), *self.args)
        self.assertSameFile(self.context[self.fn](self.filename),
                            expected)
        self.assertEqual(list(self.build.sources()), [self.bfgfile, expected])

    def test_no_dist(self):
        expected = self.type(srcpath(self.filename), *self.args)
        self.assertSameFile(
            self.context[self.fn](self.filename, dist=False), expected
        )
        self.assertEqual(list(self.build.sources()), [self.bfgfile])

    def test_path(self):
        path = srcpath(self.filename)
        expected = self.type(path, *self.args)
        self.assertSameFile(self.context[self.fn](path), expected)
        self.assertEqual(list(self.build.sources()), [self.bfgfile, expected])

    def test_submodule(self):
        with self.context.push_path(Path('dir/build.bfg', Root.srcdir)):
            expected = self.type(srcpath(self.filename), *self.args)
            self.assertIs(self.context[self.fn](expected), expected)
            self.assertEqual(list(self.build.sources()), [self.bfgfile])

            expected = self.type(srcpath('dir/' + self.filename), *self.args)
            self.assertSameFile(self.context[self.fn](self.filename),
                                expected)
            self.assertEqual(list(self.build.sources()),
                             [self.bfgfile, expected])


class TestModuleDefFile(TestGenericFile):
    type = ModuleDefFile
    fn = 'module_def_file'
    filename = 'file.def'


class TestSourceFile(TestGenericFile):
    type = SourceFile
    args = ('c++',)
    fn = 'source_file'
    filename = 'file.cpp'
    lang = 'c++'

    def test_lang(self):
        expected = self.type(srcpath('file.goofy'), self.lang)
        self.assertSameFile(self.context[self.fn](
            'file.goofy', lang=self.lang
        ), expected)
        self.assertEqual(list(self.build.sources()), [self.bfgfile, expected])


class TestHeaderFile(TestSourceFile):
    type = HeaderFile
    fn = 'header_file'
    filename = 'file.hpp'


class TestDirectory(TestGenericFile):
    type = Directory
    fn = 'directory'
    filename = 'dir'

    def test_include(self):
        def mock_walk(path, variables=None):
            p = srcpath
            return [
                (p('dir'), [p('dir/sub')], [p('dir/file.txt')]),
                (p('dir/sub'), [], [p('dir/sub/file2.txt')]),
            ]

        expected = self.type(srcpath(self.filename), [
            File(srcpath('dir/file.txt')),
            File(srcpath('dir/sub/file2.txt')),
        ])
        with mock.patch('bfg9000.builtins.find.walk', mock_walk):
            self.assertSameFile(
                self.context[self.fn](self.filename, include='**/*.txt'),
                expected
            )
            self.assertEqual(list(self.build.sources()),
                             [self.bfgfile] + expected.files + [expected])


class TestHeaderDirectory(TestDirectory):
    type = HeaderDirectory
    fn = 'header_directory'
    filename = 'include'

    def test_include(self):
        def mock_walk(path, variables=None):
            p = srcpath
            return [
                (p('include'), [p('include/sub')], [p('include/file.hpp')]),
                (p('include/sub'), [], [p('include/sub/file2.hpp')]),
            ]

        expected = self.type(srcpath(self.filename), [
            HeaderFile(srcpath('include/file.hpp'), 'c++'),
            HeaderFile(srcpath('include/sub/file2.hpp'), 'c++'),
        ], langs=['c++'])
        with mock.patch('bfg9000.builtins.find.walk', mock_walk):
            self.assertSameFile(
                self.context[self.fn](self.filename, include='**/*.hpp'),
                expected
            )
            self.assertEqual(list(self.build.sources()),
                             [self.bfgfile] + expected.files + [expected])
