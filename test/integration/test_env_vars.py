import re

from . import *


class TestEnvVars(IntegrationTest):
    def __init__(self, *args, **kwargs):
        IntegrationTest.__init__(self, 'env_vars', *args, **kwargs)

    @skip_if_backend('msbuild')
    def test_test(self):
        self.build('test')

    def test_command(self):
        assertRegex(self, self.build('script'),
                    re.compile(r'^\s*hello script$', re.MULTILINE))
        self.assertExists(output_file('file'))
