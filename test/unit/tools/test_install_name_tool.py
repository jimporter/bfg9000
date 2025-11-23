from . import *

from bfg9000 import file_types, options as opts
from bfg9000.path import InstallRoot, Path
from bfg9000.tools.install_name_tool import (
    install_name, InstallNameTool, post_install
)


class TestInstallNameTool(ToolTestCase):
    tool_type = InstallNameTool

    def test_env(self):
        with mock.patch('bfg9000.shell.which', return_value=['command']):
            self.assertIsInstance(self.env.tool('install_name_tool'),
                                  InstallNameTool)

    def test_none(self):
        self.assertEqual(self.tool('path'), None)

    def test_id(self):
        self.assertEqual(self.tool('path', id='id'), [
            self.tool, '-id', 'id', 'path'
        ])

    def test_changes(self):
        self.assertEqual(self.tool('path', changes=[('old', 'new')]),
                         [self.tool, '-change', 'old', 'new', 'path'])

    def test_rpaths(self):
        self.assertEqual(self.tool('path', rpaths=[
            ('old', 'new'), ('old2', None), (None, 'new2')
        ]), [self.tool, '-rpath', 'old', 'new', '-delete_rpath', 'old2',
             '-add_rpath', 'new2', 'path'])

    def test_all(self):
        self.assertEqual(
            self.tool('path', id='id', changes=[('old', 'new')],
                      rpaths=[('old', 'new'), ('old2', None), (None, 'new2')]),
            [self.tool, '-id', 'id', '-change', 'old', 'new', '-rpath', 'old',
             'new', '-delete_rpath', 'old2', '-add_rpath', 'new2', 'path']
        )


class TestDarwinInstallName(TestCase):
    def setUp(self):
        self.env = make_env()

    def test_shared_library(self):
        lib = file_types.SharedLibrary(Path('libfoo.dylib'), 'native')
        self.assertEqual(install_name(self.env, lib),
                         os.path.join('@rpath', 'libfoo.dylib'))

    def test_installed_shared_library(self):
        lib = file_types.SharedLibrary(
            Path('libfoo.dylib', InstallRoot.libdir), 'native'
        )
        self.assertEqual(install_name(self.env, lib), lib.path)

    def test_versioned_shared_library(self):
        lib = file_types.VersionedSharedLibrary(
            Path('libfoo.1.2.3.dylib'), 'native', 'c', Path('libfoo.1.dylib'),
            Path('libfoo.dylib')
        )

        expected = os.path.join('@rpath', 'libfoo.1.dylib')
        self.assertEqual(install_name(self.env, lib), expected)
        self.assertEqual(install_name(self.env, lib.soname), expected)
        self.assertEqual(install_name(self.env, lib.link), expected)

    def test_installed_versioned_shared_library(self):
        lib = file_types.VersionedSharedLibrary(
            Path('libfoo.1.2.3.dylib', InstallRoot.libdir), 'native', 'c',
            Path('libfoo.1.dylib', InstallRoot.libdir),
            Path('libfoo.dylib', InstallRoot.libdir)
        )

        self.assertEqual(install_name(self.env, lib), lib.soname.path)
        self.assertEqual(install_name(self.env, lib.soname), lib.soname.path)
        self.assertEqual(install_name(self.env, lib.link), lib.soname.path)

    def test_static_library(self):
        lib = file_types.StaticLibrary(Path('libfoo.a'), 'native')
        self.assertRaises(TypeError, install_name, self.env, lib)
        self.assertEqual(install_name(self.env, lib, strict=False), None)


class TestPostInstall(TestCase):
    def setUp(self):
        self.env = make_env()
        with mock.patch('bfg9000.shell.which', return_value=['command']):
            self.tool = self.env.tool('install_name_tool')
        self.install_db = MockInstallOutputs(self.env)
        self.exe = file_types.Executable(Path('exe'), None)
        self.lib = file_types.SharedLibrary(Path('lib'), None)

    def test_executable(self):
        self.assertEqual(post_install(
            self.env, opts.option_list(opts.install_name_change(
                '/lib/libfoo.dylib', '/lib/libbar.dylib'
            )), self.exe, self.install_db
        ), [self.tool, '-change', '/lib/libfoo.dylib', '/lib/libbar.dylib',
            Path('exe', InstallRoot.bindir, True)])

    def test_library(self):
        self.assertEqual(post_install(
            self.env, opts.option_list(opts.install_name_change(
                '/lib/libfoo.dylib', '/lib/libbar.dylib'
            )), self.lib, self.install_db, is_library=True
        ), [self.tool, '-id', Path('lib', InstallRoot.libdir), '-change',
            '/lib/libfoo.dylib', '/lib/libbar.dylib',
            Path('lib', InstallRoot.libdir, True)])

    def test_empty(self):
        self.assertEqual(post_install(
            self.env, opts.option_list(), self.exe, self.install_db
        ), None)
        self.assertEqual(post_install(
            self.env, opts.option_list(opts.debug()), self.exe, self.install_db
        ), None)
