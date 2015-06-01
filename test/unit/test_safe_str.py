import os
import sys
import unittest

basedir = os.path.abspath(os.path.dirname(__file__))
sys.path.append(os.path.join(basedir, '..', '..', 'src'))

from safe_str import *

class TestSafeStr(unittest.TestCase):
    def test_construct_from_strings(self):
        s = jbos('foo', 'bar', escaped_str('baz'))
        self.assertEqual(s.bits, ['foo', 'bar', escaped_str('baz')])

    def test_construct_from_jbos(self):
        s = jbos(jbos('foo', 'bar'), jbos(escaped_str('baz')))
        self.assertEqual(s.bits, ['foo', 'bar', escaped_str('baz')])

    def test_concatenate_from_strings(self):
        s = escaped_str('foo') + 'bar'
        self.assertEqual(s.bits, [escaped_str('foo'), 'bar'])

        s = 'foo' + escaped_str('bar')
        self.assertEqual(s.bits, ['foo', escaped_str('bar')])

        s = escaped_str('foo') + escaped_str('bar')
        self.assertEqual(s.bits, [escaped_str('foo'), escaped_str('bar')])

    def test_concatenate_from_jbos(self):
        s = jbos('foo', 'bar') + escaped_str('baz')
        self.assertEqual(s.bits, ['foo', 'bar', escaped_str('baz')])

        s = jbos('foo', 'bar') + 'baz'
        self.assertEqual(s.bits, ['foo', 'bar', 'baz'])

        s = escaped_str('foo') + jbos('bar', 'baz')
        self.assertEqual(s.bits, [escaped_str('foo'), 'bar', 'baz'])

        s = 'foo' + jbos('bar', 'baz')
        self.assertEqual(s.bits, ['foo', 'bar', 'baz'])

    def test_safe_str(self):
        self.assertEqual(safe_str('foo'), 'foo')
        self.assertEqual(safe_str(escaped_str('foo')), escaped_str('foo'))
        self.assertEqual(safe_str(jbos('foo')).bits, jbos('foo').bits)
        self.assertRaises(NotImplementedError, safe_str, 123)

if __name__ == '__main__':
    unittest.main()
