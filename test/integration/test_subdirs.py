import os
import unittest

from integration import *
pjoin = os.path.join

class TestSubdirs(IntegrationTest):
    def __init__(self, *args, **kwargs):
        IntegrationTest.__init__(
            self, pjoin(examples_dir, '04_subdirs'), *args, **kwargs
        )

        self.distdir = pjoin(self.srcdir, 'dist')
        self.includedir = pjoin(self.distdir, 'include')
        self.bindir = pjoin(self.distdir, 'bin')
        self.libdir = pjoin(self.distdir, 'lib')
        self.extra_args = ['--prefix', self.distdir]

    def setUp(self):
        IntegrationTest.setUp(self)
        cleandir(self.distdir)

    def test_all(self):
        self.build()
        self.assertOutput([executable('sub/program')], 'hello, library!\n')

    def test_install(self):
        self.build('install')

        self.assertExists(pjoin(self.includedir, 'library.hpp'))
        self.assertExists(pjoin(self.bindir, executable('sub/program')))
        self.assertExists(pjoin(self.libdir, shared_library('sub/library')))

        cleandir(self.builddir)
        self.assertOutput([pjoin(self.bindir, executable('sub/program'))],
                          'hello, library!\n')

    def test_install_existing_paths(self):
        os.mkdir(self.includedir)
        os.mkdir(self.bindir)
        os.mkdir(self.libdir)
        self.build('install')

        self.assertExists(pjoin(self.includedir, 'library.hpp'))
        self.assertExists(pjoin(self.bindir, executable('sub/program')))
        self.assertExists(pjoin(self.libdir, shared_library('sub/library')))

        cleandir(self.builddir)
        self.assertOutput([pjoin(self.bindir, executable('sub/program'))],
                          'hello, library!\n')

if __name__ == '__main__':
    unittest.main()
