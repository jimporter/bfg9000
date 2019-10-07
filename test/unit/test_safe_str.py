from bfg9000 import safe_str

from . import *

jbos = safe_str.jbos
literal = safe_str.literal
shell_literal = safe_str.shell_literal


class MyString(object):
    def _safe_str(self):
        return 'foo'


class MyLiteral(object):
    def _safe_str(self):
        return literal('foo')


class MySafeStr(safe_str.safe_string):
    def __init__(self, i):
        self.i = i

    def __eq__(self, rhs):
        return type(self) == type(rhs) and self.i == rhs.i


class TestSafeStr(TestCase):
    def test_string(self):
        self.assertEqual(safe_str.safe_str('foo'), 'foo')

    def test_literals(self):
        self.assertEqual(safe_str.safe_str(literal('foo')), literal('foo'))
        self.assertEqual(safe_str.safe_str(shell_literal('foo')),
                         shell_literal('foo'))

    def test_jbos(self):
        self.assertEqual(safe_str.safe_str(jbos('foo')), jbos('foo'))

    def test_objects(self):
        self.assertEqual(safe_str.safe_str(MyString()), 'foo')
        self.assertEqual(safe_str.safe_str(MyLiteral()), literal('foo'))
        self.assertEqual(safe_str.safe_str(MySafeStr(1)), MySafeStr(1))

    def test_invalid(self):
        self.assertRaises(NotImplementedError, safe_str.safe_str, 123)


class TestLiteral(TestCase):
    def test_construct_from_string(self):
        self.assertEqual(literal('foo').string, 'foo')
        self.assertEqual(shell_literal('foo').string, 'foo')

    def test_construct_invalid(self):
        self.assertRaises(TypeError, literal, 123)
        self.assertRaises(TypeError, shell_literal, 123)

    def test_convert_to_str(self):
        with self.assertRaises(NotImplementedError):
            str(safe_str.literal('foo'))
        with self.assertRaises(NotImplementedError):
            str(safe_str.shell_literal('foo'))

    def test_equality(self):
        self.assertTrue(literal('foo') == literal('foo'))
        self.assertTrue(shell_literal('foo') == shell_literal('foo'))
        self.assertFalse(literal('foo') != literal('foo'))
        self.assertFalse(shell_literal('foo') != shell_literal('foo'))

        self.assertFalse(literal('foo') == literal('bar'))
        self.assertFalse(shell_literal('foo') == shell_literal('bar'))
        self.assertTrue(literal('foo') != literal('bar'))
        self.assertTrue(shell_literal('foo') != shell_literal('bar'))

        self.assertFalse(literal('foo') == shell_literal('foo'))
        self.assertFalse(shell_literal('foo') == literal('foo'))
        self.assertTrue(literal('foo') != shell_literal('foo'))
        self.assertTrue(shell_literal('foo') != literal('foo'))

    def test_concatenate(self):
        s = literal('foo') + 'bar'
        self.assertEqual(s.bits, (literal('foo'), 'bar'))

        s = 'foo' + literal('bar')
        self.assertEqual(s.bits, ('foo', literal('bar')))

        s = literal('foo') + literal('bar')
        self.assertEqual(s.bits, (literal('foobar'),))

        s = shell_literal('foo') + 'bar'
        self.assertEqual(s.bits, (shell_literal('foo'), 'bar'))

        s = 'foo' + shell_literal('bar')
        self.assertEqual(s.bits, ('foo', shell_literal('bar')))

        s = shell_literal('foo') + shell_literal('bar')
        self.assertEqual(s.bits, (shell_literal('foobar'),))

        s = literal('foo') + shell_literal('bar')
        self.assertEqual(s.bits, (literal('foo'), shell_literal('bar')))

        s = shell_literal('foo') + literal('bar')
        self.assertEqual(s.bits, (shell_literal('foo'), literal('bar')))


class TestJbos(TestCase):
    def test_construct_from_strings(self):
        s = jbos('foo', literal('bar'), shell_literal('baz'))
        self.assertEqual(s.bits, ('foo', literal('bar'), shell_literal('baz')))

    def test_construct_from_jbos(self):
        s = jbos(jbos('foo', literal('bar')), jbos(shell_literal('baz')))
        self.assertEqual(s.bits, ('foo', literal('bar'), shell_literal('baz')))

    def test_canonicalize(self):
        s = jbos('foo', 'bar')
        self.assertEqual(s.bits, ('foobar',))

        s = jbos(literal('foo'), literal('bar'))
        self.assertEqual(s.bits, (literal('foobar'),))

        s = jbos(shell_literal('foo'), shell_literal('bar'))
        self.assertEqual(s.bits, (shell_literal('foobar'),))

    def test_construct_invalid(self):
        self.assertRaises(TypeError, jbos, 123)

    def test_concatenate(self):
        s = jbos('foo') + literal('bar')
        self.assertEqual(s.bits, ('foo', literal('bar')))

        s = jbos('foo') + shell_literal('bar')
        self.assertEqual(s.bits, ('foo', shell_literal('bar')))

        s = jbos('foo') + 'bar'
        self.assertEqual(s.bits, ('foobar',))

        s = literal('foo') + jbos('bar')
        self.assertEqual(s.bits, (literal('foo'), 'bar'))

        s = shell_literal('foo') + jbos('bar')
        self.assertEqual(s.bits, (shell_literal('foo'), 'bar'))

        s = 'foo' + jbos('bar')
        self.assertEqual(s.bits, ('foobar',))

    def test_simplify(self):
        self.assertEqual(jbos().simplify(), '')

        self.assertEqual(jbos('foo').simplify(), 'foo')
        self.assertEqual(jbos(literal('foo')).simplify(), literal('foo'))
        self.assertEqual(jbos(shell_literal('foo')).simplify(),
                         shell_literal('foo'))

        self.assertEqual(jbos('foo', literal('bar')).simplify(),
                         jbos('foo', literal('bar')))

    def test_equality(self):
        self.assertTrue(jbos() == jbos())
        self.assertFalse(jbos() != jbos())

        self.assertTrue(jbos('foo') == jbos('foo'))
        self.assertTrue(jbos('foo', literal('bar')) ==
                        jbos('foo', literal('bar')))
        self.assertFalse(jbos('foo') != jbos('foo'))
        self.assertFalse(jbos('foo', literal('bar')) !=
                         jbos('foo', literal('bar')))

        self.assertFalse(jbos('foo', literal('bar')) ==
                         jbos('foo', literal('quux')))
        self.assertTrue(jbos('foo', literal('bar')) !=
                        jbos('foo', literal('quux')))

        self.assertFalse(jbos('foo') == jbos('foo', literal('bar')))
        self.assertTrue(jbos('foo') != jbos('foo', literal('bar')))


