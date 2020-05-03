from . import *

from bfg9000 import options as opts
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


class TestPkgConfigPackage(ToolTestCase):
    tool_type = PkgConfig

    def tearDown(self):
        PkgConfigPackage._call._reset()

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
