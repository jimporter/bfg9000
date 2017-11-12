import unittest
from collections import namedtuple

from bfg9000.iterutils import *


class TestIsIterable(unittest.TestCase):
    def test_list(self):
        self.assertTrue(isiterable([]))

    def test_dict(self):
        self.assertTrue(isiterable([]))

    def test_generator(self):
        gen = (i for i in range(10))
        self.assertTrue(isiterable(gen))

    def test_string(self):
        self.assertFalse(isiterable('foo'))

    def test_none(self):
        self.assertFalse(isiterable(None))


class TestIterate(unittest.TestCase):
    def test_none(self):
        self.assertEqual(list(iterate(None)), [])

    def test_one(self):
        self.assertEqual(list(iterate('foo')), ['foo'])

    def test_many(self):
        self.assertEqual(list(iterate(['foo', 'bar'])), ['foo', 'bar'])


class TestListify(unittest.TestCase):
    def test_none(self):
        self.assertEqual(listify(None), [])

    def test_one(self):
        self.assertEqual(listify('foo'), ['foo'])

    def test_many(self):
        x = ['foo', 'bar']
        res = listify(x)
        self.assertEqual(res, x)
        self.assertTrue(x is res)

    def test_always_copy(self):
        x = ['foo', 'bar']
        res = listify(x, always_copy=True)
        self.assertEqual(res, x)
        self.assertTrue(x is not res)

    def test_no_scalar(self):
        self.assertRaises(TypeError, listify, 1, scalar_ok=False)


class TestFirst(unittest.TestCase):
    def test_none(self):
        self.assertRaises(LookupError, first, None)

    def test_none_default(self):
        self.assertEqual(first(None, default='foo'), 'foo')

    def test_one(self):
        self.assertEqual(first('foo'), 'foo')

    def test_many(self):
        self.assertEqual(first(['foo', 'bar']), 'foo')


class TestUnlistify(unittest.TestCase):
    def test_none(self):
        self.assertEqual(unlistify([]), None)

    def test_one(self):
        self.assertEqual(unlistify(['foo']), 'foo')

    def test_many(self):
        x = ['foo', 'bar']
        res = unlistify(x)
        self.assertEqual(res, x)
        self.assertTrue(x is res)


class TestTween(unittest.TestCase):
    def test_none(self):
        self.assertEqual(list(tween([], ',')), [])
        self.assertEqual(list(tween([], ',', '[', ']')), [])

    def test_one(self):
        self.assertEqual(list(tween([1], ',')), [1])
        self.assertEqual(list(tween([1], ',', '[', ']')), ['[', 1, ']'])

    def test_many(self):
        self.assertEqual(list(tween([1, 2], ',')), [1, ',', 2])
        self.assertEqual(list(tween([1, 2], ',', '[', ']')),
                         ['[', 1, ',', 2, ']'])


class TestUniques(unittest.TestCase):
    def test_none(self):
        self.assertEqual(uniques([]), [])

    def test_one(self):
        self.assertEqual(uniques([1]), [1])

    def test_many(self):
        self.assertEqual(uniques([1, 2, 1, 3]), [1, 2, 3])


class TestRecursiveWalk(unittest.TestCase):
    def test_unified(self):
        T = namedtuple('T', ['children'])
        x = T([ T([T([])]), T([]) ])
        self.assertEqual(list(recursive_walk(x, 'children')),
                         [ T([T([])]), T([]), T([]) ])

    def test_split(self):
        T = namedtuple('T', ['friends', 'children'])
        x = T(['alice', 'bob'], [
            T(['carrie'], [T(['dan'], [])]),
            T(['ellen'], [])
        ])
        self.assertEqual(list(recursive_walk(x, 'friends', 'children')),
                         ['alice', 'bob', 'carrie', 'dan', 'ellen'])


