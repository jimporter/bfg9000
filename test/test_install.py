import os.path
import subprocess
import unittest

from integration import IntegrationTest, cleandir

class TestInstall(IntegrationTest):
    def __init__(self, *args, **kwargs):
        IntegrationTest.__init__(self, 'install', *args, **kwargs)
        self.extra_args = ['--prefix', 'dist']

    def setUp(self):
        IntegrationTest.setUp(self)
        cleandir(os.path.join(self.srcdir, 'dist'))

    def test_install(self):
        subprocess.check_call([self.backend, 'install'])

        self.assertTrue(os.path.exists(os.path.join(
            self.srcdir, 'dist', 'include', 'library.hpp'
        )))
        # TODO: Support other platform naming schemes
        self.assertTrue(os.path.exists(os.path.join(
            self.srcdir, 'dist', 'bin', 'program'
        )))
        self.assertTrue(os.path.exists(os.path.join(
            self.srcdir, 'dist', 'lib', 'liblibrary.so'
        )))

        self.assertEqual(subprocess.check_output(
            [os.path.join(self.srcdir, 'dist', 'bin', 'program')]
        ), 'hello, library!\n')

if __name__ == '__main__':
    unittest.main()
