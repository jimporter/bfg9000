import argparse
import logging
import mock
import re
import unittest
from six import assertRegex
from six.moves import cStringIO as StringIO

from bfg9000 import driver, log, path
from bfg9000.environment import EnvVersionError


class TestDirectory(unittest.TestCase):
    def test_existent(self):
        with mock.patch('os.path.exists', return_value=True), \
             mock.patch('os.path.isdir', return_value=True):  # noqa
            self.assertEqual(driver.Directory()('foo'), path.abspath('foo'))
            self.assertEqual(driver.Directory(True)('foo'),
                             path.abspath('foo'))

    def test_not_dir(self):
        with mock.patch('os.path.exists', return_value=True), \
             mock.patch('os.path.isdir', return_value=False):  # noqa
            with self.assertRaises(argparse.ArgumentTypeError):
                driver.Directory()('foo')
            with self.assertRaises(argparse.ArgumentTypeError):
                driver.Directory(True)('foo')

    def test_nonexistent(self):
        with mock.patch('os.path.exists', return_value=False):
            self.assertEqual(driver.Directory()('foo'), path.abspath('foo'))
            with self.assertRaises(argparse.ArgumentTypeError):
                driver.Directory(True)('foo')


class TestDirectoryPair(unittest.TestCase):
    def setUp(self):
        self.pair = driver.directory_pair('srcdir', 'builddir')(None, None)

    def test_pass_srcdir(self):
        ns = argparse.Namespace()
        with mock.patch('bfg9000.build.is_srcdir', return_value=True):
            self.pair(None, ns, path.abspath('foo'))
        self.assertEqual(ns, argparse.Namespace(
            srcdir=path.abspath('foo'),
            builddir=path.abspath('.')
        ))

    def test_pass_builddir(self):
        ns = argparse.Namespace()
        with mock.patch('bfg9000.build.is_srcdir', return_value=False):
            self.pair(None, ns, path.abspath('foo'))
        self.assertEqual(ns, argparse.Namespace(
            srcdir=path.abspath('.'),
            builddir=path.abspath('foo')
        ))


class TestReloadException(unittest.TestCase):
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
            re.MULTILINE
        )

    def test_no_message_rerun(self):
        try:
            raise EnvVersionError()
        except EnvVersionError as e:
            driver.handle_reload_exception(e, True)

        assertRegex(self, self.stream.getvalue(),
                    'Unable to reload environment\n' +
                    '  Please re-run bfg9000 manually\n'
        )
