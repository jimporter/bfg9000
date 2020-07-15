from .. import *

from bfg9000 import options as opts
from bfg9000.file_types import *
from bfg9000.languages import Languages
from bfg9000.path import Path, Root
from bfg9000.tools.yacc import YaccBuilder

known_langs = Languages()
with known_langs.make('yacc') as x:
    x.vars(compiler='YACC', flags='YFLAGS')


class TestYaccBuilder(CrossPlatformTestCase):
    def __init__(self, *args, **kwargs):
        super().__init__(clear_variables=True, *args, **kwargs)

    def setUp(self):
        self.yacc = YaccBuilder(self.env, known_langs['yacc'], ['yacc'],
                                'version')
        self.compiler = self.yacc.transpiler

    def test_properties(self):
        self.assertEqual(self.compiler.num_outputs, 1)
        self.assertEqual(self.compiler.deps_flavor, None)

    def test_call(self):
        self.assertEqual(self.compiler('in', 'out'),
                         [self.compiler, 'in', '-o', 'out'])
        self.assertEqual(self.compiler('in', 'out', ['flags']),
                         [self.compiler, 'flags', 'in', '-o', 'out'])

    def test_default_name(self):
        src = SourceFile(Path('file.l', Root.srcdir), 'yacc')
        self.assertEqual(self.compiler.default_name(src, None),
                         ['file.tab.c', 'file.tab.h'])
        self.assertEqual(self.compiler.default_name(src, AttrDict(
            user_options=opts.option_list(opts.lang('c++'))
        )), ['file.tab.cpp', 'file.tab.hpp'])

        with self.assertRaises(ValueError):
            self.compiler.default_name(src, AttrDict(
                user_options=opts.option_list(opts.lang('java'))
            ))

    def test_output_file(self):
        src = SourceFile(Path('file.tab.c'), 'c')
        hdr = HeaderFile(Path('file.tab.h'), 'c')

        self.assertEqual(self.compiler.output_file('file.tab.c', None), src)
        self.assertEqual(self.compiler.output_file(
            ['file.tab.c', 'file.tab.h'], None
        ), [src, hdr])

        src = SourceFile(Path('file.tab.cpp'), 'c++')
        hdr = HeaderFile(Path('file.tab.hpp'), 'c++')
        context = AttrDict(user_options=opts.option_list(opts.lang('c++')))
        self.assertEqual(self.compiler.output_file('file.tab.cpp', context),
                         src)
        self.assertEqual(self.compiler.output_file(
            ['file.tab.cpp', 'file.tab.hpp'], context
        ), [src, hdr])

        with self.assertRaises(ValueError):
            self.compiler.output_file(['file.tab.c', 'file.tab.h', 'extra'],
                                      None)

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
        )), ['--language=c++'])

    def test_flags_string(self):
        self.assertEqual(self.compiler.flags(opts.option_list('-i')), ['-i'])

    def test_flags_invalid(self):
        with self.assertRaises(TypeError):
            self.compiler.flags(opts.option_list(123))
