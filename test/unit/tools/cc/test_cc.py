from unittest import mock

from ... import *
from .common import known_langs, mock_execute, mock_which

from bfg9000 import options as opts, platforms
from bfg9000.exceptions import PackageResolutionError
from bfg9000.file_types import HeaderDirectory, Library, SharedLibrary
from bfg9000.options import option_list
from bfg9000.packages import PackageKind
from bfg9000.path import abspath, Path, Root
from bfg9000.tools.cc import CcBuilder
from bfg9000.versioning import SpecifierSet, Version


def mock_execute_pkgconf(args, **kwargs):
    if '--modversion' in args:
        return '1.2.3\n'
    elif '--variable=pcfiledir' in args:
        return '/path/to/pkg-config\n'
    elif '--cflags' in args:
        return '-I/path\n'
    elif '--libs-only-L' in args:
        return '-L/path\n'
    elif '--libs-only-l' in args:
        return '-lfoo\n'
    elif '--variable=install_names' in args:
        return '\n'
    elif '--print-requires' in args:
        return '\n'
    raise OSError('unknown command: {}'.format(args))


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

        self.assertEqual(cc.compiler.needs_package_options, True)
        self.assertEqual(cc.pch_compiler.needs_package_options, True)
        self.assertEqual(cc.linker('executable').needs_package_options, True)
        self.assertEqual(cc.linker('shared_library').needs_package_options,
                         True)

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


class TestCcPackageResolver(CrossPlatformTestCase):
    def __init__(self, *args, **kwargs):
        super().__init__(clear_variables=True, *args, **kwargs)

    def lib(self, path, name):
        t = Library if self.platform_name == 'winnt' else SharedLibrary
        ext = {'linux': '.so', 'winnt': '.dll.a', 'macos': '.dylib'}
        return t(path.append('lib{}{}'.format(name, ext[self.platform_name])),
                 format=self.packages.builder.object_format)

    def setUp(self):
        with mock.patch('bfg9000.shell.which', mock_which), \
             mock.patch('bfg9000.shell.execute', mock_execute):  # noqa
            self.builder = CcBuilder(self.env, known_langs['c++'], ['c++'],
                                     'version')
            self.packages = self.builder.packages
            self.compiler = self.builder.compiler
            self.linker = self.builder.linker('executable')

    def test_header(self):
        with mock.patch('bfg9000.tools.cc.exists', return_value=True):
            p = abspath('/path/to/include')
            hdr = self.packages.header('foo.hpp', [p])
            self.assertEqual(hdr, HeaderDirectory(p))

    def test_header_not_found(self):
        with mock.patch('bfg9000.tools.cc.exists', return_value=False):
            with self.assertRaises(PackageResolutionError):
                self.packages.header('foo.hpp')

    def test_header_relpath(self):
        with self.assertRaises(ValueError):
            self.packages.header('foo.hpp', [Path('dir', Root.srcdir)])

    def test_library(self):
        p = abspath('/path/to/lib')
        with mock.patch('bfg9000.tools.cc.exists', return_value=True):
            lib = self.packages.library('foo', search_dirs=[p])
            self.assertEqual(lib, self.lib(p, 'foo'))

    def test_library_not_found(self):
        with mock.patch('bfg9000.tools.cc.exists', return_value=False):
            with self.assertRaises(PackageResolutionError):
                self.packages.library('foo')

    def test_library_relpath(self):
        with self.assertRaises(ValueError):
            p = Path('dir', Root.srcdir)
            self.packages.library('foo', search_dirs=[p])

    def test_resolve_pkg_config(self):
        with mock.patch('bfg9000.shell.which', mock_which), \
             mock.patch('bfg9000.shell.execute', mock_execute):
            self.env.tool('pkg_config')

        usage = {'type': 'pkg_config', 'pcfiles': ['foo'],
                 'path': ['/path/to/include'], 'extra_args': []}
        with mock.patch('bfg9000.shell.execute', mock_execute_pkgconf), \
             mock.patch('bfg9000.tools.msvc.exists', return_value=True), \
             mock.patch('bfg9000.tools.mopack.get_usage',
                        return_value=usage), \
             mock.patch('bfg9000.log.info'):  # noqa
            pkg = self.packages.resolve('foo', None, SpecifierSet(),
                                        PackageKind.any)
            self.assertEqual(pkg.name, 'foo')
            self.assertEqual(pkg.compile_options(self.compiler),
                             option_list('-I/path'))

            ldflags = option_list('-L/path', opts.lib_literal('-lfoo'))
            if self.platform_name == 'linux':
                ldflags.append(opts.rpath_dir(Path('/path')))
            self.assertEqual(pkg.link_options(self.linker), ldflags)

    def test_resolve_path(self):
        usage = {'type': 'path', 'headers': ['foo.hpp'],
                 'include_path': ['/path/to/include'],
                 'libraries': ['foo'], 'library_path': ['/path/to/lib']}
        with mock.patch('bfg9000.tools.cc.exists', return_value=True), \
             mock.patch('bfg9000.tools.mopack.get_usage',
                        return_value=usage), \
             mock.patch('bfg9000.log.info'):  # noqa
            pkg = self.packages.resolve('foo', None, SpecifierSet(),
                                        PackageKind.any)
            self.assertEqual(pkg.name, 'foo')
            self.assertEqual(pkg.compile_options(None), opts.option_list(
                opts.include_dir(HeaderDirectory(abspath('/path/to/include')))
            ))
            self.assertEqual(pkg.link_options(None), opts.option_list(
                opts.lib(self.lib(abspath('/path/to/lib'), 'foo'))
            ))

    def test_resolve_path_include_path(self):
        usage = {'type': 'path', 'include_path': ['/path/to/include']}
        with mock.patch('bfg9000.tools.mopack.get_usage',
                        return_value=usage), \
             mock.patch('bfg9000.log.info'):  # noqa
            pkg = self.packages.resolve('foo', None, SpecifierSet(),
                                        PackageKind.any)
            self.assertEqual(pkg.name, 'foo')
            self.assertEqual(pkg.compile_options(None), opts.option_list(
                opts.include_dir(HeaderDirectory(abspath('/path/to/include')))
            ))
            self.assertEqual(pkg.link_options(None), opts.option_list())

    def test_resolve_path_auto_link(self):
        usage = {'type': 'path', 'auto_link': True, 'libraries': ['foo'],
                 'library_path': ['/path/to/lib']}
        with mock.patch('bfg9000.tools.mopack.get_usage',
                        return_value=usage), \
             self.assertRaises(PackageResolutionError):  # noqa
            self.packages.resolve('foo', None, SpecifierSet(), PackageKind.any)

    def test_resolve_invalid(self):
        with mock.patch('bfg9000.tools.mopack.get_usage',
                        return_value={'type': 'unknown'}), \
             self.assertRaises(PackageResolutionError):  # noqa
            self.packages.resolve('foo', None, SpecifierSet(), PackageKind.any)
