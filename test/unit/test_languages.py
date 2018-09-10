import unittest
from six import assertRaisesRegex

from bfg9000.languages import Languages


class TestLanguages(unittest.TestCase):
    def setUp(self):
        self.known_langs = Languages()
        with self.known_langs.make('c') as x:
            x.vars(compiler='CC')
            x.exts(source='.c')

    def test_make(self):
        with self.known_langs.make('c++') as x:
            x.vars(compiler='CXX')
            x.exts(source=['.cxx', '.cpp'])

        self.assertEqual(self.known_langs['c'].name, 'c')
        self.assertEqual(self.known_langs['c'].var('compiler'), 'CC')
        self.assertEqual(self.known_langs['c'].exts('source'), ['.c'])

        self.assertEqual(self.known_langs['c++'].name, 'c++')
        self.assertEqual(self.known_langs['c++'].var('compiler'), 'CXX')
        self.assertEqual(self.known_langs['c++'].exts('source'),
                         ['.cxx', '.cpp'])

    def test_make_duplicate_ext(self):
        msg = r"^'\.c' already used by 'c'$"
        with assertRaisesRegex(self, ValueError, msg):
            with self.known_langs.make('c++') as x:
                x.exts(source=['.c', '.cpp'])

    def test_get_unrecognized_lang(self):
        msg = r"^unrecognized language 'c\+\+'$"
        with assertRaisesRegex(self, ValueError, msg):
            self.known_langs['c++']

    def test_get_unrecognized_var(self):
        msg = r"^language 'c' does not support var 'goofy'$"
        with assertRaisesRegex(self, ValueError, msg):
            self.known_langs['c'].var('goofy')

    def test_get_unrecognized_exts(self):
        msg = r"^language 'c' does not support file type 'goofy'$"
        with assertRaisesRegex(self, ValueError, msg):
            self.known_langs['c'].exts('goofy')

    def test_fromext(self):
        self.assertEqual(self.known_langs.fromext('.c', 'source'), 'c')
        self.assertEqual(self.known_langs.fromext('.c', 'header'), None)
        self.assertEqual(self.known_langs.fromext('.c', 'goofy'), None)
        self.assertEqual(self.known_langs.fromext('.foo', 'source'), None)
