import mock
import unittest

from ... import make_env

from bfg9000 import file_types, options as opts
from bfg9000.languages import Languages
from bfg9000.packages import Framework
from bfg9000.path import Path
from bfg9000.safe_str import jbos
from bfg9000.tools.cc import CcBuilder
from bfg9000.versioning import Version

known_langs = Languages()
with known_langs.make('c++') as x:
    x.vars(compiler='CXX', cflags='CXXFLAGS')
with known_langs.make('java') as x:
    x.vars(compiler='JAVAC', cflags='JAVAFLAGS')


def mock_which(*args, **kwargs):
    return ['command']


def mock_execute(args, **kwargs):
    if args[-1] == '-Wl,--version':
        return '', '/usr/bin/ld --version\n'
    elif args[-1] == '-print-search-dirs':
        return 'libraries: =/lib/search/dir1:/lib/search/dir2\n'
    elif args[-1] == '-print-sysroot':
        return '/'
    elif args[-1] == '--verbose':
        return 'SEARCH_DIR("/usr")\n'


class TestCcBuilder(unittest.TestCase):
    def setUp(self):
        self.env = make_env()

    def test_properties(self):
        with mock.patch('bfg9000.shell.which', mock_which), \
             mock.patch('bfg9000.shell.execute', mock_execute):  # noqa
            cc = CcBuilder(self.env, known_langs['c++'], ['c++'], 'version')

        self.assertEqual(cc.flavor, 'cc')
        self.assertEqual(cc.compiler.flavor, 'cc')
        self.assertEqual(cc.pch_compiler.flavor, 'cc')
        self.assertEqual(cc.linker('executable').flavor, 'cc')
        self.assertEqual(cc.linker('shared_library').flavor, 'cc')
        self.assertEqual(cc.linker('raw').flavor, 'ld')

        self.assertEqual(cc.family, 'native')
        self.assertEqual(cc.auto_link, False)
        self.assertEqual(cc.can_dual_link, True)

        self.assertEqual(cc.compiler.num_outputs, 1)
        self.assertEqual(cc.pch_compiler.num_outputs, 1)
        self.assertEqual(cc.linker('executable').num_outputs, 1)

        num_outputs = 2 if self.env.target_platform.has_import_library else 1
        self.assertEqual(cc.linker('shared_library').num_outputs, num_outputs)

        self.assertEqual(cc.compiler.deps_flavor, 'gcc')
        self.assertEqual(cc.pch_compiler.deps_flavor, 'gcc')

        self.assertEqual(cc.compiler.needs_libs, False)
        self.assertEqual(cc.pch_compiler.needs_libs, False)

        self.assertEqual(cc.compiler.accepts_pch, True)
        self.assertEqual(cc.pch_compiler.accepts_pch, False)

        self.assertRaises(KeyError, lambda: cc.linker('unknown'))

    def test_gcc(self):
        version = ('g++ (Ubuntu 5.4.0-6ubuntu1~16.04.6) 5.4.0 20160609\n' +
                   'Copyright (C) 2015 Free Software Foundation, Inc.')

        with mock.patch('bfg9000.shell.which', mock_which), \
             mock.patch('bfg9000.shell.execute', mock_execute):  # noqa
            cc = CcBuilder(self.env, known_langs['c++'], ['g++'], version)

        self.assertEqual(cc.brand, 'gcc')
        self.assertEqual(cc.compiler.brand, 'gcc')
        self.assertEqual(cc.pch_compiler.brand, 'gcc')
        self.assertEqual(cc.linker('executable').brand, 'gcc')
        self.assertEqual(cc.linker('shared_library').brand, 'gcc')

        self.assertEqual(cc.version, Version('5.4.0'))
        self.assertEqual(cc.compiler.version, Version('5.4.0'))
        self.assertEqual(cc.pch_compiler.version, Version('5.4.0'))
        self.assertEqual(cc.linker('executable').version, Version('5.4.0'))
        self.assertEqual(cc.linker('shared_library').version, Version('5.4.0'))

    def test_clang(self):
        version = 'clang version 3.8.0-2ubuntu4 (tags/RELEASE_380/final)'

        with mock.patch('bfg9000.shell.which', mock_which), \
             mock.patch('bfg9000.shell.execute', mock_execute):  # noqa
            cc = CcBuilder(self.env, known_langs['c++'], ['clang++'], version)

        self.assertEqual(cc.brand, 'clang')
        self.assertEqual(cc.compiler.brand, 'clang')
        self.assertEqual(cc.pch_compiler.brand, 'clang')
        self.assertEqual(cc.linker('executable').brand, 'clang')
        self.assertEqual(cc.linker('shared_library').brand, 'clang')

        self.assertEqual(cc.version, Version('3.8.0'))
        self.assertEqual(cc.compiler.version, Version('3.8.0'))
        self.assertEqual(cc.pch_compiler.version, Version('3.8.0'))
        self.assertEqual(cc.linker('executable').version, Version('3.8.0'))
        self.assertEqual(cc.linker('shared_library').version, Version('3.8.0'))

    def test_unknown_brand(self):
        version = 'unknown'

        with mock.patch('bfg9000.shell.which', mock_which), \
             mock.patch('bfg9000.shell.execute', mock_execute):  # noqa
            cc = CcBuilder(self.env, known_langs['c++'], ['c++'], version)

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


