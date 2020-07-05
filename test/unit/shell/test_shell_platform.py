import importlib
from unittest import mock

from .. import *

from bfg9000 import shell  # noqa


class TestShellPlatform(TestCase):
    @classmethod
    def tearDownClass(cls):
        importlib.reload(shell)

    def test_windows(self):
        with mock.patch('bfg9000.platforms.platform_name',
                        return_value='winnt'):
            importlib.reload(shell)
            self.assertEqual(shell.quote('foo bar'), '"foo bar"')

    def test_linux(self):
        with mock.patch('bfg9000.platforms.platform_name',
                        return_value='linux'):
            importlib.reload(shell)
            self.assertEqual(shell.quote('foo bar'), "'foo bar'")
