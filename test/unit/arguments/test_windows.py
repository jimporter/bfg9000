from .. import *

from bfg9000.arguments.windows import *


class TestWindowsArgParse(TestCase):
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
        warn.add('v', type=str, dest='version')

        self.assertEqual(parser.parse_known([]), ({
            'warn': {'level': None, 'error': None, 'version': None}
        }, []))
        self.assertEqual(parser.parse_known(['/W2']), ({
            'warn': {'level': '2', 'error': None, 'version': None}
        }, []))
        self.assertEqual(parser.parse_known(['/W2', '/W4']), ({
            'warn': {'level': '4', 'error': None, 'version': None}
        }, []))
        self.assertEqual(parser.parse_known(['/W2', '/WX']), ({
            'warn': {'level': '2', 'error': True, 'version': None}
        }, []))
        self.assertEqual(parser.parse_known(['/Wv17']), ({
            'warn': {'level': None, 'error': None, 'version': '17'}
        }, []))
        self.assertEqual(parser.parse_known(
            ['/WX', '/W2', '/WX-', '/Wall', '/Wv17']
        ), ({'warn': {'level': 'all', 'error': False, 'version': '17'}}, []))

    def test_long_dict(self):
        parser = ArgumentParser()
        warn = parser.add('/Warn', type=dict, dest='warn')
        warn.add('1', '2', '3', '4', 'all', dest='level')
        warn.add('X', type=bool, dest='error')
        warn.add('X-', type=bool, dest='error', value=False)
        warn.add('v', type=str, dest='version')

        self.assertEqual(parser.parse_known([]), ({
            'warn': {'level': None, 'error': None, 'version': None}
        }, []))
        self.assertEqual(parser.parse_known(['/Warn:2']), ({
            'warn': {'level': '2', 'error': None, 'version': None}
        }, []))
        self.assertEqual(parser.parse_known(['/Warn:2', '/Warn:4']), ({
            'warn': {'level': '4', 'error': None, 'version': None}
        }, []))
        self.assertEqual(parser.parse_known(['/Warn:2', '/Warn:X']), ({
            'warn': {'level': '2', 'error': True, 'version': None}
        }, []))
        self.assertEqual(parser.parse_known(['/Warn:v17']), ({
            'warn': {'level': None, 'error': None, 'version': '17'}
        }, []))
        self.assertEqual(parser.parse_known(
            ['/Warn:X', '/Warn:2', '/Warn:X-', '/Warn:all', '/Warn:v17']
        ), ({'warn': {'level': 'all', 'error': False, 'version': '17'}}, []))

    def test_alias(self):
        parser = ArgumentParser()
        nologo = parser.add('/nologo')
        warn = parser.add('/W', type=dict, dest='warn')
        warn.add('0', '1', '2', '3', '4', 'all', dest='level')
        parser.add('/N', type='alias', base=nologo)
        parser.add('/w', type='alias', base=warn, value='0')

        self.assertEqual(parser.parse_known([]),
                         ({'nologo': None, 'warn': {'level': None}}, []))
        self.assertEqual(parser.parse_known(['/N']),
                         ({'nologo': True, 'warn': {'level': None}}, []))
        self.assertEqual(parser.parse_known(['/w']),
                         ({'nologo': None, 'warn': {'level': '0'}}, []))

    def test_unnamed(self):
        parser = ArgumentParser()
        parser.add('/a')
        parser.add_unnamed('libs')

        self.assertEqual(parser.parse_known([]),
                         ({'a': None, 'libs': []}, []))
        self.assertEqual(parser.parse_known(['foo']),
                         ({'a': None, 'libs': ['foo']}, []))
        self.assertEqual(parser.parse_known(['foo', '/a', 'bar']),
                         ({'a': True, 'libs': ['foo', 'bar']}, []))

    def test_collision(self):
        parser = ArgumentParser()
        parser.add('/a', '/longa')
        with self.assertRaises(ValueError):
            parser.add('/a')
        with self.assertRaises(ValueError):
            parser.add('/abc')
        with self.assertRaises(ValueError):
            parser.add('/longa')

    def test_invalid_prefix_char(self):
        parser = ArgumentParser()
        with self.assertRaises(ValueError):
            parser.add('warn')

    def test_unexpected_value(self):
        parser = ArgumentParser()
        parser.add('/a', '/longa')

        with self.assertRaises(ValueError):
            parser.parse_known(['/afoo'])
        with self.assertRaises(ValueError):
            parser.parse_known(['/longa:foo'])

    def test_expected_value(self):
        parser = ArgumentParser()
        parser.add('/a', '/longa', type=str)
        parser.add('/list', type=list)
        warn = parser.add('/warn', type=dict, dest='warn')
        warn.add('1', '2', '3', '4', 'all', dest='level')

        with self.assertRaises(ValueError):
            parser.parse_known(['/a'])
        with self.assertRaises(ValueError):
            parser.parse_known(['/longa'])
        with self.assertRaises(ValueError):
            parser.parse_known(['/list'])
        with self.assertRaises(ValueError):
            parser.parse_known(['/warn'])

    def test_invalid_dict_child(self):
        parser = ArgumentParser()
        warn = parser.add('/W', type=dict, dest='warn')
        with self.assertRaises(ValueError):
            warn.add('version', type=str)

    def test_unexpected_dict_value(self):
        parser = ArgumentParser()
        warn = parser.add('/W', type=dict, dest='warn')
        warn.add('1', '2', '3', '4', 'all', dest='level')

        with self.assertRaises(ValueError):
            parser.parse_known(['/WX'])

    def test_invalid_alias_base(self):
        parser = ArgumentParser()
        warn = parser.add('/W')
        with self.assertRaises(TypeError):
            parser.add('/w', type='alias', base=warn, value='0')