class TestMergeIntoDict(unittest.TestCase):
    def test_merge_empty(self):
        d = {}
        merge_into_dict(d, {})
        self.assertEqual(d, {})

        d = {}
        merge_into_dict(d, {'foo': 1})
        self.assertEqual(d, {'foo': 1})

        d = {'foo': 1}
        merge_into_dict(d, {})
        self.assertEqual(d, {'foo': 1})

    def test_merge(self):
        d = {'foo': 1}
        merge_into_dict(d, {'bar': 2})
        self.assertEqual(d, {'foo': 1, 'bar': 2})

        d = {'foo': 1}
        merge_into_dict(d, {'foo': 2})
        self.assertEqual(d, {'foo': 2})

    def test_merge_several(self):
        d = {'foo': 1}
        merge_into_dict(d, {'bar': 2}, {'baz': 3})
        self.assertEqual(d, {'foo': 1, 'bar': 2, 'baz': 3})

        d = {'foo': 1}
        merge_into_dict(d, {'foo': 2}, {'foo': 3})
        self.assertEqual(d, {'foo': 3})


class TestMergeDicts(unittest.TestCase):
    def test_merge_empty(self):
        self.assertEqual(merge_dicts({}, {}), {})
        self.assertEqual(merge_dicts({}, {'foo': 1}), {'foo': 1})
        self.assertEqual(merge_dicts({'foo': 1}, {}), {'foo': 1})

    def test_merge_none(self):
        self.assertEqual(merge_dicts({'foo': None}, {'foo': 1}), {'foo': 1})
        self.assertEqual(merge_dicts({'foo': 1}, {'foo': None}), {'foo': 1})

    def test_merge_single(self):
        self.assertEqual(merge_dicts({'foo': 1}, {'foo': 2}), {'foo': 2})

    def test_merge_list(self):
        self.assertEqual(merge_dicts({'foo': [1]}, {'foo': [2]}),
                         {'foo': [1, 2]})

    def test_merge_dict(self):
        self.assertEqual(merge_dicts(
            {'foo': {'bar': [1], 'baz': 2}},
            {'foo': {'bar': [2], 'quux': 3}}
        ), {'foo': {'bar': [1, 2], 'baz': 2, 'quux': 3}})

    def test_merge_incompatible(self):
        self.assertRaises(TypeError, merge_dicts, {'foo': 1}, {'foo': [2]})
        self.assertRaises(TypeError, merge_dicts, {'foo': [1]}, {'foo': 2})
        self.assertRaises(TypeError, merge_dicts, {'foo': {}}, {'foo': 2})
        self.assertRaises(TypeError, merge_dicts, {'foo': 1}, {'foo': {}})

    def test_merge_several(self):
        self.assertEqual(merge_dicts({}, {}, {}), {})
        self.assertEqual(merge_dicts({'foo': 1}, {'bar': 2}, {'baz': 3}),
                         {'foo': 1, 'bar': 2, 'baz': 3})
        self.assertEqual(merge_dicts({'foo': 1}, {'foo': 2, 'bar': 3},
                                     {'baz': 4}),
                         {'foo': 2, 'bar': 3, 'baz': 4})

    def test_merge_makes_copies(self):
        d = {'foo': [1]}
        self.assertEqual(merge_dicts({}, d, {'foo': [2]}), {'foo': [1, 2]})
        self.assertEqual(d, {'foo': [1]})


class TestSliceDict(unittest.TestCase):
    def test_present(self):
        d = {'foo': 1, 'bar': 2, 'baz': 3}
        self.assertEqual(slice_dict(d, ['foo', 'bar']), {'foo': 1, 'bar': 2})
        self.assertEqual(d, {'baz': 3})

    def test_not_present(self):
        d = {'foo': 1, 'bar': 2, 'baz': 3}
        self.assertEqual(slice_dict(d, ['foo', 'quux']), {'foo': 1})
        self.assertEqual(d, {'bar': 2, 'baz': 3})
