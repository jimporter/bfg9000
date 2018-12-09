import unittest

from bfg9000.shell import syntax


class TestVariable(unittest.TestCase):
    def test_equality(self):
        self.assertTrue(syntax.Variable('foo') == syntax.Variable('foo'))
        self.assertFalse(syntax.Variable('foo') != syntax.Variable('foo'))

        self.assertFalse(syntax.Variable('foo') == syntax.Variable('bar'))
        self.assertTrue(syntax.Variable('foo') != syntax.Variable('bar'))
