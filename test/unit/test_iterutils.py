import unittest

from bfg9000.iterutils import *


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
