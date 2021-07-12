from unittest import mock

from ... import *
from .common import known_langs, mock_execute, mock_which

from bfg9000 import options as opts
from bfg9000.exceptions import PackageResolutionError
from bfg9000.file_types import Directory, HeaderDirectory, Library
from bfg9000.options import option_list
from bfg9000.packages import PackageKind
from bfg9000.path import abspath, Path, Root
from bfg9000.tools.msvc import MsvcBuilder
from bfg9000.versioning import SpecifierSet, Version


def mock_execute_pkgconf(args, **kwargs):
    if '--modversion' in args:
        return '1.2.3\n'
    elif '--variable=pcfiledir' in args:
        return '/path/to/pkg-config\n'
    elif '--cflags' in args:
        return '/Ipath\n'
    elif '--libs-only-L' in args:
        return '/LIBPATH:path\n'
    elif '--libs-only-l' in args:
        return 'foo.lib\n'
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
             mock.patch('bfg9000.shell.execute', mock_execute):  # noqa
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
        with mock.patch('bfg9000.shell.which', mock_which):
            self.builder = MsvcBuilder(self.env, known_langs['c++'], ['cl'],
                                       True, 'version')
            self.packages = self.builder.packages
            self.compiler = self.builder.compiler
            self.linker = self.builder.linker('executable')

    def test_lang(self):
        self.assertEqual(self.packages.lang, 'c++')

    def test_header(self):
        with mock.patch('bfg9000.tools.msvc.exists', return_value=True):
            p = abspath('/path/to/include')
            hdr = self.packages.header('foo.hpp', [p])
            self.assertEqual(hdr, HeaderDirectory(p))

    def test_header_not_found(self):
        with mock.patch('bfg9000.tools.msvc.exists', return_value=False):
            with self.assertRaises(PackageResolutionError):
                self.packages.header('foo.hpp')

    def test_header_relpath(self):
        with self.assertRaises(ValueError):
            self.packages.header('foo.hpp', [Path('dir', Root.srcdir)])

    def test_library(self):
        p = Path('/path/to/lib')
        with mock.patch('bfg9000.tools.msvc.exists', return_value=True):
            lib = self.packages.library('foo', search_dirs=[p])
            fmt = self.packages.builder.object_format
            self.assertEqual(lib, Library(p.append('foo.lib'), format=fmt))

    def test_library_not_found(self):
        with mock.patch('bfg9000.tools.msvc.exists', return_value=False):
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
                             option_list('/Ipath'))
            self.assertEqual(pkg.link_options(self.linker), option_list(
                '/LIBPATH:path', opts.lib_literal('foo.lib')
            ))

    def test_resolve_path(self):
        usage = {'type': 'path', 'headers': ['foo.hpp'],
                 'include_path': ['/path/to/include'],
                 'libraries': ['foo'], 'library_path': ['/path/to/lib']}
        with mock.patch('bfg9000.tools.msvc.exists', return_value=True), \
             mock.patch('bfg9000.tools.mopack.get_usage',
                        return_value=usage), \
             mock.patch('bfg9000.log.info'):  # noqa
            pkg = self.packages.resolve('foo', None, SpecifierSet(),
                                        PackageKind.any)
            self.assertEqual(pkg.name, 'foo')
            self.assertEqual(pkg.compile_options(self.compiler), option_list(
                opts.include_dir(HeaderDirectory(abspath('/path/to/include')))
            ))
            self.assertEqual(pkg.link_options(self.linker), option_list(
                opts.lib(Library(abspath('/path/to/lib/foo.lib'),
                                 format=self.builder.object_format))
            ))

    def test_resolve_path_include_path(self):
        usage = {'type': 'path', 'include_path': ['/path/to/include']}
        with mock.patch('bfg9000.tools.mopack.get_usage',
                        return_value=usage), \
             mock.patch('bfg9000.log.info'):  # noqa
            pkg = self.packages.resolve('foo', None, SpecifierSet(),
                                        PackageKind.any)
            self.assertEqual(pkg.name, 'foo')
            self.assertEqual(pkg.compile_options(self.compiler), option_list(
                opts.include_dir(HeaderDirectory(abspath('/path/to/include')))
            ))
            self.assertEqual(pkg.link_options(self.linker), option_list())

    def test_resolve_path_auto_link(self):
        usage = {'type': 'path', 'auto_link': True, 'libraries': ['foo'],
                 'library_path': ['/path/to/lib']}
        with mock.patch('bfg9000.tools.mopack.get_usage',
                        return_value=usage), \
             mock.patch('bfg9000.log.info'):  # noqa
            pkg = self.packages.resolve('foo', None, SpecifierSet(),
                                        PackageKind.any)
            self.assertEqual(pkg.name, 'foo')
            self.assertEqual(pkg.compile_options(self.compiler), option_list())
            self.assertEqual(pkg.link_options(self.linker), option_list(
                opts.lib_dir(Directory(abspath('/path/to/lib')))
            ))

    def test_resolve_invalid(self):
        with mock.patch('bfg9000.tools.mopack.get_usage',
                        return_value={'type': 'unknown'}), \
             self.assertRaises(PackageResolutionError):  # noqa
            self.packages.resolve('foo', None, SpecifierSet(), PackageKind.any)
