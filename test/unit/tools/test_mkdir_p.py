from . import *

from bfg9000.tools.mkdir_p import MkdirP


class TestMkdirP(ToolTestCase):
    tool_type = MkdirP

    def test_env(self):
        with mock.patch('bfg9000.shell.which', return_value=['command']):
            self.assertIsInstance(self.env.tool('mkdir_p'), MkdirP)

    def test_mkdir(self):
        self.assertEqual(self.tool('path'), [self.tool, 'path'])
