from .. import *

from bfg9000.shell import posix


class TestSplit(TestCase):
    def test_single(self):
        self.assertEqual(posix.split('foo'), ['foo'])

    def test_multiple(self):
        self.assertEqual(posix.split('foo bar baz'), ['foo', 'bar', 'baz'])

    def test_quote(self):
        self.assertEqual(posix.split('foo "bar baz"'), ['foo', 'bar baz'])
        self.assertEqual(posix.split('foo"bar baz"'), ['foobar baz'])

    def test_type(self):
        self.assertEqual(posix.split('foo bar baz', type=tuple),
                         ('foo', 'bar', 'baz'))

    def test_invalid(self):
        self.assertRaises(TypeError, posix.split, 1)


class TestListify(TestCase):
    def test_string(self):
        self.assertEqual(posix.listify('foo bar baz'), ['foo', 'bar', 'baz'])

    def test_list(self):
        self.assertEqual(posix.listify(['foo bar', 'baz']), ['foo bar', 'baz'])

    def test_type(self):
        self.assertEqual(posix.listify('foo bar baz', type=tuple),
                         ('foo', 'bar', 'baz'))
        self.assertEqual(posix.listify(['foo bar', 'baz'], type=tuple),
                         ('foo bar', 'baz'))


class TestQuote(TestCase):
    def test_simple(self):
        self.assertEqual(posix.quote('foo'), 'foo')

    def test_space(self):
        self.assertEqual(posix.quote('foo bar'), "'foo bar'")

    def test_quote(self):
        self.assertEqual(posix.quote('"foo"'), '\'"foo"\'')

    def test_shell_chars(self):
        self.assertEqual(posix.quote('&&'), "'&&'")
        self.assertEqual(posix.quote('>'), "'>'")
        self.assertEqual(posix.quote('|'), "'|'")
