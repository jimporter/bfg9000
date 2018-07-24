import unittest

from bfg9000.file_types import *
from bfg9000.path import Path


class TestNode(unittest.TestCase):
    def test_equality(self):
        self.assertTrue(Node('foo') == Node('foo'))
        self.assertFalse(Node('foo') != Node('foo'))

        self.assertFalse(Node('foo') == Node('bar'))
        self.assertTrue(Node('foo') != Node('bar'))


class TestDualUseLibrary(unittest.TestCase):
    def test_equality(self):
        shared_a = SharedLibrary(Path('shared_a'), 'elf')
        shared_b = SharedLibrary(Path('shared_b'), 'elf')
        static_a = SharedLibrary(Path('static_a'), 'elf')
        static_b = SharedLibrary(Path('static_b'), 'elf')

        D = DualUseLibrary

        self.assertTrue(D(shared_a, static_a) == D(shared_a, static_a))
        self.assertFalse(D(shared_a, static_a) != D(shared_a, static_a))

        self.assertFalse(D(shared_a, static_a) == D(shared_b, static_b))
        self.assertTrue(D(shared_a, static_a) != D(shared_b, static_b))


class TestFramework(unittest.TestCase):
    def test_full_name(self):
        self.assertEqual(Framework('foo').full_name, 'foo')
        self.assertEqual(Framework('foo', 'bar').full_name, 'foo,bar')

    def test_equality(self):
        self.assertTrue(Framework('foo') == Framework('foo'))
        self.assertFalse(Framework('foo') != Framework('foo'))
        self.assertTrue(Framework('foo', 'x') == Framework('foo', 'x'))
        self.assertFalse(Framework('foo', 'x') != Framework('foo', 'x'))

        self.assertFalse(Framework('foo') == Framework('bar'))
        self.assertTrue(Framework('foo') != Framework('bar'))
        self.assertFalse(Framework('foo', 'x') == Framework('bar', 'x'))
        self.assertTrue(Framework('foo', 'x') != Framework('bar', 'x'))
        self.assertFalse(Framework('foo', 'x') == Framework('foo', 'y'))
        self.assertTrue(Framework('foo', 'x') != Framework('foo', 'y'))
        self.assertFalse(Framework('foo', 'x') == Framework('foo'))
        self.assertTrue(Framework('foo', 'x') != Framework('foo'))
