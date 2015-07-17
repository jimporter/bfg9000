import errno
import os
import shutil
import subprocess
import sys
import time
import unittest

from collections import namedtuple

from bfg9000.path import Path
from bfg9000.platforms import platform_info
from bfg9000.makedirs import makedirs

this_dir = os.path.abspath(os.path.dirname(__file__))
examples_dir = os.path.join(this_dir, '..', '..', 'examples')
test_data_dir = os.path.join(this_dir, '..', 'test_data')
test_stage_dir = os.path.join(this_dir, '..', 'stage')

Target = namedtuple('Target', ['name', 'path'])

def cleandir(path, recreate=True):
    if os.path.exists(path):
        try:
            shutil.rmtree(path)
        except Exception as e:
            if e.errno == errno.ENOTEMPTY:
                # Windows seems to keep an executable file open a little bit
                # after the process returns from wait(), so sleep a bit and try
                # again in case this bites us.
                time.sleep(0.5)
                shutil.rmtree(path)
            elif e.errno != errno.ENOENT:
                raise
    if recreate:
        makedirs(path)

def stagedir(path):
    dest = os.path.join(test_stage_dir, os.path.basename(path))
    cleandir(dest, recreate=False)
    shutil.copytree(os.path.join(test_data_dir, path), dest)
    return dest

def skip_if_backend(backend):
    def wrap(fn):
        def inner(self, *args, **kwargs):
            if self.backend == backend:
                raise unittest.SkipTest(
                    "skipped for backend '{}'".format(backend)
                )
            return fn(self, *args, **kwargs)
        return inner
    return wrap

class SubprocessError(unittest.TestCase.failureException):
    def __init__(self, message):
        unittest.TestCase.failureException.__init__(
            self, '\n{line}\n{msg}\n{line}'.format(line='-' * 60, msg=message)
        )

class IntegrationTest(unittest.TestCase):
    def __init__(self, srcdir, *args, **kwargs):
        dist = kwargs.pop('dist', False)
        unittest.TestCase.__init__(self, *args, **kwargs)

        self.backend = os.getenv('BACKEND', 'make')
        self.extra_args = []

        self.srcdir = os.path.join(test_data_dir, srcdir)
        srcbase = os.path.basename(srcdir)
        self.builddir = os.path.join(test_stage_dir, srcbase + '-build')

        if dist:
            self.distdir = os.path.join(test_stage_dir, srcbase + '-dist')
            self.extra_args = ['--prefix', self.distdir]

            install_dirs = platform_info().install_dirs
            path_vars = {Path.prefix: self.distdir}
            self.bindir = install_dirs['bindir'].realize(path_vars)
            self.libdir = install_dirs['libdir'].realize(path_vars)
            self.includedir = install_dirs['includedir'].realize(path_vars)

    def _target_name(self, target):
        if isinstance(target, Target):
            target = target.name
        if self.backend == 'msbuild':
            return '/target:' + target
        return target

    def _target_path(self, target):
        if isinstance(target, Target):
            prefix = '.'
            if self.backend == 'msbuild':
                prefix = 'Debug'
                if os.getenv('PLATFORM') == 'X64':
                    prefix = os.path.join('X64', prefix)
            return os.path.join(prefix, target.path)
        return target

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
            args.append(self._target_name(target))
        return self.assertPopen(args, True)

    def wait(self, t=1):
        time.sleep(t)

    def assertPopen(self, args, bad=False):
        args = [self._target_path(i) for i in args]
        proc = subprocess.Popen(
            args, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
            universal_newlines=True
        )
        output = proc.communicate()[0]
        if proc.returncode != 0:
            raise SubprocessError(output)
        return output

    def assertOutput(self, args, output):
        args = [self._target_path(i) for i in args]
        self.assertEqual(
            subprocess.check_output(args, universal_newlines=True), output
        )

    def assertExists(self, path):
        if not os.path.exists(self._target_path(path)):
            raise unittest.TestCase.failureException(
                "'{}' does not exist".format(os.path.normpath(path))
            )

def executable(name):
    info = platform_info()
    return Target(name, os.path.normpath(os.path.join(
        '.', name + info.executable_ext
    )))

def shared_library(name):
    info = platform_info()
    prefix = '' if info.name == 'windows' else 'lib'

    head, tail = os.path.split(name)
    return Target(name, os.path.normpath(os.path.join(
        '.', head, prefix + tail + info.shared_library_ext
    )))

def static_library(name):
    info = platform_info()
    prefix = '' if info.name == 'windows' else 'lib'
    suffix = '.lib' if info.name == 'windows' else '.a'

    head, tail = os.path.split(name)
    return Target(name, os.path.normpath(os.path.join(
        '.', head, prefix + tail + suffix
    )))
