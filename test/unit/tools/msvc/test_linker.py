from unittest import mock

from ... import *
from .common import known_langs, mock_which

from bfg9000 import options as opts
from bfg9000.file_types import *
from bfg9000.iterutils import merge_dicts
from bfg9000.path import Path
from bfg9000.tools.msvc import MsvcBuilder


class TestMsvcLinker(CrossPlatformTestCase):
    def __init__(self, *args, **kwargs):
        super().__init__(clear_variables=True, *args, **kwargs)

    def _get_linker(self, lang):
        version = ('Microsoft (R) C/C++ Optimizing Compiler Version ' +
                   '19.12.25831 for x86')
        with mock.patch('bfg9000.shell.which', mock_which):
            return MsvcBuilder(self.env, known_langs[lang], ['cl'], True,
                               version).linker('executable')

    def setUp(self):
        self.linker = self._get_linker('c++')

    def test_call(self):
        extra = self.linker._always_flags
        self.assertEqual(self.linker(['in'], 'out'),
                         [self.linker] + extra + ['in', '/OUT:out'])
        self.assertEqual(self.linker(['in'], 'out', flags=['flags']),
                         [self.linker] + extra + ['flags', 'in', '/OUT:out'])

        self.assertEqual(self.linker(['in'], 'out', ['lib']),
                         [self.linker] + extra + ['in', 'lib', '/OUT:out'])
        self.assertEqual(
            self.linker(['in'], 'out', ['lib'], ['flags']),
            [self.linker] + extra + ['flags', 'in', 'lib', '/OUT:out']
        )

    def test_output_file(self):
        fmt = self.env.target_platform.object_format
        ext = self.env.target_platform.executable_ext
        self.assertEqual(self.linker.output_file('prog', None),
                         Executable(Path('prog' + ext), fmt, 'c++'))

    def test_can_link(self):
        fmt = self.env.target_platform.object_format
        self.assertTrue(self.linker.can_link(fmt, ['c', 'c++']))
        self.assertTrue(self.linker.can_link(fmt, ['goofy']))
        self.assertFalse(self.linker.can_link('goofy', ['c']))

        c_linker = self._get_linker('c')
        self.assertFalse(c_linker.can_link(fmt, ['c++']))

    def test_flags_empty(self):
        self.assertEqual(self.linker.flags(opts.option_list()), [])

    def test_flags_lib_dir(self):
        libdir = self.Path('/path/to/lib')
        lib = self.Path('/path/to/lib/foo.so')

        # Lib dir
        self.assertEqual(self.linker.flags(opts.option_list(
            opts.lib_dir(Directory(libdir))
        )), ['/LIBPATH:' + libdir])
        self.assertEqual(self.linker.flags(opts.option_list(
            opts.lib_dir(Directory(libdir))
        ), mode='pkg-config'), ['-L' + libdir])

        # Shared library
        self.assertEqual(self.linker.flags(opts.option_list(
            opts.lib(SharedLibrary(lib, 'native'))
        )), [])

        # Static library
        self.assertEqual(self.linker.flags(opts.option_list(
            opts.lib(StaticLibrary(lib, 'native'))
        )), [])

        # Mixed
        self.assertEqual(self.linker.flags(opts.option_list(
            opts.lib_dir(Directory(libdir)),
            opts.lib(SharedLibrary(lib, 'native'))
        )), ['/LIBPATH:' + libdir])

    def test_flags_module_def(self):
        path = self.Path('/path/to/module.def')
        self.assertEqual(
            self.linker.flags(opts.option_list(
                opts.module_def(ModuleDefFile(path))
            )), ['/DEF:' + path]
        )

    def test_flags_static(self):
        self.assertEqual(self.linker.flags(opts.option_list(
            opts.static()
        )), [])

    def test_flags_debug(self):
        self.assertEqual(self.linker.flags(opts.option_list(
            opts.debug()
        )), ['/DEBUG'])

    def test_flags_optimize(self):
        self.assertEqual(self.linker.flags(opts.option_list(
            opts.optimize('disable')
        )), [])
        self.assertEqual(self.linker.flags(opts.option_list(
            opts.optimize('size')
        )), [])
        self.assertEqual(self.linker.flags(opts.option_list(
            opts.optimize('speed')
        )), [])
        self.assertEqual(self.linker.flags(opts.option_list(
            opts.optimize('linktime')
        )), ['/LTCG'])

        self.assertEqual(self.linker.flags(opts.option_list(
            opts.optimize('speed', 'linktime')
        )), ['/LTCG'])

    def test_flags_entry_point(self):
        self.assertEqual(self.linker.flags(opts.option_list(
            opts.entry_point('symbol')
        )), ['/ENTRY:symbol'])

    def test_flags_gui(self):
        self.assertEqual(self.linker.flags(opts.option_list(opts.gui())),
                         ['/SUBSYSTEM:WINDOWS'])
        self.assertEqual(self.linker.flags(opts.option_list(opts.gui(False))),
                         ['/SUBSYSTEM:WINDOWS'])
        self.assertEqual(self.linker.flags(opts.option_list(opts.gui(True))),
                         ['/SUBSYSTEM:WINDOWS', '/ENTRY:mainCRTStartup'])

        self.assertEqual(self.linker.flags(opts.option_list(
            opts.entry_point('symbol'), opts.gui(True)
        )), ['/ENTRY:symbol', '/SUBSYSTEM:WINDOWS'])
        self.assertEqual(self.linker.flags(opts.option_list(
            opts.gui(True), opts.entry_point('symbol')
        )), ['/SUBSYSTEM:WINDOWS', '/ENTRY:symbol'])

    def test_flags_string(self):
        self.assertEqual(self.linker.flags(opts.option_list('-v')), ['-v'])

    def test_flags_lib_literal(self):
        self.assertEqual(self.linker.flags(opts.option_list(
            opts.lib_literal('-lfoo')
        )), [])

    def test_flags_invalid(self):
        with self.assertRaises(TypeError):
            self.linker.flags(opts.option_list(123))

    def test_lib_flags_empty(self):
        self.assertEqual(self.linker.lib_flags(opts.option_list()), [])

    def test_lib_flags_lib(self):
        lib = self.Path('/path/to/lib/foo.lib')

        self.assertEqual(self.linker.lib_flags(opts.option_list(
            opts.lib(SharedLibrary(lib, 'native'))
        )), [lib])
        self.assertEqual(self.linker.lib_flags(opts.option_list(
            opts.lib(SharedLibrary(lib, 'native'))
        ), mode='pkg-config'), ['-lfoo'])

        self.assertEqual(self.linker.lib_flags(opts.option_list(
            opts.lib(WholeArchive(
                SharedLibrary(lib, 'native'))
            )
        )), ['/WHOLEARCHIVE:' + lib])

        version = ('Microsoft (R) C/C++ Optimizing Compiler Version ' +
                   '18.00.25831 for x86')
        with mock.patch('bfg9000.shell.which', mock_which):
            linker = MsvcBuilder(self.env, known_langs['c++'], ['cl'], True,
                                 version).linker('executable')
        with self.assertRaises(TypeError):
            linker.lib_flags(opts.option_list(
                opts.lib(WholeArchive(
                    StaticLibrary(lib, 'native')
                ))
            ))

        with self.assertRaises(TypeError):
            self.linker.lib_flags(opts.option_list(
                opts.framework('cocoa')
            ))

    def test_lib_flags_lib_literal(self):
        self.assertEqual(self.linker.lib_flags(opts.option_list(
            opts.lib_literal('/?')
        )), ['/?'])

    def test_lib_flags_ignored(self):
        self.assertEqual(self.linker.lib_flags(opts.option_list('-Lfoo')), [])

    def test_parse_flags(self):
        default = {
            'nologo': None,
            'debug': None,
            'libdirs': [],
            'libs': [],
            'extra': [],
        }

        def assertFlags(flags, libflags, extra={}):
            self.assertEqual(self.linker.parse_flags(flags, libflags),
                             merge_dicts(default, extra))

        assertFlags([], [])
        assertFlags(['/foo', 'bar'], ['/baz', 'quux'],
                    {'libs': ['quux'], 'extra': ['/foo', 'bar', '/baz']})
        assertFlags(['/nologo'], [], {'nologo': True})
        assertFlags([], ['/nologo'], {'nologo': True})
        assertFlags(['/nologo'], ['/nologo'], {'nologo': True})
        assertFlags(['/DEBUG'], [], {'debug': True})
        assertFlags(['/debug'], [], {'debug': True})
        assertFlags(['/libpath:foo', '/LIBPATH:bar'], [],
                    {'libdirs': ['foo', 'bar']})


