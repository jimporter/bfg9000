from . import *

from bfg9000.objutils import *


class TestIdentity(TestCase):
    def test_identity(self):
        a = 1
        self.assertIs(identity(a), a)


class TestObjectify(TestCase):
    def test_create(self):
        self.assertEqual(objectify('foo', list, None), ['f', 'o', 'o'])

    def test_already_created(self):
        self.assertEqual(objectify(['foo'], list, None), ['foo'])

    def test_creator(self):
        self.assertEqual(objectify('foo', list, lambda x: [x]), ['foo'])

    def test_wrong_type(self):
        self.assertRaises(TypeError, objectify, 5, list, None)

    def test_in_type(self):
        self.assertEqual(objectify((1, 2), list, None, in_type=tuple), [1, 2])

    def test_extra_args(self):
        self.assertEqual(objectify('foo', list, lambda x, y: [x, y], y='bar'),
                         ['foo', 'bar'])
