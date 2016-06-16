import unittest

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


class TestFirst(unittest.TestCase):
    def test_none(self):
        self.assertRaises(LookupError, first, None)

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

    def test_merge_incompatible(self):
        self.assertRaises(TypeError, merge_dicts, {'foo': 1}, {'foo': [2]})
        self.assertRaises(TypeError, merge_dicts, {'foo': [1]}, {'foo': 2})

    def test_merge_several(self):
        self.assertEqual(merge_dicts({}, {}, {}), {})
        self.assertEqual(merge_dicts({'foo': 1}, {'bar': 2}, {'baz': 3}),
                         {'foo': 1, 'bar': 2, 'baz': 3})
        self.assertEqual(merge_dicts({'foo': 1}, {'foo': 2, 'bar': 3},
                                     {'baz': 4}),
                         {'foo': 2, 'bar': 3, 'baz': 4})
