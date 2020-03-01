import re

from . import *


class TestEnvVars(IntegrationTest):
    def __init__(self, *args, **kwargs):
        super().__init__('env_vars', *args, **kwargs)

    @skip_if_backend('msbuild')
    def test_test(self):
        self.build('test')

    def test_command(self):
        self.assertRegex(self.build('script'),
                         re.compile(r'^\s*hello script$', re.MULTILINE))
        self.assertExists(output_file('file'))