class TestCcCompiler(unittest.TestCase):
    def setUp(self):
        self.env = make_env()
        with mock.patch('bfg9000.shell.which', mock_which), \
             mock.patch('bfg9000.shell.execute', mock_execute):  # noqa
            self.compiler = CcBuilder(self.env, known_langs['c++'], ['c++'],
                                      'version').compiler

    def test_flags_empty(self):
        self.assertEqual(self.compiler.flags(opts.option_list()), [])

    def test_flags_include_dir(self):
        p = Path('/path/to/include')
        self.assertEqual(self.compiler.flags(opts.option_list(
            opts.include_dir(file_types.HeaderDirectory(p))
        )), ['-I' + p])

        self.assertEqual(self.compiler.flags(opts.option_list(
            opts.include_dir(file_types.HeaderDirectory(p, system=True))
        )), ['-isystem', p])

        if self.env.target_platform.name == 'linux':
            p = Path('/usr/include')
            self.assertEqual(self.compiler.flags(opts.option_list(
                opts.include_dir(file_types.HeaderDirectory(p, system=True))
            )), ['-I' + p])

    def test_flags_define(self):
        self.assertEqual(self.compiler.flags(opts.option_list(
            opts.define('NAME')
        )), ['-DNAME'])
        self.assertEqual(self.compiler.flags(opts.option_list(
            opts.define('NAME', 'value')
        )), ['-DNAME=value'])

    def test_flags_std(self):
        self.assertEqual(self.compiler.flags(opts.option_list(
            opts.std('c++14')
        )), ['-std=c++14'])

    def test_flags_pthread(self):
        self.assertEqual(self.compiler.flags(opts.option_list(
            opts.pthread()
        )), ['-pthread'])

    def test_flags_pic(self):
        self.assertEqual(self.compiler.flags(opts.option_list(
            opts.pic()
        )), ['-fPIC'])

    def test_flags_include_pch(self):
        p = Path('/path/to/header.hpp')
        self.assertEqual(self.compiler.flags(opts.option_list(
            opts.pch(file_types.PrecompiledHeader(p))
        )), ['-include', p.stripext()])

    def test_flags_string(self):
        self.assertEqual(self.compiler.flags(opts.option_list('-v')), ['-v'])

    def test_flags_invalid(self):
        with self.assertRaises(TypeError):
            self.compiler.flags(opts.option_list(123))


