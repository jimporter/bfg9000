import os.path
import re
import unittest
from six import assertRegex

from .integration import *


class TestCommand(IntegrationTest):
    def __init__(self, *args, **kwargs):
        IntegrationTest.__init__(
            self, os.path.join(examples_dir, '06_commands'), *args, **kwargs
        )

    @skip_if_backend('msbuild')
    def test_hello(self):
        assertRegex(self,
            self.build('hello'),
            re.compile('^hello$', re.MULTILINE)
        )

    @skip_if_backend('msbuild')
    def test_world(self):
        assertRegex(self,
            self.build('world'),
            re.compile('^world$', re.MULTILINE)
        )

    @skip_if_backend('msbuild')
    def test_script(self):
        assertRegex(self,
            self.build('script'),
            re.compile('^hello, world!$', re.MULTILINE)
        )
        self.assertExists(os.path.join(self.builddir, 'file'))

    @skip_if_backend('msbuild')
    def test_alias(self):
        output = self.build('hello-world')
        assertRegex(self, output, re.compile('^hello$', re.MULTILINE))
        assertRegex(self, output, re.compile('^world$', re.MULTILINE))


if __name__ == '__main__':
    unittest.main()
