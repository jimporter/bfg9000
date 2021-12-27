from unittest import mock

from ... import *
from .. import MockInstallOutputs
from .common import known_langs, mock_execute, mock_which

from bfg9000 import options as opts
from bfg9000.builtins.install import installify
from bfg9000.file_types import *
from bfg9000.tools.cc import CcBuilder
from bfg9000.packages import Framework
from bfg9000.path import InstallRoot, Path, Root


class TestCcLinker(CrossPlatformTestCase):
    shared = False

    def __init__(self, *args, **kwargs):
        super().__init__(clear_variables=True, *args, **kwargs)

    def _get_linker(self, lang):
        with mock.patch('bfg9000.shell.which', mock_which), \
             mock.patch('bfg9000.shell.execute', mock_execute):
            return CcBuilder(self.env, known_langs[lang], ['c++'],
                             True, 'version').linker('executable')

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

    def test_can_link(self):
        fmt = self.env.target_platform.object_format
        self.assertTrue(self.linker.can_link(fmt, ['c', 'c++']))
        self.assertTrue(self.linker.can_link(fmt, ['goofy']))
        self.assertFalse(self.linker.can_link('goofy', ['c']))
        self.assertFalse(self.linker.can_link(fmt, ['objc++']))

    def test_sysroot(self):
        def mock_execute(*args, **kwargs):
            raise OSError()

        with mock.patch('bfg9000.shell.execute', mock_execute):
            self.assertRegex(self.linker.sysroot(), '/?')
        with mock.patch('bfg9000.shell.execute', mock_execute), \
             self.assertRaises(OSError):
            self.linker.sysroot(True)

    def test_search_dirs(self):
        def mock_execute(*args, **kwargs):
            raise OSError()

        with mock.patch('bfg9000.shell.execute', mock_execute):
            self.assertEqual(self.linker.search_dirs(), [])
        with mock.patch('bfg9000.shell.execute', mock_execute), \
             self.assertRaises(OSError):
            self.linker.search_dirs(True)

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
        ), output=output), ['-L' + libdir] + rpath + soname)
        self.assertEqual(self.linker.flags(opts.option_list(
            opts.lib(SharedLibrary(srclib, 'native'))
        ), output=output), ['-L' + srclibdir] + srcdir_rpath + soname)

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
                ), output=output),
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

        if self.env.target_platform.family == 'windows':
            mingw_lib = self.Path('/path/to/lib/foo.lib')
            self.assertEqual(self.linker.flags(opts.option_list(
                opts.lib(Library(mingw_lib, 'native'))
            )), ['-L' + libdir])

        # Non-standard library name
        goofy_lib = self.Path('/path/to/lib/foo.goofy')
        self.assertEqual(self.linker.flags(opts.option_list(
            opts.lib(Library(goofy_lib, 'native'))
        )), [])
        with self.assertRaises(ValueError):
            self.linker.flags(opts.option_list(
                opts.lib(Library(goofy_lib, 'native'))
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
        ), output=output), ['-L' + libdir] + rpath + soname)

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

    def test_flags_entry_point(self):
        java_linker = self._get_linker('java')
        self.assertEqual(java_linker.flags(opts.option_list(
            opts.entry_point('symbol')
        )), ['--main=symbol'])

        self.assertEqual(self.linker.flags(opts.option_list(
            opts.entry_point('symbol')
        )), ['-Wl,-e,symbol'])

    def test_flags_string(self):
        self.assertEqual(self.linker.flags(opts.option_list('-v')), ['-v'])

    def test_flags_gui(self):
        self.assertEqual(
            self.linker.flags(opts.option_list(opts.gui())),
            (['-mwindows'] if self.env.target_platform.family == 'windows'
             else [])
        )

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

        if self.env.target_platform.family == 'windows':
            mingw_lib = self.Path('/path/to/lib/foo.lib')
            self.assertEqual(self.linker.lib_flags(opts.option_list(
                opts.lib(Library(mingw_lib, 'native'))
            )), ['-lfoo'])

        # Non-standard library name
        goofy_lib = self.Path('/path/to/lib/foo.goofy')
        self.assertEqual(self.linker.lib_flags(opts.option_list(
            opts.lib(Library(goofy_lib, 'native'))
        )), [goofy_lib])
        with self.assertRaises(ValueError):
            self.linker.lib_flags(opts.option_list(
                opts.lib(Library(goofy_lib, 'native'))
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

        install_outputs = MockInstallOutputs(self.env)
        with mock.patch('bfg9000.shell.which', return_value=['command']):
            # Local shared lib
            fn = self.linker.post_install(opts.option_list(opts.lib(shared)),
                                          output, None)
            self.assertEqual(fn(install_outputs), [
                self.env.tool('patchelf'), '--set-rpath',
                self.Path('', InstallRoot.libdir), installify(output).path
            ])

            # Absolute shared lib
            fn = self.linker.post_install(
                opts.option_list(opts.lib(shared_abs)), output, None
            )
            self.assertEqual(fn(install_outputs), None)

            # Local static lib
            fn = self.linker.post_install(opts.option_list(opts.lib(static)),
                                          output, None)
            self.assertEqual(fn(install_outputs), None)

            # Explicit rpath dir
            fn = self.linker.post_install(opts.option_list(
                opts.rpath_dir(self.Path('/path'))
            ), output, None)
            self.assertEqual(fn(install_outputs), None)

            # Mixed
            fn = self.linker.post_install(opts.option_list(
                opts.lib(shared), opts.lib(shared_abs), opts.lib(static),
                opts.rpath_dir(self.Path('/path')),
                opts.rpath_dir(self.Path('/path/to'))
            ), output, None)
            self.assertEqual(fn(install_outputs), [
                self.env.tool('patchelf'), '--set-rpath',
                (self.Path('', InstallRoot.libdir) + ':' +
                 self.Path('/path/to') + ':' + self.Path('/path')),
                installify(output).path
            ])

    @only_if_platform('macos', hide=True)
    def test_post_installed_macos(self):
        output = self._get_output_file()
        installed = installify(output).path
        deplib = SharedLibrary(self.Path('libfoo.so'), 'native')

        install_outputs = MockInstallOutputs(self.env)
        with mock.patch('bfg9000.shell.which', return_value=['command']):
            install_name_tool = self.env.tool('install_name_tool')

            # No runtime deps
            fn = self.linker.post_install(opts.option_list(), output, None)
            self.assertEqual(fn(install_outputs), [
                install_name_tool, '-id', installed.cross(self.env), installed
            ] if self.shared else None)

            fn = self.linker.post_install(opts.option_list(
                opts.install_name_change('old.dylib', 'new.dylib')
            ), output, None)
            self.assertEqual(fn(install_outputs), (
                [install_name_tool] +
                (['-id', installed.cross(self.env)] if self.shared else []) +
                ['-change', 'old.dylib', 'new.dylib', installed]
            ))

            # Dependent on local shared lib
            output.runtime_deps = [deplib]
            fn = self.linker.post_install(
                opts.option_list(opts.lib(deplib)), output, None
            )
            self.assertEqual(fn(install_outputs), (
                [install_name_tool] +
                (['-id', installed.cross(self.env)] if self.shared else []) +
                ['-change', deplib.path.string(self.env.base_dirs),
                 installify(deplib, cross=self.env).path, installed]
            ))


class TestCcSharedLinker(TestCcLinker):
    shared = True

    def _get_linker(self, lang):
        with mock.patch('bfg9000.shell.which', mock_which), \
             mock.patch('bfg9000.shell.execute', mock_execute):
            return CcBuilder(self.env, known_langs[lang], ['c++'],
                             True, 'version').linker('shared_library')

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
