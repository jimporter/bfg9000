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

class TestSubdirs(unittest.TestCase):
    def __init__(self, *args, **kwargs):
        unittest.TestCase.__init__(self, *args, **kwargs)
        self.backend = os.getenv('BACKEND', 'make')

    def setUp(self):
        os.chdir(os.path.join(basedir, os.path.join('subdirs')))
        cleandir('build')
        subprocess.check_call([bfg9000, 'build', '--backend', self.backend])

    def test_all(self):
        os.chdir('build')
        subprocess.check_call([self.backend, 'subdirs'])
        self.assertEqual(subprocess.check_output(['./subdirs']),
                         'hello, world!\n')

if __name__ == '__main__':
    unittest.main()
