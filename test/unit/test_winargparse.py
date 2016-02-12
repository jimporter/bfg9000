import unittest

from bfg9000.tools.winargparse import *


class TestWinArgParse(unittest.TestCase):
    def test_empty(self):
        parser = ArgumentParser()
        self.assertEqual(parser.parse_known([]), ({}, []))
        self.assertEqual(parser.parse_known(['extra']), ({}, ['extra']))
        self.assertEqual(parser.parse_known(['/extra']), ({}, ['/extra']))

    def test_short_bool(self):
        parser = ArgumentParser()
        parser.add('/a')
        self.assertEqual(parser.parse_known([]), ({'a': False}, []))
        self.assertEqual(parser.parse_known(['/a']), ({'a': True}, []))
        self.assertEqual(parser.parse_known(['/a', '/a']), ({'a': True}, []))

        parser = ArgumentParser()
        parser.add('/a', '-a')
        self.assertEqual(parser.parse_known([]), ({'a': False}, []))
        self.assertEqual(parser.parse_known(['/a']), ({'a': True}, []))
        self.assertEqual(parser.parse_known(['-a']), ({'a': True}, []))

    def test_long_bool(self):
        parser = ArgumentParser()
        parser.add('/foo')
        self.assertEqual(parser.parse_known([]), ({'foo': False}, []))
        self.assertEqual(parser.parse_known(['/foo']), ({'foo': True}, []))
        self.assertEqual(parser.parse_known(['/foo', '/foo']),
                         ({'foo': True}, []))

        parser = ArgumentParser()
        parser.add('/foo', '-foo')
        self.assertEqual(parser.parse_known([]), ({'foo': False}, []))
        self.assertEqual(parser.parse_known(['/foo']), ({'foo': True}, []))
        self.assertEqual(parser.parse_known(['-foo']), ({'foo': True}, []))

    def test_short_str(self):
        parser = ArgumentParser()
        parser.add('/a', type=str)
        self.assertEqual(parser.parse_known([]), ({'a': ''}, []))
        self.assertEqual(parser.parse_known(['/afoo']), ({'a': 'foo'}, []))
        self.assertEqual(parser.parse_known(['/a', 'foo']), ({'a': 'foo'}, []))
        self.assertEqual(parser.parse_known(['/afoo', '/a', 'bar']),
                         ({'a': 'bar'}, []))

        parser = ArgumentParser()
        parser.add('/a', '-a', type=str)
        self.assertEqual(parser.parse_known([]), ({'a': ''}, []))
        self.assertEqual(parser.parse_known(['/afoo']), ({'a': 'foo'}, []))
        self.assertEqual(parser.parse_known(['-afoo']), ({'a': 'foo'}, []))
        self.assertEqual(parser.parse_known(['/a', 'foo']), ({'a': 'foo'}, []))
        self.assertEqual(parser.parse_known(['-a', 'foo']), ({'a': 'foo'}, []))
        self.assertEqual(parser.parse_known(['/afoo', '-a', 'bar']),
                         ({'a': 'bar'}, []))

    def test_long_str(self):
        parser = ArgumentParser()
        parser.add('/foo', type=str)
        self.assertEqual(parser.parse_known([]), ({'foo': ''}, []))
        self.assertEqual(parser.parse_known(['/foo:bar']),
                         ({'foo': 'bar'}, []))
        self.assertEqual(parser.parse_known(['/foo:bar', '/foo:baz']),
                         ({'foo': 'baz'}, []))

        parser = ArgumentParser()
        parser.add('/foo', '-foo', type=str)
        self.assertEqual(parser.parse_known([]), ({'foo': ''}, []))
        self.assertEqual(parser.parse_known(['/foo:bar']),
                         ({'foo': 'bar'}, []))
        self.assertEqual(parser.parse_known(['-foo:bar']),
                         ({'foo': 'bar'}, []))
        self.assertEqual(parser.parse_known(['/foo:bar', '-foo:baz']),
                         ({'foo': 'baz'}, []))

    def test_short_list(self):
        parser = ArgumentParser()
        parser.add('/a', type=list)
        self.assertEqual(parser.parse_known([]), ({'a': []}, []))
        self.assertEqual(parser.parse_known(['/afoo']), ({'a': ['foo']}, []))
        self.assertEqual(parser.parse_known(['/a', 'foo']),
                         ({'a': ['foo']}, []))
        self.assertEqual(parser.parse_known(['/afoo', '/a', 'bar']),
                         ({'a': ['foo', 'bar']}, []))

        parser = ArgumentParser()
        parser.add('/a', '-a', type=list)
        self.assertEqual(parser.parse_known([]), ({'a': []}, []))
        self.assertEqual(parser.parse_known(['/afoo']), ({'a': ['foo']}, []))
        self.assertEqual(parser.parse_known(['-afoo']), ({'a': ['foo']}, []))
        self.assertEqual(parser.parse_known(['/a', 'foo']),
                         ({'a': ['foo']}, []))
        self.assertEqual(parser.parse_known(['-a', 'foo']),
                         ({'a': ['foo']}, []))
        self.assertEqual(parser.parse_known(['/afoo', '-a', 'bar']),
                         ({'a': ['foo', 'bar']}, []))

    def test_long_list(self):
        parser = ArgumentParser()
        parser.add('/foo', type=list)
        self.assertEqual(parser.parse_known([]), ({'foo': []}, []))
        self.assertEqual(parser.parse_known(['/foo:bar']),
                         ({'foo': ['bar']}, []))
        self.assertEqual(parser.parse_known(['/foo:bar', '/foo:baz']),
                         ({'foo': ['bar', 'baz']}, []))

        parser = ArgumentParser()
        parser.add('/foo', '-foo', type=list)
        self.assertEqual(parser.parse_known([]), ({'foo': []}, []))
        self.assertEqual(parser.parse_known(['/foo:bar']),
                         ({'foo': ['bar']}, []))
        self.assertEqual(parser.parse_known(['-foo:bar']),
                         ({'foo': ['bar']}, []))
        self.assertEqual(parser.parse_known(['/foo:bar', '-foo:baz']),
                         ({'foo': ['bar', 'baz']}, []))
