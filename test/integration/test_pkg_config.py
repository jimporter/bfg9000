import os
from . import *

from bfg9000 import shell

pkg_config_cmd = os.getenv('PKG_CONFIG', 'pkg-config')


def pkg_config(args, path='pkgconfig'):
    env = os.environ.copy()
    env['PKG_CONFIG_PATH'] = os.path.abspath(path)
    return shell.execute([pkg_config_cmd] + args, stdout=shell.Mode.pipe,
                         env=env).rstrip()


@unittest.skipIf(platform_name() == 'windows',
                 'no pkg-config on windows (for now)')
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
                         '-lhello')

    def test_configure_dual(self):
        self.configure(extra_args=['--enable-shared', '--enable-static'])
        self.assertExists(os.path.join('pkgconfig', 'hello.pc'))

        self.assertEqual(pkg_config(['hello', '--libs-only-l']), '-lhello')
        self.assertEqual(pkg_config(['hello', '--libs-only-l', '--static']),
                         '-lhello -linner')

    def test_configure_static(self):
        self.configure(extra_args=['--disable-shared', '--enable-static'])
        self.assertExists(os.path.join('pkgconfig', 'hello.pc'))

        self.assertEqual(pkg_config(['hello', '--libs-only-l']), '-lhello')
        self.assertEqual(pkg_config(['hello', '--libs-only-l', '--static']),
                         '-lhello -linner')

    def test_install(self):
        self.configure()
        self.build('install')
        self.assertDirectory(self.installdir, [
            os.path.join(self.includedir, 'hello.hpp'),
            os.path.join(self.libdir, shared_library('hello').path),
            os.path.join(self.libdir, shared_library('inner').path),
            os.path.join(self.libdir, 'pkgconfig', 'hello.pc'),
        ])

        self.configure(srcdir='pkg_config_use', installdir=None, env={
            'PKG_CONFIG_PATH': os.path.join(self.libdir, 'pkgconfig')
        })
        self.build()
        self.assertOutput([executable('program')], 'hello, library!\n')


@unittest.skipIf(platform_name() == 'windows',
                 'no pkg-config on windows (for now)')
class TestPkgConfigAuto(IntegrationTest):
    def __init__(self, *args, **kwargs):
        IntegrationTest.__init__(self, 'pkg_config_auto', configure=False,
                                 install=True, *args, **kwargs)

    def test_configure_default(self):
        self.configure()
        self.assertExists(os.path.join('pkgconfig', 'hello.pc'))

        self.assertEqual(pkg_config(['hello', '--libs-only-l']), '-lhello')
        self.assertEqual(pkg_config(['hello', '--libs-only-l', '--static']),
                         '-lhello')

    def test_configure_dual(self):
        self.configure(extra_args=['--enable-shared', '--enable-static'])
        self.assertExists(os.path.join('pkgconfig', 'hello.pc'))

        self.assertEqual(pkg_config(['hello', '--libs-only-l']), '-lhello')
        self.assertEqual(pkg_config(['hello', '--libs-only-l', '--static']),
                         '-lhello -linner')

    def test_configure_static(self):
        self.configure(extra_args=['--disable-shared', '--enable-static'])
        self.assertExists(os.path.join('pkgconfig', 'hello.pc'))

        self.assertEqual(pkg_config(['hello', '--libs-only-l']), '-lhello')
        self.assertEqual(pkg_config(['hello', '--libs-only-l', '--static']),
                         '-lhello -linner')

    def test_install(self):
        self.configure()
        self.build('install')
        self.assertDirectory(self.installdir, [
            os.path.join(self.includedir, 'hello.hpp'),
            os.path.join(self.libdir, shared_library('hello').path),
            os.path.join(self.libdir, shared_library('inner').path),
            os.path.join(self.libdir, 'pkgconfig', 'hello.pc'),
        ])

        self.configure(srcdir='pkg_config_use', installdir=None, env={
            'PKG_CONFIG_PATH': os.path.join(self.libdir, 'pkgconfig')
        })
        self.build()
        self.assertOutput([executable('program')], 'hello, library!\n')
