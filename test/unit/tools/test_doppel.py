from . import *

from bfg9000.tools.doppel import Doppel


class TestDoppel(ToolTestCase):
    tool_type = Doppel

    def test_env(self):
        with mock.patch('bfg9000.shell.which', return_value=['command']):
            self.assertIsInstance(self.env.tool('doppel'), Doppel)

    def test_kind_args(self):
        self.assertEqual(type(self.tool.kind_args('program')), list)
        self.assertEqual(type(self.tool.kind_args('data')), list)
        self.assertRaises(ValueError, self.tool.kind_args, 'unknown')

    def test_call_onto(self):
        self.assertEqual(self.tool('onto', 'src', 'dst'),
                         [self.tool, '-p', 'src', 'dst'])

    def test_call_into(self):
        self.assertEqual(self.tool('into', 'src', 'dst'),
                         [self.tool, '-ipN', 'src', 'dst'])
        self.assertEqual(self.tool('into', ['src1', 'src2'], 'dst'),
                         [self.tool, '-ipN', 'src1', 'src2', 'dst'])
        self.assertEqual(self.tool('into', 'src', 'dst', directory='dir'),
                         [self.tool, '-ipN', '-C', 'dir', 'src', 'dst'])

    def test_call_archive(self):
        self.assertEqual(self.tool('archive', 'src', 'dst', format='tar'),
                         [self.tool, '-ipN', '-f', 'tar', 'src', 'dst'])
        self.assertEqual(
            self.tool('archive', ['src1', 'src2'], 'dst', format='tar'),
            [self.tool, '-ipN', '-f', 'tar', 'src1', 'src2', 'dst']
        )
        self.assertEqual(
            self.tool('archive', 'src', 'dst', directory='dir', format='tar'),
            [self.tool, '-ipN', '-f', 'tar', '-C', 'dir', 'src', 'dst']
        )
        self.assertEqual(
            self.tool('archive', 'src', 'dst', format='tar',
                      dest_prefix='pre'),
            [self.tool, '-ipN', '-f', 'tar', '-P', 'pre', 'src', 'dst']
        )

    def test_call_invalid(self):
        self.assertRaises(ValueError, self.tool, 'unknown', 'src', 'dst')
