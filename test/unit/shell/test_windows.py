from .. import *

from bfg9000.shell import windows


class TestSplit(TestCase):
    def test_single(self):
        self.assertEqual(windows.split('foo'), ['foo'])

    def test_multiple(self):
        self.assertEqual(windows.split('foo bar baz'), ['foo', 'bar', 'baz'])

    def test_backslash(self):
        self.assertEqual(windows.split(r'C:\path\to\file'),
                         [r'C:\path\to\file'])

    def test_quote(self):
        self.assertEqual(windows.split('foo "bar baz"'), ['foo', 'bar baz'])
        self.assertEqual(windows.split('foo"bar baz"'), ['foobar baz'])
        self.assertEqual(windows.split(r'foo "c:\path\\"'),
                         ['foo', 'c:\\path\\'])
        self.assertEqual(windows.split('foo "it\'s \\"good\\""'),
                         ['foo', 'it\'s "good"'])

    def test_type(self):
        self.assertEqual(windows.split('foo bar baz', type=tuple),
                         ('foo', 'bar', 'baz'))

    def test_invalid(self):
        self.assertRaises(TypeError, windows.split, 1)


class TestListify(TestCase):
    def test_string(self):
        self.assertEqual(windows.listify('foo bar baz'), ['foo', 'bar', 'baz'])

    def test_list(self):
        self.assertEqual(windows.listify(['foo bar', 'baz']),
                         ['foo bar', 'baz'])

    def test_type(self):
        self.assertEqual(windows.listify('foo bar baz', type=tuple),
                         ('foo', 'bar', 'baz'))
        self.assertEqual(windows.listify(['foo bar', 'baz'], type=tuple),
                         ('foo bar', 'baz'))


class TestQuote(TestCase):
    def test_simple(self):
        self.assertEqual(windows.quote('foo'), 'foo')

    def test_space(self):
        self.assertEqual(windows.quote('foo bar'), '"foo bar"')

    def test_quote(self):
        self.assertEqual(windows.quote('"foo"'), '"\\"foo\\""')

    def test_backslash(self):
        self.assertEqual(windows.quote(r'foo\bar'), r'foo\bar')
        self.assertEqual(windows.quote('foo\\bar\\'), r'"foo\bar\\"')

    def test_escaped_quote(self):
        self.assertEqual(windows.quote(r'foo\"bar'), r'"foo\\\"bar"')
