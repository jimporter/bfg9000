import errno
import os
import shutil
import subprocess
import sys
import time
import unittest

from bfg9000.platforms import platform_info
from bfg9000.makedirs import makedirs

this_dir = os.path.abspath(os.path.dirname(__file__))
examples_dir = os.path.join(this_dir, '..', '..', 'examples')
test_data_dir = os.path.join(this_dir, '..', 'test_data')
test_stage_dir = os.path.join(this_dir, '..', 'stage')

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

class SubprocessError(unittest.TestCase.failureException):
    def __init__(self, message):
        unittest.TestCase.failureException.__init__(
            self, '\n{line}\n{msg}\n{line}'.format(line='-' * 60, msg=message)
        )

class IntegrationTest(unittest.TestCase):
    def __init__(self, srcdir, *args, **kwargs):
        unittest.TestCase.__init__(self, *args, **kwargs)
        self.srcdir = os.path.join(test_data_dir, srcdir)

        srcbase = os.path.basename(srcdir)
        self.builddir = os.path.join(test_stage_dir, srcbase + '-build')
        makedirs(self.builddir, exist_ok=True)

        self.extra_args = []
        self.backend = os.getenv('BACKEND', 'make')

    def setUp(self):
        os.chdir(self.srcdir)
        cleandir(self.builddir)
        self.assertPopen(
            ['bfg9000', self.srcdir, self.builddir, '--backend', self.backend] +
            self.extra_args
        )
        os.chdir(self.builddir)

    def build(self, target=None):
        args = [self.backend]
        if target:
            if self.backend == 'msbuild':
                args.append('/target:' + target)
            else:
                args.append(target)
        return self.assertPopen(args, True)

    def assertPopen(self, args, bad=False):
        proc = subprocess.Popen(
            args, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
            universal_newlines=True
        )
        output = proc.communicate()[0]
        if proc.returncode != 0:
            raise SubprocessError(output)
        return output

    def assertOutput(self, args, output):
        if self.backend == 'msbuild':
            args = list(args)
            args[0] = os.path.join('Debug', args[0])
        self.assertEqual(
            subprocess.check_output(args, universal_newlines=True), output
        )

def executable(name):
    info = platform_info()
    return os.path.join('bin', name + info.executable_ext)

def shared_library(name):
    info = platform_info()
    prefix = '' if info.name == 'windows' else 'lib'

    head, tail = os.path.split(name)
    return os.path.join('lib', head, prefix + tail + info.shared_library_ext)

def static_library(name):
    info = platform_info()
    prefix = '' if info.name == 'windows' else 'lib'
    suffix = '.lib' if info.name == 'windows' else '.a'

    head, tail = os.path.split(name)
    return os.path.join('lib', head, prefix + tail + suffix)
