from . import *

from bfg9000.safe_str import shell_literal
from bfg9000.shell.list import shell_list
from bfg9000.tools.internal import Bfg9000, Depfixer, JvmOutput, RccDep


class TestBfg9000(ToolTestCase):
    tool_type = Bfg9000

    def test_env(self):
        with mock.patch('bfg9000.shell.which', return_value=['command']):
            self.assertIsInstance(self.env.tool('bfg9000'), Bfg9000)

    def test_regenerate(self):
        self.assertEqual(self.tool('regenerate', 'builddir'),
                         [self.tool, 'regenerate', 'builddir'])

    def test_run(self):
        self.assertEqual(self.tool('run', args=['echo', 'hi']),
                         [self.tool, 'run', '--', 'echo', 'hi'])
        self.assertEqual(self.tool('run', args=['echo', 'hi'], initial=True),
                         [self.tool, 'run', '-I', '--', 'echo', 'hi'])

    def test_call_invalid(self):
        self.assertRaises(TypeError, self.tool, 'unknown')


class TestDepfixer(ToolTestCase):
    tool_type = Depfixer

    def test_env(self):
        with mock.patch('bfg9000.shell.which', return_value=['command']):
            self.assertIsInstance(self.env.tool('depfixer'), Depfixer)

    def test_depfixer(self):
        self.assertEqual(self.tool('depfile'), shell_list([
            self.tool, shell_literal('<'), 'depfile', shell_literal('>>'),
            'depfile'
        ]))


class TestJvmOutput(ToolTestCase):
    tool_type = JvmOutput

    def test_env(self):
        with mock.patch('bfg9000.shell.which', return_value=['command']):
            self.assertIsInstance(self.env.tool('jvmoutput'), JvmOutput)

    def test_jvmoutput(self):
        self.assertEqual(self.tool('output', ['echo', 'hi']),
                         [self.tool, '-o', 'output', '--', 'echo', 'hi'])


class TestRccDep(ToolTestCase):
    tool_type = RccDep

    def test_env(self):
        with mock.patch('bfg9000.shell.which', return_value=['command']):
            self.assertIsInstance(self.env.tool('rccdep'), RccDep)

    def test_rccdep(self):
        self.assertEqual(self.tool(['echo', 'hi'], 'depfile'),
                         [self.tool, 'echo', 'hi', '-d', 'depfile'])
