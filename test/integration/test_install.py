import os.path
import subprocess
import unittest

from integration import *

class TestInstall(IntegrationTest):
    def __init__(self, *args, **kwargs):
        IntegrationTest.__init__(self, 'install', *args, **kwargs)
        self.distdir = os.path.join(self.srcdir, 'dist')
        self.extra_args = ['--prefix', self.distdir]

    def setUp(self):
        IntegrationTest.setUp(self)
        cleandir(self.distdir)

    def test_all(self):
        self.build()
        self.assertOutput([executable('program')], 'hello, library!\n')

    def test_install(self):
        subprocess.check_call([self.backend, 'install'])

        self.assertTrue(os.path.exists(os.path.join(
            self.distdir, 'include', 'library.hpp'
        )))
        self.assertTrue(os.path.exists(os.path.join(
            self.distdir, executable('program')
        )))
        self.assertTrue(os.path.exists(os.path.join(
            self.distdir, shared_library('library')
        )))

        cleandir(self.builddir)
        self.assertOutput(
            [os.path.join(self.distdir, executable('program'))],
            'hello, library!\n'
        )

if __name__ == '__main__':
    unittest.main()
