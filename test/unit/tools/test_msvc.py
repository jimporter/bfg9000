import mock
import unittest

from ... import make_env

from bfg9000 import file_types, options as opts
from bfg9000.languages import Languages
from bfg9000.packages import Framework
from bfg9000.path import Path
from bfg9000.tools.msvc import MsvcBuilder
from bfg9000.versioning import Version

known_langs = Languages()
with known_langs.make('c++') as x:
    x.vars(compiler='CXX', cflags='CXXFLAGS')


def mock_which(*args, **kwargs):
    return ['command']


class TestMsvcBuilder(unittest.TestCase):
    def setUp(self):
        self.env = make_env()

    def test_properties(self):
        with mock.patch('bfg9000.shell.which', mock_which):
            cc = MsvcBuilder(self.env, known_langs['c++'], ['cl'], 'version')

        self.assertEqual(cc.flavor, 'msvc')
        self.assertEqual(cc.compiler.flavor, 'msvc')
        self.assertEqual(cc.pch_compiler.flavor, 'msvc')
        self.assertEqual(cc.linker('executable').flavor, 'msvc')
        self.assertEqual(cc.linker('shared_library').flavor, 'msvc')
        self.assertEqual(cc.linker('static_library').flavor, 'msvc')

        self.assertEqual(cc.family, 'native')
        self.assertEqual(cc.auto_link, True)
        self.assertEqual(cc.can_dual_link, False)

        self.assertEqual(cc.compiler.num_outputs, 1)
        self.assertEqual(cc.pch_compiler.num_outputs, 2)
        self.assertEqual(cc.linker('executable').num_outputs, 1)
        self.assertEqual(cc.linker('shared_library').num_outputs, 2)

        self.assertEqual(cc.compiler.deps_flavor, 'msvc')
        self.assertEqual(cc.pch_compiler.deps_flavor, 'msvc')

        self.assertEqual(cc.compiler.needs_libs, False)
        self.assertEqual(cc.pch_compiler.needs_libs, False)

        self.assertEqual(cc.compiler.accepts_pch, True)
        self.assertEqual(cc.pch_compiler.accepts_pch, False)

        self.assertRaises(KeyError, lambda: cc.linker('unknown'))

    def test_msvc(self):
        version = ('Microsoft (R) C/C++ Optimizing Compiler Version ' +
                   '19.12.25831 for x86')

        with mock.patch('bfg9000.shell.which', mock_which):
            cc = MsvcBuilder(self.env, known_langs['c++'], ['cl'], version)

        self.assertEqual(cc.brand, 'msvc')
        self.assertEqual(cc.compiler.brand, 'msvc')
        self.assertEqual(cc.pch_compiler.brand, 'msvc')
        self.assertEqual(cc.linker('executable').brand, 'msvc')
        self.assertEqual(cc.linker('shared_library').brand, 'msvc')

        self.assertEqual(cc.version, Version('19.12.25831'))
        self.assertEqual(cc.compiler.version, Version('19.12.25831'))
        self.assertEqual(cc.pch_compiler.version, Version('19.12.25831'))
        self.assertEqual(cc.linker('executable').version,
                         Version('19.12.25831'))
        self.assertEqual(cc.linker('shared_library').version,
                         Version('19.12.25831'))

    def test_unknown_brand(self):
        version = 'unknown'

        with mock.patch('bfg9000.shell.which', mock_which):
            cc = MsvcBuilder(self.env, known_langs['c++'], ['c++'], version)

        self.assertEqual(cc.brand, 'unknown')
        self.assertEqual(cc.compiler.brand, 'unknown')
        self.assertEqual(cc.pch_compiler.brand, 'unknown')
        self.assertEqual(cc.linker('executable').brand, 'unknown')
        self.assertEqual(cc.linker('shared_library').brand, 'unknown')

        self.assertEqual(cc.version, None)
        self.assertEqual(cc.compiler.version, None)
        self.assertEqual(cc.pch_compiler.version, None)
        self.assertEqual(cc.linker('executable').version, None)
        self.assertEqual(cc.linker('shared_library').version, None)


