from unittest import mock

from .. import *

from bfg9000 import options as opts, platforms
from bfg9000.exceptions import PackageResolutionError
from bfg9000.file_types import *
from bfg9000.languages import Languages
from bfg9000.packages import Framework
from bfg9000.path import InstallRoot, Path, Root
from bfg9000.tools.cc import CcBuilder
from bfg9000.versioning import Version

known_langs = Languages()
with known_langs.make('c++') as x:
    x.vars(compiler='CXX', flags='CXXFLAGS')
with known_langs.make('java') as x:
    x.vars(compiler='JAVAC', flags='JAVAFLAGS')


def mock_which(*args, **kwargs):
    return ['command']


def mock_execute(args, **kwargs):
    if args[-1] == '-Wl,--version':
        return '', ('COLLECT_GCC=g++\n/usr/bin/collect2 --version\n' +
                    '/usr/bin/ld --version\n')
    elif args[-1] == '-print-search-dirs':
        return 'libraries: =/lib/search/dir1:/lib/search/dir2\n'
    elif args[-1] == '-print-sysroot':
        return '/'
    elif args[-1] == '--verbose':
        return 'SEARCH_DIR("/usr")\n'


class TestCcBuilder(CrossPlatformTestCase):
    def __init__(self, *args, **kwargs):
        super().__init__(clear_variables=True, *args, **kwargs)

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

        self.assertEqual(cc.compiler.num_outputs, 'all')
        self.assertEqual(cc.pch_compiler.num_outputs, 'all')
        self.assertEqual(cc.linker('executable').num_outputs, 'all')

        num_out = 2 if self.env.target_platform.has_import_library else 'all'
        self.assertEqual(cc.linker('shared_library').num_outputs, num_out)

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

    def test_cross_gcc(self):
        def mock_cross_exec(args, **kwargs):
            if args[-1] == '-dumpmachine':
                return self.env.host_platform.triplet
            return mock_execute(args, **kwargs)

        subtests = (
            ('x86_64', 'x86_64', []),
            ('x86_64', 'i686', ['-m32']),
            ('x86_64', 'i386', ['-m32']),
            ('i686', 'x86_64', ['-m64']),
            ('i686', 'i686', []),
            ('i686', 'i386', []),
            ('i386', 'x86_64', ['-m64']),
            ('i386', 'i686', []),
            ('i386', 'i386', []),
            ('x86_64', 'goofy', []),
        )
        for host, target, flags in subtests:
            self.env.host_platform = platforms.host.platform_info(
                self.env.host_platform.name, host
            )
            self.env.target_platform = platforms.target.platform_info(
                'linux', target
            )

            version = ('g++ (Ubuntu 5.4.0-6ubuntu1~16.04.6) 5.4.0 20160609\n' +
                       'Copyright (C) 2015 Free Software Foundation, Inc.')

            with mock.patch('bfg9000.shell.which', mock_which), \
                 mock.patch('bfg9000.shell.execute', mock_cross_exec):  # noqa
                cc = CcBuilder(self.env, known_langs['c++'], ['g++'], version)
            self.assertEqual(cc.compiler.global_flags, flags)

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

    def test_cross_clang(self):
        self.env.target_platform = platforms.target.platform_info(
            'linux', self.env.target_platform.arch
        )

        version = 'clang version 3.8.0-2ubuntu4 (tags/RELEASE_380/final)'
        with mock.patch('bfg9000.shell.which', mock_which), \
             mock.patch('bfg9000.shell.execute', mock_execute):  # noqa
            cc = CcBuilder(self.env, known_langs['c++'], ['g++'], version)
        self.assertEqual(cc.compiler.global_flags,
                         ['-target', self.env.target_platform.triplet]
                         if self.env.host_platform.name != 'linux' else [])

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

    def test_set_ld_gold(self):
        version = ('g++ (Ubuntu 5.4.0-6ubuntu1~16.04.6) 5.4.0 20160609\n' +
                   'Copyright (C) 2015 Free Software Foundation, Inc.')

        self.env.variables['LD'] = '/usr/bin/ld.gold'
        with mock.patch('bfg9000.shell.which', mock_which), \
             mock.patch('bfg9000.shell.execute', mock_execute), \
             mock.patch('logging.log'):  # noqa
            cc = CcBuilder(self.env, known_langs['c++'], ['g++'], version)
        self.assertEqual(cc.linker('executable').command,
                         ['g++', '-fuse-ld=gold'])

    def test_set_ld_unknown(self):
        version = ('g++ (Ubuntu 5.4.0-6ubuntu1~16.04.6) 5.4.0 20160609\n' +
                   'Copyright (C) 2015 Free Software Foundation, Inc.')

        self.env.variables['LD'] = '/usr/bin/ld.goofy'
        with mock.patch('bfg9000.shell.which', mock_which), \
             mock.patch('bfg9000.shell.execute', mock_execute), \
             mock.patch('logging.log'):  # noqa
            cc = CcBuilder(self.env, known_langs['c++'], ['g++'], version)
        self.assertEqual(cc.linker('executable').command, ['g++'])

    def test_execution_failure(self):
        def bad_execute(args, **kwargs):
            raise OSError()

        def weird_execute(args, **kwargs):
            if args[-1] == '-Wl,--version':
                return '', 'stderr\n'
            return mock_execute(args, **kwargs)

        version = ('g++ (Ubuntu 5.4.0-6ubuntu1~16.04.6) 5.4.0 20160609\n' +
                   'Copyright (C) 2015 Free Software Foundation, Inc.')

        with mock.patch('bfg9000.shell.which', mock_which), \
             mock.patch('bfg9000.shell.execute', bad_execute), \
             mock.patch('logging.log'):  # noqa
            cc = CcBuilder(self.env, known_langs['c++'], ['g++'], version)
        self.assertRaises(KeyError, cc.linker, 'raw')

        with mock.patch('bfg9000.shell.which', mock_which), \
             mock.patch('bfg9000.shell.execute', weird_execute), \
             mock.patch('logging.log'):  # noqa
            cc = CcBuilder(self.env, known_langs['c++'], ['g++'], version)
        self.assertRaises(KeyError, cc.linker, 'raw')


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


