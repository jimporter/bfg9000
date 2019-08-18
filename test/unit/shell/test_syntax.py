from .. import *

from bfg9000 import path
from bfg9000 import safe_str
from bfg9000.shell.syntax import *


class TestVariable(TestCase):
    def test_equality(self):
        self.assertTrue(Variable('foo') == Variable('foo'))
        self.assertFalse(Variable('foo') != Variable('foo'))

        self.assertFalse(Variable('foo') == Variable('bar'))
        self.assertTrue(Variable('foo') != Variable('bar'))

    def test_concat_str(self):
        self.assertEqual(Variable('foo') + 'bar', safe_str.jbos(
            safe_str.literal('${foo}'), 'bar'
        ))
        self.assertEqual('foo' + Variable('bar'), safe_str.jbos(
            'foo', safe_str.literal('${bar}')
        ))

    def test_concat_path(self):
        self.assertEqual(Variable('foo') + path.Path('bar'), safe_str.jbos(
            safe_str.literal('${foo}'), path.Path('bar')
        ))
        self.assertEqual(path.Path('foo') + Variable('bar'), safe_str.jbos(
            path.Path('foo'), safe_str.literal('${bar}')
        ))

    def test_concat_var(self):
        self.assertEqual(Variable('foo') + Variable('bar'), safe_str.jbos(
            safe_str.literal('${foo}'), safe_str.literal('${bar}')
        ))
