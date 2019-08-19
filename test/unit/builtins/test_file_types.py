from .common import BuiltinTest

from bfg9000.builtins.file_types import static_file
from bfg9000.file_types import File, HeaderFile, SourceFile
from bfg9000.path import Path, Root


class TestStaticFile(BuiltinTest):
    def test_basic(self):
        expected = File(Path('file.txt', Root.srcdir))
        self.assertSameFile(static_file(self.build, File, 'file.txt'),
                            expected)
        self.assertEqual(list(self.build.sources()), [self.bfgfile, expected])

    def test_path(self):
        p = Path('file.txt', Root.srcdir)
        expected = File(p)
        self.assertSameFile(static_file(self.build, File, p), expected)
        self.assertEqual(list(self.build.sources()), [self.bfgfile, expected])

    def test_builddir_path(self):
        p = Path('file.txt', Root.builddir)
        expected = File(p)
        self.assertSameFile(static_file(self.build, File, p), expected)
        self.assertEqual(list(self.build.sources()), [self.bfgfile])

    def test_params_default(self):
        expected = SourceFile(Path('file.txt', Root.srcdir), 'c')
        self.assertSameFile(static_file(
            self.build, SourceFile, 'file.txt', [('lang', 'c')]
        ), expected)
        self.assertEqual(list(self.build.sources()), [self.bfgfile, expected])

    def test_params_custom(self):
        expected = SourceFile(Path('file.txt', Root.srcdir), 'c++')
        self.assertSameFile(static_file(
            self.build, SourceFile, 'file.txt', [('lang', 'c')],
            {'lang': 'c++'}
        ), expected)
        self.assertEqual(list(self.build.sources()), [self.bfgfile, expected])

    def test_extra_kwargs(self):
        self.assertRaises(TypeError, static_file, self.build,
                          SourceFile, 'file.txt', [('lang', 'c')],
                          {'lang': 'c++', 'extra': 'value'})
        self.assertEqual(list(self.build.sources()), [self.bfgfile])


class TestAutoFile(BuiltinTest):
    def test_identity(self):
        expected = File(Path('file.txt', Root.srcdir))
        self.assertIs(self.builtin_dict['auto_file'](expected), expected)
        self.assertEqual(list(self.build.sources()), [self.bfgfile])

    def test_source_file(self):
        expected = SourceFile(Path('file.cpp', Root.srcdir), 'c++')
        self.assertSameFile(self.builtin_dict['auto_file']('file.cpp'),
                            expected)
        self.assertEqual(list(self.build.sources()), [self.bfgfile, expected])

    def test_header_file(self):
        expected = HeaderFile(Path('file.hpp', Root.srcdir), 'c++')
        self.assertSameFile(self.builtin_dict['auto_file']('file.hpp'),
                            expected)
        self.assertEqual(list(self.build.sources()), [self.bfgfile, expected])

    def test_other_file(self):
        expected = File(Path('file.txt', Root.srcdir))
        self.assertSameFile(self.builtin_dict['auto_file']('file.txt'),
                            expected)
        self.assertEqual(list(self.build.sources()), [self.bfgfile, expected])

    def test_auxext(self):
        expected = HeaderFile(Path('file.h', Root.srcdir), 'c++')
        self.assertSameFile(self.builtin_dict['auto_file']('file.h', 'c++'),
                            expected)
        self.assertEqual(list(self.build.sources()), [self.bfgfile, expected])

    def test_unknown_ext(self):
        expected = SourceFile(Path('file.goofy', Root.srcdir), 'c++')
        self.assertSameFile(self.builtin_dict['auto_file'](
            'file.goofy', 'c++'
        ), expected)
        self.assertEqual(list(self.build.sources()), [self.bfgfile, expected])

    def test_unknown_lang(self):
        expected = SourceFile(Path('file.goofy', Root.srcdir), 'goofy')
        self.assertSameFile(self.builtin_dict['auto_file'](
            'file.goofy', 'goofy'
        ), expected)
        self.assertEqual(list(self.build.sources()), [self.bfgfile, expected])
