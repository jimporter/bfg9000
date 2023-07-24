from unittest import mock

from ... import *
from .common import known_langs, mock_execute, mock_which

from bfg9000 import options as opts
from bfg9000.file_types import Directory, HeaderDirectory
from bfg9000.options import option_list
from bfg9000.packages import PackageKind
from bfg9000.path import Path
from bfg9000.tools.msvc import MsvcBuilder
from bfg9000.versioning import SpecifierSet, Version


def mock_execute_pkgconf(args, **kwargs):
    if '--modversion' in args:
        return '1.2.3\n'
    elif '--variable=pcfiledir' in args:
        return '/path/to/pkg-config\n'
    elif '--cflags-only-I' in args:
        return '/I/path\n' if '--msvc-syntax' in args else '-I/path\n'
    elif '--cflags-only-other' in args:
        return '/DMACRO\n' if '--msvc-syntax' in args else '-DMACRO\n'
    elif '--libs-only-L' in args:
        return '/LIBPATH:/path\n' if '--msvc-syntax' in args else '-L/path\n'
    elif '--libs-only-other' in args:
        return '/DEBUG\n' if '--msvc-syntax' in args else '-DEBUG\n'
    elif '--libs-only-l' in args:
        return 'foo.lib\n' if '--msvc-syntax' in args else '-lfoo\n'
    elif '--variable=install_names' in args:
        return '\n'
    elif '--print-requires' in args:
        return '\n'
    raise OSError('unknown command: {}'.format(args))


class TestMsvcBuilder(CrossPlatformTestCase):
    def __init__(self, *args, **kwargs):
        super().__init__(clear_variables=True, *args, **kwargs)

    def test_properties(self):
        with mock.patch('bfg9000.shell.which', mock_which):
            cc = MsvcBuilder(self.env, known_langs['c++'], ['cl'], True,
                             'version')

        self.assertEqual(cc.flavor, 'msvc')
        self.assertEqual(cc.compiler.flavor, 'msvc')
        self.assertEqual(cc.pch_compiler.flavor, 'msvc')
        self.assertEqual(cc.linker('executable').flavor, 'msvc')
        self.assertEqual(cc.linker('shared_library').flavor, 'msvc')
        self.assertEqual(cc.linker('static_library').flavor, 'msvc')

        self.assertEqual(cc.compiler.found, True)
        self.assertEqual(cc.pch_compiler.found, True)
        self.assertEqual(cc.linker('executable').found, True)
        self.assertEqual(cc.linker('shared_library').found, True)

        self.assertEqual(cc.family, 'native')
        self.assertEqual(cc.auto_link, True)
        self.assertEqual(cc.can_dual_link, False)

        self.assertEqual(cc.compiler.num_outputs, 'all')
        self.assertEqual(cc.pch_compiler.num_outputs, 2)
        self.assertEqual(cc.linker('executable').num_outputs, 'all')
        self.assertEqual(cc.linker('shared_library').num_outputs, 2)

        self.assertEqual(cc.compiler.deps_flavor, 'msvc')
        self.assertEqual(cc.pch_compiler.deps_flavor, 'msvc')

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

    def test_msvc(self):
        version = ('Microsoft (R) C/C++ Optimizing Compiler Version ' +
                   '19.12.25831 for x86')

        with mock.patch('bfg9000.shell.which', mock_which):
            cc = MsvcBuilder(self.env, known_langs['c++'], ['cl'], True,
                             version)

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

    def test_clang(self):
        def mock_execute(args, **kwargs):
            if '--version' in args:
                return 'clang version 10.0.0'

        version = 'OVERVIEW: clang LLVM compiler'

        with mock.patch('bfg9000.shell.which', mock_which), \
             mock.patch('bfg9000.shell.execute', mock_execute):
            cc = MsvcBuilder(self.env, known_langs['c++'], ['cl'], True,
                             version)

        self.assertEqual(cc.brand, 'clang')
        self.assertEqual(cc.compiler.brand, 'clang')
        self.assertEqual(cc.pch_compiler.brand, 'clang')
        self.assertEqual(cc.linker('executable').brand, 'clang')
        self.assertEqual(cc.linker('shared_library').brand, 'clang')

        self.assertEqual(cc.version, Version('10.0.0'))
        self.assertEqual(cc.compiler.version, Version('10.0.0'))
        self.assertEqual(cc.pch_compiler.version, Version('10.0.0'))
        self.assertEqual(cc.linker('executable').version,
                         Version('10.0.0'))
        self.assertEqual(cc.linker('shared_library').version,
                         Version('10.0.0'))

    def test_unknown_brand(self):
        version = 'unknown'

        with mock.patch('bfg9000.shell.which', mock_which):
            cc = MsvcBuilder(self.env, known_langs['c++'], ['c++'], True,
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


class TestMsvcPackageResolver(CrossPlatformTestCase):
    def __init__(self, *args, **kwargs):
        super().__init__(clear_variables=True, *args, **kwargs)

    def setUp(self):
        with mock.patch('bfg9000.shell.which', mock_which), \
             mock.patch('bfg9000.shell.execute', mock_execute):
            self.builder = MsvcBuilder(self.env, known_langs['c++'], ['cl'],
                                       True, 'version')
            self.packages = self.builder.packages
            self.compiler = self.builder.compiler
            self.linker = self.builder.linker('executable')

            self.env.tool('pkg_config')

    def check_package(self, pkg):
        self.assertEqual(pkg.name, 'foo')
        self.assertEqual(pkg.compile_options(self.compiler), option_list(
            '/DMACRO', opts.include_dir(HeaderDirectory(Path('/path')))
        ))
        self.assertEqual(pkg.link_options(self.linker), option_list(
            '/DEBUG', opts.lib_dir(Directory(Path('/path'))),
            opts.lib_literal('foo.lib'),
            (opts.rpath_dir(Path('/path')) if self.platform_name == 'linux'
             else None)
        ))

    def test_lang(self):
        self.assertEqual(self.packages.lang, 'c++')

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
             mock.patch('bfg9000.tools.msvc.exists', return_value=True), \
             mock.patch('bfg9000.tools.mopack.get_linkage',
                        return_value=linkage), \
             mock.patch('bfg9000.log.info'):
            pkg = self.packages.resolve('foo', None, SpecifierSet(),
                                        PackageKind.any)
            self.check_package(pkg)

    def test_resolve_path_auto_link(self):
        linkage = {'type': 'path', 'generated': True, 'auto_link': True,
                   'pcnames': ['foo'], 'pkg_config_path': '/path/to/pkgconfig'}
        with mock.patch('bfg9000.shell.execute', mock_execute_pkgconf), \
             mock.patch('bfg9000.tools.msvc.exists', return_value=True), \
             mock.patch('bfg9000.tools.mopack.get_linkage',
                        return_value=linkage), \
             mock.patch('bfg9000.log.info'):
            pkg = self.packages.resolve('foo', None, SpecifierSet(),
                                        PackageKind.any)
            self.check_package(pkg)
