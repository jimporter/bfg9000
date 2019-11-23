import mock

from ... import *

from bfg9000.backends.ninja.writer import version
from bfg9000.versioning import Version


def mock_bad_which(*args, **kwargs):
    raise IOError()


def mock_bad_execute(*args, **kwargs):
    raise OSError()


class TestNinjaVersion(TestCase):
    def test_good(self):
        with mock.patch('bfg9000.shell.which', return_value=['command']), \
             mock.patch('bfg9000.shell.execute', return_value='1.23'):  # noqa
            self.assertEqual(version({}), Version('1.23'))

    def test_not_found(self):
        with mock.patch('bfg9000.shell.which', mock_bad_which):
            self.assertEqual(version({}), None)

    def test_bad_execute(self):
        with mock.patch('bfg9000.shell.which', return_value=['command']), \
             mock.patch('bfg9000.shell.execute', mock_bad_execute):  # noqa
            self.assertEqual(version({}), None)