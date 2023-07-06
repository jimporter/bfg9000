import os
import shutil
import subprocess
import time
import unittest
from collections import namedtuple

from .. import *

from bfg9000.backends import list_backends
from bfg9000.iterutils import listify
from bfg9000.path import InstallRoot, Path, Root

this_dir = os.path.abspath(os.path.dirname(__file__))
examples_dir = os.path.join(this_dir, '..', '..', 'examples')
test_data_dir = os.path.join(this_dir, '..', 'data')
test_stage_dir = os.path.join(this_dir, '..', 'stage')

default_env = env = make_env()

Target = namedtuple('Target', ['name', 'path'])

if os.getenv('BACKENDS', '').strip():
    backends = os.getenv('BACKENDS').split(' ')
else:
    backends = [k for k, v in list_backends().items() if v.priority > 0]
    # Only test with MSBuild by default on Windows.
    if env.host_platform.family != 'windows' and 'msbuild' in backends:
        backends.remove('msbuild')

# Also supported: 'gcj', 'mingw-cross'
test_features = {'boost', 'fortran', 'java', 'objc', 'pch', 'qt', 'scala'}
for i in os.getenv('BFG_EXTRA_TESTS', '').split(' '):
    if i:
        test_features.add(i)
for i in os.getenv('BFG_SKIPPED_TESTS', '').split(' '):
    if i:
        test_features.remove(i)

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
        os.makedirs(path)


def skip_if_backend(backend, hide=False):
    return skip_pred(lambda x: x.backend == backend,
                     'not supported for backend "{}"'.format(backend), hide)


def only_if_backend(backend, hide=False):
    return skip_pred(lambda x: x.backend != backend,
                     'only supported for backend "{}"'.format(backend), hide)


class SubprocessError(unittest.TestCase.failureException):
    def __init__(self, returncode, env, message):
        envstr = ''.join('  {} = {}\n'.format(k, v)
                         for k, v in (env or {}).items())
        msg = 'returned {returncode}\n{env}{line}\n{msg}\n{line}'.format(
            returncode=returncode, env=envstr, line='-' * 60, msg=message
        )
        super().__init__(msg)


class SubprocessTestCase(TestCase):
    def target_name(self, target):
        if self.backend == 'msbuild':
            if isinstance(target, Target):
                target = target.name
            return '/target:' + target
        else:
            if isinstance(target, Target):
                target = target.path
            return target

    def target_path(self, target, prefix=''):
        if isinstance(target, Target):
            if self.backend == 'msbuild':
                if os.getenv('PLATFORM') == 'x64':
                    prefix = os.path.join(prefix, 'x64')
                prefix = os.path.join(prefix, 'Default')
            elif not prefix:
                prefix = '.'
            return os.path.join(prefix, target.path)
        return target

    def assertPopen(self, command, input=None, *, env=None, extra_env=None,
                    returncode=0):
        final_env = env if env is not None else os.environ
        if extra_env:
            final_env = final_env.copy()
            final_env.update(extra_env)

        command = [self.target_path(i) for i in command]
        proc = subprocess.run(
            command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
            input=input, env=final_env, universal_newlines=True
        )
        if not (returncode == 'any' or
                (returncode == 'fail' and proc.returncode != 0) or
                proc.returncode in listify(returncode)):
            raise SubprocessError(proc.returncode, extra_env or env,
                                  proc.stdout)
        return proc.stdout

    def assertOutput(self, command, output, *args, **kwargs):
        self.assertEqual(self.assertPopen(command, *args, **kwargs), output)

    def assertExists(self, path):
        realpath = self.target_path(path)
        if not os.path.exists(realpath):
            raise unittest.TestCase.failureException(
                '{!r} does not exist'.format(os.path.normpath(realpath))
            )

    def assertNotExists(self, path):
        realpath = self.target_path(path)
        if os.path.exists(realpath):
            raise unittest.TestCase.failureException(
                '{!r} exists'.format(os.path.normpath(realpath))
            )

    def assertDirectory(self, path, contents, optional=[]):
        path = os.path.normpath(path)
        actual = set(os.path.normpath(os.path.join(base, f))
                     for base, dirs, files in os.walk(path) for f in files)
        expected = set(os.path.normpath(os.path.join(path, i))
                       for i in contents)
        optional = set(os.path.normpath(os.path.join(path, i))
                       for i in optional)
        actual -= optional
        if actual != expected:
            missing = [os.path.relpath(i, path) for i in (expected - actual)]
            extra = [os.path.relpath(i, path) for i in (actual - expected)]
            raise unittest.TestCase.failureException(
                'missing: {}, extra: {}'.format(missing, extra)
            )


