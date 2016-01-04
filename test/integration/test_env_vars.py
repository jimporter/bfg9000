import os.path
import re
import unittest

from integration import *


class TestEnvVars(IntegrationTest):
    def __init__(self, *args, **kwargs):
        IntegrationTest.__init__(self, 'env_vars', *args, **kwargs)

    @skip_if_backend('msbuild')
    def test_test(self):
        self.build('test')

    @skip_if_backend('msbuild')
    def test_command(self):
        self.assertRegexpMatches(
            self.build('script'),
            re.compile('^hello script$', re.MULTILINE)
        )
        self.assertExists(os.path.join(self.builddir, 'file'))


if __name__ == '__main__':
    unittest.main()
