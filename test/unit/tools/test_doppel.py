import mock

from .. import *

from bfg9000.tools.doppel import Doppel


class TestDoppel(CrossPlatformTestCase):
    def __init__(self, *args, **kwargs):
        CrossPlatformTestCase.__init__(self, clear_variables=True, *args,
                                       **kwargs)

    def setUp(self):
        with mock.patch('bfg9000.shell.which', return_value=['command']):
            self.doppel = Doppel(self.env)

    def test_data_args(self):
        self.assertEqual(type(self.doppel.data_args), list)

    def test_call_onto(self):
        self.assertEqual(self.doppel('onto', 'src', 'dst'),
                         [self.doppel, '-p', 'src', 'dst'])

    def test_call_into(self):
        self.assertEqual(self.doppel('into', 'src', 'dst'),
                         [self.doppel, '-ipN', 'src', 'dst'])
        self.assertEqual(self.doppel('into', ['src1', 'src2'], 'dst'),
                         [self.doppel, '-ipN', 'src1', 'src2', 'dst'])
        self.assertEqual(self.doppel('into', 'src', 'dst', directory='dir'),
                         [self.doppel, '-ipN', '-C', 'dir', 'src', 'dst'])

    def test_call_archive(self):
        self.assertEqual(self.doppel('archive', 'src', 'dst', format='tar'),
                         [self.doppel, '-ipN', '-f', 'tar', 'src', 'dst'])
        self.assertEqual(
            self.doppel('archive', ['src1', 'src2'], 'dst', format='tar'),
            [self.doppel, '-ipN', '-f', 'tar', 'src1', 'src2', 'dst']
        )
        self.assertEqual(
            self.doppel('archive', 'src', 'dst', directory='dir',
                        format='tar'),
            [self.doppel, '-ipN', '-f', 'tar', '-C', 'dir', 'src', 'dst']
        )
        self.assertEqual(
            self.doppel('archive', 'src', 'dst', format='tar',
                        dest_prefix='pre'),
            [self.doppel, '-ipN', '-f', 'tar', '-P', 'pre', 'src', 'dst']
        )

    def test_call_invalid(self):
        self.assertRaises(ValueError, self.doppel, 'unknown', 'src', 'dst')
