import unittest

from bfg9000.builtins.pkg_config import *
from bfg9000.safe_str import safe_str, shell_literal


class TestPkgConfigRequirement(unittest.TestCase):
    def test_merge_requirements(self):
        a = Requirement('foo', '>=1.0')
        b = Requirement('foo', '<=2.0')
        c = Requirement('bar', '<=2.0')

        self.assertEqual(a & b, Requirement('foo', '>=1.0,<=2.0'))
        a &= b
        self.assertEqual(a, Requirement('foo', '>=1.0,<=2.0'))
        self.assertRaises(ValueError, lambda: b & c)

    def test_split_requirement(self):
        a = Requirement('foo')
        self.assertEqual(set(a.split()), {SimpleRequirement('foo')})
        a = Requirement('foo', '>=1.0')
        self.assertEqual(set(a.split()), {SimpleRequirement('foo', '>=1.0')})
        a = Requirement('foo', '>=1.0,<=2.0')
        self.assertEqual(set(a.split()), {SimpleRequirement('foo', '>=1.0'),
                                          SimpleRequirement('foo', '<=2.0')})

    def test_split_requirement_single(self):
        a = Requirement('foo')
        self.assertEqual(set(a.split(True)), {SimpleRequirement('foo')})
        a = Requirement('foo', '>=1.0')
        self.assertEqual(set(a.split(True)),
                         {SimpleRequirement('foo', '>=1.0')})
        a = Requirement('foo', '>=1.0,<=2.0')
        self.assertRaises(ValueError, lambda: a.split(True))


class TestPkgConfigSimpleRequirement(unittest.TestCase):
    def test_stringify(self):
        r = SimpleRequirement('foo', '>=1.0')
        self.assertEqual(safe_str(r), shell_literal('foo >= 1.0'))

    def test_stringify_equal(self):
        r = SimpleRequirement('foo', '==1.0')
        self.assertEqual(safe_str(r), shell_literal('foo = 1.0'))

    def test_stringify_no_version(self):
        r = SimpleRequirement('foo')
        self.assertEqual(safe_str(r), shell_literal('foo'))


class TestPkgConfigRequirementSet(unittest.TestCase):
    def test_init(self):
        s = RequirementSet([Requirement('foo', '>=1.0'),
                            Requirement('foo', '<=2.0'),
                            Requirement('bar', '>=3.0')])
        self.assertEqual(set(s), {Requirement('foo', '>=1.0,<=2.0'),
                                  Requirement('bar', '>=3.0')})

    def test_add(self):
        s = RequirementSet()
        s.add(Requirement('foo', '>=1.0'))
        s.add(Requirement('foo', '<=2.0'))
        s.add(Requirement('bar', '>=3.0'))
        self.assertEqual(set(s), {Requirement('foo', '>=1.0,<=2.0'),
                                  Requirement('bar', '>=3.0')})

    def test_remove(self):
        s = RequirementSet([Requirement('foo', '>=1.0'),
                            Requirement('foo', '<=2.0'),
                            Requirement('bar', '>=3.0')])
        s.remove('foo')
        self.assertEqual(set(s), {Requirement('bar', '>=3.0')})

    def test_update(self):
        a = RequirementSet([Requirement('foo', '>=1.0'),
                            Requirement('bar', '>=3.0')])
        b = RequirementSet([Requirement('foo', '<=2.0'),
                            Requirement('baz', '>=4.0')])
        a.update(b)
        self.assertEqual(set(a), {Requirement('foo', '>=1.0,<=2.0'),
                                  Requirement('bar', '>=3.0'),
                                  Requirement('baz', '>=4.0')})

    def test_merge_from(self):
        a = RequirementSet([Requirement('foo', '>=1.0'),
                            Requirement('bar', '>=3.0')])
        b = RequirementSet([Requirement('foo', '<=2.0'),
                            Requirement('baz', '>=4.0')])
        a.merge_from(b)
        self.assertEqual(set(a), {Requirement('foo', '>=1.0,<=2.0'),
                                  Requirement('bar', '>=3.0')})
        self.assertEqual(set(b), {Requirement('baz', '>=4.0')})

    def test_split(self):
        s = RequirementSet([Requirement('foo', '>=1.0'),
                            Requirement('foo', '<=2.0'),
                            Requirement('bar', '>=3.0')])
        self.assertEqual(set(s.split()), {SimpleRequirement('bar', '>=3.0'),
                                          SimpleRequirement('foo', '>=1.0'),
                                          SimpleRequirement('foo', '<=2.0')})
