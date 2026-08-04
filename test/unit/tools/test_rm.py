from . import *

from bfg9000.tools.rm import Rm


class TestRm(ToolTestCase):
    tool_type = Rm

    def test_env(self):
        with mock.patch('bfg9000.shell.which', mock_which):
            self.assertIsInstance(self.env.tool('rm'), Rm)

    def test_rm(self):
        self.assertEqual(self.tool(['foo', 'bar']), [self.tool, 'foo', 'bar'])
