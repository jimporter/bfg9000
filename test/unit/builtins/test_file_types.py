from .common import BuiltinTest

from bfg9000 import file_types
from bfg9000.builtins.file_types import static_file
from bfg9000.path import Path, Root


class TestStaticFile(BuiltinTest):
    def test_basic(self):
        expected = file_types.File(Path('file.txt', Root.srcdir))
        self.assertSame(static_file(self.build, file_types.File, 'file.txt'),
                        expected)
        self.assertEqual(list(self.build.sources()), [self.bfgfile, expected])

    def test_path(self):
        p = Path('file.txt', Root.srcdir)
        expected = file_types.File(p)
        self.assertSame(static_file(self.build, file_types.File, p), expected)
        self.assertEqual(list(self.build.sources()), [self.bfgfile, expected])

    def test_builddir_path(self):
        p = Path('file.txt', Root.builddir)
        expected = file_types.File(p)
        self.assertSame(static_file(self.build, file_types.File, p), expected)
        self.assertEqual(list(self.build.sources()), [self.bfgfile])

    def test_params_default(self):
        expected = file_types.SourceFile(Path('file.txt', Root.srcdir), 'c')
        self.assertSame(static_file(
            self.build, file_types.SourceFile, 'file.txt', [('lang', 'c')]
        ), expected)
        self.assertEqual(list(self.build.sources()), [self.bfgfile, expected])

    def test_params_custom(self):
        expected = file_types.SourceFile(Path('file.txt', Root.srcdir), 'c++')
        self.assertSame(static_file(
            self.build, file_types.SourceFile, 'file.txt', [('lang', 'c')],
            {'lang': 'c++'}
        ), expected)
        self.assertEqual(list(self.build.sources()), [self.bfgfile, expected])

    def test_extra_kwargs(self):
        self.assertRaises(TypeError, static_file, self.build,
                          file_types.SourceFile, 'file.txt', [('lang', 'c')],
                          {'lang': 'c++', 'extra': 'value'})
        self.assertEqual(list(self.build.sources()), [self.bfgfile])


class TestAutoFile(BuiltinTest):
    def test_identity(self):
        expected = file_types.File(Path('file.txt', Root.srcdir))
        self.assertIs(self.builtin_dict['auto_file'](expected), expected)
        self.assertEqual(list(self.build.sources()), [self.bfgfile])

    def test_source_file(self):
        expected = file_types.SourceFile(Path('file.cpp', Root.srcdir), 'c++')
        self.assertSame(self.builtin_dict['auto_file']('file.cpp'), expected)
        self.assertEqual(list(self.build.sources()), [self.bfgfile, expected])

    def test_header_file(self):
        expected = file_types.HeaderFile(Path('file.hpp', Root.srcdir), 'c++')
        self.assertSame(self.builtin_dict['auto_file']('file.hpp'), expected)
        self.assertEqual(list(self.build.sources()), [self.bfgfile, expected])

    def test_other_file(self):
        expected = file_types.File(Path('file.txt', Root.srcdir))
        self.assertSame(self.builtin_dict['auto_file']('file.txt'), expected)
        self.assertEqual(list(self.build.sources()), [self.bfgfile, expected])

    def test_auxext(self):
        expected = file_types.HeaderFile(Path('file.h', Root.srcdir), 'c++')
        self.assertSame(self.builtin_dict['auto_file']('file.h', 'c++'),
                        expected)
        self.assertEqual(list(self.build.sources()), [self.bfgfile, expected])

    def test_unknown_ext(self):
        ex = file_types.SourceFile(Path('file.goofy', Root.srcdir), 'c++')
        self.assertSame(self.builtin_dict['auto_file'](
            'file.goofy', 'c++'
        ), ex)
        self.assertEqual(list(self.build.sources()), [self.bfgfile, ex])

    def test_unknown_lang(self):
        ex = file_types.SourceFile(Path('file.goofy', Root.srcdir), 'goofy')
        self.assertSame(self.builtin_dict['auto_file'](
            'file.goofy', 'goofy'
        ), ex)
        self.assertEqual(list(self.build.sources()), [self.bfgfile, ex])
