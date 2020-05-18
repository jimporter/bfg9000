from collections import namedtuple

from . import *

from bfg9000 import iterutils
from bfg9000.shell.list import shell_list


class TestIsIterable(TestCase):
    def test_list(self):
        self.assertTrue(iterutils.isiterable([]))

    def test_dict(self):
        self.assertFalse(iterutils.isiterable({}))

    def test_generator(self):
        gen = (i for i in range(10))
        self.assertTrue(iterutils.isiterable(gen))

    def test_string(self):
        self.assertFalse(iterutils.isiterable('foo'))

    def test_none(self):
        self.assertFalse(iterutils.isiterable(None))


class TestIsMapping(TestCase):
    def test_list(self):
        self.assertFalse(iterutils.ismapping([]))

    def test_dict(self):
        self.assertTrue(iterutils.ismapping({}))

    def test_string(self):
        self.assertFalse(iterutils.ismapping('foo'))

    def test_none(self):
        self.assertFalse(iterutils.ismapping(None))


class TestIterate(TestCase):
    def test_none(self):
        self.assertEqual(list(iterutils.iterate(None)), [])

    def test_one(self):
        self.assertEqual(list(iterutils.iterate('foo')), ['foo'])

    def test_many(self):
        self.assertEqual(list(iterutils.iterate(['foo', 'bar'])),
                         ['foo', 'bar'])


class TestIterateEach(TestCase):
    def test_empty(self):
        self.assertEqual(list(iterutils.iterate_each([])), [])

    def test_one(self):
        self.assertEqual(list(iterutils.iterate_each([None])), [])
        self.assertEqual(list(iterutils.iterate_each(['foo'])), ['foo'])
        self.assertEqual(list(iterutils.iterate_each([['foo', 'bar']])),
                         ['foo', 'bar'])

    def test_many(self):
        self.assertEqual(
            list(iterutils.iterate_each([None, 'foo', ['bar', 'baz']])),
            ['foo', 'bar', 'baz']
        )


class TestMapIterable(TestCase):
    def test_none(self):
        self.assertEqual(iterutils.map_iterable(len, None), None)

    def test_one(self):
        self.assertEqual(iterutils.map_iterable(len, 'foo'), 3)

    def test_many(self):
        self.assertEqual(iterutils.map_iterable(len, ['foo', 'bars']), [3, 4])
        self.assertEqual(iterutils.map_iterable(len, ('foo', 'bars')), (3, 4))
        self.assertEqual(iterutils.map_iterable(len, iter(('foo', 'bars'))),
                         [3, 4])


class TestListify(TestCase):
    def test_none(self):
        self.assertEqual(iterutils.listify(None), [])

    def test_one(self):
        self.assertEqual(iterutils.listify('foo'), ['foo'])

    def test_many(self):
        x = ['foo', 'bar']
        res = iterutils.listify(x)
        self.assertEqual(res, x)
        self.assertTrue(x is res)

    def test_always_copy(self):
        x = ['foo', 'bar']
        res = iterutils.listify(x, always_copy=True)
        self.assertEqual(res, x)
        self.assertTrue(x is not res)

    def test_no_scalar(self):
        self.assertEqual(iterutils.listify(['foo'], scalar_ok=False), ['foo'])
        self.assertEqual(iterutils.listify(['foo'], always_copy=True,
                                           scalar_ok=False), ['foo'])
        self.assertRaises(TypeError, iterutils.listify, 1, scalar_ok=False)
        self.assertRaises(TypeError, iterutils.listify, 'foo', scalar_ok=False)

    def test_type(self):
        x = 'foo'
        res = iterutils.listify(x, type=tuple)
        self.assertEqual(res, ('foo',))

        y = ['foo', 'bar']
        res = iterutils.listify(y, type=tuple)
        self.assertEqual(res, ('foo', 'bar'))


class TestFirst(TestCase):
    def test_none(self):
        self.assertRaises(LookupError, iterutils.first, None)

    def test_none_default(self):
        self.assertEqual(iterutils.first(None, default='foo'), 'foo')

    def test_one(self):
        self.assertEqual(iterutils.first('foo'), 'foo')

    def test_many(self):
        self.assertEqual(iterutils.first(['foo', 'bar']), 'foo')


