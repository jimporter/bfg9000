from . import *

from bfg9000 import options as opts
from bfg9000.iterutils import first
from bfg9000.path import Path
from bfg9000.shell import CalledProcessError
from bfg9000.tools.pkg_config import PkgConfig, PkgConfigPackage
from bfg9000.packages import PackageKind
from bfg9000.versioning import SpecifierSet, Version


def mock_execute(args, **kwargs):
    name = args[1]
    if name.endswith('-uninstalled'):
        raise CalledProcessError(1, args)

    if args[2] == '--modversion':
        return '1.0\n'
    elif args[2] == '--print-requires':
        return '\n'
    elif args[2] == '--variable=install_names':
        return '/usr/lib/lib{}.dylib'.format(name)
    elif args[2] == '--cflags':
        return '-I/usr/include\n'
    elif args[2] == '--libs-only-L':
        return '-L/usr/lib\n'
    elif args[2] == '--libs-only-l':
        return '-l{}\n'.format(name)


def mock_execute_uninst(args, *, env=None, **kwargs):
    if not env or env.get('PKG_CONFIG_DISABLE_UNINSTALLED') != '1':
        name = args[1].replace('-uninstalled', '')
        if args[2] == '--libs-only-L':
            return '-L/path/to/build/{}\n'.format(name)
        elif args[2] == '--variable=install_names':
            return '/path/to/build/{0}/lib{0}.dylib'.format(name)
    return mock_execute(args, **kwargs)


def mock_execute_requires(args, **kwargs):
    if args[1].startswith('foo') and args[2] == '--print-requires':
        return 'bar\nbaz >= 1.0\n'
    return mock_execute_uninst(args, **kwargs)


def mock_execute_cc(args, **kwargs):
    if args[-1] == '--version':
        return 'version\n'
    raise OSError('bad option')


class TestPkgConfig(TestCase):
    def test_implicit(self):
        env = make_env(platform='linux', clear_variables=True)
        with mock.patch('bfg9000.tools.pkg_config.which') as mwhich, \
             mock.patch('bfg9000.tools.pkg_config.check_which',
                        lambda names, env: [first(names)]), \
             mock.patch('bfg9000.shell.which', return_value=['cc']), \
             mock.patch('bfg9000.shell.execute', mock_execute_cc):  # noqa
            self.assertEqual(PkgConfig(env).command, ['pkg-config'])
            mwhich.assert_not_called()

    def test_explicit(self):
        env = make_env(platform='linux', clear_variables=True,
                       variables={'PKG_CONFIG': 'pkgconf'})
        with mock.patch('bfg9000.tools.pkg_config.which') as mwhich, \
             mock.patch('bfg9000.tools.pkg_config.check_which',
                        lambda names, env: [first(names)]), \
             mock.patch('bfg9000.shell.which', return_value=['cc']), \
             mock.patch('bfg9000.shell.execute', mock_execute_cc):  # noqa
            self.assertEqual(PkgConfig(env).command, ['pkgconf'])
            mwhich.assert_not_called()

    def test_guess_sibling(self):
        env = make_env(platform='linux', clear_variables=True,
                       variables={'CC': 'i686-w64-mingw32-gcc-99'})
        with mock.patch('bfg9000.tools.pkg_config.which',
                        lambda names, env: [first(names)]), \
             mock.patch('bfg9000.tools.pkg_config.check_which') as mcwhich, \
             mock.patch('bfg9000.shell.which',
                        return_value=['i686-w64-mingw32-gcc-99']), \
             mock.patch('bfg9000.shell.execute', mock_execute_cc), \
             mock.patch('bfg9000.log.info'):  # noqa
            self.assertEqual(PkgConfig(env).command,
                             ['i686-w64-mingw32-pkg-config'])
            mcwhich.assert_not_called()

    def test_guess_sibling_nonexist(self):
        env = make_env(platform='linux', clear_variables=True,
                       variables={'CC': 'i686-w64-mingw32-gcc-99'})
        with mock.patch('bfg9000.tools.pkg_config.which',
                        lambda names, env: [first(names)]), \
             mock.patch('bfg9000.tools.pkg_config.check_which') as mcwhich, \
             mock.patch('bfg9000.shell.which', side_effect=IOError()), \
             mock.patch('bfg9000.log.info'), \
             mock.patch('warnings.warn'):  # noqa
            self.assertEqual(PkgConfig(env).command,
                             ['i686-w64-mingw32-pkg-config'])
            mcwhich.assert_not_called()

    def test_guess_sibling_indirect(self):
        env = make_env(platform='linux', clear_variables=True,
                       variables={'CXX': 'i686-w64-mingw32-g++-99'})
        with mock.patch('bfg9000.tools.pkg_config.which',
                        lambda names, env: [first(names)]), \
             mock.patch('bfg9000.tools.pkg_config.check_which') as mcwhich, \
             mock.patch('bfg9000.shell.which',
                        return_value=['i686-w64-mingw32-gcc-99']), \
             mock.patch('bfg9000.shell.execute', mock_execute_cc), \
             mock.patch('bfg9000.log.info'):  # noqa
            self.assertEqual(PkgConfig(env).command,
                             ['i686-w64-mingw32-pkg-config'])
            mcwhich.assert_not_called()

    def test_guess_sibling_matches_default(self):
        env = make_env(platform='linux', clear_variables=True,
                       variables={'CC': 'gcc'})
        with mock.patch('bfg9000.tools.pkg_config.which') as mwhich, \
             mock.patch('bfg9000.tools.pkg_config.check_which',
                        lambda names, env: [first(names)]), \
             mock.patch('bfg9000.shell.which', return_value=['cc']), \
             mock.patch('bfg9000.shell.execute', mock_execute_cc):  # noqa
            self.assertEqual(PkgConfig(env).command, ['pkg-config'])
            mwhich.assert_not_called()

    def test_guess_sibling_error(self):
        def mock_check_which(*args, **kwargs):
            raise IOError('bad')

        env = make_env(platform='linux', clear_variables=True,
                       variables={'CC': 'i686-w64-mingw32-gcc-99'})
        with mock.patch('bfg9000.tools.pkg_config.which',
                        mock_check_which), \
             mock.patch('bfg9000.tools.pkg_config.check_which',
                        return_value=['pkgconf']), \
             mock.patch('bfg9000.log.info'), \
             mock.patch('warnings.warn'):  # noqa
            self.assertEqual(PkgConfig(env).command, ['pkgconf'])


