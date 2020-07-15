from .. import *

from bfg9000 import options as opts
from bfg9000.file_types import *
from bfg9000.languages import Languages
from bfg9000.path import Path, Root
from bfg9000.tools.lex import LexBuilder

known_langs = Languages()
with known_langs.make('lex') as x:
    x.vars(compiler='LEX', flags='LFLAGS')


class TestLexBuilder(CrossPlatformTestCase):
    def __init__(self, *args, **kwargs):
        super().__init__(clear_variables=True, *args, **kwargs)

    def setUp(self):
        self.lex = LexBuilder(self.env, known_langs['lex'], ['lex'],
                              'version')
        self.compiler = self.lex.transpiler

    def test_properties(self):
        self.assertEqual(self.compiler.num_outputs, 'all')
        self.assertEqual(self.compiler.deps_flavor, None)

    def test_call(self):
        self.assertEqual(self.compiler('in', 'out'),
                         [self.compiler, '-o', 'out', 'in'])
        self.assertEqual(self.compiler('in', 'out', ['flags']),
                         [self.compiler, 'flags', '-o', 'out', 'in'])

    def test_default_name(self):
        src = SourceFile(Path('file.l', Root.srcdir), 'lex')
        self.assertEqual(self.compiler.default_name(src, None), 'file.yy.c')
        self.assertEqual(self.compiler.default_name(src, AttrDict(
            user_options=opts.option_list(opts.lang('c++'))
        )), 'file.yy.cpp')

        with self.assertRaises(ValueError):
            self.compiler.default_name(src, AttrDict(
                user_options=opts.option_list(opts.lang('java'))
            ))

    def test_output_file(self):
        self.assertEqual(self.compiler.output_file('file.yy.c', None),
                         SourceFile(Path('file.yy.c'), 'c'))
        self.assertEqual(self.compiler.output_file('file.yy.cpp', AttrDict(
            user_options=opts.option_list(opts.lang('c++'))
        )), SourceFile(Path('file.yy.cpp'), 'c++'))

    def test_flags_empty(self):
        self.assertEqual(self.compiler.flags(opts.option_list()), [])

    def test_flags_define(self):
        self.assertEqual(self.compiler.flags(opts.option_list(
            opts.define('NAME')
        )), ['-DNAME'])
        self.assertEqual(self.compiler.flags(opts.option_list(
            opts.define('NAME', 'value')
        )), ['-DNAME=value'])

    def test_flags_warning(self):
        self.assertEqual(self.compiler.flags(opts.option_list(
            opts.warning('disable')
        )), ['-w'])

        with self.assertRaises(ValueError):
            self.compiler.flags(opts.option_list(opts.warning('all')))

    def test_flags_lang(self):
        self.assertEqual(self.compiler.flags(opts.option_list(
            opts.lang('c++')
        )), ['--c++'])

    def test_flags_string(self):
        self.assertEqual(self.compiler.flags(opts.option_list('-i')), ['-i'])

    def test_flags_invalid(self):
        with self.assertRaises(TypeError):
            self.compiler.flags(opts.option_list(123))
