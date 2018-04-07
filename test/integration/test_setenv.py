import os.path
import re
import sys
from six import assertRegex

from . import *


class TestSetEnv(TestCase):
    def assertRun(self, extra, *args, **kwargs):
        # This is a bit complex because `bfg9000-setenv` is only actually
        # installed on Windows.
        self.assertOutput(
            [sys.executable, '-c',
             'from bfg9000.setenv import main; exit(main())'] + extra,
            *args, **kwargs
        )

    def test_no_args(self):
        self.assertRun([], output='bfg9000-setenv: COMMAND is required\n',
                       returncode=1)

    def test_no_command(self):
        self.assertRun(['FOO=bar'],
                       output='bfg9000-setenv: COMMAND is required\n',
                       returncode=1)

    def test_command(self):
        self.assertRun(['--', sys.executable, '-c', 'print("hi")'],
                       output='hi\n')

    def test_command_and_args(self):
        self.assertRun(['--', 'FOO=bar', sys.executable, '-c',
                        'import os; print(os.environ["FOO"])'],
                       output='bar\n')
