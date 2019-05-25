import mock
import sys

from .. import *

from bfg9000.tools import scripts
from bfg9000.environment import Environment
from bfg9000.file_types import SourceFile, HeaderFile
from bfg9000.path import Root


def mock_getvar(self, key, default=None):
    return default


def mock_which(*args, **kwargs):
    return args[0]


class TestPython(CrossPlatformTestCase):
    ToolType = scripts.Python
    lang = 'python'
    default_cmd = sys.executable

    def setUp(self):
        with mock.patch.object(Environment, 'getvar', mock_getvar), \
             mock.patch('bfg9000.shell.which', mock_which):  # noqa
            self.tool = self.ToolType(self.env)

    def test_call(self):
        self.assertEqual(self.tool('file'), [self.tool, 'file'])

    def test_run_arguments(self):
        src_file = SourceFile(self.Path('file', Root.srcdir), lang=self.lang)
        self.assertEqual(self.tool.run_arguments(src_file),
                         [self.tool, src_file])

        with mock.patch('bfg9000.shell.which', mock_which):
            args = self.env.run_arguments(src_file)
        self.assertEqual(len(args), 2)
        self.assertEqual(type(args[0]), self.ToolType)
        self.assertEqual(args[1], src_file)

    def test_invalid_run_arguments(self):
        bad_file = HeaderFile(self.Path('file', Root.srcdir), lang=self.lang)
        with self.assertRaises(TypeError):
            self.tool.run_arguments(bad_file)

        with mock.patch('bfg9000.shell.which', mock_which), \
             self.assertRaises(TypeError):  # noqa
            self.env.run_arguments(bad_file)


class TestLua(TestPython):
    ToolType = scripts.Lua
    default_cmd = 'lua'
    lang = 'lua'


class TestPerl(TestPython):
    ToolType = scripts.Perl
    lang = 'perl'
    default_cmd = 'perl'


class TestRuby(TestPython):
    ToolType = scripts.Ruby
    lang = 'ruby'
    default_cmd = 'ruby'
