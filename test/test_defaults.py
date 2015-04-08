import shutil
import unittest

import os
import subprocess

basedir = os.path.abspath(os.path.dirname(__file__))
builddir = 'build'
bfg9000 = os.path.join(basedir, '../src/bfg9000')

def cleandir(path):
    try:
        shutil.rmtree(path)
    except:
        pass
    os.mkdir(path)

class TestDefaults(unittest.TestCase):
    def __init__(self, *args, **kwargs):
        unittest.TestCase.__init__(self, *args, **kwargs)
        self.backend = os.getenv('BACKEND', 'make')

    def setUp(self):
        os.chdir(os.path.join(basedir, os.path.join('defaults')))
        cleandir('build')
        subprocess.check_call([bfg9000, 'build', '--backend', self.backend])
        os.chdir('build')

    def test_default(self):
        subprocess.check_call([self.backend])
        self.assertEqual(subprocess.check_output(['./a']),
                         'hello, a!\n')
        self.assertEqual(subprocess.check_output(['./b']),
                         'hello, b!\n')

if __name__ == '__main__':
    unittest.main()
