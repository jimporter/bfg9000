import os.path
from . import *

library_path = {
    'windows': 'PATH',
    'linux': 'LD_LIBRARY_PATH',
    'darwin': 'DYLD_LIBRARY_PATH',
}


@unittest.skipIf(platform_name() == 'windows',
                 'no pkg-config on windows (for now)')
class TestPkgConfig(IntegrationTest):
    def __init__(self, *args, **kwargs):
        IntegrationTest.__init__(
            self, os.path.join(examples_dir, '11_pkg_config'), install=True,
            *args, **kwargs
        )

    def test_build(self):
        self.build(shared_library('hello'))
        self.assertExists(os.path.join('pkgconfig', 'hello.pc'))

    def test_install(self):
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
        self.assertOutput([executable('program')], 'hello, library!\n',
                          env={library_path[platform_name()]: self.libdir})


@unittest.skipIf(platform_name() == 'windows',
                 'no pkg-config on windows (for now)')
class TestPkgConfigAuto(IntegrationTest):
    def __init__(self, *args, **kwargs):
        IntegrationTest.__init__(self, 'pkg_config_auto', install=True, *args,
                                 **kwargs)

    def test_build(self):
        self.build(shared_library('hello'))
        self.assertExists(os.path.join('pkgconfig', 'hello.pc'))

    def test_install(self):
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
        self.assertOutput([executable('program')], 'hello, library!\n',
                          env={library_path[platform_name()]: self.libdir})
