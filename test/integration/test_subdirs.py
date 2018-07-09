import os
import tarfile

from . import *
pjoin = os.path.join


class TestSubdirs(IntegrationTest):
    def __init__(self, *args, **kwargs):
        IntegrationTest.__init__(self, pjoin(examples_dir, '05_subdirs'),
                                 install=True, *args, **kwargs)

    def setUp(self):
        IntegrationTest.setUp(self)
        cleandir(self.installdir)

    def test_build(self):
        self.build()
        self.assertOutput([executable('sub/program')], 'hello, library!\n')

    def _check_installed(self):
        extra = []
        if env.target_platform.has_import_library:
            extra = [pjoin(self.libdir, import_library('sub/library').path)]

        self.assertDirectory(self.installdir, [
            pjoin(self.includedir, 'library.hpp'),
            pjoin(self.includedir, 'detail', 'export.hpp'),
            pjoin(self.bindir, executable('sub/program').path),
            pjoin(self.libdir, shared_library('sub/library').path),
        ] + extra)

    @skip_if_backend('msbuild')
    def test_dist(self):
        dist = output_file('05_subdirs.tar.gz')
        self.build('dist')
        self.assertExists(dist)
        with tarfile.open(self.target_path(dist)) as t:
            self.assertEqual(set(t.getnames()), {
                '05_subdirs/build.bfg',
                '05_subdirs/include/library.hpp',
                '05_subdirs/include/detail/export.hpp',
                '05_subdirs/src/library.cpp',
                '05_subdirs/src/program.cpp',
            })

    @only_if_backend('make', hide=True)
    def test_dir_sentinels(self):
        self.build()
        self.assertTrue(os.path.isfile('sub/.dir'))

    @skip_if_backend('msbuild')
    def test_install(self):
        self.build('install')
        self._check_installed()

        os.chdir(self.srcdir)
        cleandir(self.builddir)
        self.assertOutput([pjoin(self.bindir, executable('sub/program').path)],
                          'hello, library!\n')

    @skip_if_backend('msbuild')
    def test_install_existing_paths(self):
        makedirs(self.includedir, exist_ok=True)
        makedirs(self.bindir, exist_ok=True)
        makedirs(self.libdir, exist_ok=True)
        self.build('install')
        self._check_installed()

        os.chdir(self.srcdir)
        cleandir(self.builddir)
        self.assertOutput([pjoin(self.bindir, executable('sub/program').path)],
                          'hello, library!\n')

    @skip_if_backend('msbuild')
    def test_uninstall(self):
        self.build('install')
        self._check_installed()

        self.build('uninstall')
        self.assertDirectory(self.installdir, [])
