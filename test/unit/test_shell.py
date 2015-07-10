import os
import unittest

from bfg9000.shell import split, quote_posix, quote_windows

class TestSplit(unittest.TestCase):
    def test_single(self):
        self.assertEqual(split('foo'), ['foo'])

    def test_multiple(self):
        self.assertEqual(split('foo bar baz'), ['foo', 'bar', 'baz'])

    def test_quote(self):
        self.assertEqual(split('foo "bar baz"'), ['foo', 'bar baz'])
        self.assertEqual(split('foo"bar baz"'), ['foobar baz'])

class TestQuotePosix(unittest.TestCase):
    def test_simple(self):
        self.assertEqual(quote_posix('foo'), 'foo')

    def test_space(self):
        self.assertEqual(quote_posix('foo bar'), "'foo bar'")

    def test_quote(self):
        self.assertEqual(quote_posix('"foo"'), '\'"foo"\'')

    def test_shell_chars(self):
        self.assertEqual(quote_posix('&&'), "'&&'")
        self.assertEqual(quote_posix('>'), "'>'")
        self.assertEqual(quote_posix('|'), "'|'")

class TestQuoteWindows(unittest.TestCase):
    def test_simple(self):
        self.assertEqual(quote_windows('foo'), 'foo')

    def test_space(self):
        self.assertEqual(quote_windows('foo bar'), '"foo bar"')

    def test_quote(self):
        self.assertEqual(quote_windows('"foo"'), '"\\"foo\\""')

    def test_backslash(self):
        self.assertEqual(quote_windows(r'foo\bar'), r'foo\bar')
        self.assertEqual(quote_windows('foo\\bar\\'), r'"foo\bar\\"')

    def test_escaped_quote(self):
        self.assertEqual(quote_windows(r'foo\"bar'), r'"foo\\\"bar"')

if __name__ == '__main__':
    unittest.main()
