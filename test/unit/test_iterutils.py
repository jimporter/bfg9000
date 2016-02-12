import unittest

from bfg9000.iterutils import *


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
