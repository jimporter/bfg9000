import os.path
import re
from six import assertRegex

from . import *


class TestCommand(IntegrationTest):
    def __init__(self, *args, **kwargs):
        IntegrationTest.__init__(
            self, os.path.join(examples_dir, '07_commands'), *args, **kwargs
        )

    def test_hello(self):
        assertRegex(self, self.build('hello'),
                    re.compile(r'^\s*hello$', re.MULTILINE))

    def test_world(self):
        assertRegex(self, self.build('world'),
                    re.compile(r'^\s*world$', re.MULTILINE))

    def test_script(self):
        assertRegex(self, self.build('script'),
                    re.compile(r'^\s*hello, world!$', re.MULTILINE))
        self.assertExists(output_file('file'))

    def test_alias(self):
        output = self.build('hello-world')
        assertRegex(self, output, re.compile(r'^\s*hello$', re.MULTILINE))
        assertRegex(self, output, re.compile(r'^\s*world$', re.MULTILINE))