class TestJoin(TestCase):
    def test_join_empty(self):
        s = safe_str.join([], ',')
        self.assertEqual(s, '')

        s = safe_str.join([], literal(','))
        self.assertEqual(s, '')

    def test_join_strings(self):
        s = safe_str.join(['foo'], ',')
        self.assertEqual(s, 'foo')

        s = safe_str.join(['foo', 'bar'], ',')
        self.assertEqual(s, 'foo,bar')

    def test_join_literals(self):
        s = safe_str.join([literal('foo'), 'bar'], ',')
        self.assertEqual(s.bits, (literal('foo'), ',bar'))

        s = safe_str.join([shell_literal('foo'), 'bar'], ',')
        self.assertEqual(s.bits, (shell_literal('foo'), ',bar'))

        s = safe_str.join([literal('foo'), 'bar'], literal(','))
        self.assertEqual(s.bits, (literal('foo,'), 'bar'))

        s = safe_str.join([shell_literal('foo'), 'bar'], shell_literal(','))
        self.assertEqual(s.bits, (shell_literal('foo,'), 'bar'))


class TestSafeFormat(TestCase):
    def test_simple(self):
        self.assertEqual(safe_str.safe_format('foo'), 'foo')

    def test_auto(self):
        self.assertEqual(safe_str.safe_format('{}', 'foo'), 'foo')
        self.assertEqual(safe_str.safe_format('a{}z', 'foo'), 'afooz')

        foo = literal('foo')
        self.assertEqual(safe_str.safe_format('{}', foo), foo)
        self.assertEqual(safe_str.safe_format('a{}z', foo),
                         jbos('a', foo, 'z'))

        self.assertEqual(safe_str.safe_format('{}', MyString()), 'foo')
        self.assertEqual(safe_str.safe_format('a{}z', MyString()), 'afooz')

        self.assertEqual(safe_str.safe_format('{}', MyLiteral()), foo)
        self.assertEqual(safe_str.safe_format('a{}z', MyLiteral()),
                         jbos('a', foo, 'z'))

    def test_index(self):
        self.assertEqual(safe_str.safe_format('{0}', 'foo'), 'foo')
        self.assertEqual(safe_str.safe_format('a{0}z', 'foo'), 'afooz')

        foo = literal('foo')
        self.assertEqual(safe_str.safe_format('{0}', foo), foo)
        self.assertEqual(safe_str.safe_format('a{0}z', foo),
                         jbos('a', foo, 'z'))

        self.assertEqual(safe_str.safe_format('{0}', MyString()), 'foo')
        self.assertEqual(safe_str.safe_format('a{0}z', MyString()), 'afooz')

        self.assertEqual(safe_str.safe_format('{0}', MyLiteral()), foo)
        self.assertEqual(safe_str.safe_format('a{0}z', MyLiteral()),
                         jbos('a', foo, 'z'))

    def test_name(self):
        self.assertEqual(safe_str.safe_format('{f}', f='foo'), 'foo')
        self.assertEqual(safe_str.safe_format('a{f}z', f='foo'), 'afooz')

        foo = literal('foo')
        self.assertEqual(safe_str.safe_format('{f}', f=foo), foo)
        self.assertEqual(safe_str.safe_format('a{f}z', f=foo),
                         jbos('a', foo, 'z'))

        self.assertEqual(safe_str.safe_format('{f}', f=MyString()), 'foo')
        self.assertEqual(safe_str.safe_format('a{f}z', f=MyString()), 'afooz')

        self.assertEqual(safe_str.safe_format('{f}', f=MyLiteral()), foo)
        self.assertEqual(safe_str.safe_format('a{f}z', f=MyLiteral()),
                         jbos('a', foo, 'z'))

    def test_invalid(self):
        self.assertRaises(ValueError, safe_str.safe_format, '{}{0}', 'foo')
        self.assertRaises(ValueError, safe_str.safe_format, '{0}{}', 'foo')
