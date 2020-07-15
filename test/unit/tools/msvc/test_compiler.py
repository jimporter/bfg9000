from unittest import mock

from ... import *
from .common import known_langs, mock_which

from bfg9000 import options as opts
from bfg9000.file_types import (HeaderDirectory, HeaderFile,
                                MsvcPrecompiledHeader, ObjectFile, SourceFile)
from bfg9000.iterutils import merge_dicts
from bfg9000.path import Path, Root
from bfg9000.tools.msvc import MsvcBuilder


class TestMsvcCompiler(CrossPlatformTestCase):
    def __init__(self, *args, **kwargs):
        super().__init__(clear_variables=True, *args, **kwargs)

    def setUp(self):
        with mock.patch('bfg9000.shell.which', mock_which):
            self.compiler = MsvcBuilder(self.env, known_langs['c++'], ['cl'],
                                        'version').compiler

    def test_call(self):
        extra = self.compiler._always_flags
        self.assertEqual(self.compiler('in', 'out'),
                         [self.compiler] + extra + ['/c', 'in', '/Foout'])
        self.assertEqual(
            self.compiler('in', 'out', flags=['flags']),
            [self.compiler] + extra + ['flags', '/c', 'in', '/Foout']
        )

        self.assertEqual(
            self.compiler('in', 'out', 'out.d'),
            [self.compiler] + extra + ['/showIncludes', '/c', 'in', '/Foout']
        )
        self.assertEqual(
            self.compiler('in', 'out', 'out.d', ['flags']),
            [self.compiler] + extra + ['flags', '/showIncludes', '/c', 'in',
                                       '/Foout']
        )

    def test_default_name(self):
        src = SourceFile(Path('file.cpp', Root.srcdir), 'c++')
        self.assertEqual(self.compiler.default_name(src, None), 'file')

    def test_output_file(self):
        fmt = self.env.target_platform.object_format
        self.assertEqual(self.compiler.output_file('file', None),
                         ObjectFile(Path('file.obj'), fmt, 'c++'))

    def test_flags_empty(self):
        self.assertEqual(self.compiler.flags(opts.option_list()), ['/MD'])

    def test_flags_include_dir(self):
        p = self.Path('/path/to/include')
        self.assertEqual(self.compiler.flags(opts.option_list(
            opts.include_dir(HeaderDirectory(p))
        )), ['/I' + p, '/MD'])
        self.assertEqual(self.compiler.flags(opts.option_list(
            opts.include_dir(HeaderDirectory(p))
        ), mode='pkg-config'), ['-I' + p])

    def test_flags_define(self):
        self.assertEqual(self.compiler.flags(opts.option_list(
            opts.define('NAME')
        )), ['/DNAME', '/MD'])
        self.assertEqual(self.compiler.flags(opts.option_list(
            opts.define('NAME')
        ), mode='pkg-config'), ['-DNAME'])

        self.assertEqual(self.compiler.flags(opts.option_list(
            opts.define('NAME', 'value')
        )), ['/DNAME=value', '/MD'])
        self.assertEqual(self.compiler.flags(opts.option_list(
            opts.define('NAME', 'value')
        ), mode='pkg-config'), ['-DNAME=value'])

    def test_flags_std(self):
        self.assertEqual(self.compiler.flags(opts.option_list(
            opts.std('c++14')
        )), ['/std:c++14', '/MD'])

    def test_flags_static(self):
        self.assertEqual(self.compiler.flags(opts.option_list(
            opts.static()
        )), ['/MT'])

        self.assertEqual(self.compiler.flags(
            opts.option_list(),
            opts.option_list(opts.static()),
        ), ['/MT'])

    def test_flags_debug(self):
        self.assertEqual(self.compiler.flags(opts.option_list(
            opts.debug()
        )), ['/Zi', '/MDd'])
        self.assertEqual(self.compiler.flags(opts.option_list(
            opts.debug(), opts.static()
        )), ['/Zi', '/MTd'])

        self.assertEqual(self.compiler.flags(
            opts.option_list(),
            opts.option_list(opts.debug()),
        ), ['/MDd'])
        self.assertEqual(self.compiler.flags(
            opts.option_list(opts.static()),
            opts.option_list(opts.debug()),
        ), ['/MTd'])

    def test_flags_warning(self):
        self.assertEqual(self.compiler.flags(opts.option_list(
            opts.warning('disable')
        )), ['/w', '/MD'])
        self.assertEqual(self.compiler.flags(opts.option_list(
            opts.warning('all')
        )), ['/W3', '/MD'])
        self.assertEqual(self.compiler.flags(opts.option_list(
            opts.warning('extra')
        )), ['/W4', '/MD'])
        self.assertEqual(self.compiler.flags(opts.option_list(
            opts.warning('error')
        )), ['/WX', '/MD'])

        self.assertEqual(self.compiler.flags(opts.option_list(
            opts.warning('all', 'extra', 'error')
        )), ['/W3', '/W4', '/WX', '/MD'])

        with self.assertRaises(ValueError):
            self.compiler.flags(opts.option_list(opts.warning('unknown')))

    def test_flags_optimize(self):
        self.assertEqual(self.compiler.flags(opts.option_list(
            opts.optimize('disable')
        )), ['/Od', '/MD'])
        self.assertEqual(self.compiler.flags(opts.option_list(
            opts.optimize('size')
        )), ['/O1', '/MD'])
        self.assertEqual(self.compiler.flags(opts.option_list(
            opts.optimize('speed')
        )), ['/O2', '/MD'])
        self.assertEqual(self.compiler.flags(opts.option_list(
            opts.optimize('linktime')
        )), ['/GL', '/MD'])

        self.assertEqual(self.compiler.flags(opts.option_list(
            opts.optimize('speed', 'linktime')
        )), ['/O2', '/GL', '/MD'])

    def test_flags_include_pch(self):
        p = self.Path('/path/to/header.hpp')
        self.assertEqual(self.compiler.flags(opts.option_list(opts.pch(
            MsvcPrecompiledHeader(p, p, 'header', 'native', 'c++')
        ))), ['/Yuheader', '/MD'])

    def test_flags_sanitize(self):
        self.assertEqual(self.compiler.flags(opts.option_list(
            opts.sanitize()
        )), ['/RTC1', '/MD'])

    def test_flags_string(self):
        self.assertEqual(self.compiler.flags(opts.option_list('-v')),
                         ['-v', '/MD'])

    def test_flags_invalid(self):
        with self.assertRaises(TypeError):
            self.compiler.flags(opts.option_list(123))

    def test_parse_flags(self):
        default = {
            'debug': None,
            'defines': [],
            'extra': [],
            'includes': [],
            'nologo': None,
            'pch': {'create': None, 'use': None},
            'runtime': None,
            'warnings': {'as_error': None, 'level': None}
        }

        def assertFlags(flags, extra={}):
            self.assertEqual(self.compiler.parse_flags(flags),
                             merge_dicts(default, extra))

        assertFlags([])
        assertFlags(['/un', 'known'], {'extra': ['/un', 'known']})
        assertFlags(['/nologo'], {'nologo': True})
        assertFlags(['/Dfoo'], {'defines': ['foo']})
        assertFlags(['/Idir'], {'includes': ['dir']})

        assertFlags(['/Z7'], {'debug': 'old'})
        assertFlags(['/Zi'], {'debug': 'pdb'})
        assertFlags(['/ZI'], {'debug': 'edit'})

        assertFlags(['/W0'], {'warnings': {'level': '0'}})
        assertFlags(['/Wall'], {'warnings': {'level': 'all'}})
        assertFlags(['/WX'], {'warnings': {'as_error': True}})
        assertFlags(['/WX-'], {'warnings': {'as_error': False}})
        assertFlags(['/w'], {'warnings': {'level': '0'}})

        assertFlags(['/Yufoo'], {'pch': {'use': 'foo'}})
        assertFlags(['/Ycfoo'], {'pch': {'create': 'foo'}})


