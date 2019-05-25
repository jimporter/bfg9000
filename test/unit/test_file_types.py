from . import *

from bfg9000 import file_types
from bfg9000.path import Path


class TestNode(TestCase):
    def test_equality(self):
        self.assertTrue(file_types.Node('foo') == file_types.Node('foo'))
        self.assertFalse(file_types.Node('foo') != file_types.Node('foo'))

        self.assertFalse(file_types.Node('foo') == file_types.Node('bar'))
        self.assertTrue(file_types.Node('foo') != file_types.Node('bar'))


class TestDualUseLibrary(TestCase):
    def test_equality(self):
        shared_a = file_types.SharedLibrary(Path('shared_a'), 'elf')
        shared_b = file_types.SharedLibrary(Path('shared_b'), 'elf')
        static_a = file_types.SharedLibrary(Path('static_a'), 'elf')
        static_b = file_types.SharedLibrary(Path('static_b'), 'elf')

        Dual = file_types.DualUseLibrary

        self.assertTrue(Dual(shared_a, static_a) == Dual(shared_a, static_a))
        self.assertFalse(Dual(shared_a, static_a) != Dual(shared_a, static_a))

        self.assertFalse(Dual(shared_a, static_a) == Dual(shared_b, static_b))
        self.assertTrue(Dual(shared_a, static_a) != Dual(shared_b, static_b))
