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
