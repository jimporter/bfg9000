from unittest import mock

from .. import *


class ToolTestCase(CrossPlatformTestCase):
    def __init__(self, *args, **kwargs):
        CrossPlatformTestCase.__init__(self, clear_variables=True, *args,
                                       **kwargs)

    def setUp(self):
        with mock.patch('bfg9000.shell.which', return_value=['command']):
            self.tool = self.tool_type(self.env)
