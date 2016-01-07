import unittest

from bfg9000.shell.windows import *


class TestSplit(unittest.TestCase):
    def test_single(self):
        self.assertEqual(split('foo'), ['foo'])

    def test_multiple(self):
        self.assertEqual(split('foo bar baz'), ['foo', 'bar', 'baz'])

    def test_backslash(self):
        self.assertEqual(split(r'C:\path\to\file'), [r'C:\path\to\file'])

    def test_quote(self):
        self.assertEqual(split('foo "bar baz"'), ['foo', 'bar baz'])
        self.assertEqual(split('foo"bar baz"'), ['foobar baz'])
        self.assertEqual(split(r'foo "c:\path\\"'), ['foo', 'c:\\path\\'])
        self.assertEqual(split('foo "it\'s \\"good\\""'),
                         ['foo', 'it\'s "good"'])


class TestQuote(unittest.TestCase):
    def test_simple(self):
        self.assertEqual(quote('foo'), 'foo')

    def test_space(self):
        self.assertEqual(quote('foo bar'), '"foo bar"')

    def test_quote(self):
        self.assertEqual(quote('"foo"'), '"\\"foo\\""')

    def test_backslash(self):
        self.assertEqual(quote(r'foo\bar'), r'foo\bar')
        self.assertEqual(quote('foo\\bar\\'), r'"foo\bar\\"')

    def test_escaped_quote(self):
        self.assertEqual(quote(r'foo\"bar'), r'"foo\\\"bar"')