class TestUnlistify(TestCase):
    def test_none(self):
        self.assertEqual(iterutils.unlistify([]), None)

    def test_one(self):
        self.assertEqual(iterutils.unlistify(['foo']), 'foo')

    def test_many(self):
        x = ['foo', 'bar']
        res = iterutils.unlistify(x)
        self.assertEqual(res, x)
        self.assertTrue(x is res)


class TestFlatten(TestCase):
    def test_empty(self):
        self.assertEqual(iterutils.flatten([]), [])
        self.assertEqual(iterutils.flatten(i for i in range(0)), [])

    def test_default_type(self):
        self.assertEqual(iterutils.flatten([[0, 1]] * 3), [0, 1, 0, 1, 0, 1])
        self.assertEqual(iterutils.flatten([i, i + 1] for i in range(3)),
                         [0, 1, 1, 2, 2, 3])

    def test_custom_type(self):
        class custom_list(list):
            def __eq__(self, rhs):
                return type(self) == type(rhs) and super().__eq__(rhs)

        self.assertEqual(iterutils.flatten([[0, 1]] * 3, custom_list),
                         custom_list([0, 1, 0, 1, 0, 1]))
        self.assertEqual(iterutils.flatten(([i, i + 1] for i in range(3)),
                                           custom_list),
                         custom_list([0, 1, 1, 2, 2, 3]))


class TestTween(TestCase):
    def test_none(self):
        self.assertEqual(list(iterutils.tween([], ',')), [])
        self.assertEqual(list(iterutils.tween([], ',', '[', ']')), [])

    def test_one(self):
        self.assertEqual(list(iterutils.tween([1], ',')), [1])
        self.assertEqual(list(iterutils.tween([1], ',', '[', ']')),
                         ['[', 1, ']'])

    def test_many(self):
        self.assertEqual(list(iterutils.tween([1, 2], ',')), [1, ',', 2])
        self.assertEqual(list(iterutils.tween([1, 2], ',', '[', ']')),
                         ['[', 1, ',', 2, ']'])


class TestUniques(TestCase):
    def test_none(self):
        self.assertEqual(iterutils.uniques([]), [])

    def test_one(self):
        self.assertEqual(iterutils.uniques([1]), [1])

    def test_many(self):
        self.assertEqual(iterutils.uniques([1, 2, 1, 3]), [1, 2, 3])


class TestRecursiveWalk(TestCase):
    def test_unified(self):
        T = namedtuple('T', ['children'])
        x = T([ T([T([])]), T([]) ])
        self.assertEqual(list(iterutils.recursive_walk(x, 'children')),
                         [ T([T([])]), T([]), T([]) ])

    def test_split(self):
        T = namedtuple('T', ['friends', 'children'])
        x = T(['alice', 'bob'], [
            T(['carrie'], [T(['dan'], [])]),
            T(['ellen'], [])
        ])
        self.assertEqual(
            list(iterutils.recursive_walk(x, 'friends', 'children')),
            ['alice', 'bob', 'carrie', 'dan', 'ellen']
        )


class TestMergeIntoDict(TestCase):
    def test_merge_empty(self):
        d = {}
        iterutils.merge_into_dict(d, {})
        self.assertEqual(d, {})

        d = {}
        iterutils.merge_into_dict(d, {'foo': 1})
        self.assertEqual(d, {'foo': 1})

        d = {'foo': 1}
        iterutils.merge_into_dict(d, {})
        self.assertEqual(d, {'foo': 1})

    def test_merge(self):
        d = {'foo': 1}
        iterutils.merge_into_dict(d, {'bar': 2})
        self.assertEqual(d, {'foo': 1, 'bar': 2})

        d = {'foo': 1}
        iterutils.merge_into_dict(d, {'foo': 2})
        self.assertEqual(d, {'foo': 2})

    def test_merge_several(self):
        d = {'foo': 1}
        iterutils.merge_into_dict(d, {'bar': 2}, {'baz': 3})
        self.assertEqual(d, {'foo': 1, 'bar': 2, 'baz': 3})

        d = {'foo': 1}
        iterutils.merge_into_dict(d, {'foo': 2}, {'foo': 3})
        self.assertEqual(d, {'foo': 3})

    def test_merge_lists(self):
        d = {'foo': [1]}
        iterutils.merge_into_dict(d, {'foo': [2]})
        self.assertEqual(d, {'foo': [1, 2]})

        d = {'foo': shell_list([1])}
        iterutils.merge_into_dict(d, {'foo': shell_list([2])})
        self.assertEqual(d, {'foo': shell_list([1, 2])})


