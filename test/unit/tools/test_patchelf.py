from . import *

from bfg9000 import options as opts
from bfg9000.file_types import Executable, StaticLibrary, SharedLibrary
from bfg9000.path import InstallRoot, Path, Root
from bfg9000.tools.patchelf import (PatchElf, local_rpath, installed_rpath,
                                    post_install)


class TestPatchElf(ToolTestCase):
    tool_type = PatchElf

    def test_env(self):
        with mock.patch('bfg9000.shell.which', return_value=['command']):
            self.assertIsInstance(self.env.tool('patchelf'), PatchElf)

    def test_rpath(self):
        self.assertEqual(self.tool('path', ['foo', 'bar']), [
            self.tool, '--set-rpath', 'foo:bar', 'path'
        ])

    def test_none(self):
        self.assertEqual(self.tool('path'), [
            self.tool, '--set-rpath', '', 'path'
        ])


class TestLocalRpath(TestCase):
    def setUp(self):
        self.env = make_env()

    def test_same_root(self):
        exe = Executable(Path('exe'), None)
        lib = SharedLibrary(Path('libfoo.so'), None)
        self.assertEqual(local_rpath(self.env, lib, exe), '$ORIGIN')

    def test_different_roots(self):
        exe = Executable(Path('exe'), None)
        lib = SharedLibrary(Path('libfoo.so', Root.srcdir), None)
        self.assertEqual(local_rpath(self.env, lib, exe),
                         Path('', Root.srcdir))

    def test_absolute(self):
        lib = SharedLibrary(Path('/lib/libfoo.so', Root.absolute), None)
        self.assertEqual(local_rpath(self.env, lib, None), Path('/lib'))

    def test_install_root(self):
        lib = SharedLibrary(Path('libfoo.so', InstallRoot.libdir), None)
        self.assertEqual(local_rpath(self.env, lib, None),
                         Path('', InstallRoot.libdir))

        lib = SharedLibrary(Path('dir/libfoo.so', InstallRoot.libdir), None)
        self.assertEqual(local_rpath(self.env, lib, None),
                         Path('dir', InstallRoot.libdir))

    def test_static(self):
        lib = StaticLibrary(Path('libfoo.a'), None)
        self.assertEqual(local_rpath(self.env, lib, None), None)

    def test_missing_output(self):
        lib = SharedLibrary(Path('libfoo.so'), None)
        self.assertRaises(ValueError, local_rpath, self.env, lib, None)


class TestInstalledRpath(TestCase):
    def setUp(self):
        self.env = make_env()
        self.install_db = MockInstallOutputs(self.env)

    def test_relative(self):
        lib = SharedLibrary(Path('libfoo.so'), None)
        self.assertEqual(installed_rpath(self.env, lib, self.install_db),
                         Path('', InstallRoot.libdir))

    def test_absolute(self):
        lib = SharedLibrary(Path('/lib/libfoo.so', Root.absolute), None)
        self.assertEqual(installed_rpath(self.env, lib, self.install_db),
                         Path('/lib'))

    def test_static(self):
        lib = StaticLibrary(Path('libfoo.a'), None)
        self.assertEqual(installed_rpath(self.env, lib, self.install_db), None)

    def test_missing(self):
        lib = SharedLibrary(Path('libfoo.so'), None)
        install_db = MockInstallOutputs(self.env, bad={lib})
        self.assertRaises(KeyError, installed_rpath, self.env, lib, install_db)


class TestPostInstall(TestCase):
    def setUp(self):
        self.env = make_env()
        with mock.patch('bfg9000.shell.which', return_value=['command']):
            self.tool = self.env.tool('patchelf')
        self.install_db = MockInstallOutputs(self.env)
        self.exe = Executable(Path('exe'), None)

    def test_empty(self):
        self.assertEqual(post_install(
            self.env, [], self.exe, self.install_db
        ), None)
        self.assertEqual(post_install(
            self.env, [opts.debug()], self.exe, self.install_db
        ), None)

    def test_shared(self):
        lib = SharedLibrary(Path('libfoo.so'), None)
        self.assertEqual(post_install(
            self.env, [opts.lib(lib)], self.exe, self.install_db
        ), [self.tool, '--set-rpath', Path('', InstallRoot.libdir),
            Path('exe', InstallRoot.bindir, True)])

    def test_shared_absolute(self):
        lib = SharedLibrary(Path('/lib/libfoo.a', Root.absolute), None)
        self.assertEqual(post_install(
            self.env, [opts.lib(lib)], self.exe, self.install_db
        ), None)

    def test_rpath_dir_always(self):
        self.assertEqual(post_install(
            self.env, [opts.rpath_dir(Path('/lib'))], self.exe, self.install_db
        ), None)

    def test_rpath_dir_installed_only(self):
        options = [opts.rpath_dir(Path('/lib'), opts.RpathWhen.installed)]
        self.assertEqual(post_install(
            self.env, options, self.exe, self.install_db
        ), [self.tool, '--set-rpath', Path('/lib'),
            Path('exe', InstallRoot.bindir, True)])

    def test_rpath_dir_uninstalled_only(self):
        options = [opts.rpath_dir(Path('/lib'), opts.RpathWhen.uninstalled)]
        self.assertEqual(post_install(
            self.env, options, self.exe, self.install_db
        ), [self.tool, '--set-rpath', '',
            Path('exe', InstallRoot.bindir, True)])

    def test_mixed(self):
        libs = [SharedLibrary(Path('libfoo.so'), None),
                StaticLibrary(Path('libbar.a'), None),
                SharedLibrary(Path('/lib/libbaz.a', Root.absolute), None)]
        self.assertEqual(post_install(
            self.env, [opts.lib(i) for i in libs], self.exe, self.install_db
        ), [self.tool, '--set-rpath',
            Path('', InstallRoot.libdir) + ':' + Path('/lib'),
            Path('exe', InstallRoot.bindir, True)])

    def test_static(self):
        lib = StaticLibrary(Path('libfoo.a'), None)
        self.assertEqual(post_install(
            self.env, [opts.lib(lib)], self.exe, self.install_db
        ), None)

    def test_string_lib(self):
        self.assertEqual(post_install(
            self.env, [opts.lib('stdc++')], self.exe, self.install_db
        ), None)
