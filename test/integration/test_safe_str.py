import os.path
import re

from . import *


class TestSafeStr(IntegrationTest):
    def __init__(self, *args, **kwargs):
        IntegrationTest.__init__(
            self, 'safe_str', *args, **kwargs
        )

    def test_foo(self):
        f = re.escape(os.path.normpath(os.path.join(
            test_data_dir, 'safe_str', 'foo.txt'
        )))
        if env.host_platform.family == 'windows':
            f = '"?' + f + '"?'
        assertRegex(self, self.build('foo'), r"(?m)^\s*{}$".format(f))

    def test_bar(self):
        f = re.escape(os.path.normpath(os.path.join(
            test_data_dir, 'safe_str', 'bar.txt'
        )))
        if env.host_platform.family == 'windows':
            f = '"?' + f + '"?'
        assertRegex(self, self.build('bar'), r"(?m)^\s*{}$".format(f))
