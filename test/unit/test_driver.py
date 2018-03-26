import logging
import mock
import re
import unittest
from six import assertRegex
from six.moves import cStringIO as StringIO

from bfg9000 import driver, log
from bfg9000.environment import EnvVersionError


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
