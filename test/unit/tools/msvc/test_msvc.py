from unittest import mock

from ... import *
from .common import known_langs, mock_which

from bfg9000.exceptions import PackageResolutionError
from bfg9000.path import Path, Root
from bfg9000.tools.msvc import MsvcBuilder
from bfg9000.versioning import Version


class TestMsvcBuilder(CrossPlatformTestCase):
    def __init__(self, *args, **kwargs):
        super().__init__(clear_variables=True, *args, **kwargs)

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

    def test_clang(self):
        def mock_execute(args, **kwargs):
            if args[-1] == '--version':
                return 'clang version 10.0.0'

        version = 'OVERVIEW: clang LLVM compiler'

        with mock.patch('bfg9000.shell.which', mock_which), \
             mock.patch('bfg9000.shell.execute', mock_execute):  # noqa
            cc = MsvcBuilder(self.env, known_langs['c++'], ['cl'], version)

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


class TestMsvcPackageResolver(CrossPlatformTestCase):
    def __init__(self, *args, **kwargs):
        super().__init__(clear_variables=True, *args, **kwargs)

    def setUp(self):
        with mock.patch('bfg9000.shell.which', mock_which):
            self.packages = MsvcBuilder(self.env, known_langs['c++'], ['cl'],
                                        'version').packages

    def test_header_not_found(self):
        with mock.patch('bfg9000.tools.msvc.exists', return_value=False):
            with self.assertRaises(PackageResolutionError):
                self.packages.header('foo.hpp')

    def test_header_relpath(self):
        with self.assertRaises(ValueError):
            self.packages.header('foo.hpp', [Path('dir', Root.srcdir)])

    def test_library_not_found(self):
        with mock.patch('bfg9000.tools.msvc.exists', return_value=False):
            with self.assertRaises(PackageResolutionError):
                self.packages.library('foo')

    def test_library_relpath(self):
        with self.assertRaises(ValueError):
            p = Path('dir', Root.srcdir)
            self.packages.library('foo', search_dirs=[p])