class TestCcLinker(unittest.TestCase):
    def _get_linker(self, lang):
        with mock.patch('bfg9000.shell.which', mock_which), \
             mock.patch('bfg9000.shell.execute', mock_execute):  # noqa
            return CcBuilder(self.env, known_langs[lang], ['c++'],
                             'version').linker('executable')

    def setUp(self):
        self.env = make_env()
        self.linker = self._get_linker('c++')

    def test_flags_empty(self):
        self.assertEqual(self.linker.flags(opts.option_list()), [])

    def test_flags_lib_dir(self):
        libdir = Path('/path/to/lib')
        lib = Path('/path/to/lib/libfoo.a')
        output = file_types.Executable(Path('exe'), 'native')

        if self.env.target_platform.name == 'linux':
            rpath = rpath_with_output = ['-Wl,-rpath,' + libdir]
        elif self.env.target_platform.name == 'darwin':
            rpath = []
            rpath_with_output = [jbos('-Wl,-rpath,', '@loader_path')]
        else:
            rpath = rpath_with_output = []

        # Lib dir
        self.assertEqual(self.linker.flags(opts.option_list(
            opts.lib_dir(file_types.Directory(libdir))
        )), ['-L' + libdir])

        # Shared library
        self.assertEqual(self.linker.flags(opts.option_list(
            opts.lib(file_types.SharedLibrary(lib, 'native'))
        )), ['-L' + libdir] + rpath)
        self.assertEqual(self.linker.flags(opts.option_list(
            opts.lib(file_types.SharedLibrary(lib, 'native'))
        ), output), ['-L' + libdir] + rpath_with_output)

        if self.env.target_platform.name == 'linux':
            libdir2 = Path('foo')
            lib2 = Path('foo/libbar.a')

            with self.assertRaises(ValueError):
                self.linker.flags(opts.option_list(
                    opts.lib(file_types.SharedLibrary(lib2, 'native'))
                ))
            self.assertEqual(
                self.linker.flags(opts.option_list(
                    opts.lib(file_types.SharedLibrary(lib2, 'native'))
                ), output),
                ['-L' + libdir2, jbos('-Wl,-rpath,', '$ORIGIN/foo')]
            )

        # Static library
        self.assertEqual(self.linker.flags(opts.option_list(
            opts.lib(file_types.StaticLibrary(lib, 'native'))
        )), [])
        self.assertEqual(self.linker.flags(opts.option_list(
            opts.lib(file_types.StaticLibrary(lib, 'native'))
        ), mode='pkg-config'), ['-L' + libdir])

        # Framework
        self.assertEqual(self.linker.flags(opts.option_list(
            opts.lib(Framework('cocoa'))
        )), [])

        # Mixed
        self.assertEqual(self.linker.flags(opts.option_list(
            opts.lib_dir(file_types.Directory(libdir)),
            opts.lib(file_types.SharedLibrary(lib, 'native'))
        )), ['-L' + libdir] + rpath)
        self.assertEqual(self.linker.flags(opts.option_list(
            opts.lib_dir(file_types.Directory(libdir)),
            opts.lib(file_types.SharedLibrary(lib, 'native'))
        ), output), ['-L' + libdir] + rpath_with_output)

    def test_flags_rpath(self):
        p1 = Path('path1')
        p2 = Path('path2')

        self.assertEqual(self.linker.flags(opts.option_list(
            opts.rpath_dir(p1)
        )), ['-Wl,-rpath,' + p1])

        self.assertEqual(self.linker.flags(opts.option_list(
            opts.rpath_dir(p1),
            opts.rpath_dir(p2)
        )), ['-Wl,-rpath,' + p1 + ':' + p2])

    def test_flags_rpath_link(self):
        p1 = Path('/path/to/lib')
        p2 = Path('/path/to/another/lib')

        self.assertEqual(self.linker.flags(opts.option_list(
            opts.rpath_link_dir(p1)
        )), ['-Wl,-rpath-link,' + p1])

        self.assertEqual(self.linker.flags(opts.option_list(
            opts.rpath_link_dir(p1),
            opts.rpath_link_dir(p2)
        )), ['-Wl,-rpath-link,' + p1 + ':' + p2])

    def test_flags_entry_point(self):
        java_linker = self._get_linker('java')
        self.assertEqual(java_linker.flags(opts.option_list(
            opts.entry_point('Main')
        )), ['--main=Main'])

        with self.assertRaises(ValueError):
            self.linker.flags(opts.option_list(opts.entry_point('Main')))

    def test_flags_pthread(self):
        self.assertEqual(
            self.linker.flags(opts.option_list(opts.pthread())),
            [] if self.env.target_platform.name == 'darwin' else ['-pthread']
        )

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
        lib = Path('/path/to/lib/libfoo.a')

        # Shared library
        self.assertEqual(self.linker.lib_flags(opts.option_list(
            opts.lib(file_types.SharedLibrary(lib, 'native'))
        )), ['-lfoo'])

        # Static library
        self.assertEqual(self.linker.lib_flags(opts.option_list(
            opts.lib(file_types.StaticLibrary(lib, 'native'))
        )), [lib])
        self.assertEqual(self.linker.lib_flags(opts.option_list(
            opts.lib(file_types.SharedLibrary(lib, 'native'))
        ), mode='pkg-config'), ['-lfoo'])

        # Whole archive
        flags = self.linker.lib_flags(opts.option_list(
            opts.lib(file_types.WholeArchive(
                file_types.StaticLibrary(lib, 'native')
            ))
        ))
        if self.env.target_platform.name == 'darwin':
            self.assertEqual(flags, ['-Wl,-force_load', lib])
        else:
            self.assertEqual(flags, ['-Wl,--whole-archive', lib,
                                     '-Wl,--no-whole-archive'])

        # Framework
        fw = opts.lib(Framework('cocoa'))
        if self.env.target_platform.name == 'darwin':
            self.assertEqual(self.linker.lib_flags(opts.option_list(fw)),
                             ['-framework', 'cocoa'])
        else:
            with self.assertRaises(TypeError):
                self.linker.lib_flags(opts.option_list(fw))

    def test_lib_flags_lib_literal(self):
        self.assertEqual(self.linker.lib_flags(opts.option_list(
            opts.lib_literal('-lfoo')
        )), ['-lfoo'])

    def test_lib_flags_ignored(self):
        self.assertEqual(self.linker.lib_flags(opts.option_list('-Lfoo')), [])
