from io import StringIO

from .common import BuiltinTest, TestCase

from bfg9000.builtins import project  # noqa
from bfg9000.builtins.pkg_config import *
from bfg9000.file_types import PkgConfigPcFile
from bfg9000.path import Path
from bfg9000.safe_str import safe_str, shell_literal


class TestPkgConfigRequirement(TestCase):
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

    def test_equality(self):
        R, S = Requirement, SimpleRequirement
        self.assertTrue(R('foo', '>=1.0') == R('foo', '>=1.0'))
        self.assertFalse(R('foo', '>=1.0') != R('foo', '>=1.0'))

        self.assertTrue(S('foo', '>=1.0') == S('foo', '>=1.0'))
        self.assertFalse(S('foo', '>=1.0') != S('foo', '>=1.0'))

        self.assertFalse(R('foo', '>=1.0') == R('bar', '>=1.0'))
        self.assertTrue(R('foo', '>=1.0') != R('bar', '>=1.0'))
        self.assertFalse(R('foo', '>=1.0') == R('foo', '>=2.0'))
        self.assertTrue(R('foo', '>=1.0') != R('foo', '>=2.0'))

        self.assertFalse(S('foo', '>=1.0') == S('bar', '>=1.0'))
        self.assertTrue(S('foo', '>=1.0') != S('bar', '>=1.0'))
        self.assertFalse(S('foo', '>=1.0') == S('foo', '>=2.0'))
        self.assertTrue(S('foo', '>=1.0') != S('foo', '>=2.0'))

        self.assertFalse(R('foo', '>=1.0') == S('foo', '>=1.0'))
        self.assertTrue(R('foo', '>=1.0') != S('foo', '>=1.0'))
        self.assertFalse(S('foo', '>=1.0') == R('foo', '>=1.0'))
        self.assertTrue(S('foo', '>=1.0') != R('foo', '>=1.0'))


class TestPkgConfigSimpleRequirement(TestCase):
    def test_stringify(self):
        r = SimpleRequirement('foo', '>=1.0')
        self.assertEqual(safe_str(r), shell_literal('foo >= 1.0'))

    def test_stringify_equal(self):
        r = SimpleRequirement('foo', '==1.0')
        self.assertEqual(safe_str(r), shell_literal('foo = 1.0'))

    def test_stringify_no_version(self):
        r = SimpleRequirement('foo')
        self.assertEqual(safe_str(r), shell_literal('foo'))


class TestPkgConfigRequirementSet(TestCase):
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


class TestPkgConfig(BuiltinTest):
    def test_minimal(self):
        pkg = PkgConfigInfo(self.context, name='package',
                            version='1.0')
        self.assertEqual(pkg.output, PkgConfigPcFile(Path(
            'pkgconfig/package.pc'
        )))

        out = StringIO()
        pkg.write(out, self.env)
        self.assertRegex(out.getvalue(),
                         '\n\nName: package\n' +
                         'Description: package library\n' +
                         'Version: 1.0\n$')

    def test_metadata(self):
        pkg = PkgConfigInfo(
            self.context, name='package', desc_name='my-package',
            desc='a cool package', url='http://www.example.com/', version='1.0'
        )
        self.assertEqual(pkg.output, PkgConfigPcFile(Path(
            'pkgconfig/package.pc'
        )))

        out = StringIO()
        pkg.write(out, self.env)
        self.assertRegex(out.getvalue(),
                         '\n\nName: my-package\n' +
                         'Description: a cool package\n' +
                         'URL: http://www.example.com/\n' +
                         'Version: 1.0\n$')

    def test_requires(self):
        pkg = PkgConfigInfo(
            self.context, name='package', version='1.0',
            requires=['req', ('vreq', '>=1.0')]
        )

        out = StringIO()
        pkg.write(out, self.env)
        self.assertRegex(out.getvalue(),
                         '\nRequires: req, vreq >= 1.0\n')

        with self.assertRaises(TypeError):
            pkg = PkgConfigInfo(self.context, requires=[1])
