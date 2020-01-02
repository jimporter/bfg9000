from unittest import mock

from .. import *

from bfg9000 import options as opts
from bfg9000.file_types import *
from bfg9000.languages import Languages
from bfg9000.path import Path, Root
from bfg9000.tools.qt import MocBuilder, RccBuilder, UicBuilder

known_langs = Languages()
with known_langs.make('qtmoc') as x:
    x.vars(compiler='MOC', flags='MOCFLAGS')
with known_langs.make('qrc') as x:
    x.vars(compiler='RCC', flags='RCCFLAGS')
with known_langs.make('qtui') as x:
    x.vars(compiler='UIC', flags='UICFLAGS')


def mock_which(*args, **kwargs):
    return ['command']


class TestMocBuilder(CrossPlatformTestCase):
    def __init__(self, *args, **kwargs):
        CrossPlatformTestCase.__init__(self, clear_variables=True, *args,
                                       **kwargs)

    def setUp(self):
        self.moc = MocBuilder(self.env, known_langs['qtmoc'], ['moc'],
                              'version')
        self.compiler = self.moc.transpiler

    def test_properties(self):
        self.assertEqual(self.compiler.num_outputs, 'all')
        self.assertEqual(self.compiler.deps_flavor, None)
        self.assertEqual(self.compiler.needs_libs, False)

    def test_call(self):
        self.assertEqual(self.compiler('in', 'out'),
                         [self.compiler, 'in', '-o', 'out'])
        self.assertEqual(self.compiler('in', 'out', ['flags']),
                         [self.compiler, 'flags', 'in', '-o', 'out'])

    def test_default_name(self):
        src = SourceFile(Path('file.cpp', Root.srcdir), 'c++')
        self.assertEqual(self.compiler.default_name(src, None), 'file.moc')

        hdr = HeaderFile(Path('file.hpp', Root.srcdir), 'c++')
        self.assertEqual(self.compiler.default_name(hdr, None), 'moc_file.cpp')

    def test_output_file(self):
        self.assertEqual(self.compiler.output_file('file.moc', None),
                         SourceFile(Path('file.moc'), 'c++'))

    def test_flags_empty(self):
        self.assertEqual(self.compiler.flags(opts.option_list()), [])

    def test_flags_include_dir(self):
        p = self.Path('/path/to/include')
        self.assertEqual(self.compiler.flags(opts.option_list(
            opts.include_dir(HeaderDirectory(p))
        )), ['-I' + p])

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
        )), ['--no-warnings'])

        with self.assertRaises(ValueError):
            self.compiler.flags(opts.option_list(opts.warning('all')))

    def test_flags_string(self):
        self.assertEqual(self.compiler.flags(opts.option_list('-i')), ['-i'])

    def test_flags_invalid(self):
        with self.assertRaises(TypeError):
            self.compiler.flags(opts.option_list(123))


class TestRccBuilder(CrossPlatformTestCase):
    def __init__(self, *args, **kwargs):
        CrossPlatformTestCase.__init__(
            self, clear_variables=True, variables={'RCCDEP': 'rccdep'}, *args,
            **kwargs
        )

    def setUp(self):
        self.rcc = RccBuilder(self.env, known_langs['qrc'], ['rcc'], 'version')
        self.compiler = self.rcc.transpiler

    def test_properties(self):
        self.assertEqual(self.compiler.num_outputs, 'all')
        self.assertEqual(self.compiler.deps_flavor, 'gcc')
        self.assertEqual(self.compiler.needs_libs, False)

    def test_call(self):
        self.assertEqual(self.compiler('in', 'out'),
                         [self.compiler, 'in', '-o', 'out'])
        self.assertEqual(self.compiler('in', 'out', flags=['flags']),
                         [self.compiler, 'flags', 'in', '-o', 'out'])

        with mock.patch('bfg9000.shell.which', mock_which):
            rccdep = self.env.tool('rccdep')
            self.assertEqual(
                self.compiler('in', 'out', 'out.d'),
                [rccdep, self.compiler, 'in', '-o', 'out', '-d', 'out.d']
            )
            self.assertEqual(
                self.compiler('in', 'out', 'out.d', ['flags']),
                [rccdep, self.compiler, 'flags', 'in', '-o', 'out', '-d',
                 'out.d']
            )

    def test_default_name(self):
        src = ResourceFile(Path('file.qrc', Root.srcdir), 'qrc')
        self.assertEqual(self.compiler.default_name(src, None), 'file.cpp')

    def test_output_file(self):
        self.assertEqual(self.compiler.output_file('file.cpp', None),
                         SourceFile(Path('file.cpp'), 'c++'))

    def test_flags_empty(self):
        self.assertEqual(self.compiler.flags(opts.option_list()), [])

    def test_flags_string(self):
        self.assertEqual(self.compiler.flags(opts.option_list('-v')), ['-v'])

    def test_flags_invalid(self):
        with self.assertRaises(TypeError):
            self.compiler.flags(opts.option_list(123))


class TestUicBuilder(CrossPlatformTestCase):
    def __init__(self, *args, **kwargs):
        CrossPlatformTestCase.__init__(self, clear_variables=True, *args,
                                       **kwargs)

    def setUp(self):
        self.uic = UicBuilder(self.env, known_langs['qtui'], ['uic'],
                              'version')
        self.compiler = self.uic.transpiler

    def test_properties(self):
        self.assertEqual(self.compiler.num_outputs, 'all')
        self.assertEqual(self.compiler.deps_flavor, None)
        self.assertEqual(self.compiler.needs_libs, False)

    def test_call(self):
        self.assertEqual(self.compiler('in', 'out'),
                         [self.compiler, 'in', '-o', 'out'])
        self.assertEqual(self.compiler('in', 'out', ['flags']),
                         [self.compiler, 'flags', 'in', '-o', 'out'])

    def test_default_name(self):
        src = ResourceFile(Path('file.ui', Root.srcdir), 'qtui')
        self.assertEqual(self.compiler.default_name(src, None), 'ui_file.h')

    def test_output_file(self):
        self.assertEqual(self.compiler.output_file('ui_file.h', None),
                         HeaderFile(Path('ui_file.h'), 'c++'))

    def test_flags_empty(self):
        self.assertEqual(self.compiler.flags(opts.option_list()), [])

    def test_flags_string(self):
        self.assertEqual(self.compiler.flags(opts.option_list('-v')), ['-v'])

    def test_flags_invalid(self):
        with self.assertRaises(TypeError):
            self.compiler.flags(opts.option_list(123))