class TestCcLinker(CrossPlatformTestCase):
    shared = False

    def __init__(self, *args, **kwargs):
        super().__init__(clear_variables=True, *args, **kwargs)

    def _get_linker(self, lang):
        with mock.patch('bfg9000.shell.which', mock_which), \
             mock.patch('bfg9000.shell.execute', mock_execute):  # noqa
            return CcBuilder(self.env, known_langs[lang], ['c++'],
                             'version').linker('executable')

    def _get_output_file(self):
        return Executable(self.Path('program'), 'native')

    def setUp(self):
        self.linker = self._get_linker('c++')

    def test_call(self):
        extra = self.linker._always_flags
        self.assertEqual(self.linker(['in'], 'out'),
                         [self.linker] + extra + ['in', '-o', 'out'])
        self.assertEqual(self.linker(['in'], 'out', flags=['flags']),
                         [self.linker] + extra + ['flags', 'in', '-o', 'out'])

        self.assertEqual(self.linker(['in'], 'out', ['lib']),
                         [self.linker] + extra + ['in', 'lib', '-o', 'out'])
        self.assertEqual(
            self.linker(['in'], 'out', ['lib'], ['flags']),
            [self.linker] + extra + ['flags', 'in', 'lib', '-o', 'out']
        )

    def test_output_file(self):
        fmt = self.env.target_platform.object_format
        ext = self.env.target_platform.executable_ext
        self.assertEqual(self.linker.output_file('prog', None),
                         Executable(Path('prog' + ext), fmt, 'c++'))

    def test_flags_empty(self):
        self.assertEqual(self.linker.flags(opts.option_list()), [])

    def test_flags_lib_dir(self):
        libdir = self.Path('/path/to/lib')
        lib = self.Path('/path/to/lib/libfoo.a')
        srclibdir = self.Path('.', Root.srcdir)
        srclib = self.Path('libfoo.a', Root.srcdir)

        if self.shared:
            output = SharedLibrary(self.Path('out'), 'native')
            if self.env.target_platform.genus == 'darwin':
                soname = ['-install_name',
                          self.Path('out').string(self.env.base_dirs)]
            else:
                soname = ['-Wl,-soname,out']
        else:
            output = Executable(self.Path('exe'), 'native')
            soname = []

        if self.env.target_platform.genus == 'linux':
            rpath = ['-Wl,-rpath,' + libdir]
            srcdir_rpath = ['-Wl,-rpath,' + srclibdir]
        else:
            rpath = srcdir_rpath = []

        # Lib dir
        self.assertEqual(self.linker.flags(opts.option_list(
            opts.lib_dir(Directory(libdir))
        )), ['-L' + libdir])

        # Shared library
        self.assertEqual(self.linker.flags(opts.option_list(
            opts.lib(SharedLibrary(lib, 'native'))
        )), ['-L' + libdir] + rpath)
        self.assertEqual(self.linker.flags(opts.option_list(
            opts.lib(SharedLibrary(lib, 'native'))
        ), output), ['-L' + libdir] + rpath + soname)
        self.assertEqual(self.linker.flags(opts.option_list(
            opts.lib(SharedLibrary(srclib, 'native'))
        ), output), ['-L' + srclibdir] + srcdir_rpath + soname)

        if self.env.target_platform.genus == 'linux':
            libdir2 = self.Path('foo')
            lib2 = self.Path('foo/libbar.a')

            with self.assertRaises(ValueError):
                self.linker.flags(opts.option_list(
                    opts.lib(SharedLibrary(lib2, 'native'))
                ))
            self.assertEqual(
                self.linker.flags(opts.option_list(
                    opts.lib(SharedLibrary(lib2, 'native'))
                ), output),
                ['-L' + libdir2, '-Wl,-rpath,$ORIGIN/foo'] + soname
            )

        # Static library
        self.assertEqual(self.linker.flags(opts.option_list(
            opts.lib(StaticLibrary(lib, 'native'))
        )), [])
        self.assertEqual(self.linker.flags(opts.option_list(
            opts.lib(StaticLibrary(lib, 'native'))
        ), mode='pkg-config'), ['-L' + libdir])

        # Generic library
        self.assertEqual(self.linker.flags(opts.option_list(
            opts.lib(Library(lib, 'native'))
        )), ['-L' + libdir])

        mingw_lib = self.Path('/path/to/lib/foo.lib')
        self.assertEqual(self.linker.flags(opts.option_list(
            opts.lib(Library(mingw_lib, 'native'))
        )), [])
        with self.assertRaises(ValueError):
            self.linker.flags(opts.option_list(
                opts.lib(Library(mingw_lib, 'native'))
            ), mode='pkg-config')

        # Framework
        self.assertEqual(self.linker.flags(opts.option_list(
            opts.lib(Framework('cocoa'))
        )), [])

        # Mixed
        self.assertEqual(self.linker.flags(opts.option_list(
            opts.lib_dir(Directory(libdir)),
            opts.lib(SharedLibrary(lib, 'native'))
        )), ['-L' + libdir] + rpath)
        self.assertEqual(self.linker.flags(opts.option_list(
            opts.lib_dir(Directory(libdir)),
            opts.lib(SharedLibrary(lib, 'native'))
        ), output), ['-L' + libdir] + rpath + soname)

    def test_flags_rpath(self):
        p1 = self.Path('path1')
        p2 = self.Path('path2')

        self.assertEqual(self.linker.flags(opts.option_list(
            opts.rpath_dir(p1)
        )), ['-Wl,-rpath,' + p1])

        self.assertEqual(self.linker.flags(opts.option_list(
            opts.rpath_dir(p1),
            opts.rpath_dir(p2)
        )), ['-Wl,-rpath,' + p1 + ':' + p2])

        self.assertEqual(self.linker.flags(opts.option_list(
            opts.rpath_dir(p1)
        ), mode='pkg-config'), [])

    def test_flags_rpath_link(self):
        p1 = self.Path('/path/to/lib')
        p2 = self.Path('/path/to/another/lib')

        self.assertEqual(self.linker.flags(opts.option_list(
            opts.rpath_link_dir(p1)
        )), ['-Wl,-rpath-link,' + p1])

        self.assertEqual(self.linker.flags(opts.option_list(
            opts.rpath_link_dir(p1),
            opts.rpath_link_dir(p2)
        )), ['-Wl,-rpath-link,' + p1 + ':' + p2])

        self.assertEqual(self.linker.flags(opts.option_list(
            opts.rpath_link_dir(p1)
        ), mode='pkg-config'), [])

    def test_flags_module_def(self):
        path = self.Path('/path/to/module.def')
        self.assertEqual(
            self.linker.flags(opts.option_list(
                opts.module_def(ModuleDefFile(path))
            )),
            [path] if self.env.target_platform.family == 'windows' else []
        )

    def test_flags_entry_point(self):
        java_linker = self._get_linker('java')
        self.assertEqual(java_linker.flags(opts.option_list(
            opts.entry_point('Main')
        )), ['--main=Main'])

        with self.assertRaises(ValueError):
            self.linker.flags(opts.option_list(opts.entry_point('Main')))

    def test_flags_optimize(self):
        self.assertEqual(self.linker.flags(opts.option_list(
            opts.optimize('disable')
        )), ['-O0'])
        self.assertEqual(self.linker.flags(opts.option_list(
            opts.optimize('size')
        )), ['-Osize'])
        self.assertEqual(self.linker.flags(opts.option_list(
            opts.optimize('speed')
        )), ['-O3'])
        self.assertEqual(self.linker.flags(opts.option_list(
            opts.optimize('linktime')
        )), ['-flto'])

        self.assertEqual(self.linker.flags(opts.option_list(
            opts.optimize('speed', 'linktime')
        )), ['-O3', '-flto'])

    def test_flags_debug(self):
        self.assertEqual(self.linker.flags(opts.option_list(
            opts.debug()
        )), ['-g'])

    def test_flags_static(self):
        self.assertEqual(self.linker.flags(opts.option_list(
            opts.static()
        )), ['-static'])

    def test_flags_pthread(self):
        self.assertEqual(
            self.linker.flags(opts.option_list(opts.pthread())),
            [] if self.env.target_platform.genus == 'darwin' else ['-pthread']
        )

    def test_flags_string(self):
        self.assertEqual(self.linker.flags(opts.option_list('-v')), ['-v'])

    def test_flags_install_name_change(self):
        self.assertEqual(self.linker.flags(opts.option_list(
            opts.install_name_change('foo.dylib', 'bar.dylib')
        )), [])

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
        lib = self.Path('/path/to/lib/libfoo.a')

        # Shared library
        self.assertEqual(self.linker.lib_flags(opts.option_list(
            opts.lib(SharedLibrary(lib, 'native'))
        )), ['-lfoo'])
        self.assertEqual(self.linker.lib_flags(opts.option_list(
            opts.lib(SharedLibrary(lib, 'native'))
        ), mode='pkg-config'), ['-lfoo'])

        # Shared library with creator
        x = SharedLibrary(lib, 'native')
        x.creator = 'test'
        self.assertEqual(self.linker.lib_flags(opts.option_list(opts.lib(x))),
                         [lib])
        self.assertEqual(self.linker.lib_flags(opts.option_list(opts.lib(x)),
                                               mode='pkg-config'),
                         ['-lfoo'])

        # Static library
        self.assertEqual(self.linker.lib_flags(opts.option_list(
            opts.lib(StaticLibrary(lib, 'native'))
        )), [lib])
        self.assertEqual(self.linker.lib_flags(opts.option_list(
            opts.lib(StaticLibrary(lib, 'native'))
        ), mode='pkg-config'), ['-lfoo'])

        # Whole archive
        flags = self.linker.lib_flags(opts.option_list(
            opts.lib(WholeArchive(
                StaticLibrary(lib, 'native')
            ))
        ))
        if self.env.target_platform.genus == 'darwin':
            self.assertEqual(flags, ['-Wl,-force_load', lib])
        else:
            self.assertEqual(flags, ['-Wl,--whole-archive', lib,
                                     '-Wl,--no-whole-archive'])

        # Generic library
        self.assertEqual(self.linker.lib_flags(opts.option_list(
            opts.lib(Library(lib, 'native'))
        )), ['-lfoo'])

        mingw_lib = self.Path('/path/to/lib/foo.lib')
        self.assertEqual(self.linker.lib_flags(opts.option_list(
            opts.lib(Library(mingw_lib, 'native'))
        )), [mingw_lib])
        with self.assertRaises(ValueError):
            self.linker.lib_flags(opts.option_list(
                opts.lib(Library(mingw_lib, 'native'))
            ), mode='pkg-config')

        # Framework
        fw = opts.lib(Framework('cocoa'))
        if self.env.target_platform.genus == 'darwin':
            self.assertEqual(self.linker.lib_flags(opts.option_list(fw)),
                             ['-framework', 'cocoa'])
        else:
            with self.assertRaises(TypeError):
                self.linker.lib_flags(opts.option_list(fw))

        # String
        self.assertEqual(self.linker.lib_flags(
            opts.option_list(opts.lib('foo'))
        ), ['-lfoo'])

    def test_lib_flags_lib_literal(self):
        self.assertEqual(self.linker.lib_flags(opts.option_list(
            opts.lib_literal('-lfoo')
        )), ['-lfoo'])

    def test_lib_flags_ignored(self):
        self.assertEqual(self.linker.lib_flags(opts.option_list('-Lfoo')), [])

    @only_if_platform('linux', hide=True)
    def test_post_installed_linux(self):
        output = self._get_output_file()
        shared = SharedLibrary(self.Path('libfoo.so'), 'native')
        shared_abs = SharedLibrary(self.Path('/path/to/libfoo.so'), 'native')
        static = StaticLibrary(self.Path('libfoo.a'), 'native')

        with mock.patch('bfg9000.shell.which', return_value=['command']):
            # Local shared lib
            cmd = self.linker.post_install(opts.option_list(opts.lib(shared)),
                                           output, None)
            self.assertEqual(cmd, [
                self.env.tool('patchelf'), '--set-rpath',
                self.Path('', InstallRoot.libdir), file_install_path(output)
            ])

            # Absolute shared lib
            cmd = self.linker.post_install(
                opts.option_list(opts.lib(shared_abs)), output, None
            )
            self.assertEqual(cmd, None)

            # Local static lib
            cmd = self.linker.post_install(opts.option_list(opts.lib(static)),
                                           output, None)
            self.assertEqual(cmd, None)

            # Explicit rpath dir
            cmd = self.linker.post_install(opts.option_list(
                opts.rpath_dir(self.Path('/path'))
            ), output, None)
            self.assertEqual(cmd, None)

            # Mixed
            cmd = self.linker.post_install(opts.option_list(
                opts.lib(shared), opts.lib(shared_abs), opts.lib(static),
                opts.rpath_dir(self.Path('/path')),
                opts.rpath_dir(self.Path('/path/to'))
            ), output, None)
            self.assertEqual(cmd, [
                self.env.tool('patchelf'), '--set-rpath',
                (self.Path('', InstallRoot.libdir) + ':' +
                 self.Path('/path/to') + ':' + self.Path('/path')),
                file_install_path(output)
            ])

    @only_if_platform('macos', hide=True)
    def test_post_installed_macos(self):
        output = self._get_output_file()
        installed = file_install_path(output)
        deplib = SharedLibrary(self.Path('libfoo.so'), 'native')

        with mock.patch('bfg9000.shell.which', return_value=['command']):
            install_name_tool = self.env.tool('install_name_tool')

            # No runtime deps
            cmd = self.linker.post_install(opts.option_list(), output, None)
            self.assertEqual(cmd, [
                install_name_tool, '-id', installed.cross(self.env), installed
            ] if self.shared else None)

            cmd = self.linker.post_install(opts.option_list(
                opts.install_name_change('old.dylib', 'new.dylib')
            ), output, None)
            self.assertEqual(cmd, (
                [install_name_tool] +
                (['-id', installed.cross(self.env)] if self.shared else []) +
                ['-change', 'old.dylib', 'new.dylib', installed]
            ))

            # Dependent on local shared lib
            output.runtime_deps = [deplib]
            cmd = self.linker.post_install(
                opts.option_list(opts.lib(deplib)), output, None
            )
            self.assertEqual(cmd, (
                [install_name_tool] +
                (['-id', installed.cross(self.env)] if self.shared else []) +
                ['-change', deplib.path.string(self.env.base_dirs),
                 file_install_path(deplib, cross=self.env), installed]
            ))


