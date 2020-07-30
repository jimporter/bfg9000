from unittest import mock

from bfg9000.builtins.install import installify
from bfg9000.path import Root

from .. import *


class MockInstallOutputs:
    class Mapping:
        def __init__(self, env=None, bad=set()):
            self.env = env
            self.bad = bad

        def __getitem__(self, key):
            if key.path.root == Root.absolute or key in self.bad:
                raise KeyError(key)
            return installify(key, cross=self.env)

    def __init__(self, env, bad=set()):
        self.host = self.Mapping(bad)
        self.target = self.Mapping(env, bad)


class ToolTestCase(CrossPlatformTestCase):
    def __init__(self, *args, **kwargs):
        super().__init__(clear_variables=True, *args, **kwargs)

    def setUp(self):
        with mock.patch('bfg9000.shell.which', return_value=['command']):
            self.tool = self.tool_type(self.env)
