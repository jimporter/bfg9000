import os
import unittest

from bfg9000.shell import split, posix_quote, windows_quote

class TestSplit(unittest.TestCase):
    def test_single(self):
        self.assertEqual(split('foo'), ['foo'])

    def test_multiple(self):
        self.assertEqual(split('foo bar baz'), ['foo', 'bar', 'baz'])

    def test_quote(self):
        self.assertEqual(split('foo "bar baz"'), ['foo', 'bar baz'])
        self.assertEqual(split('foo"bar baz"'), ['foobar baz'])

class TestPosixQuote(unittest.TestCase):
    def test_simple(self):
        self.assertEqual(posix_quote('foo'), 'foo')

    def test_space(self):
        self.assertEqual(posix_quote('foo bar'), "'foo bar'")

    def test_quote(self):
        self.assertEqual(posix_quote('"foo"'), '\'"foo"\'')

    def test_shell_chars(self):
        self.assertEqual(posix_quote('&&'), "'&&'")
        self.assertEqual(posix_quote('>'), "'>'")
        self.assertEqual(posix_quote('|'), "'|'")

class TestWindowsQuote(unittest.TestCase):
    def test_simple(self):
        self.assertEqual(windows_quote('foo'), 'foo')

    def test_space(self):
        self.assertEqual(windows_quote('foo bar'), '"foo bar"')

    def test_quote(self):
        self.assertEqual(windows_quote('"foo"'), '"\\"foo\\""')

    def test_backslash(self):
        self.assertEqual(windows_quote(r'foo\bar'), r'foo\bar')
        self.assertEqual(windows_quote('foo\\bar\\'), r'"foo\bar\\"')

    def test_escaped_quote(self):
        self.assertEqual(windows_quote(r'foo\"bar'), r'"foo\\\"bar"')

if __name__ == '__main__':
    unittest.main()
