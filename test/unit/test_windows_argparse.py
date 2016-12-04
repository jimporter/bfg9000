import unittest

from bfg9000.arguments.windows import *


class TestWindowsArgParse(unittest.TestCase):
    def test_empty(self):
        parser = ArgumentParser()
        self.assertEqual(parser.parse_known([]), ({}, []))
        self.assertEqual(parser.parse_known(['extra']), ({}, ['extra']))
        self.assertEqual(parser.parse_known(['/extra']), ({}, ['/extra']))

    def test_short_bool(self):
        parser = ArgumentParser()
        parser.add('/a')
        self.assertEqual(parser.parse_known([]), ({'a': None}, []))
        self.assertEqual(parser.parse_known(['/a']), ({'a': True}, []))
        self.assertEqual(parser.parse_known(['/a', '/a']), ({'a': True}, []))

        parser = ArgumentParser()
        parser.add('/a', '-a')
        self.assertEqual(parser.parse_known([]), ({'a': None}, []))
        self.assertEqual(parser.parse_known(['/a']), ({'a': True}, []))
        self.assertEqual(parser.parse_known(['-a']), ({'a': True}, []))

    def test_long_bool(self):
        parser = ArgumentParser()
        parser.add('/foo')
        self.assertEqual(parser.parse_known([]), ({'foo': None}, []))
        self.assertEqual(parser.parse_known(['/foo']), ({'foo': True}, []))
        self.assertEqual(parser.parse_known(['/foo', '/foo']),
                         ({'foo': True}, []))

        parser = ArgumentParser()
        parser.add('/foo', '-foo')
        self.assertEqual(parser.parse_known([]), ({'foo': None}, []))
        self.assertEqual(parser.parse_known(['/foo']), ({'foo': True}, []))
        self.assertEqual(parser.parse_known(['-foo']), ({'foo': True}, []))

    def test_short_str(self):
        parser = ArgumentParser()
        parser.add('/a', type=str)
        self.assertEqual(parser.parse_known([]), ({'a': None}, []))
        self.assertEqual(parser.parse_known(['/afoo']), ({'a': 'foo'}, []))
        self.assertEqual(parser.parse_known(['/a', 'foo']), ({'a': 'foo'}, []))
        self.assertEqual(parser.parse_known(['/afoo', '/a', 'bar']),
                         ({'a': 'bar'}, []))

        parser = ArgumentParser()
        parser.add('/a', '-a', type=str)
        self.assertEqual(parser.parse_known([]), ({'a': None}, []))
        self.assertEqual(parser.parse_known(['/afoo']), ({'a': 'foo'}, []))
        self.assertEqual(parser.parse_known(['-afoo']), ({'a': 'foo'}, []))
        self.assertEqual(parser.parse_known(['/a', 'foo']), ({'a': 'foo'}, []))
        self.assertEqual(parser.parse_known(['-a', 'foo']), ({'a': 'foo'}, []))
        self.assertEqual(parser.parse_known(['/afoo', '-a', 'bar']),
                         ({'a': 'bar'}, []))

    def test_long_str(self):
        parser = ArgumentParser()
        parser.add('/foo', type=str)
        self.assertEqual(parser.parse_known([]), ({'foo': None}, []))
        self.assertEqual(parser.parse_known(['/foo:bar']),
                         ({'foo': 'bar'}, []))
        self.assertEqual(parser.parse_known(['/foo:bar', '/foo:baz']),
                         ({'foo': 'baz'}, []))

        parser = ArgumentParser()
        parser.add('/foo', '-foo', type=str)
        self.assertEqual(parser.parse_known([]), ({'foo': None}, []))
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

    def test_short_dict(self):
        parser = ArgumentParser()
        warn = parser.add('/W', type=dict, dest='warn')
        warn.add('1', '2', '3', '4', 'all', dest='level')
        warn.add('X', type=bool, dest='error')
        warn.add('X-', type=bool, dest='error', value=False)

        self.assertEqual(parser.parse_known([]),
                         ({'warn': {'level': None, 'error': None}}, []))
        self.assertEqual(parser.parse_known(['/W2']),
                         ({'warn': {'level': '2', 'error': None}}, []))
        self.assertEqual(parser.parse_known(['/W2', '/W4']),
                         ({'warn': {'level': '4', 'error': None}}, []))
        self.assertEqual(parser.parse_known(['/W2', '/WX']),
                         ({'warn': {'level': '2', 'error': True}}, []))
        self.assertEqual(parser.parse_known(['/WX', '/W2', '/WX-', '/Wall']),
                         ({'warn': {'level': 'all', 'error': False}}, []))

    def test_long_dict(self):
        parser = ArgumentParser()
        warn = parser.add('/Warn', type=dict, dest='warn')
        warn.add('1', '2', '3', '4', 'all', dest='level')
        warn.add('X', type=bool, dest='error')
        warn.add('X-', type=bool, dest='error', value=False)

        self.assertEqual(parser.parse_known(
            []
        ), ({'warn': {'level': None, 'error': None}}, []))

        self.assertEqual(parser.parse_known(
            ['/Warn:2']
        ), ({'warn': {'level': '2', 'error': None}}, []))

        self.assertEqual(parser.parse_known(
            ['/Warn:2', '/Warn:4']
        ), ({'warn': {'level': '4', 'error': None}}, []))

        self.assertEqual(parser.parse_known(
            ['/Warn:2', '/Warn:X']
        ), ({'warn': {'level': '2', 'error': True}}, []))

        self.assertEqual(parser.parse_known(
            ['/Warn:X', '/Warn:2', '/Warn:X-', '/Warn:all']
        ), ({'warn': {'level': 'all', 'error': False}}, []))
