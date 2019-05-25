from bfg9000 import safe_str

from . import *

jbos = safe_str.jbos
literal = safe_str.literal
shell_literal = safe_str.shell_literal


class TestSafeStr(TestCase):
    def test_string(self):
        self.assertEqual(safe_str.safe_str('foo'), 'foo')

    def test_literals(self):
        self.assertEqual(safe_str.safe_str(literal('foo')), literal('foo'))
        self.assertEqual(safe_str.safe_str(shell_literal('foo')),
                         shell_literal('foo'))

    def test_jbos(self):
        self.assertEqual(safe_str.safe_str(jbos('foo')).bits, jbos('foo').bits)

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
        self.assertEqual(s.bits, (literal('foo'), literal('bar')))

        s = shell_literal('foo') + 'bar'
        self.assertEqual(s.bits, (shell_literal('foo'), 'bar'))

        s = 'foo' + shell_literal('bar')
        self.assertEqual(s.bits, ('foo', shell_literal('bar')))

        s = shell_literal('foo') + shell_literal('bar')
        self.assertEqual(s.bits, (shell_literal('foo'), shell_literal('bar')))

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

    def test_construct_invalid(self):
        self.assertRaises(TypeError, jbos, 123)

    def test_concatenate(self):
        s = jbos('foo', 'bar') + literal('baz')
        self.assertEqual(s.bits, ('foo', 'bar', literal('baz')))

        s = jbos('foo', 'bar') + shell_literal('baz')
        self.assertEqual(s.bits, ('foo', 'bar', shell_literal('baz')))

        s = jbos('foo', 'bar') + 'baz'
        self.assertEqual(s.bits, ('foo', 'bar', 'baz'))

        s = literal('foo') + jbos('bar', 'baz')
        self.assertEqual(s.bits, (literal('foo'), 'bar', 'baz'))

        s = shell_literal('foo') + jbos('bar', 'baz')
        self.assertEqual(s.bits, (shell_literal('foo'), 'bar', 'baz'))

        s = 'foo' + jbos('bar', 'baz')
        self.assertEqual(s.bits, ('foo', 'bar', 'baz'))

    def test_equality(self):
        self.assertTrue(jbos() == jbos())
        self.assertFalse(jbos() != jbos())

        self.assertTrue(jbos('foo', 'bar') == jbos('foo', 'bar'))
        self.assertTrue(jbos('foo', literal('bar')) ==
                        jbos('foo', literal('bar')))
        self.assertFalse(jbos('foo', 'bar') != jbos('foo', 'bar'))
        self.assertFalse(jbos('foo', literal('bar')) !=
                         jbos('foo', literal('bar')))

        self.assertFalse(jbos('foo', 'bar') == jbos('foo', 'quux'))
        self.assertFalse(jbos('foo', literal('bar')) ==
                         jbos('foo', literal('quux')))
        self.assertTrue(jbos('foo', 'bar') != jbos('foo', 'quux'))
        self.assertTrue(jbos('foo', literal('bar')) !=
                        jbos('foo', literal('quux')))

        self.assertFalse(jbos('foo') == jbos('foo', 'bar'))
        self.assertTrue(jbos('foo') != jbos('foo', 'bar'))


class TestJoin(TestCase):
    def test_join_empty(self):
        s = safe_str.join([], ',')
        self.assertEqual(s.bits, ())

    def test_join_strings(self):
        s = safe_str.join(['foo'], ',')
        self.assertEqual(s.bits, ('foo',))

        s = safe_str.join(['foo', 'bar'], ',')
        self.assertEqual(s.bits, ('foo', ',', 'bar'))

    def test_join_literals(self):
        s = safe_str.join([literal('foo'), 'bar'], ',')
        self.assertEqual(s.bits, (literal('foo'), ',', 'bar'))

        s = safe_str.join([shell_literal('foo'), 'bar'], ',')
        self.assertEqual(s.bits, (shell_literal('foo'), ',', 'bar'))

        s = safe_str.join([literal('foo'), 'bar'], literal(','))
        self.assertEqual(s.bits, (literal('foo'), literal(','), 'bar'))

        s = safe_str.join([shell_literal('foo'), 'bar'], shell_literal(','))
        self.assertEqual(s.bits, (shell_literal('foo'), shell_literal(','),
                                  'bar'))
