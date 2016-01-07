import errno
import os
import shutil
import subprocess
import time
import unittest
from collections import namedtuple

from six import iteritems

from bfg9000.path import InstallRoot
from bfg9000.platforms import platform_info, platform_name
from bfg9000.makedirs import makedirs
from bfg9000.backends import get_backends

this_dir = os.path.abspath(os.path.dirname(__file__))
examples_dir = os.path.join(this_dir, '..', '..', 'examples')
test_data_dir = os.path.join(this_dir, '..', 'data')
test_stage_dir = os.path.join(this_dir, '..', 'stage')

Target = namedtuple('Target', ['name', 'path'])

if os.getenv('BACKENDS', '').strip():
    backends = os.getenv('BACKENDS').split(' ')
else:
    backends = [k for k, v in iteritems(get_backends()) if v.priority > 0]


def cleandir(path, recreate=True):
    if os.path.exists(path):
        # Windows seems to keep an executable file open a little bit after the
        # process returns from wait(), so try a few times, sleeping a bit in
        # between.
        for t in [0.1, 0.25, 0.5, 1.0, 2.0, None]:
            try:
                shutil.rmtree(path)
                break
            except Exception as e:
                if e.errno == errno.ENOTEMPTY:
                    if t is None:
                        raise RuntimeError('unable to remove {}'.format(path))
                    time.sleep(t)
                elif e.errno != errno.ENOENT:
                    raise
    if recreate:
        makedirs(path)


def skip_pred(predicate, msg='skipped'):
    def wrap(fn):
        def inner(self, *args, **kwargs):
            if predicate(self):
                raise unittest.SkipTest(msg)
            return fn(self, *args, **kwargs)
        return inner
    return wrap


def skip_if_backend(backend):
    return skip_pred(lambda x: x.backend == backend,
                     'not supported for backend "{}"'.format(backend))


def only_if_backend(backend):
    return skip_pred(lambda x: x.backend != backend,
                     'only supported for backend "{}"'.format(backend))


def xfail_if(xfail):
    def wrap(fn):
        if xfail:
            return unittest.expectedFailure(fn)
        else:
            return fn
    return wrap


def xfail_if_platform(platform):
    return xfail_if(platform_name() == platform)


class SubprocessError(unittest.TestCase.failureException):
    def __init__(self, message):
        unittest.TestCase.failureException.__init__(
            self, '\n{line}\n{msg}\n{line}'.format(line='-' * 60, msg=message)
        )


class IntegrationTest(unittest.TestCase):
    def __init__(self, srcdir, *args, **kwargs):
        dist = kwargs.pop('dist', False)
        self._args = args
        self._kwargs = kwargs

        self.stage_src = kwargs.pop('stage_src', False)
        self.backend = kwargs.pop('backend', None)
        unittest.TestCase.__init__(self, *args, **kwargs)
        if self.backend is None:
            return

        self.extra_args = []

        srcname = os.path.basename(srcdir)
        self.srcdir = os.path.join(test_data_dir, srcdir)
        if self.stage_src:
            self.orig_srcdir = self.srcdir
            self.srcdir = os.path.join(test_stage_dir, srcname)

        self.builddir = os.path.join(test_stage_dir, srcname + '-build')

        if dist:
            self.distdir = os.path.join(test_stage_dir, srcname + '-dist')
            self.extra_args = ['--prefix', self.distdir]

            install_dirs = platform_info().install_dirs
            path_vars = {InstallRoot.prefix: self.distdir}
            for i in InstallRoot:
                setattr(self, i.name, install_dirs[i].realize(path_vars))

    def parameterize(self):
        return [ self.__class__(backend=i, *self._args, **self._kwargs)
                 for i in backends ]

    def shortDescription(self):
        return self.backend

    def _target_name(self, target):
        if self.backend == 'msbuild':
            if isinstance(target, Target):
                target = target.name
            return '/target:' + target
        else:
            if isinstance(target, Target):
                target = target.path
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
        if self.stage_src:
            cleandir(self.srcdir, recreate=False)
            shutil.copytree(self.orig_srcdir, self.srcdir)
        os.chdir(self.srcdir)
        cleandir(self.builddir)
        self.assertPopen(
            ['bfg9000', self.srcdir, self.builddir, '--backend',
             self.backend] + self.extra_args
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


def load_tests(loader, standard_tests, pattern):
    all_tests = unittest.TestSuite()
    for suite in standard_tests:
        for case in suite:
            all_tests.addTests(case.parameterize())
    return all_tests
