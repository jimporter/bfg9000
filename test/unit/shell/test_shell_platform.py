import subprocess
import sys
from textwrap import dedent

from .. import *


class TestShellPlatform(TestCase):
    def _do_quote(self, platform_name):
        # Run this test in a subprocess so we don't foul up the state of our
        # imported `bfg9000.shell` module for other tests.
        return subprocess.run([
            sys.executable, '-c', dedent("""
            from unittest import mock
            with mock.patch('bfg9000.platforms.core.platform_name',
                            return_value={!r}):
                from bfg9000 import shell
            print(shell.quote('foo bar'), end='')
            """.format(platform_name)),
        ], stdout=subprocess.PIPE, universal_newlines=True).stdout

    def test_windows(self):
        self.assertEqual(self._do_quote('winnt'), '"foo bar"')

    def test_linux(self):
        self.assertEqual(self._do_quote('linux'), "'foo bar'")
