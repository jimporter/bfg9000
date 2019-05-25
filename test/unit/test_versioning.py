from . import *

from bfg9000.versioning import *


class TestSpecifierSet(TestCase):
    def test_empty(self):
        spec = SpecifierSet('')
        self.assertEqual(set(spec), set())

    def test_single(self):
        spec = SpecifierSet('>1.0')
        self.assertEqual(set(spec), {Specifier('>1.0')})

    def test_multiple(self):
        spec = SpecifierSet('>1.0,>1.1')
        self.assertEqual(set(spec), {Specifier('>1.0'), Specifier('>1.1')})

    def test_whitespace(self):
        spec = SpecifierSet(', >1.0, , >1.1 , ')
        self.assertEqual(set(spec), {Specifier('>1.0'), Specifier('>1.1')})


class TestSimplifySpecifiers(TestCase):
    def test_duplicate_equals(self):
        spec = SpecifierSet('==1.0,==1.0')
        self.assertEqual(simplify_specifiers(spec), SpecifierSet('==1.0'))

    def test_inconsistent_equals(self):
        spec = SpecifierSet('==1.0,==1.1')
        self.assertRaises(ValueError, simplify_specifiers, spec)

    def test_not_equals(self):
        spec = SpecifierSet('!=1.0,!=1.1')
        self.assertEqual(simplify_specifiers(spec), spec)

    def test_greater(self):
        spec = SpecifierSet('>1.0,>1.1')
        self.assertEqual(simplify_specifiers(spec), SpecifierSet('>1.1'))

    def test_greater_equal(self):
        spec = SpecifierSet('>=1.0,>=1.1')
        self.assertEqual(simplify_specifiers(spec), SpecifierSet('>=1.1'))

    def test_greater_mixed(self):
        spec = SpecifierSet('>1.0,>=1.1')
        self.assertEqual(simplify_specifiers(spec), SpecifierSet('>=1.1'))

    def test_less(self):
        spec = SpecifierSet('<1.0,<1.1')
        self.assertEqual(simplify_specifiers(spec), SpecifierSet('<1.0'))

    def test_less_equal(self):
        spec = SpecifierSet('<=1.0,<=1.1')
        self.assertEqual(simplify_specifiers(spec), SpecifierSet('<=1.0'))

    def test_less_mixed(self):
        spec = SpecifierSet('<=1.0,<1.1')
        self.assertEqual(simplify_specifiers(spec), SpecifierSet('<=1.0'))

    def test_range(self):
        spec = SpecifierSet('>1.0,<1.1')
        self.assertEqual(simplify_specifiers(spec), spec)

    def test_range_equals(self):
        spec = SpecifierSet('>1.0,<2.0,==1.1')
        self.assertEqual(simplify_specifiers(spec), SpecifierSet('==1.1'))

    def test_range_identifies_single_version(self):
        spec = SpecifierSet('>=1.0,<=1.0')
        self.assertEqual(simplify_specifiers(spec), SpecifierSet('==1.0'))

    def test_inconsistent_range(self):
        spec = SpecifierSet('<1.0,>1.1')
        self.assertRaises(ValueError, simplify_specifiers, spec)

    def test_range_equals_out_of_range(self):
        spec = SpecifierSet('>1.0,<2.0,==3.0')
        self.assertRaises(ValueError, simplify_specifiers, spec)
        spec = SpecifierSet('>1.0,<2.0,==0.1')
        self.assertRaises(ValueError, simplify_specifiers, spec)

    def test_python_specifier_set(self):
        spec = PythonSpecifierSet('>1.0,<1.1')
        self.assertEqual(simplify_specifiers(spec), SpecifierSet('>1.0,<1.1'))

    def test_invalid_specifier(self):
        spec = PythonSpecifierSet('~=1.0')
        self.assertRaises(ValueError, simplify_specifiers, spec)


class TestCheckVersion(TestCase):
    def test_success(self):
        check_version(Version('1.0'), SpecifierSet('>=1.0'), 'compiler')

    def test_failure(self):
        assertRaisesRegex(
            self,
            VersionError,
            "^compiler version 1.0 doesn't meet requirement >=2.0$",
            check_version, Version('1.0'), SpecifierSet('>=2.0'), 'compiler'
        )


class TestDetectVersion(TestCase):
    def test_simple(self):
        self.assertEqual(detect_version('gcc 1.2.3 4.5'), Version('1.2.3'))

    def test_pre(self):
        self.assertEqual(detect_version('4.5 gcc 1.2.3', pre=r'gcc\s+'),
                         Version('1.2.3'))

    def test_post(self):
        self.assertEqual(detect_version('4.5 gcc 1.2.3', post=r'$'),
                         Version('1.2.3'))

    def test_no_match(self):
        self.assertEqual(detect_version('gcc'), None)
