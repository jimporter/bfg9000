from . import *

from bfg9000 import packages


class TestPackage(TestCase):
    def test_equality(self):
        P = packages.Package
        self.assertTrue(P('foo', format='elf') == P('foo', format='elf'))
        self.assertFalse(P('foo', format='elf') != P('foo', format='elf'))

        self.assertFalse(P('foo', format='elf') == P('bar', format='elf'))
        self.assertTrue(P('foo', format='elf') != P('bar', format='elf'))
        self.assertFalse(P('foo', format='elf') == P('foo', format='coff'))
        self.assertTrue(P('foo', format='elf') != P('foo', format='coff'))


class TestFramework(TestCase):
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
