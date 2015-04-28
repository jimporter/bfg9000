import os.path
import subprocess
import unittest

from integration import IntegrationTest, cleandir

class TestInstall(IntegrationTest):
    def __init__(self, *args, **kwargs):
        IntegrationTest.__init__(self, 'install', *args, **kwargs)
        self.distdir = os.path.join(self.srcdir, 'dist')
        self.extra_args = ['--prefix', self.distdir]

    def setUp(self):
        IntegrationTest.setUp(self)
        cleandir(self.distdir)

    def test_all(self):
        subprocess.check_call([self.backend])
        self.assertEqual(subprocess.check_output(
            [os.path.join('bin', 'program')],
        ), 'hello, library!\n')

    def test_install(self):
        subprocess.check_call([self.backend, 'install'])
        cleandir(self.builddir)

        self.assertTrue(os.path.exists(os.path.join(
            self.distdir, 'include', 'library.hpp'
        )))
        # TODO: Support other platform naming schemes
        self.assertTrue(os.path.exists(os.path.join(
            self.distdir, 'bin', 'program'
        )))
        self.assertTrue(os.path.exists(os.path.join(
            self.distdir, 'lib', 'liblibrary.so'
        )))

        self.assertEqual(subprocess.check_output(
            [os.path.join(self.distdir, 'bin', 'program')]
        ), 'hello, library!\n')

if __name__ == '__main__':
    unittest.main()
