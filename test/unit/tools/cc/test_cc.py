from unittest import mock

from ... import *
from .common import known_langs, mock_execute, mock_which

from bfg9000 import options as opts, platforms
from bfg9000.exceptions import PackageResolutionError
from bfg9000.file_types import Directory, HeaderDirectory
from bfg9000.options import option_list
from bfg9000.packages import PackageKind
from bfg9000.path import Path
from bfg9000.tools.cc import CcBuilder
from bfg9000.versioning import SpecifierSet, Version


def mock_execute_pkgconf(args, **kwargs):
    if '--modversion' in args:
        return '1.2.3\n'
    elif '--variable=pcfiledir' in args:
        return '/path/to/pkg-config\n'
    elif '--cflags-only-I' in args:
        return '-I/path\n'
    elif '--cflags-only-other' in args:
        return '-DMACRO\n'
    elif '--libs-only-L' in args:
        return '-L/path\n'
    elif '--libs-only-l' in args:
        return '-lfoo\n'
    elif '--libs-only-other' in args:
        return '-pthread\n'
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
             mock.patch('bfg9000.shell.execute', mock_execute):
            cc = CcBuilder(self.env, known_langs['c++'], ['c++'], True,
                           'version')

        self.assertEqual(cc.flavor, 'cc')
        self.assertEqual(cc.compiler.flavor, 'cc')
        self.assertEqual(cc.pch_compiler.flavor, 'cc')
        self.assertEqual(cc.linker('executable').flavor, 'cc')
        self.assertEqual(cc.linker('shared_library').flavor, 'cc')
        self.assertEqual(cc.linker('raw').flavor, 'ld')

        self.assertEqual(cc.compiler.found, True)
        self.assertEqual(cc.pch_compiler.found, True)
        self.assertEqual(cc.linker('executable').found, True)
        self.assertEqual(cc.linker('shared_library').found, True)
        self.assertEqual(cc.linker('static_library').found, True)
        self.assertEqual(cc.linker('raw').found, True)

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
             mock.patch('bfg9000.shell.execute', mock_execute):
            cc = CcBuilder(self.env, known_langs['c++'], ['g++'], True,
                           version)

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
                 mock.patch('bfg9000.shell.execute', mock_cross_exec):
                cc = CcBuilder(self.env, known_langs['c++'], ['g++'], True,
                               version)
            self.assertEqual(cc.compiler.global_flags, flags)

    def test_clang(self):
        version = 'clang version 3.8.0-2ubuntu4 (tags/RELEASE_380/final)'

        with mock.patch('bfg9000.shell.which', mock_which), \
             mock.patch('bfg9000.shell.execute', mock_execute):
            cc = CcBuilder(self.env, known_langs['c++'], ['clang++'], True,
                           version)

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
             mock.patch('bfg9000.shell.execute', mock_execute):
            cc = CcBuilder(self.env, known_langs['c++'], ['g++'], True,
                           version)
        self.assertEqual(cc.compiler.global_flags,
                         ['-target', self.env.target_platform.triplet]
                         if self.env.host_platform.name != 'linux' else [])

    def test_unknown_brand(self):
        version = 'unknown'

        with mock.patch('bfg9000.shell.which', mock_which), \
             mock.patch('bfg9000.shell.execute', mock_execute):
            cc = CcBuilder(self.env, known_langs['c++'], ['c++'], True,
                           version)

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
             mock.patch('logging.log'):
            cc = CcBuilder(self.env, known_langs['c++'], ['g++'], True,
                           version)
        self.assertEqual(cc.linker('executable').command,
                         ['g++', '-fuse-ld=gold'])

    def test_set_ld_unknown(self):
        version = ('g++ (Ubuntu 5.4.0-6ubuntu1~16.04.6) 5.4.0 20160609\n' +
                   'Copyright (C) 2015 Free Software Foundation, Inc.')

        self.env.variables['LD'] = '/usr/bin/ld.goofy'
        with mock.patch('bfg9000.shell.which', mock_which), \
             mock.patch('bfg9000.shell.execute', mock_execute), \
             mock.patch('logging.log'):
            cc = CcBuilder(self.env, known_langs['c++'], ['g++'], True,
                           version)
        self.assertEqual(cc.linker('executable').command, ['g++'])

    def test_execution_failure(self):
        def bad_execute(args, **kwargs):
            raise OSError()

        def weird_execute(args, **kwargs):
            if args[-1] == '-Wl,--not-a-real-flag':
                return 'stderr\n'
            return mock_execute(args, **kwargs)

        version = ('g++ (Ubuntu 5.4.0-6ubuntu1~16.04.6) 5.4.0 20160609\n' +
                   'Copyright (C) 2015 Free Software Foundation, Inc.')

        with mock.patch('bfg9000.shell.which', mock_which), \
             mock.patch('bfg9000.shell.execute', bad_execute), \
             mock.patch('logging.log'):
            cc = CcBuilder(self.env, known_langs['c++'], ['g++'], True,
                           version)
        self.assertRaises(KeyError, cc.linker, 'raw')

        with mock.patch('bfg9000.shell.which', mock_which), \
             mock.patch('bfg9000.shell.execute', weird_execute), \
             mock.patch('logging.log'):
            cc = CcBuilder(self.env, known_langs['c++'], ['g++'], True,
                           version)
        self.assertRaises(KeyError, cc.linker, 'raw')


