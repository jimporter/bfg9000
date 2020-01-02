from . import *

from bfg9000.languages import Formats, Languages


class TestLanguages(TestCase):
    def setUp(self):
        self.known_langs = Languages()
        with self.known_langs.make('c') as x:
            x.vars(compiler='CC')
            x.exts(source='.c', header='.h')

    def test_make(self):
        with self.known_langs.make('c++') as x:
            x.vars(compiler='CXX')
            x.exts(source=['.cxx', '.cpp'], header=['.hpp'])
            x.auxexts(header=['.h'])
        with self.known_langs.make('goofy', base='c++') as x:
            x.vars(compiler='GOOFY')
            x.exts(source=['.goofy'])
            x.auxexts(header=['.h'])

        c = self.known_langs['c']
        self.assertEqual(c.name, 'c')
        self.assertEqual(c.src_lang, 'c')
        self.assertEqual(c.var('compiler'), 'CC')
        self.assertEqual(c.exts('source'), ['.c'])
        self.assertEqual(c.exts('header'), ['.h'])
        self.assertEqual(c.auxexts('source'), [])
        self.assertEqual(c.auxexts('header'), [])
        self.assertEqual(c.allexts('source'), ['.c'])
        self.assertEqual(c.allexts('header'), ['.h'])
        self.assertEqual(c.default_ext('source'), '.c')
        self.assertEqual(c.default_ext('header'), '.h')
        self.assertEqual(c.extkind('.c'), 'source')
        self.assertEqual(c.extkind('.h'), 'header')
        self.assertEqual(c.extkind('.none'), None)

        cxx = self.known_langs['c++']
        self.assertEqual(cxx.name, 'c++')
        self.assertEqual(cxx.src_lang, 'c++')
        self.assertEqual(cxx.var('compiler'), 'CXX')
        self.assertEqual(cxx.exts('source'), ['.cxx', '.cpp'])
        self.assertEqual(cxx.exts('header'), ['.hpp'])
        self.assertEqual(cxx.auxexts('header'), ['.h'])
        self.assertEqual(cxx.allexts('source'), ['.cxx', '.cpp'])
        self.assertEqual(cxx.allexts('header'), ['.hpp', '.h'])
        self.assertEqual(cxx.default_ext('source'), '.cxx')
        self.assertEqual(cxx.default_ext('header'), '.hpp')
        self.assertEqual(cxx.extkind('.cxx'), 'source')
        self.assertEqual(cxx.extkind('.hpp'), 'header')
        self.assertEqual(cxx.extkind('.h'), 'header')
        self.assertEqual(cxx.extkind('.none'), None)

        g = self.known_langs['goofy']
        self.assertEqual(g.name, 'goofy')
        self.assertEqual(g.src_lang, 'c++')
        self.assertEqual(g.var('compiler'), 'GOOFY')
        self.assertEqual(g.exts('source'), ['.goofy'])
        self.assertEqual(g.exts('header'), [])
        self.assertEqual(g.auxexts('header'), ['.h'])
        self.assertEqual(g.allexts('source'), ['.goofy'])
        self.assertEqual(g.allexts('header'), ['.h'])
        self.assertEqual(g.default_ext('source'), '.goofy')
        self.assertEqual(g.default_ext('header'), '.h')
        self.assertEqual(g.extkind('.goofy'), 'source')
        self.assertEqual(g.extkind('.h'), 'header')
        self.assertEqual(g.extkind('.none'), None)

    def test_make_duplicate_ext(self):
        msg = r"^'\.c' already used by 'c'$"
        with self.assertRaisesRegex(ValueError, msg):
            with self.known_langs.make('c++') as x:
                x.exts(source=['.c', '.cpp'])

    def test_make_invalid_attr(self):
        with self.known_langs.make('c++') as x:
            with self.assertRaises(AttributeError):
                x.unknown()

    def test_in(self):
        self.assertTrue('c' in self.known_langs)
        self.assertFalse('c' not in self.known_langs)
        self.assertFalse('c++' in self.known_langs)
        self.assertTrue('c++' not in self.known_langs)

    def test_get_unrecognized_lang(self):
        msg = r"^unrecognized language 'c\+\+'$"
        with self.assertRaisesRegex(ValueError, msg):
            self.known_langs['c++']

    def test_get_unrecognized_var(self):
        msg = r"^language 'c' does not support var 'goofy'$"
        with self.assertRaisesRegex(ValueError, msg):
            self.known_langs['c'].var('goofy')

    def test_get_unrecognized_exts(self):
        msg = r"^language 'c' does not support file type 'goofy'$"
        with self.assertRaisesRegex(ValueError, msg):
            self.known_langs['c'].exts('goofy')

    def test_fromext(self):
        self.assertEqual(self.known_langs.fromext('.c', 'source'), 'c')
        self.assertEqual(self.known_langs.fromext('.c', 'header'), None)
        self.assertEqual(self.known_langs.fromext('.c', 'goofy'), None)
        self.assertEqual(self.known_langs.fromext('.foo', 'source'), None)


class TestFormats(TestCase):
    def setUp(self):
        self.known_formats = Formats()
        with self.known_formats.make('native', 'static') as x:
            x.vars(linker='AR')
        with self.known_formats.make('native', 'dynamic') as x:
            x.vars(linker='LD')

    def test_make(self):
        with self.known_formats.make('goofy', 'dynamic') as x:
            x.vars(linker='GOOFY')

        native = self.known_formats['native', 'static']
        self.assertEqual(native.name, ('native', 'static'))
        self.assertEqual(native.var('linker'), 'AR')

        native = self.known_formats['native', 'dynamic']
        self.assertEqual(native.name, ('native', 'dynamic'))
        self.assertEqual(native.var('linker'), 'LD')

        goofy = self.known_formats['goofy', 'dynamic']
        self.assertEqual(goofy.name, ('goofy', 'dynamic'))
        self.assertEqual(goofy.var('linker'), 'GOOFY')

    def test_make_invalid_attr(self):
        with self.known_formats.make('goofy', 'dynamic') as x:
            with self.assertRaises(AttributeError):
                x.unknown()

    def test_get_unrecognized_format(self):
        msg = r"^unrecognized format 'goofy \(dynamic\)'$"
        with self.assertRaisesRegex(ValueError, msg):
            self.known_formats['goofy', 'dynamic']
