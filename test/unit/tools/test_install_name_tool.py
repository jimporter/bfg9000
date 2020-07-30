from . import *

from bfg9000 import file_types, options as opts
from bfg9000.path import InstallRoot, Path
from bfg9000.tools.install_name_tool import (
    darwin_install_name, InstallNameTool, post_install
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
        self.assertEqual(self.tool('path', changes=['foo', 'bar']), [
            self.tool, '-change', 'foo', '-change', 'bar', 'path'
        ])

    def test_all(self):
        self.assertEqual(self.tool('path', id='id', changes=['changes']), [
            self.tool, '-id', 'id', '-change',
            'changes', 'path'
        ])


class TestDarwinInstallName(TestCase):
    def setUp(self):
        self.env = make_env()

    def test_shared_library(self):
        lib = file_types.SharedLibrary(Path('libfoo.dylib'), 'native')
        self.assertEqual(darwin_install_name(lib, self.env),
                         self.env.builddir.append('libfoo.dylib').string())

    def test_versioned_shared_library(self):
        lib = file_types.VersionedSharedLibrary(
            Path('libfoo.1.2.3.dylib'), 'native', 'c', Path('libfoo.1.dylib'),
            Path('libfoo.dylib')
        )
        self.assertEqual(darwin_install_name(lib, self.env),
                         self.env.builddir.append('libfoo.1.dylib').string())
        self.assertEqual(darwin_install_name(lib.soname, self.env),
                         self.env.builddir.append('libfoo.1.dylib').string())
        self.assertEqual(darwin_install_name(lib.link, self.env),
                         self.env.builddir.append('libfoo.1.dylib').string())

    def test_static_library(self):
        lib = file_types.StaticLibrary(Path('libfoo.a'), 'native')
        self.assertRaises(TypeError, darwin_install_name, lib, self.env)
        self.assertEqual(darwin_install_name(lib, self.env, False), None)


class TestPostInstall(TestCase):
    def setUp(self):
        self.env = make_env()
        with mock.patch('bfg9000.shell.which', return_value=['command']):
            self.tool = self.env.tool('install_name_tool')
        self.install_db = MockInstallOutputs(self.env)
        self.exe = file_types.Executable(Path('exe'), None)

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
            )), self.exe, self.install_db, is_library=True
        ), [self.tool, '-id', Path('exe', InstallRoot.bindir), '-change',
            '/lib/libfoo.dylib', '/lib/libbar.dylib',
            Path('exe', InstallRoot.bindir, True)])

    def test_empty(self):
        self.assertEqual(post_install(
            self.env, opts.option_list(), self.exe, self.install_db
        ), None)
        self.assertEqual(post_install(
            self.env, opts.option_list(opts.debug()), self.exe, self.install_db
        ), None)
