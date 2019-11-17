from . import *

from bfg9000.tools.patchelf import PatchElf


class TestPatchElf(ToolTestCase):
    tool_type = PatchElf

    def test_env(self):
        with mock.patch('bfg9000.shell.which', return_value=['command']):
            self.assertIsInstance(self.env.tool('patchelf'), PatchElf)

    def test_none(self):
        self.assertEqual(self.tool('path'), None)

    def test_rpath(self):
        self.assertEqual(self.tool('path', ['foo', 'bar']), [
            self.tool, '--set-rpath', 'foo:bar', 'path'
        ])
