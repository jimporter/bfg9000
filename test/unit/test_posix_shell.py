import unittest

from bfg9000.shell.posix import *


class TestSplit(unittest.TestCase):
    def test_single(self):
        self.assertEqual(split('foo'), ['foo'])

    def test_multiple(self):
        self.assertEqual(split('foo bar baz'), ['foo', 'bar', 'baz'])

    def test_quote(self):
        self.assertEqual(split('foo "bar baz"'), ['foo', 'bar baz'])
        self.assertEqual(split('foo"bar baz"'), ['foobar baz'])


class TestQuote(unittest.TestCase):
    def test_simple(self):
        self.assertEqual(quote('foo'), 'foo')

    def test_space(self):
        self.assertEqual(quote('foo bar'), "'foo bar'")

    def test_quote(self):
        self.assertEqual(quote('"foo"'), '\'"foo"\'')

    def test_shell_chars(self):
        self.assertEqual(quote('&&'), "'&&'")
        self.assertEqual(quote('>'), "'>'")
        self.assertEqual(quote('|'), "'|'")
