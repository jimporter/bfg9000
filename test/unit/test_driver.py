import argparse
import re
from io import StringIO
from unittest import mock

from . import *

from bfg9000 import driver, log, path
from bfg9000.environment import EnvVersionError


class TestEnvironmentFromArgs(TestCase):
    def setUp(self):
        self.args = argparse.Namespace(
            backend='make',

            srcdir=path.abspath('.'),
            builddir=path.abspath('build'),

            prefix=path.abspath('.'),
            exec_prefix=path.abspath('.'),
            bindir=path.abspath('bin'),
            libdir=path.abspath('lib'),
            includedir=path.abspath('include'),
            datadir=path.abspath('share'),
            mandir=path.abspath('man'),

            shared=True,
            static=False,
            compdb=True,
        )

    def test_basic(self):
        env, backend = driver.environment_from_args(self.args)
        self.assertEqual(env.srcdir, path.abspath('.'))
        self.assertTrue('make' in backend.__name__)

        driver.finalize_environment(env, self.args)
        self.assertEqual(env.install_dirs, {
            k: getattr(self.args, k.name) for k in path.InstallRoot
        })

    def test_extra_args(self):
        env, backend = driver.environment_from_args(self.args)
        driver.finalize_environment(env, self.args, ['--foo'])
        self.assertEqual(env.extra_args, ['--foo'])


class TestDirectoryPair(TestCase):
    def setUp(self):
        self.pair = driver.directory_pair('srcdir', 'builddir')(None, None)

    def test_pass_srcdir(self):
        args = argparse.Namespace()
        with mock.patch('bfg9000.build.is_srcdir', return_value=True):
            self.pair(None, args, path.abspath('foo'))
        self.assertEqual(args, argparse.Namespace(
            srcdir=path.abspath('foo'),
            builddir=path.abspath('.')
        ))

    def test_pass_builddir(self):
        args = argparse.Namespace()
        with mock.patch('bfg9000.build.is_srcdir', return_value=False):
            self.pair(None, args, path.abspath('foo'))
        self.assertEqual(args, argparse.Namespace(
            srcdir=path.abspath('.'),
            builddir=path.abspath('foo')
        ))


class TestReloadException(TestCase):
    def setUp(self):
        self.stream = StringIO()
        self.logger = log.getLogger('bfg9000.test.unit')
        self.logger.propagate = False
        log._init_logging(self.logger, debug=False, stream=self.stream)

        patch_logger = mock.patch('bfg9000.driver.logger', self.logger)
        patch_logger.start()
        self.addCleanup(patch_logger.stop)

    def test_message(self):
        try:
            raise ValueError('message')
        except ValueError as e:
            driver.handle_reload_exception(e)

        self.assertRegex(self.stream.getvalue(),
                         'unable to reload environment: message\n')

    def test_no_message(self):
        try:
            raise ValueError()
        except ValueError as e:
            driver.handle_reload_exception(e)

        self.assertRegex(self.stream.getvalue(),
                         'unable to reload environment\n')

    def test_message_rerun(self):
        try:
            raise EnvVersionError('message')
        except EnvVersionError as e:
            driver.handle_reload_exception(e, True)

        self.assertRegex(self.stream.getvalue(),
                         'unable to reload environment: message\n' +
                         '  please re-run bfg9000 manually\n',
                         re.MULTILINE)

    def test_no_message_rerun(self):
        try:
            raise EnvVersionError()
        except EnvVersionError as e:
            driver.handle_reload_exception(e, True)

        self.assertRegex(self.stream.getvalue(),
                         'unable to reload environment\n' +
                         '  please re-run bfg9000 manually\n')
