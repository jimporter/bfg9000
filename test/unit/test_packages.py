import unittest

from bfg9000 import packages


class TestPackage(unittest.TestCase):
    def test_equality(self):
        Package = packages.Package
        self.assertTrue(Package('foo', 'elf') == Package('foo', 'elf'))
        self.assertFalse(Package('foo', 'elf') != Package('foo', 'elf'))

        self.assertFalse(Package('foo', 'elf') == Package('bar', 'elf'))
        self.assertTrue(Package('foo', 'elf') != Package('bar', 'elf'))
        self.assertFalse(Package('foo', 'elf') == Package('foo', 'coff'))
        self.assertTrue(Package('foo', 'elf') != Package('foo', 'coff'))


class TestFramework(unittest.TestCase):
    def test_full_name(self):
        self.assertEqual(packages.Framework('foo').full_name, 'foo')
        self.assertEqual(packages.Framework('foo', 'bar').full_name, 'foo,bar')

    def test_equality(self):
        Framework = packages.Framework
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