class BasicIntegrationTest(SubprocessTestCase):
    def __init__(self, srcdir, *args, install=False, configure=True,
                 stage_src=False, backend=None, env=None, extra_env=None,
                 extra_args=None, **kwargs):
        self._configure = configure
        self.backend = backend
        self.env = env
        self.extra_env = extra_env
        self.extra_args = extra_args or []

        super().__init__(*args, **kwargs)
        if self.backend is None:
            return

        srcname = os.path.basename(srcdir)
        self.srcdir = os.path.join(test_data_dir, srcdir)
        if stage_src:
            srcname = os.path.basename(srcdir)
            self.orig_srcdir = self.srcdir
            self.srcdir = os.path.join(test_stage_dir, srcname)
        else:
            self.orig_srcdir = None

        if install is True:
            install = os.path.join(test_stage_dir, srcname + '-install')
        if install:
            self.installdir = install
            install_dirs = default_env.target_platform.install_dirs.copy()
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
        return ([] if self._hideTest() else
                [self.__class__(backend='', *self._args, **self._kwargs)])

    def shortDescription(self):
        return self.backend

    def setUp(self):
        if self._configure:
            self.configure()

    def configure(self, srcdir=None, builddir=None, installdir=_unset,
                  orig_srcdir=_unset, extra_args=_unset, env=_unset,
                  extra_env=_unset, backend=_unset, returncode=0):
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
        if backend is _unset:
            backend = self.backend

        if env is _unset:
            env = self.env
            if extra_env is _unset:
                extra_env = self.extra_env
        elif extra_env is _unset:
            extra_env = None

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

        result = self.assertPopen(
            ['bfg9000', '--debug', 'configure', builddir,
             '--backend', backend] + install_args + extra_args,
            env=env, extra_env=extra_env, returncode=returncode
        )
        os.chdir(builddir)
        return result

    def build(self, target=None, extra_args=[]):
        args = [os.getenv(self.backend.upper(), self.backend)] + extra_args
        if target:
            args.append(self.target_name(target))
        return self.assertPopen(args)

    def clean(self):
        if self.backend == 'ninja':
            return self.build(extra_args=['clean'])
        elif self.backend == 'make':
            return self.build('clean')
        else:  # self.backend == 'msbuild'
            return self.build(extra_args=['/t:Clean'])

    def wait(self, t=1):
        time.sleep(t)


class IntegrationTest(BasicIntegrationTest):
    def parameterize(self):
        return parameterize_tests(self, backend=backends)


def output_file(name):
    return Target(name, os.path.normpath(os.path.join('.', name)))


def executable(name):
    return Target(name, os.path.normpath(os.path.join(
        '.', name + env.target_platform.executable_ext
    )))


if env.builder('c++').flavor == 'msvc':
    _shared_library_prefix = ''
    _static_library_prefix = ''
elif env.target_platform.family == 'windows':
    _shared_library_prefix = ''
    _static_library_prefix = 'lib'
else:
    _shared_library_prefix = 'lib'
    _static_library_prefix = 'lib'


def shared_library(name, version=None):
    head, tail = os.path.split(name)
    ext = env.target_platform.shared_library_ext
    if version:
        if not env.target_platform.has_versioned_library:
            raise ValueError('no versioned libraries on this platform')
        if env.target_platform.genus == 'darwin':
            tail += '.' + version
        else:
            ext += '.' + version
    return Target(name, os.path.normpath(os.path.join(
        '.', head, _shared_library_prefix + tail + ext
    )))


def static_library(name):
    suffix = '.lib' if env.builder('c++').flavor == 'msvc' else '.a'
    head, tail = os.path.split(name)
    return Target(name, os.path.normpath(os.path.join(
        '.', head, _static_library_prefix + tail + suffix
    )))


def import_library(name):
    if not env.target_platform.has_import_library:
        raise ValueError('no import libraries on this platform')
    if env.builder('c++').flavor == 'msvc':
        return static_library(name)
    else:
        head, tail = os.path.split(shared_library(name).path)
        path = os.path.join(head, _static_library_prefix + tail + '.a')
        return Target(name, path)
