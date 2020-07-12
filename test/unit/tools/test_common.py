from unittest import mock

from .. import *

from bfg9000 import file_types
from bfg9000.languages import Languages
from bfg9000.path import Path, Root
from bfg9000.tools import cc, common

known_langs = Languages()
with known_langs.make('c') as x:
    x.vars(compiler='CC', flags='CFLAGS')


def mock_which(*args, **kwargs):
    return ['command']


def mock_execute(args, **kwargs):
    if args[-1] == '--version':
        return ('g++ (Ubuntu 5.4.0-6ubuntu1~16.04.6) 5.4.0 20160609\n' +
                'Copyright (C) 2015 Free Software Foundation, Inc.')
    elif args[-1] == '-Wl,--version':
        return '', '/usr/bin/ld --version\n'
    elif args[-1] == '-print-search-dirs':
        return 'libraries: =/lib/search/dir1:/lib/search/dir2\n'
    elif args[-1] == '-print-sysroot':
        return '/'
    elif args[-1] == '--verbose':
        return 'SEARCH_DIR("/usr")\n'


class TestLibraryMacro(TestCase):
    def test_simple(self):
        self.assertEqual(common.library_macro('libfoo', 'shared_library'),
                         'LIBFOO_EXPORTS')
        self.assertEqual(common.library_macro('libfoo', 'static_library'),
                         'LIBFOO_STATIC')

    def test_subdir(self):
        self.assertEqual(common.library_macro('dir/libfoo', 'shared_library'),
                         'DIR_LIBFOO_EXPORTS')
        self.assertEqual(common.library_macro('dir/libfoo', 'static_library'),
                         'DIR_LIBFOO_STATIC')

    def test_leading_underscore(self):
        self.assertEqual(common.library_macro('_dir/libfoo', 'shared_library'),
                         'LIB_DIR_LIBFOO_EXPORTS')
        self.assertEqual(common.library_macro('_dir/libfoo', 'static_library'),
                         'LIB_DIR_LIBFOO_STATIC')

    def test_leading_digits(self):
        self.assertEqual(common.library_macro('1/libfoo', 'shared_library'),
                         'LIB_1_LIBFOO_EXPORTS')
        self.assertEqual(common.library_macro('1/libfoo', 'static_library'),
                         'LIB_1_LIBFOO_STATIC')


class TestDarwinInstallName(TestCase):
    def setUp(self):
        self.env = make_env()

    def test_shared_library(self):
        lib = file_types.SharedLibrary(Path('libfoo.dylib'), 'native')
        self.assertEqual(common.darwin_install_name(lib, self.env),
                         self.env.builddir.append('libfoo.dylib').string())

    def test_versioned_shared_library(self):
        lib = file_types.VersionedSharedLibrary(
            Path('libfoo.1.2.3.dylib'), 'native', 'c', Path('libfoo.1.dylib'),
            Path('libfoo.dylib')
        )
        self.assertEqual(common.darwin_install_name(lib, self.env),
                         self.env.builddir.append('libfoo.1.dylib').string())
        self.assertEqual(common.darwin_install_name(lib.soname, self.env),
                         self.env.builddir.append('libfoo.1.dylib').string())
        self.assertEqual(common.darwin_install_name(lib.link, self.env),
                         self.env.builddir.append('libfoo.1.dylib').string())

    def test_static_library(self):
        lib = file_types.StaticLibrary(Path('libfoo.a'), 'native')
        self.assertRaises(TypeError, common.darwin_install_name, lib, self.env)
        self.assertEqual(common.darwin_install_name(lib, self.env, False),
                         None)


class TestNotBuildroot(CrossPlatformTestCase):
    def test_none(self):
        self.assertFalse(common.not_buildroot(None))

    def test_path(self):
        self.assertTrue(common.not_buildroot(self.Path('foo')))
        self.assertFalse(common.not_buildroot(self.Path('.')))
        self.assertTrue(common.not_buildroot(self.Path('.', Root.srcdir)))

    def test_misc(self):
        self.assertTrue(common.not_buildroot('foo'))


class TestChooseBuilder(CrossPlatformTestCase):
    def __init__(self, *args, **kwargs):
        super().__init__(clear_variables=True, *args, **kwargs)

    def test_choose(self):
        with mock.patch('bfg9000.shell.which', mock_which), \
             mock.patch('bfg9000.shell.execute', mock_execute):  # noqa
            builder = common.choose_builder(self.env, known_langs['c'],
                                            (cc.CcBuilder,), candidates='cc')
        self.assertEqual(builder.brand, 'gcc')

    def test_not_found(self):
        def bad_which(*args, **kwargs):
            if args[0] == ['cc']:
                raise IOError('badness')
            else:
                return mock_which(*args, **kwargs)

        with mock.patch('bfg9000.shell.which', bad_which), \
             mock.patch('bfg9000.shell.execute', mock_execute), \
             mock.patch('warnings.warn', lambda s: None):  # noqa
            builder = common.choose_builder(self.env, known_langs['c'],
                                            (cc.CcBuilder,), candidates='cc')
        self.assertEqual(builder.brand, 'unknown')

    def test_nonworking(self):
        def bad_execute(args, **kwargs):
            raise ValueError()

        with mock.patch('bfg9000.shell.which', mock_which), \
             mock.patch('bfg9000.shell.execute', bad_execute):  # noqa
            msg = "^no working c compiler found; tried 'cc'$"
            with self.assertRaisesRegex(IOError, msg):
                common.choose_builder(self.env, known_langs['c'],
                                      (cc.CcBuilder,), candidates='cc')