class TestMsvcPchCompiler(TestMsvcCompiler):
    def setUp(self):
        with mock.patch('bfg9000.shell.which', mock_which):
            self.compiler = MsvcBuilder(self.env, known_langs['c++'], ['cl'],
                                        'version').pch_compiler

    def test_call(self):
        extra = self.compiler._always_flags
        self.assertEqual(self.compiler('in', ['out_pch', 'out']),
                         [self.compiler] + extra + ['/c', 'in', '/Foout',
                                                    '/Fpout_pch'])
        self.assertEqual(
            self.compiler('in', ['out_pch', 'out'], flags=['flags']),
            [self.compiler] + extra + ['flags', '/c', 'in', '/Foout',
                                       '/Fpout_pch']
        )

        self.assertEqual(
            self.compiler('in', ['out_pch', 'out'], 'out.d'),
            [self.compiler] + extra + ['/showIncludes', '/c', 'in', '/Foout',
                                       '/Fpout_pch']
        )
        self.assertEqual(
            self.compiler('in', ['out_pch', 'out'], 'out.d', ['flags']),
            [self.compiler] + extra + ['flags', '/showIncludes', '/c', 'in',
                                       '/Foout', '/Fpout_pch']
        )

    def test_default_name(self):
        hdr = HeaderFile(Path('file.hpp', Root.srcdir), 'c++')
        self.assertEqual(self.compiler.default_name(hdr, None), 'file.hpp')

    def test_output_file(self):
        fmt = self.env.target_platform.object_format
        out = MsvcPrecompiledHeader(
            Path('hdr.pch'), Path('src.obj'), 'hdr.h', fmt, 'c++'
        )
        self.assertEqual(self.compiler.output_file('hdr.h', AttrDict(
            pch_source=SourceFile(Path('src.c'), 'c')
        )), [out, out.object_file])
