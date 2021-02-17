import re
from unittest import mock

from .. import *

from bfg9000 import shell
from bfg9000.languages import Languages
from bfg9000.path import Root
from bfg9000.tools import cc, common

known_langs = Languages()
with known_langs.make('c') as x:
    x.vars(compiler='CC', flags='CFLAGS')


def mock_which(*args, **kwargs):
    return ['command']


def mock_execute(args, **kwargs):
    if '--version' in args:
        return ('g++ (Ubuntu 5.4.0-6ubuntu1~16.04.6) 5.4.0 20160609\n' +
                'Copyright (C) 2015 Free Software Foundation, Inc.')
    elif '-Wl,--version' in args:
        return '', '/usr/bin/ld --version\n'
    elif '-print-search-dirs' in args:
        return 'libraries: =/lib/search/dir1:/lib/search/dir2\n'
    elif '-print-sysroot' in args:
        return '/'
    elif '--verbose' in args:
        return 'SEARCH_DIR("/usr")\n'
    raise OSError('unknown command: {}'.format(args))


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


class TestMakeCommandConverter(TestCase):
    def test_simple(self):
        converter = common.make_command_converter([('gcc', 'g++')])
        self.assertEqual(converter('gcc'), 'g++')
        self.assertEqual(converter('foo-gcc'), 'foo-g++')
        self.assertEqual(converter('gcc-foo'), 'g++-foo')

        self.assertEqual(converter('foo'), None)
        self.assertEqual(converter('foogcc'), None)
        self.assertEqual(converter('gccfoo'), None)

    def test_order(self):
        converter = common.make_command_converter([
            ('clang-cl', 'clang-cl++'),
            ('clang', 'clang++'),
        ])

        self.assertEqual(converter('clang'), 'clang++')
        self.assertEqual(converter('foo-clang'), 'foo-clang++')
        self.assertEqual(converter('clang-foo'), 'clang++-foo')

        self.assertEqual(converter('clang-cl'), 'clang-cl++')
        self.assertEqual(converter('foo-clang-cl'), 'foo-clang-cl++')
        self.assertEqual(converter('clang-cl-foo'), 'clang-cl++-foo')

        self.assertEqual(converter('foo'), None)

    def test_regex(self):
        converter = common.make_command_converter([
            (re.compile(r'gcc(?:-[\d.]+)?(?:-(?:posix|win32))?'), 'windres'),
        ])

        self.assertEqual(converter('gcc'), 'windres')
        self.assertEqual(converter('gcc-9.1'), 'windres')
        self.assertEqual(converter('gcc-posix'), 'windres')
        self.assertEqual(converter('gcc-win32'), 'windres')
        self.assertEqual(converter('gcc-9.1-posix'), 'windres')
        self.assertEqual(converter('gcc-9.1-win32'), 'windres')
        self.assertEqual(converter('i686-w64-mingw32-gcc-9.1-win32'),
                         'i686-w64-mingw32-windres')

    def test_pair(self):
        c_to_cxx, cxx_to_c = common.make_command_converter_pair([
            ('gcc', 'g++'),
        ])

        self.assertEqual(c_to_cxx('gcc'), 'g++')
        self.assertEqual(c_to_cxx('foo-gcc'), 'foo-g++')
        self.assertEqual(c_to_cxx('gcc-foo'), 'g++-foo')
        self.assertEqual(c_to_cxx('foo'), None)
        self.assertEqual(c_to_cxx('foogcc'), None)
        self.assertEqual(c_to_cxx('gccfoo'), None)

        self.assertEqual(cxx_to_c('g++'), 'gcc')
        self.assertEqual(cxx_to_c('foo-g++'), 'foo-gcc')
        self.assertEqual(cxx_to_c('g++-foo'), 'gcc-foo')
        self.assertEqual(cxx_to_c('foo'), None)
        self.assertEqual(cxx_to_c('foog++'), None)
        self.assertEqual(cxx_to_c('g++foo'), None)

    def test_invalid_regex(self):
        with self.assertRaises(re.error):
            common.make_command_converter([(re.compile(r'([\d.]+)'), '')])


class TestNotBuildroot(CrossPlatformTestCase):
    def test_none(self):
        self.assertFalse(common.not_buildroot(None))

    def test_path(self):
        self.assertTrue(common.not_buildroot(self.Path('foo')))
        self.assertFalse(common.not_buildroot(self.Path('.')))
        self.assertTrue(common.not_buildroot(self.Path('.', Root.srcdir)))

    def test_misc(self):
        self.assertTrue(common.not_buildroot('foo'))


class TestCommand(TestCase):
    class MyCommand(common.Command):
        def _call(self, cmd, *args):
            return cmd + list(args)

    def setUp(self):
        self.env = make_env(platform='linux')
        self.cmd = self.MyCommand(self.env, command=['mycmd', ['command']])

    def test_call(self):
        self.assertEqual(self.cmd(), [self.cmd])
        self.assertEqual(self.cmd('--foo'), [self.cmd, '--foo'])
        self.assertEqual(self.cmd(cmd='cmd'), ['cmd'])
        self.assertEqual(self.cmd('--foo', cmd='cmd'), ['cmd', '--foo'])

    def test_run(self):
        M = shell.Mode

        def assert_called(mock, command, **kwargs):
            kwargs.update({'env': self.env.variables,
                           'base_dirs': self.env.base_dirs})
            mock.assert_called_once_with(command, **kwargs)

        with mock.patch('bfg9000.shell.execute') as e:
            self.cmd.run()
            assert_called(e, ['command'], stdout=M.pipe, stderr=M.devnull)
        with mock.patch('bfg9000.shell.execute') as e:
            self.cmd.run('--foo')
            assert_called(e, ['command', '--foo'], stdout=M.pipe,
                          stderr=M.devnull)
        with mock.patch('bfg9000.shell.execute') as e:
            self.cmd.run(stdout=M.normal)
            assert_called(e, ['command'], stdout=M.normal)
        with mock.patch('bfg9000.shell.execute') as e:
            self.cmd.run(stdout=M.normal, stderr='err')
            assert_called(e, ['command'], stdout=M.normal, stderr='err')
        with mock.patch('bfg9000.shell.execute') as e:
            self.cmd.run(stdout='out')
            assert_called(e, ['command'], stdout='out', stderr=M.devnull)
        with mock.patch('bfg9000.shell.execute') as e:
            self.cmd.run(stdout='out', stderr='err')
            assert_called(e, ['command'], stdout='out', stderr='err')


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
