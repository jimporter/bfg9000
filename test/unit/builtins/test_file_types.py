from .common import BuiltinTest

from bfg9000 import file_types
from bfg9000.builtins.file_types import static_file
from bfg9000.path import Path, Root


class TestStaticFile(BuiltinTest):
    def setUp(self):
        BuiltinTest.setUp(self)
        self.bfgfile = file_types.File(self.build.bfgpath)

    def assertSame(self, a, b):
        self.assertEqual(type(a), type(b))
        for i in a.__dict__:
            self.assertEqual(getattr(a, i), getattr(b, i))

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