class TestCcSharedLinker(TestCcLinker):
    shared = True

    def _get_linker(self, lang):
        with mock.patch('bfg9000.shell.which', mock_which), \
             mock.patch('bfg9000.shell.execute', mock_execute):  # noqa
            return CcBuilder(self.env, known_langs[lang], ['c++'],
                             'version').linker('shared_library')

    def _get_output_file(self):
        return SharedLibrary(self.Path('liboutput.so'), 'native')

    def test_call(self):
        if not self.env.target_platform.has_import_library:
            return super().test_call()

        extra = self.linker._always_flags
        self.assertEqual(
            self.linker(['in'], ['out', 'imp']),
            [self.linker] + extra + ['in', '-o', 'out', '-Wl,--out-implib=imp']
        )
        self.assertEqual(
            self.linker(['in'], ['out', 'imp'], flags=['flags']),
            [self.linker] + extra + ['flags', 'in', '-o', 'out',
                                     '-Wl,--out-implib=imp']
        )

        self.assertEqual(
            self.linker(['in'], ['out', 'imp'], ['lib']),
            [self.linker] + extra + ['in', 'lib', '-o', 'out',
                                     '-Wl,--out-implib=imp']
        )
        self.assertEqual(
            self.linker(['in'], ['out', 'imp'], ['lib'], ['flags']),
            [self.linker] + extra + ['flags', 'in', 'lib', '-o', 'out',
                                     '-Wl,--out-implib=imp']
        )

    def test_output_file(self):
        fmt = self.env.target_platform.object_format
        ext = self.env.target_platform.shared_library_ext
        if self.env.target_platform.has_import_library:
            out = DllBinary(Path('foo' + ext), fmt, 'c++',
                            Path('libfoo.dll.a'))
            self.assertEqual(self.linker.output_file('foo', None),
                             [out, out.import_lib])
        else:
            self.assertEqual(self.linker.output_file('foo', None),
                             SharedLibrary(Path('libfoo' + ext), fmt, 'c++'))


class TestCcPackageResolver(CrossPlatformTestCase):
    def __init__(self, *args, **kwargs):
        super().__init__(clear_variables=True, *args, **kwargs)

    def setUp(self):
        with mock.patch('bfg9000.shell.which', mock_which), \
             mock.patch('bfg9000.shell.execute', mock_execute):  # noqa
            self.packages = CcBuilder(self.env, known_langs['c++'], ['c++'],
                                      'version').packages

    def test_header_not_found(self):
        with mock.patch('bfg9000.tools.cc.exists', return_value=False):
            with self.assertRaises(PackageResolutionError):
                self.packages.header('foo.hpp')

    def test_header_relpath(self):
        with self.assertRaises(ValueError):
            self.packages.header('foo.hpp', [Path('dir', Root.srcdir)])

    def test_library_not_found(self):
        with mock.patch('bfg9000.tools.cc.exists', return_value=False):
            with self.assertRaises(PackageResolutionError):
                self.packages.library('foo')

    def test_library_relpath(self):
        with self.assertRaises(ValueError):
            p = Path('dir', Root.srcdir)
            self.packages.library('foo', search_dirs=[p])
