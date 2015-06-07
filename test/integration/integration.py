import errno
import os
import platform
import shutil
import subprocess
import sys
import time
import unittest

basedir = os.path.abspath(os.path.dirname(__file__))
bfg9000 = os.path.join(basedir, '..', '..', 'src', 'bfg9000')

def cleandir(path):
    try:
        shutil.rmtree(path)
    except Exception as e:
        if e.errno == errno.ENOTEMPTY:
            # Windows seems to keep an executable file open a little bit after
            # the process returns from wait(), so sleep a bit and try again in
            # case this bites us.
            time.sleep(0.5)
            shutil.rmtree(path)
        elif e.errno != errno.ENOENT:
            raise
    os.mkdir(path)

class IntegrationTest(unittest.TestCase):
    def __init__(self, srcdir, *args, **kwargs):
        unittest.TestCase.__init__(self, *args, **kwargs)
        self.srcdir = os.path.join(basedir, srcdir)
        self.builddir = os.path.join(self.srcdir, 'build')
        self.extra_args = []
        self.backend = os.getenv('BACKEND', 'make')

    def setUp(self):
        os.chdir(self.srcdir)
        cleandir(self.builddir)
        subprocess.check_call(
            # TODO: Remove sys.executable?
            [sys.executable, bfg9000, self.srcdir, self.builddir, '--backend',
             self.backend] + self.extra_args
        )
        os.chdir(self.builddir)

    def build(self, target=None):
        args = [self.backend]
        if target:
            if self.backend == 'msbuild':
                args.append('/target:' + target)
            else:
                args.append(target)
        subprocess.check_call(args)

    def assertOutput(self, args, output):
        if self.backend == 'msbuild':
            args = args[:]
            args[0] = os.path.join('Debug', args[0])
        self.assertEqual(
            subprocess.check_output(args, universal_newlines=True), output
        )

def executable(name):
    return os.path.join('bin', name)

def shared_library(name):
    if platform.system() == 'Linux':
        head, tail = os.path.split(name)
        return os.path.join('lib', head, 'lib' + tail + '.so')
    else:
        return os.path.join('lib', name + '.dll')

def static_library(name):
    if platform.system() == 'Linux':
        head, tail = os.path.split(name)
        return os.path.join('lib', head, 'lib' + tail + '.a')
    else:
        return os.path.join('lib', name + '.lib')