class TestPkgConfigPackage(ToolTestCase):
    tool_type = PkgConfig

    def setUp(self):
        with mock.patch('bfg9000.shell.execute', mock_execute_cc):
            super().setUp()

    def test_create(self):
        specifier = SpecifierSet('')
        with mock.patch('bfg9000.shell.execute', mock_execute):
            pkg = PkgConfigPackage('foo', 'elf', specifier, PackageKind.shared,
                                   self.tool)
            self.assertEqual(pkg.name, 'foo')
            self.assertEqual(pkg.format, 'elf')
            self.assertEqual(pkg.version, Version('1.0'))
            self.assertEqual(pkg.specifier, specifier)
            self.assertEqual(pkg.static, False)

    def test_compile_options(self):
        compiler = AttrDict(flavor='gcc')
        with mock.patch('bfg9000.shell.execute', mock_execute):
            pkg = PkgConfigPackage('foo', 'elf', SpecifierSet(''),
                                   PackageKind.shared, self.tool)

            self.assertEqual(pkg.compile_options(compiler),
                             opts.option_list(['-I/usr/include']))

    def test_link_options_coff(self):
        linker = AttrDict(flavor='gcc', builder=AttrDict(object_format='coff'))
        with mock.patch('bfg9000.shell.execute', mock_execute):
            pkg = PkgConfigPackage('foo', 'elf', SpecifierSet(''),
                                   PackageKind.shared, self.tool)

            self.assertEqual(pkg.link_options(linker), opts.option_list(
                '-L/usr/lib', opts.lib_literal('-lfoo')
            ))

    def test_link_options_elf(self):
        linker = AttrDict(flavor='gcc', builder=AttrDict(object_format='elf'))
        with mock.patch('bfg9000.shell.execute', mock_execute):
            pkg = PkgConfigPackage('foo', 'elf', SpecifierSet(''),
                                   PackageKind.shared, self.tool)

            self.assertEqual(pkg.link_options(linker), opts.option_list(
                '-L/usr/lib', opts.lib_literal('-lfoo'),
                opts.rpath_dir(Path('/usr/lib'))
            ))

    def test_link_options_elf_uninst(self):
        linker = AttrDict(flavor='gcc', builder=AttrDict(object_format='elf'))
        with mock.patch('bfg9000.shell.execute', mock_execute_uninst):
            pkg = PkgConfigPackage('foo', 'elf', SpecifierSet(''),
                                   PackageKind.shared, self.tool)

            self.assertEqual(pkg.link_options(linker), opts.option_list(
                '-L/path/to/build/foo', opts.lib_literal('-lfoo'),
                opts.rpath_dir(Path('/path/to/build/foo'), 'uninstalled'),
                opts.rpath_dir(Path('/usr/lib'), 'installed')
            ))

    def test_link_options_macho(self):
        linker = AttrDict(flavor='gcc',
                          builder=AttrDict(object_format='mach-o'))
        with mock.patch('bfg9000.shell.execute', mock_execute):
            pkg = PkgConfigPackage('foo', 'elf', SpecifierSet(''),
                                   PackageKind.shared, self.tool)

            self.assertEqual(pkg.link_options(linker), opts.option_list(
                '-L/usr/lib', opts.lib_literal('-lfoo')
            ))

    def test_link_options_macho_uninst(self):
        linker = AttrDict(flavor='gcc',
                          builder=AttrDict(object_format='mach-o'))
        with mock.patch('bfg9000.shell.execute', mock_execute_uninst):
            pkg = PkgConfigPackage('foo', 'elf', SpecifierSet(''),
                                   PackageKind.shared, self.tool)

            self.assertEqual(pkg.link_options(linker), opts.option_list(
                '-L/path/to/build/foo', opts.lib_literal('-lfoo'),
                opts.install_name_change('/path/to/build/foo/libfoo.dylib',
                                         '/usr/lib/libfoo.dylib')
            ))

    def test_link_options_macho_requires(self):
        linker = AttrDict(flavor='gcc',
                          builder=AttrDict(object_format='mach-o'))
        with mock.patch('bfg9000.shell.execute', mock_execute_requires):
            pkg = PkgConfigPackage('foo', 'elf', SpecifierSet(''),
                                   PackageKind.shared, self.tool)

            self.assertEqual(pkg.link_options(linker), opts.option_list(
                '-L/path/to/build/foo', opts.lib_literal('-lfoo'),
                opts.install_name_change('/path/to/build/foo/libfoo.dylib',
                                         '/usr/lib/libfoo.dylib'),
                opts.install_name_change('/path/to/build/bar/libbar.dylib',
                                         '/usr/lib/libbar.dylib'),
                opts.install_name_change('/path/to/build/baz/libbaz.dylib',
                                         '/usr/lib/libbaz.dylib'),
            ))