class TestMsvcCompiler(unittest.TestCase):
    def setUp(self):
        self.env = make_env()
        with mock.patch('bfg9000.shell.which', mock_which):
            self.compiler = MsvcBuilder(self.env, known_langs['c++'], ['cl'],
                                        'version').compiler

    def test_flags_empty(self):
        self.assertEqual(self.compiler.flags(opts.option_list()), [])

    def test_flags_include_dir(self):
        p = Path('/path/to/include')
        self.assertEqual(self.compiler.flags(opts.option_list(
            opts.include_dir(file_types.HeaderDirectory(p))
        )), ['/I' + p])
        self.assertEqual(self.compiler.flags(opts.option_list(
            opts.include_dir(file_types.HeaderDirectory(p))
        ), mode='pkg-config'), ['-I' + p])

    def test_flags_define(self):
        self.assertEqual(self.compiler.flags(opts.option_list(
            opts.define('NAME')
        )), ['/DNAME'])
        self.assertEqual(self.compiler.flags(opts.option_list(
            opts.define('NAME')
        ), mode='pkg-config'), ['-DNAME'])

        self.assertEqual(self.compiler.flags(opts.option_list(
            opts.define('NAME', 'value')
        )), ['/DNAME=value'])
        self.assertEqual(self.compiler.flags(opts.option_list(
            opts.define('NAME', 'value')
        ), mode='pkg-config'), ['-DNAME=value'])

    def test_flags_std(self):
        self.assertEqual(self.compiler.flags(opts.option_list(
            opts.std('c++14')
        )), ['/std:c++14'])

    def test_flags_debug(self):
        self.assertEqual(self.compiler.flags(opts.option_list(
            opts.debug()
        )), ['/Zi'])

    def test_flags_warning(self):
        self.assertEqual(self.compiler.flags(opts.option_list(
            opts.warning('disable')
        )), ['/w'])
        self.assertEqual(self.compiler.flags(opts.option_list(
            opts.warning('all')
        )), ['/W3'])
        self.assertEqual(self.compiler.flags(opts.option_list(
            opts.warning('extra')
        )), ['/W4'])
        self.assertEqual(self.compiler.flags(opts.option_list(
            opts.warning('error')
        )), ['/WX'])

        self.assertEqual(self.compiler.flags(opts.option_list(
            opts.warning('all', 'extra', 'error')
        )), ['/W3', '/W4', '/WX'])

        with self.assertRaises(ValueError):
            self.compiler.flags(opts.option_list(opts.warning('unknown')))

    def test_flags_optimize(self):
        self.assertEqual(self.compiler.flags(opts.option_list(
            opts.optimize('disable')
        )), ['/Od'])
        self.assertEqual(self.compiler.flags(opts.option_list(
            opts.optimize('size')
        )), ['/O1'])
        self.assertEqual(self.compiler.flags(opts.option_list(
            opts.optimize('speed')
        )), ['/O2'])
        self.assertEqual(self.compiler.flags(opts.option_list(
            opts.optimize('linktime')
        )), ['/GL'])

        self.assertEqual(self.compiler.flags(opts.option_list(
            opts.optimize('speed', 'linktime')
        )), ['/O2', '/GL'])

    def test_flags_include_pch(self):
        p = Path('/path/to/header.hpp')
        self.assertEqual(self.compiler.flags(opts.option_list(
            opts.pch(file_types.MsvcPrecompiledHeader(p, None, 'header',
                                                      'native'))
        )), ['/Yuheader'])

    def test_flags_string(self):
        self.assertEqual(self.compiler.flags(opts.option_list('-v')), ['-v'])

    def test_flags_invalid(self):
        with self.assertRaises(TypeError):
            self.compiler.flags(opts.option_list(123))