class TestMergeDicts(TestCase):
    def test_merge_empty(self):
        self.assertEqual(iterutils.merge_dicts({}, {}), {})
        self.assertEqual(iterutils.merge_dicts({}, {'foo': 1}), {'foo': 1})
        self.assertEqual(iterutils.merge_dicts({'foo': 1}, {}), {'foo': 1})

    def test_merge_none(self):
        self.assertEqual(iterutils.merge_dicts({'foo': None}, {'foo': 1}),
                         {'foo': 1})
        self.assertEqual(iterutils.merge_dicts({'foo': 1}, {'foo': None}),
                         {'foo': 1})

        self.assertEqual(iterutils.merge_dicts({'foo': None}, {'bar': 1}),
                         {'foo': None, 'bar': 1})
        self.assertEqual(iterutils.merge_dicts({'foo': 1}, {'bar': None}),
                         {'foo': 1, 'bar': None})

    def test_merge_single(self):
        self.assertEqual(iterutils.merge_dicts({'foo': 1}, {'foo': 2}),
                         {'foo': 2})

    def test_merge_list(self):
        self.assertEqual(iterutils.merge_dicts({'foo': [1]}, {'foo': [2]}),
                         {'foo': [1, 2]})

    def test_merge_dict(self):
        self.assertEqual(iterutils.merge_dicts(
            {'foo': {'bar': [1], 'baz': 2}},
            {'foo': {'bar': [2], 'quux': 3}}
        ), {'foo': {'bar': [1, 2], 'baz': 2, 'quux': 3}})

    def test_merge_incompatible(self):
        merge_dicts = iterutils.merge_dicts
        self.assertRaises(TypeError, merge_dicts, {'foo': 1}, {'foo': [2]})
        self.assertRaises(TypeError, merge_dicts, {'foo': [1]}, {'foo': 2})
        self.assertRaises(TypeError, merge_dicts, {'foo': {}}, {'foo': 2})
        self.assertRaises(TypeError, merge_dicts, {'foo': 1}, {'foo': {}})

    def test_merge_several(self):
        merge_dicts = iterutils.merge_dicts
        self.assertEqual(merge_dicts({}, {}, {}), {})
        self.assertEqual(merge_dicts({'foo': 1}, {'bar': 2}, {'baz': 3}),
                         {'foo': 1, 'bar': 2, 'baz': 3})
        self.assertEqual(merge_dicts({'foo': 1}, {'foo': 2, 'bar': 3},
                                     {'baz': 4}),
                         {'foo': 2, 'bar': 3, 'baz': 4})

    def test_merge_makes_copies(self):
        d = {'foo': [1]}
        self.assertEqual(iterutils.merge_dicts({}, d, {'foo': [2]}),
                         {'foo': [1, 2]})
        self.assertEqual(d, {'foo': [1]})


class TestSliceDict(TestCase):
    def test_present(self):
        d = {'foo': 1, 'bar': 2, 'baz': 3}
        self.assertEqual(iterutils.slice_dict(d, ['foo', 'bar']),
                         {'foo': 1, 'bar': 2})
        self.assertEqual(d, {'baz': 3})

    def test_not_present(self):
        d = {'foo': 1, 'bar': 2, 'baz': 3}
        self.assertEqual(iterutils.slice_dict(d, ['foo', 'quux']),
                         {'foo': 1})
        self.assertEqual(d, {'bar': 2, 'baz': 3})