class TestMsvcSharedLinker(TestMsvcLinker):
    def _get_linker(self, lang):
        version = ('Microsoft (R) C/C++ Optimizing Compiler Version ' +
                   '19.12.25831 for x86')
        with mock.patch('bfg9000.shell.which', mock_which):
            return MsvcBuilder(self.env, known_langs[lang], ['cl'], True,
                               version).linker('shared_library')

    def test_call(self):
        extra = self.linker._always_flags
        self.assertEqual(
            self.linker(['in'], ['out', 'imp']),
            [self.linker] + extra + ['in', '/OUT:out', '/IMPLIB:imp']
        )
        self.assertEqual(
            self.linker(['in'], ['out', 'imp'], flags=['flags']),
            [self.linker] + extra + ['flags', 'in', '/OUT:out', '/IMPLIB:imp']
        )

        self.assertEqual(
            self.linker(['in'], ['out', 'imp'], ['lib']),
            [self.linker] + extra + ['in', 'lib', '/OUT:out', '/IMPLIB:imp']
        )
        self.assertEqual(
            self.linker(['in'], ['out', 'imp'], ['lib'], ['flags']),
            [self.linker] + extra + ['flags', 'in', 'lib', '/OUT:out',
                                     '/IMPLIB:imp']
        )

    def test_output_file(self):
        fmt = self.env.target_platform.object_format
        ext = self.env.target_platform.shared_library_ext
        out = DllBinary(Path('lib' + ext), fmt, 'c++', Path('lib.lib'),
                        Path('lib.exp'))
        self.assertEqual(self.linker.output_file('lib', None),
                         [out, out.import_lib, out.export_file])


