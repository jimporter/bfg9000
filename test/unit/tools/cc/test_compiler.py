from unittest import mock

from ... import *
from .common import known_langs, mock_execute, mock_which

from bfg9000 import options as opts
from bfg9000.file_types import (HeaderDirectory, HeaderFile, ObjectFile,
                                PrecompiledHeader, SourceFile)
from bfg9000.tools.cc import CcBuilder
from bfg9000.path import Path, Root


class TestCcCompiler(CrossPlatformTestCase):
    def __init__(self, *args, **kwargs):
        super().__init__(clear_variables=True, *args, **kwargs)

    def setUp(self):
        with mock.patch('bfg9000.shell.which', mock_which), \
             mock.patch('bfg9000.shell.execute', mock_execute):  # noqa
            self.compiler = CcBuilder(self.env, known_langs['c++'], ['c++'],
                                      'version').compiler

    def test_call(self):
        extra = self.compiler._always_flags
        self.assertEqual(self.compiler('in', 'out'),
                         [self.compiler] + extra + ['-c', 'in', '-o', 'out'])
        self.assertEqual(
            self.compiler('in', 'out', flags=['flags']),
            [self.compiler] + extra + ['flags', '-c', 'in', '-o', 'out']
        )

        self.assertEqual(
            self.compiler('in', 'out', 'out.d'),
            [self.compiler] + extra + ['-c', 'in', '-MMD', '-MF', 'out.d',
                                       '-o', 'out']
        )
        self.assertEqual(
            self.compiler('in', 'out', 'out.d', ['flags']),
            [self.compiler] + extra + ['flags', '-c', 'in', '-MMD', '-MF',
                                       'out.d', '-o', 'out']
        )

    def test_default_name(self):
        src = SourceFile(Path('file.cpp', Root.srcdir), 'c++')
        self.assertEqual(self.compiler.default_name(src, None), 'file')

    def test_output_file(self):
        fmt = self.env.target_platform.object_format
        self.assertEqual(self.compiler.output_file('file', None),
                         ObjectFile(Path('file.o'), fmt, 'c++'))

    def test_flags_empty(self):
        self.assertEqual(self.compiler.flags(opts.option_list()), [])

    def test_flags_include_dir(self):
        p = self.Path('/path/to/include')
        self.assertEqual(self.compiler.flags(opts.option_list(
            opts.include_dir(HeaderDirectory(p))
        )), ['-I' + p])

        self.assertEqual(self.compiler.flags(opts.option_list(
            opts.include_dir(HeaderDirectory(p, system=True))
        )), ['-isystem', p])

        if self.env.target_platform.genus == 'linux':
            p = self.Path('/usr/include')
            self.assertEqual(self.compiler.flags(opts.option_list(
                opts.include_dir(HeaderDirectory(p, system=True))
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
        )), ['-w'])
        self.assertEqual(self.compiler.flags(opts.option_list(
            opts.warning('all')
        )), ['-Wall'])
        self.assertEqual(self.compiler.flags(opts.option_list(
            opts.warning('extra')
        )), ['-Wextra'])
        self.assertEqual(self.compiler.flags(opts.option_list(
            opts.warning('error')
        )), ['-Werror'])

        self.assertEqual(self.compiler.flags(opts.option_list(
            opts.warning('all', 'extra', 'error')
        )), ['-Wall', '-Wextra', '-Werror'])

        with self.assertRaises(ValueError):
            self.compiler.flags(opts.option_list(opts.warning('unknown')))

    def test_flags_std(self):
        self.assertEqual(self.compiler.flags(opts.option_list(
            opts.std('c++14')
        )), ['-std=c++14'])

    def test_flags_debug(self):
        self.assertEqual(self.compiler.flags(opts.option_list(
            opts.debug()
        )), ['-g'])

    def test_flags_static(self):
        self.assertEqual(self.compiler.flags(opts.option_list(
            opts.static()
        )), [])

    def test_flags_optimize(self):
        self.assertEqual(self.compiler.flags(opts.option_list(
            opts.optimize('disable')
        )), ['-O0'])
        self.assertEqual(self.compiler.flags(opts.option_list(
            opts.optimize('size')
        )), ['-Osize'])
        self.assertEqual(self.compiler.flags(opts.option_list(
            opts.optimize('speed')
        )), ['-O3'])
        self.assertEqual(self.compiler.flags(opts.option_list(
            opts.optimize('linktime')
        )), ['-flto'])

        self.assertEqual(self.compiler.flags(opts.option_list(
            opts.optimize('speed', 'linktime')
        )), ['-O3', '-flto'])

    def test_flags_pthread(self):
        self.assertEqual(self.compiler.flags(opts.option_list(
            opts.pthread()
        )), ['-pthread'])

    def test_flags_pic(self):
        self.assertEqual(self.compiler.flags(opts.option_list(
            opts.pic()
        )), ['-fPIC'])

    def test_flags_include_pch(self):
        p = self.Path('/path/to/header.hpp')
        self.assertEqual(self.compiler.flags(opts.option_list(
            opts.pch(PrecompiledHeader(p, 'c++'))
        )), ['-include', p.stripext()])

    def test_flags_sanitize(self):
        self.assertEqual(self.compiler.flags(opts.option_list(
            opts.sanitize()
        )), ['-fsanitize=address'])

    def test_flags_string(self):
        self.assertEqual(self.compiler.flags(opts.option_list('-v')), ['-v'])

    def test_flags_invalid(self):
        with self.assertRaises(TypeError):
            self.compiler.flags(opts.option_list(123))


class TestCcPchCompiler(TestCcCompiler):
    def setUp(self):
        with mock.patch('bfg9000.shell.which', mock_which), \
             mock.patch('bfg9000.shell.execute', mock_execute):  # noqa
            self.compiler = CcBuilder(self.env, known_langs['c++'], ['c++'],
                                      'version').pch_compiler

    def test_default_name(self):
        hdr = HeaderFile(Path('file.hpp', Root.srcdir), 'c++')
        self.assertEqual(self.compiler.default_name(hdr, None), 'file.hpp')

    def test_output_file(self):
        ext = '.gch' if self.compiler.brand == 'gcc' else '.pch'
        self.assertEqual(self.compiler.output_file('file.h', None),
                         PrecompiledHeader(Path('file.h' + ext), 'c++'))
