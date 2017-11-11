import os
from . import *

from bfg9000 import shell

is_mingw = platform_name() == 'windows' and env.builder('c++').flavor == 'cc'
is_msvc = env.builder('c++').flavor == 'msvc'
pkg_config_cmd = os.getenv('PKG_CONFIG', 'pkg-config')


def pkg_config(args, path='pkgconfig'):
    env = os.environ.copy()
    env['PKG_CONFIG_PATH'] = os.path.abspath(path)
    return shell.execute([pkg_config_cmd] + args, stdout=shell.Mode.pipe,
                         env=env).rstrip()


@skip_if_backend('msbuild')
@unittest.skipIf(is_mingw, 'no libogg on mingw (yet)')
class TestPkgConfig(IntegrationTest):
    def __init__(self, *args, **kwargs):
        IntegrationTest.__init__(
            self, os.path.join(examples_dir, '11_pkg_config'), configure=False,
            install=True, *args, **kwargs
        )

    def test_configure_default(self):
        self.configure()
        self.assertExists(os.path.join('pkgconfig', 'hello.pc'))

        self.assertEqual(pkg_config(['hello', '--libs-only-l']), '-lhello')
        self.assertEqual(pkg_config(['hello', '--libs-only-l', '--static']),
                         '-lhello -logg')

    @unittest.skipIf(is_msvc, 'dual-use libraries collide on msvc')
    def test_configure_dual(self):
        self.configure(extra_args=['--enable-shared', '--enable-static'])
        self.assertExists(os.path.join('pkgconfig', 'hello.pc'))

        self.assertEqual(pkg_config(['hello', '--libs-only-l']), '-lhello')
        self.assertEqual(pkg_config(['hello', '--libs-only-l', '--static']),
                         '-lhello -linner -logg')

    def test_configure_static(self):
        self.configure(extra_args=['--disable-shared', '--enable-static'])
        self.assertExists(os.path.join('pkgconfig', 'hello.pc'))

        self.assertEqual(pkg_config(['hello', '--libs-only-l']), '-lhello')
        self.assertEqual(pkg_config(['hello', '--libs-only-l', '--static']),
                         '-lhello -linner -logg')

    def test_install(self):
        self.configure()
        self.build('install')

        extra = []
        if platform_info().has_import_library:
            extra = [os.path.join(self.libdir, import_library('hello').path)]

        self.assertDirectory(self.installdir, [
            os.path.join(self.includedir, 'hello.hpp'),
            os.path.join(self.libdir, shared_library('hello').path),
            os.path.join(self.libdir, shared_library('inner').path),
            os.path.join(self.libdir, 'pkgconfig', 'hello.pc'),
        ] + extra)

        self.configure(srcdir='pkg_config_use', installdir=None, env={
            'PKG_CONFIG_PATH': os.path.join(self.libdir, 'pkgconfig')
        })
        self.build()

        env = None
        if platform_name() == 'windows':
            env = {'PATH': os.path.abspath(self.libdir)}
        self.assertOutput([executable('program')], 'hello, library!\n',
                          env=env)


@skip_if_backend('msbuild')
@unittest.skipIf(is_mingw, 'no libogg on mingw (yet)')
class TestPkgConfigAuto(IntegrationTest):
    def __init__(self, *args, **kwargs):
        IntegrationTest.__init__(self, 'pkg_config_auto', configure=False,
                                 install=True, *args, **kwargs)

    def test_configure_default(self):
        self.configure()
        self.assertExists(os.path.join('pkgconfig', 'hello.pc'))

        self.assertEqual(pkg_config(['hello', '--libs-only-l']), '-lhello')
        self.assertEqual(pkg_config(['hello', '--libs-only-l', '--static']),
                         '-lhello -logg')

    @unittest.skipIf(is_msvc, 'dual-use libraries collide on msvc')
    def test_configure_dual(self):
        self.configure(extra_args=['--enable-shared', '--enable-static'])
        self.assertExists(os.path.join('pkgconfig', 'hello.pc'))

        self.assertEqual(pkg_config(['hello', '--libs-only-l']), '-lhello')
        self.assertEqual(pkg_config(['hello', '--libs-only-l', '--static']),
                         '-lhello -linner -logg')

    def test_configure_static(self):
        self.configure(extra_args=['--disable-shared', '--enable-static'])
        self.assertExists(os.path.join('pkgconfig', 'hello.pc'))

        self.assertEqual(pkg_config(['hello', '--libs-only-l']), '-lhello')
        self.assertEqual(pkg_config(['hello', '--libs-only-l', '--static']),
                         '-lhello -linner -logg')

    def test_install(self):
        self.configure()
        self.build('install')

        extra = []
        if platform_info().has_import_library:
            extra = [os.path.join(self.libdir, import_library('hello').path)]

        self.assertDirectory(self.installdir, [
            os.path.join(self.includedir, 'hello.hpp'),
            os.path.join(self.libdir, shared_library('hello').path),
            os.path.join(self.libdir, shared_library('inner').path),
            os.path.join(self.libdir, 'pkgconfig', 'hello.pc'),
        ] + extra)

        self.configure(srcdir='pkg_config_use', installdir=None, env={
            'PKG_CONFIG_PATH': os.path.join(self.libdir, 'pkgconfig')
        })
        self.build()

        env = None
        if platform_name() == 'windows':
            env = {'PATH': os.path.abspath(self.libdir)}
        self.assertOutput([executable('program')], 'hello, library!\n',
                          env=env)
