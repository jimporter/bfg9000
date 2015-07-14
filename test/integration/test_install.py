import os.path
import unittest

from bfg9000.makedirs import makedirs
from integration import *
pjoin = os.path.join

class TestInstall(IntegrationTest):
    def __init__(self, *args, **kwargs):
        IntegrationTest.__init__(self, 'install', dist=True, *args, **kwargs)

    def setUp(self):
        IntegrationTest.setUp(self)
        cleandir(self.distdir)

    def test_all(self):
        self.build()
        self.assertOutput([executable('program')], 'hello, library!\n')

    def test_install(self):
        self.build('install')

        self.assertExists(pjoin(self.includedir, 'library.hpp'))
        self.assertExists(pjoin(self.bindir, executable('program')))
        self.assertExists(pjoin(self.libdir, shared_library('library')))

        os.chdir(self.srcdir)
        cleandir(self.builddir)
        self.assertOutput([pjoin(self.bindir, executable('program'))],
                          'hello, library!\n')

    def test_install_existing_paths(self):
        makedirs(self.includedir, exist_ok=True)
        makedirs(self.bindir, exist_ok=True)
        makedirs(self.libdir, exist_ok=True)
        self.build('install')

        self.assertExists(pjoin(self.includedir, 'library.hpp'))
        self.assertExists(pjoin(self.bindir, executable('program')))
        self.assertExists(pjoin(self.libdir, shared_library('library')))

        os.chdir(self.srcdir)
        cleandir(self.builddir)
        self.assertOutput([pjoin(self.bindir, executable('program'))],
                          'hello, library!\n')

if __name__ == '__main__':
    unittest.main()