class TestMsvcLinker(unittest.TestCase):
    def setUp(self):
        self.env = make_env()

        version = ('Microsoft (R) C/C++ Optimizing Compiler Version ' +
                   '19.12.25831 for x86')
        with mock.patch('bfg9000.shell.which', mock_which):
            self.linker = MsvcBuilder(self.env, known_langs['c++'], ['cl'],
                                      version).linker('executable')

    def test_flags_empty(self):
        self.assertEqual(self.linker.flags(opts.option_list()), [])

    def test_flags_lib_dir(self):
        libdir = Path('/path/to/lib')
        lib = Path('/path/to/lib/foo.so')

        # Lib dir
        self.assertEqual(self.linker.flags(opts.option_list(
            opts.lib_dir(file_types.Directory(libdir))
        )), ['/LIBPATH:' + libdir])
        self.assertEqual(self.linker.flags(opts.option_list(
            opts.lib_dir(file_types.Directory(libdir))
        ), mode='pkg-config'), ['-L' + libdir])

        # Shared library
        self.assertEqual(self.linker.flags(opts.option_list(
            opts.lib(file_types.SharedLibrary(lib, 'native'))
        )), ['/LIBPATH:' + libdir])

        # Static library
        self.assertEqual(self.linker.flags(opts.option_list(
            opts.lib(file_types.StaticLibrary(lib, 'native'))
        )), ['/LIBPATH:' + libdir])

        # Mixed
        self.assertEqual(self.linker.flags(opts.option_list(
            opts.lib_dir(file_types.Directory(libdir)),
            opts.lib(file_types.SharedLibrary(lib, 'native'))
        )), ['/LIBPATH:' + libdir])

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
        lib = Path('/path/to/lib/foo.lib')

        self.assertEqual(self.linker.lib_flags(opts.option_list(
            opts.lib(file_types.SharedLibrary(lib, 'native'))
        )), [lib.basename()])
        self.assertEqual(self.linker.lib_flags(opts.option_list(
            opts.lib(file_types.SharedLibrary(lib, 'native'))
        ), mode='pkg-config'), ['-lfoo'])

        self.assertEqual(self.linker.lib_flags(opts.option_list(
            opts.lib(file_types.WholeArchive(
                file_types.SharedLibrary(lib, 'native'))
            )
        )), ['/WHOLEARCHIVE:' + lib.basename()])

        version = ('Microsoft (R) C/C++ Optimizing Compiler Version ' +
                   '18.00.25831 for x86')
        with mock.patch('bfg9000.shell.which', mock_which):
            linker = MsvcBuilder(self.env, known_langs['c++'], ['cl'],
                                 version).linker('executable')
        with self.assertRaises(TypeError):
            linker.lib_flags(opts.option_list(
                opts.lib(file_types.WholeArchive(
                    file_types.StaticLibrary(lib, 'native')
                ))
            ))

        with self.assertRaises(TypeError):
            self.linker.lib_flags(opts.option_list(
                opts.lib(Framework('cocoa'))
            ))

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

    def test_lib_flags_lib_literal(self):
        self.assertEqual(self.linker.lib_flags(opts.option_list(
            opts.lib_literal('/?')
        )), ['/?'])

    def test_lib_flags_ignored(self):
        self.assertEqual(self.linker.lib_flags(opts.option_list('-Lfoo')), [])


class TestMsvcStaticLinker(unittest.TestCase):
    def setUp(self):
        self.env = make_env()
        with mock.patch('bfg9000.shell.which', mock_which):
            self.linker = MsvcBuilder(self.env, known_langs['c++'], ['cl'],
                                      'version').linker('static_library')

    def test_flags_empty(self):
        self.assertEqual(self.linker.flags(opts.option_list()), [])

    def test_flags_string(self):
        self.assertEqual(self.linker.flags(opts.option_list('-v')), ['-v'])

    def test_flags_invalid(self):
        with self.assertRaises(TypeError):
            self.linker.flags(opts.option_list(123))