class TestCcPackageResolver(CrossPlatformTestCase):
    def __init__(self, *args, **kwargs):
        super().__init__(clear_variables=True, *args, **kwargs)

    def setUp(self):
        with mock.patch('bfg9000.shell.which', mock_which), \
             mock.patch('bfg9000.shell.execute', mock_execute):
            self.builder = CcBuilder(self.env, known_langs['c++'], ['c++'],
                                     True, 'version')
            self.packages = self.builder.packages
            self.compiler = self.builder.compiler
            self.linker = self.builder.linker('executable')

            # Instantiate pkg-config so tests below can find it.
            self.env.tool('pkg_config')

    def check_package(self, pkg):
        self.assertEqual(pkg.name, 'foo')
        self.assertEqual(pkg.compile_options(self.compiler), option_list(
            '-DMACRO', opts.include_dir(HeaderDirectory(Path('/path')))
        ))
        self.assertEqual(pkg.link_options(self.linker), option_list(
            '-pthread', opts.lib_dir(Directory(Path('/path'))),
            opts.lib_literal('-lfoo'),
            (opts.rpath_dir(Path('/path')) if self.platform_name == 'linux'
             else None)
        ))

    def test_resolve_pkg_config(self):
        linkage = {'type': 'pkg_config', 'pcnames': ['foo'],
                   'pkg_config_path': ['/path/to/include']}
        with mock.patch('bfg9000.shell.execute', mock_execute_pkgconf), \
             mock.patch('bfg9000.tools.msvc.exists', return_value=True), \
             mock.patch('bfg9000.tools.mopack.get_linkage',
                        return_value=linkage), \
             mock.patch('bfg9000.log.info'):
            pkg = self.packages.resolve('foo', None, SpecifierSet(),
                                        PackageKind.any)
            self.check_package(pkg)

    def test_resolve_path(self):
        linkage = {'type': 'path', 'generated': True, 'auto_link': False,
                   'pcnames': ['foo'], 'pkg_config_path': '/path/to/pkgconfig'}
        with mock.patch('bfg9000.shell.execute', mock_execute_pkgconf), \
             mock.patch('bfg9000.tools.cc.exists', return_value=True), \
             mock.patch('bfg9000.tools.mopack.get_linkage',
                        return_value=linkage), \
             mock.patch('bfg9000.log.info'):
            pkg = self.packages.resolve('foo', None, SpecifierSet(),
                                        PackageKind.any)
            self.check_package(pkg)

    def test_resolve_path_auto_link(self):
        linkage = {'type': 'path', 'generated': True, 'auto_link': True,
                   'pcnames': ['foo'], 'pkg_config_path': '/path/to/pkgconfig'}
        with mock.patch('bfg9000.tools.mopack.get_linkage',
                        return_value=linkage), \
             self.assertRaises(PackageResolutionError):
            self.packages.resolve('foo', None, SpecifierSet(), PackageKind.any)
