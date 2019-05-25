from .. import *

from bfg9000.builtins.find import _filter_from_glob, FindResult


class TestFilterFromGlob(TestCase):
    def test_file(self):
        f = _filter_from_glob('f', '*', None, None)
        self.assertEqual(f('foo', 'foo', 'f'), FindResult.include)
        self.assertEqual(f('foo', 'foo', 'd'), FindResult.exclude)

    def test_dir(self):
        f = _filter_from_glob('d', '*', None, None)
        self.assertEqual(f('foo', 'foo', 'f'), FindResult.exclude)
        self.assertEqual(f('foo', 'foo', 'd'), FindResult.include)

    def test_either(self):
        f = _filter_from_glob('*', '*', None, None)
        self.assertEqual(f('foo', 'foo', 'f'), FindResult.include)
        self.assertEqual(f('foo', 'foo', 'd'), FindResult.include)

    def test_match(self):
        f = _filter_from_glob('*', '*.hpp', None, None)
        self.assertEqual(f('foo.hpp', 'foo.hpp', 'f'), FindResult.include)
        self.assertEqual(f('foo.cpp', 'foo.cpp', 'f'), FindResult.exclude)

    def test_extra(self):
        f = _filter_from_glob('*', None, '*.hpp', None)
        self.assertEqual(f('foo.hpp', 'foo.hpp', 'f'), FindResult.not_now)
        self.assertEqual(f('foo.cpp', 'foo.cpp', 'f'), FindResult.exclude)

    def test_match_extra(self):
        f = _filter_from_glob('*', '*.hpp', '*.?pp', None)
        self.assertEqual(f('foo.hpp', 'foo.hpp', 'f'), FindResult.include)
        self.assertEqual(f('foo.cpp', 'foo.cpp', 'f'), FindResult.not_now)
        self.assertEqual(f('foo.cxx', 'foo.cxx', 'f'), FindResult.exclude)

    def test_exclude(self):
        f = _filter_from_glob('*', '*.?pp', None, '*.cpp')
        self.assertEqual(f('foo.hpp', 'foo.hpp', 'f'), FindResult.include)
        self.assertEqual(f('foo.cpp', 'foo.cpp', 'f'), FindResult.exclude)

    def test_match_extra_exclude(self):
        f = _filter_from_glob('*', '*.c??', '*.?pp', '*.hpp')
        self.assertEqual(f('foo.hpp', 'foo.hpp', 'f'), FindResult.exclude)
        self.assertEqual(f('foo.cpp', 'foo.cpp', 'f'), FindResult.include)
        self.assertEqual(f('foo.ipp', 'foo.ipp', 'f'), FindResult.not_now)
