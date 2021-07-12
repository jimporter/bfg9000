from unittest import mock

from ... import *
from .common import mock_which

from bfg9000 import options as opts
from bfg9000.file_types import HeaderDirectory, ObjectFile, SourceFile
from bfg9000.languages import Languages
from bfg9000.path import Path, Root
from bfg9000.tools.cc.rc import CcRcBuilder
from bfg9000.versioning import Version

known_langs = Languages()
with known_langs.make('rc') as x:
    x.vars(compiler='RC', flags='RCFLAGS')


class TestCcRcBuilder(CrossPlatformTestCase):
    def __init__(self, *args, **kwargs):
        super().__init__(clear_variables=True, *args, **kwargs)

    def test_properties(self):
        with mock.patch('bfg9000.shell.which', mock_which):
            rc = CcRcBuilder(self.env, known_langs['rc'], ['windres'], True,
                             'version')

        self.assertEqual(rc.flavor, 'cc')
        self.assertEqual(rc.compiler.flavor, 'cc')
        self.assertEqual(rc.linker('executable'), None)

        self.assertEqual(rc.compiler.num_outputs, 'all')
        self.assertEqual(rc.compiler.deps_flavor, None)
        self.assertEqual(rc.compiler.needs_libs, False)
        self.assertEqual(rc.compiler.needs_package_options, False)

    def test_gcc(self):
        version = ('GNU windres (GNU Binutils) 2.30\n' +
                   'Copyright (C) 2018 Free Software Foundation, Inc.')

        with mock.patch('bfg9000.shell.which', mock_which):
            rc = CcRcBuilder(self.env, known_langs['rc'], ['windres'], True,
                             version)

        self.assertEqual(rc.brand, 'gcc')
        self.assertEqual(rc.compiler.brand, 'gcc')
        self.assertEqual(rc.version, Version('2.30'))
        self.assertEqual(rc.compiler.version, Version('2.30'))

    def test_unknown_brand(self):
        version = 'unknown'

        with mock.patch('bfg9000.shell.which', mock_which):
            rc = CcRcBuilder(self.env, known_langs['rc'], ['windres'], True,
                             version)

        self.assertEqual(rc.brand, 'unknown')
        self.assertEqual(rc.compiler.brand, 'unknown')
        self.assertEqual(rc.version, None)
        self.assertEqual(rc.compiler.version, None)


class TestCcRcCompiler(CrossPlatformTestCase):
    def __init__(self, *args, **kwargs):
        super().__init__(clear_variables=True, *args, **kwargs)

    def setUp(self):
        self.compiler = CcRcBuilder(self.env, known_langs['rc'], ['windres'],
                                    True, 'version').compiler

    def test_call(self):
        self.assertEqual(self.compiler('in', 'out'),
                         [self.compiler, 'in', '-o', 'out'])
        self.assertEqual(self.compiler('in', 'out', ['flags']),
                         [self.compiler, 'flags', 'in', '-o', 'out'])

    def test_default_name(self):
        src = SourceFile(Path('file.rc', Root.srcdir), 'rc')
        self.assertEqual(self.compiler.default_name(src, None), 'file')

    def test_output_file(self):
        self.assertEqual(self.compiler.output_file('file', None),
                         ObjectFile(Path('file.o'), 'rc'))

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

    def test_flags_string(self):
        self.assertEqual(self.compiler.flags(opts.option_list('-i')), ['-i'])

    def test_flags_invalid(self):
        with self.assertRaises(TypeError):
            self.compiler.flags(opts.option_list(123))
