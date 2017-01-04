import os.path
import re
from six import assertRegex

from . import *


@skip_if_backend('msbuild')
class TestEnvVars(IntegrationTest):
    def __init__(self, *args, **kwargs):
        IntegrationTest.__init__(self, 'env_vars', *args, **kwargs)

    def test_test(self):
        self.build('test')

    def test_command(self):
        assertRegex(self, self.build('script'),
                    re.compile('^hello script$', re.MULTILINE))
        self.assertExists(os.path.join(self.builddir, 'file'))
