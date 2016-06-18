import os
import shutil
import subprocess
import time
import unittest
from collections import namedtuple

from six import iteritems

from bfg9000.backends import list_backends
from bfg9000.environment import Environment
from bfg9000.path import InstallRoot, makedirs
from bfg9000.platforms import platform_info, platform_name

this_dir = os.path.abspath(os.path.dirname(__file__))
examples_dir = os.path.join(this_dir, '..', '..', 'examples')
test_data_dir = os.path.join(this_dir, '..', 'data')
test_stage_dir = os.path.join(this_dir, '..', 'stage')

env = Environment(None, None, None, None, None, None)

Target = namedtuple('Target', ['name', 'path'])

if os.getenv('BACKENDS', '').strip():
    backends = os.getenv('BACKENDS').split(' ')
else:
    backends = [k for k, v in iteritems(list_backends()) if v.priority > 0]


def cleandir(path, recreate=True):
    if os.path.exists(path):
        # Windows seems to keep an executable file open a little bit after the
        # process returns from wait(), so try a few times, sleeping a bit in
        # between.
        for t in [0.1, 0.25, 0.5, 1.0, 2.0, None]:
            try:
                shutil.rmtree(path)
                break
            except OSError:
                if t is None:
                    raise RuntimeError('unable to remove {}'.format(path))
                time.sleep(t)
    if recreate:
        makedirs(path)


def skip_pred(predicate, msg='skipped'):
    def wrap(fn):
        if isinstance(fn, type):
            raise TypeError('skip_pred only works on functions')

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
        else:
            self.distdir = None

    def parameterize(self):
        return [ self.__class__(backend=i, *self._args, **self._kwargs)
                 for i in backends ]

    def shortDescription(self):
        return self.backend

    def target_name(self, target):
        if self.backend == 'msbuild':
            if isinstance(target, Target):
                target = target.name
            return '/target:' + target
        else:
            if isinstance(target, Target):
                target = target.path
            return target

    def target_path(self, target):
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
        if self.distdir:
            cleandir(self.distdir)

        self.assertPopen(
            ['bfg9000', '--debug', 'configure', self.builddir,
             '--backend', self.backend] + self.extra_args
        )
        os.chdir(self.builddir)

    def build(self, target=None):
        args = [os.getenv(self.backend.upper(), self.backend)]
        if target:
            args.append(self.target_name(target))
        return self.assertPopen(args, True)

    def wait(self, t=1):
        time.sleep(t)

    def assertPopen(self, args, bad=False):
        args = [self.target_path(i) for i in args]
        proc = subprocess.Popen(
            args, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
            universal_newlines=True
        )
        output = proc.communicate()[0]
        if proc.returncode != 0:
            raise SubprocessError(output)
        return output

    def assertOutput(self, args, output):
        args = [self.target_path(i) for i in args]
        self.assertEqual(subprocess.check_output(
            args, stderr=subprocess.STDOUT, universal_newlines=True
        ), output)

    def assertExists(self, path):
        realpath = self.target_path(path)
        if not os.path.exists(realpath):
            raise unittest.TestCase.failureException(
                "'{}' does not exist".format(realpath)
            )

    def assertNotExists(self, path):
        realpath = self.target_path(path)
        if os.path.exists(realpath):
            raise unittest.TestCase.failureException(
                "'{}' exists".format(os.path.normpath(realpath))
            )

    def assertDirectory(self, path, contents):
        actual = set(os.path.normpath(os.path.join(path, base, f))
                     for base, dirs, files in os.walk(path) for f in files)
        expected = set(os.path.normpath(os.path.join(path, i))
                       for i in contents)
        if actual != expected:
            missing = [os.path.relpath(i, path) for i in (expected - actual)]
            extra = [os.path.relpath(i, path) for i in (actual - expected)]
            raise unittest.TestCase.failureException(
                'missing: {}, extra: {}'.format(missing, extra)
            )


def output_file(name):
    return Target(name, os.path.normpath(os.path.join('.', name)))


def executable(name):
    return Target(name, os.path.normpath(os.path.join(
        '.', name + platform_info().executable_ext
    )))


if env.builder('c++').flavor == 'msvc':
    _library_prefix = ''
else:
    _library_prefix = 'lib'


def shared_library(name, version=None):
    head, tail = os.path.split(name)
    ext = platform_info().shared_library_ext
    if version:
        if not platform_info().has_versioned_library:
            raise ValueError('no versioned libraries on this platform')
        if platform_name() == 'darwin':
            tail += '.' + version
        else:
            ext += '.' + version
    return Target(name, os.path.normpath(os.path.join(
        '.', head, _library_prefix + tail + ext
    )))


def static_library(name):
    suffix = '.lib' if env.builder('c++').flavor == 'msvc' else '.a'
    head, tail = os.path.split(name)
    return Target(name, os.path.normpath(os.path.join(
        '.', head, _library_prefix + tail + suffix
    )))


def import_library(name):
    if not platform_info().has_import_library:
        raise ValueError('no import libraries on this platform')
    if env.builder('c++').flavor == 'msvc':
        return static_library(name)
    else:
        return Target(name, shared_library(name).path + '.a')


def load_tests(loader, standard_tests, pattern):
    all_tests = unittest.TestSuite()
    for suite in standard_tests:
        for case in suite:
            all_tests.addTests(case.parameterize())
    return all_tests
