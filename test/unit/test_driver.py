import argparse
import logging
import mock
import re
from six.moves import cStringIO as StringIO

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

            shared=True,
            static=False,
        )

    def test_basic(self):
        env, backend = driver.environment_from_args(self.args)
        self.assertEqual(env.srcdir, path.abspath('.'))
        self.assertTrue('make' in backend.__name__)

    def test_extra_args(self):
        env, backend = driver.environment_from_args(
            self.args, extra_args=['--foo']
        )
        self.assertEqual(env.srcdir, path.abspath('.'))
        self.assertEqual(env.extra_args, ['--foo'])
        self.assertTrue('make' in backend.__name__)


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
        log.init(stream=self.stream)

    def tearDown(self):
        for i in logging.root.handlers[:]:
            logging.root.removeHandler(i)

    def test_message(self):
        try:
            raise ValueError('message')
        except ValueError as e:
            driver.handle_reload_exception(e)

        assertRegex(self, self.stream.getvalue(),
                    'Unable to reload environment: message\n')

    def test_no_message(self):
        try:
            raise ValueError()
        except ValueError as e:
            driver.handle_reload_exception(e)

        assertRegex(self, self.stream.getvalue(),
                    'Unable to reload environment\n')

    def test_message_rerun(self):
        try:
            raise EnvVersionError('message')
        except EnvVersionError as e:
            driver.handle_reload_exception(e, True)

        assertRegex(self, self.stream.getvalue(),
                    'Unable to reload environment: message\n' +
                    '  Please re-run bfg9000 manually\n',
                    re.MULTILINE)

    def test_no_message_rerun(self):
        try:
            raise EnvVersionError()
        except EnvVersionError as e:
            driver.handle_reload_exception(e, True)

        assertRegex(self, self.stream.getvalue(),
                    'Unable to reload environment\n' +
                    '  Please re-run bfg9000 manually\n')