class TestMsvcStaticLinker(CrossPlatformTestCase):
    def __init__(self, *args, **kwargs):
        super().__init__(clear_variables=True, *args, **kwargs)

    def setUp(self):
        with mock.patch('bfg9000.shell.which', mock_which):
            self.linker = MsvcBuilder(self.env, known_langs['c++'], ['cl'],
                                      True, 'version').linker('static_library')

    def test_call(self):
        self.assertEqual(self.linker(['in'], 'out'),
                         [self.linker, 'in', '/OUT:out'])
        self.assertEqual(self.linker(['in'], 'out', flags=['flags']),
                         [self.linker, 'flags', 'in', '/OUT:out'])

    def test_output_file(self):
        fmt = self.env.target_platform.object_format
        self.assertEqual(
            self.linker.output_file('lib', AttrDict(input_langs=['c++'])),
            StaticLibrary(Path('lib.lib'), fmt, ['c++'])
        )

    def test_can_link(self):
        fmt = self.env.target_platform.object_format
        self.assertTrue(self.linker.can_link(fmt, ['c', 'c++']))
        self.assertTrue(self.linker.can_link(fmt, ['goofy']))
        self.assertFalse(self.linker.can_link('goofy', ['c']))

    def test_flags_empty(self):
        self.assertEqual(self.linker.flags(opts.option_list()), [])

    def test_flags_string(self):
        self.assertEqual(self.linker.flags(opts.option_list('-v')), ['-v'])

    def test_flags_invalid(self):
        with self.assertRaises(TypeError):
            self.linker.flags(opts.option_list(123))

    def test_parse_flags(self):
        self.assertEqual(self.linker.parse_flags([]), {'extra': []})
        self.assertEqual(self.linker.parse_flags(['/foo', 'bar']),
                         {'extra': ['/foo', 'bar']})
