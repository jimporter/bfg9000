from . import *

from bfg9000.tools import scripts
from bfg9000.file_types import SourceFile, HeaderFile
from bfg9000.path import Root


class TestPython(ToolTestCase):
    tool_type = scripts.Python
    lang = 'python'

    def test_env(self):
        with mock.patch('bfg9000.shell.which', return_value=['command']):
            self.assertIsInstance(self.env.tool(self.lang), self.tool_type)

    def test_call(self):
        self.assertEqual(self.tool('file'), [self.tool, 'file'])

    def test_run_arguments(self):
        src_file = SourceFile(self.Path('file', Root.srcdir), lang=self.lang)
        self.assertEqual(self.tool.run_arguments(src_file),
                         [self.tool, src_file])

        with mock.patch('bfg9000.shell.which', return_value=['command']):
            args = self.env.run_arguments(src_file)
        self.assertEqual(len(args), 2)
        self.assertEqual(type(args[0]), self.tool_type)
        self.assertEqual(args[1], src_file)

    def test_invalid_run_arguments(self):
        bad_file = HeaderFile(self.Path('file', Root.srcdir), lang=self.lang)
        with self.assertRaises(TypeError):
            self.tool.run_arguments(bad_file)

        with mock.patch('bfg9000.shell.which', return_value=['command']), \
             self.assertRaises(TypeError):  # noqa
            self.env.run_arguments(bad_file)


class TestLua(TestPython):
    tool_type = scripts.Lua
    lang = 'lua'


class TestPerl(TestPython):
    tool_type = scripts.Perl
    lang = 'perl'


class TestRuby(TestPython):
    tool_type = scripts.Ruby
    lang = 'ruby'
