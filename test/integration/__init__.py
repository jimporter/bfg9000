import functools
import os
import shutil
import subprocess
import time
import unittest
from collections import namedtuple

from six import iteritems

from bfg9000.backends import list_backends
from bfg9000.environment import Environment
from bfg9000.path import InstallRoot, makedirs, Path, Root
from bfg9000.platforms import platform_info, platform_name

this_dir = os.path.abspath(os.path.dirname(__file__))
examples_dir = os.path.join(this_dir, '..', '..', 'examples')
test_data_dir = os.path.join(this_dir, '..', 'data')
test_stage_dir = os.path.join(this_dir, '..', 'stage')

env = Environment(None, None, None, None, None, {}, (False, False), None)

Target = namedtuple('Target', ['name', 'path'])

if os.getenv('BACKENDS', '').strip():
    backends = os.getenv('BACKENDS').split(' ')
else:
    backends = [k for k, v in iteritems(list_backends()) if v.priority > 0]

_unset = object()


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
            # XXX: Actually show these tests as skipped; right now they're
            # totally hidden.
            @functools.wraps(fn, assigned=['__name__', '__module__'],
                             updated=[])
            class Wrap(fn):
                def __init__(self, *args, **kwargs):
                    fn.__init__(self, *args, **kwargs)
                    if predicate(self):
                        raise unittest.SkipTest(msg)

            return Wrap
        else:
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


# For some reason, six doesn't have this wrapper...
def assertNotRegex(self, *args, **kwargs):
    if hasattr(self, 'assertNotRegex'):
        return self.assertNotRegex(*args, **kwargs)
    else:
        return self.assertNotRegexpMatches(*args, **kwargs)


class TestCase(unittest.TestCase):
    def parameterize(self):
        return [self]

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

    def assertPopen(self, command, env=None, env_update=True, returncode=0):
        if env is not None and env_update:
            overrides = env
            env = dict(os.environ)
            env.update(overrides)

        command = [self.target_path(i) for i in command]
        proc = subprocess.Popen(
            command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
            env=env, universal_newlines=True
        )
        output = proc.communicate()[0]
        if proc.returncode != returncode:
            raise SubprocessError(output)
        return output

    def assertOutput(self, command, output, *args, **kwargs):
        self.assertEqual(self.assertPopen(command, *args, **kwargs), output)

    def assertDirectory(self, path, contents):
        path = os.path.normpath(path)
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


class BasicIntegrationTest(TestCase):
    def __init__(self, srcdir, *args, **kwargs):
        install = kwargs.pop('install', False)

        self._configure = kwargs.pop('configure', True)
        self._args = args
        self._kwargs = kwargs

        stage_src = kwargs.pop('stage_src', False)
        self.backend = kwargs.pop('backend', None)
        self.env = kwargs.pop('env', None)

        unittest.TestCase.__init__(self, *args, **kwargs)
        if self.backend is None:
            return

        self.extra_args = []

        srcname = os.path.basename(srcdir)
        self.srcdir = os.path.join(test_data_dir, srcdir)
        if stage_src:
            srcname = os.path.basename(srcdir)
            self.orig_srcdir = self.srcdir
            self.srcdir = os.path.join(test_stage_dir, srcname)
        else:
            self.orig_srcdir = None

        if install:
            self.installdir = os.path.join(test_stage_dir,
                                           srcname + '-install')

            install_dirs = platform_info().install_dirs.copy()
            install_dirs[InstallRoot.prefix] = Path(
                self.installdir, Root.absolute
            )
            for i in InstallRoot:
                setattr(self, i.name, install_dirs[i].string(install_dirs))
        else:
            self.installdir = None

    @staticmethod
    def _make_builddir(srcdir):
        srcname = os.path.basename(srcdir)
        return os.path.join(test_stage_dir, srcname + '-build')

    @property
    def builddir(self):
        return self._make_builddir(self.srcdir)

    def parameterize(self):
        return [self.__class__(
            backend='', *self._args, **self._kwargs
        )]

    def shortDescription(self):
        return self.backend

    def setUp(self):
        if self._configure:
            self.configure()

    def configure(self, srcdir=None, builddir=None, installdir=_unset,
                  orig_srcdir=_unset, extra_args=_unset, env=_unset,
                  backend=_unset):
        if srcdir:
            srcdir = os.path.join(test_data_dir, srcdir)
        else:
            srcdir = self.srcdir
        builddir = builddir or self._make_builddir(srcdir)

        if installdir is _unset:
            installdir = self.installdir
        if orig_srcdir is _unset:
            orig_srcdir = self.orig_srcdir
        if extra_args is _unset:
            extra_args = self.extra_args
        if env is _unset:
            env = self.env
        if backend is _unset:
            backend = self.backend

        if orig_srcdir:
            cleandir(srcdir, recreate=False)
            shutil.copytree(orig_srcdir, srcdir)
        os.chdir(srcdir)
        cleandir(builddir)

        if installdir:
            cleandir(installdir)
            install_args = ['--prefix', installdir]
        else:
            install_args = []

        self.assertPopen(
            ['bfg9000', '--debug', 'configure', builddir,
             '--backend', backend] + install_args + extra_args,
            env=env, env_update=True
        )
        os.chdir(builddir)

    def build(self, target=None, extra_args=[]):
        args = [os.getenv(self.backend.upper(), self.backend)] + extra_args
        if target:
            args.append(self.target_name(target))
        return self.assertPopen(args)

    def wait(self, t=1):
        time.sleep(t)

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


class IntegrationTest(BasicIntegrationTest):
    def parameterize(self):
        result = []
        for i in backends:
            try:
                result.append(self.__class__(
                    backend=i, *self._args, **self._kwargs
                ))
            except unittest.SkipTest:
                pass
        return result


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
