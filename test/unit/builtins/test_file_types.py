from unittest import mock

from .common import BuiltinTest

from bfg9000.builtins.file_types import static_file
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

    def test_auxext(self):
        expected = HeaderFile(srcpath('file.h'), 'c++')
        self.assertSameFile(self.context['auto_file']('file.h', 'c++'),
                            expected)
        self.assertEqual(list(self.build.sources()), [self.bfgfile, expected])

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


class TestReourceFile(TestSourceFile):
    type = ResourceFile
    args = ('qrc',)
    fn = 'resource_file'
    filename = 'file.qrc'
    lang = 'qrc'


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
        with mock.patch('bfg9000.builtins.find._walk_recursive', mock_walk):
            self.assertSameFile(
                self.context[self.fn](self.filename, include='*.txt'),
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
        with mock.patch('bfg9000.builtins.find._walk_recursive', mock_walk):
            self.assertSameFile(
                self.context[self.fn](self.filename, include='*.hpp'),
                expected
            )
            self.assertEqual(list(self.build.sources()),
                             [self.bfgfile] + expected.files + [expected])
