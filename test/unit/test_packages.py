import unittest

from bfg9000.packages import *
from bfg9000.path import Path


class TestPackage(unittest.TestCase):
    def test_equality(self):
        self.assertTrue(Package('foo', 'elf') == Package('foo', 'elf'))
        self.assertFalse(Package('foo', 'elf') != Package('foo', 'elf'))

        self.assertFalse(Package('foo', 'elf') == Package('bar', 'elf'))
        self.assertTrue(Package('foo', 'elf') != Package('bar', 'elf'))
        self.assertFalse(Package('foo', 'elf') == Package('foo', 'coff'))
        self.assertTrue(Package('foo', 'elf') != Package('foo', 'coff'))


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
