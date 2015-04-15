import shutil
import unittest

import os
import subprocess

basedir = os.path.abspath(os.path.dirname(__file__))
bfg9000 = os.path.join(basedir, '../src/bfg9000')

def cleandir(path):
    try:
        shutil.rmtree(path)
    except:
        pass
    os.mkdir(path)

class IntegrationTest(unittest.TestCase):
    def __init__(self, srcdir, *args, **kwargs):
        unittest.TestCase.__init__(self, *args, **kwargs)
        self.srcdir = os.path.join(basedir, srcdir)
        self.extra_args = []
        self.backend = os.getenv('BACKEND', 'make')

    def setUp(self):
        os.chdir(self.srcdir)
        cleandir('build')
        subprocess.check_call([bfg9000, 'build', '--backend', self.backend] +
                              self.extra_args)
        os.chdir('build')

