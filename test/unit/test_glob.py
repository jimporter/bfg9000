from . import *

from bfg9000.glob import *
from bfg9000.path import Path, Root

src_file_txt = Path('file.txt', Root.srcdir)
src_dir = Path('dir/', Root.srcdir)
src_dir_file_txt = Path('dir/file.txt', Root.srcdir)
build_file_txt = Path('file.txt', Root.builddir)


class TestPathGlobResult(TestCase):
    def test_eq(self):
        R = PathGlob.Result
        self.assertTrue(R(True) == R(True))
        self.assertFalse(R(True) != R(True))
        self.assertTrue(R(False) == R(False))
        self.assertFalse(R(False) != R(False))

        self.assertFalse(R(True) == R(False))
        self.assertTrue(R(True) != R(False))
        self.assertFalse(R(False) == R(True))
        self.assertTrue(R(False) != R(True))

        self.assertTrue(R(False, False) == R(False))
        self.assertFalse(R(False, False) != R(False))
        self.assertTrue(R(False) == R(False, False))
        self.assertFalse(R(False) != R(False, False))

        self.assertTrue(R(False, True) == R(False, True))
        self.assertFalse(R(False, True) != R(False, True))
        self.assertTrue(R(False, False) == R(False, False))
        self.assertFalse(R(False, False) != R(False, False))

        self.assertFalse(R(False, True) == R(False, False))
        self.assertTrue(R(False, True) != R(False, False))
        self.assertFalse(R(False, False) == R(False, True))
        self.assertTrue(R(False, False) != R(False, True))

    def test_bool(self):
        R = PathGlob.Result
        self.assertTrue(bool(R(True)))
        self.assertFalse(bool(R(False)))
        self.assertFalse(bool(R(False, True)))
        self.assertFalse(bool(R(False, False)))

    def test_and(self):
        R = PathGlob.Result
        self.assertEqual(R(False) & R(False), R(False))
        self.assertEqual(R(False) & R(True), R(False))
        self.assertEqual(R(True) & R(False), R(False))
        self.assertEqual(R(True) & R(True), R(True))

        self.assertEqual(R(False) & R(False, True), R(False, True))
        self.assertEqual(R(False, True) & R(False), R(False, True))
        self.assertEqual(R(False, True) & R(False, True), R(False, True))

        self.assertEqual(R(True) & R(False, True), R(False, True))
        self.assertEqual(R(False, True) & R(True), R(False, True))

    def test_or(self):
        R = PathGlob.Result
        self.assertEqual(R(False) | R(False), R(False))
        self.assertEqual(R(False) | R(True), R(True))
        self.assertEqual(R(True) | R(False), R(True))
        self.assertEqual(R(True) | R(True), R(True))

        self.assertEqual(R(False) | R(False, True), R(False))
        self.assertEqual(R(False, True) | R(False), R(False))
        self.assertEqual(R(False, True) | R(False, True), R(False, True))

        self.assertEqual(R(True) | R(False, True), R(True))
        self.assertEqual(R(False, True) | R(True), R(True))


class TestPathGlob(TestCase):
    def assertMatch(self, glob, path, result, skip_base=False):
        self.assertEqual(glob.match(path, skip_base), PathGlob.Result(*result))

    def test_simple(self):
        g = PathGlob('file*')
        self.assertPathEqual(g.base, Path('', Root.srcdir))
        self.assertMatch(g, src_file_txt, [True])
        self.assertMatch(g, src_dir, [False, True])
        self.assertMatch(g, src_dir_file_txt, [False, True])
        self.assertMatch(g, build_file_txt, [False, False])

    def test_base_dir(self):
        g = PathGlob('dir/*')
        self.assertPathEqual(g.base, Path('dir/', Root.srcdir))
        self.assertMatch(g, src_file_txt, [False, True])
        self.assertMatch(g, src_dir, [False, False])
        self.assertMatch(g, src_dir_file_txt, [True])
        self.assertMatch(g, build_file_txt, [False, False])

    def test_star(self):
        g = PathGlob('*')
        self.assertMatch(g, src_file_txt, [True])
        self.assertMatch(g, src_dir, [False, False])
        self.assertMatch(g, src_dir_file_txt, [False, True])
        self.assertMatch(g, build_file_txt, [False, False])

        g = PathGlob('*/')
        self.assertMatch(g, src_file_txt, [False, False])
        self.assertMatch(g, src_dir, [True])
        self.assertMatch(g, src_dir_file_txt, [False, True])
        self.assertMatch(g, build_file_txt, [False, False])

        g = PathGlob('*', type='*')
        self.assertMatch(g, src_file_txt, [True])
        self.assertMatch(g, src_dir, [True])
        self.assertMatch(g, src_dir_file_txt, [False, True])
        self.assertMatch(g, build_file_txt, [False, False])

    def test_starstar(self):
        g = PathGlob('**')
        self.assertMatch(g, src_file_txt, [True])
        self.assertMatch(g, src_dir, [False, False])
        self.assertMatch(g, src_dir_file_txt, [True])
        self.assertMatch(g, build_file_txt, [False, False])

        g = PathGlob('**/')
        self.assertMatch(g, src_file_txt, [False, False])
        self.assertMatch(g, src_dir, [True])
        self.assertMatch(g, src_dir_file_txt, [False, False])
        self.assertMatch(g, build_file_txt, [False, False])

        g = PathGlob('**', type='*')
        self.assertMatch(g, src_file_txt, [True])
        self.assertMatch(g, src_dir, [True])
        self.assertMatch(g, src_dir_file_txt, [True])
        self.assertMatch(g, build_file_txt, [False, False])

    def test_starstar_prefix(self):
        g = PathGlob('**/file.txt')
        self.assertMatch(g, src_file_txt, [True])
        self.assertMatch(g, src_dir, [False, False])
        self.assertMatch(g, src_dir_file_txt, [True])
        self.assertMatch(g, build_file_txt, [False, False])

    def test_type(self):
        self.assertEqual(PathGlob('*').type, Glob.Type.file)
        self.assertEqual(PathGlob('*/').type, Glob.Type.dir)
        self.assertEqual(PathGlob('*', type='f').type, Glob.Type.file)
        self.assertEqual(PathGlob('*', type='d').type, Glob.Type.dir)
        self.assertEqual(PathGlob('*', type='*').type, Glob.Type.any)

        self.assertRaises(ValueError, PathGlob, '*', type='goofy')
        self.assertRaises(ValueError, PathGlob, '*/', type='f')

    def test_skip_base(self):
        def srcpath(p):
            return Path(p, Root.srcdir)

        g = PathGlob('dir/sub/*')
        self.assertMatch(g, srcpath('dir/sub/file.txt'), [True], True)
        self.assertMatch(g, srcpath('foo/bar/file.txt'), [True], True)
        self.assertMatch(g, srcpath('file.txt'), [False, False], True)

        self.assertMatch(g, Path('dir/sub/file.txt'), [True], True)
        self.assertMatch(g, Path('foo/bar/file.txt'), [True], True)
        self.assertMatch(g, Path('file.txt'), [False, False], True)

    def test_normalize(self):
        g = PathGlob('**/**')
        self.assertEqual(len(g.bits), 1)
        self.assertMatch(g, src_file_txt, [True])
        self.assertMatch(g, src_dir, [False, False])
        self.assertMatch(g, src_dir_file_txt, [True])
        self.assertMatch(g, build_file_txt, [False, False])

    def test_nonglob(self):
        self.assertRaises(ValueError, PathGlob, 'foo/bar.hpp')


class TestNameGlob(TestCase):
    def test_simple(self):
        g = NameGlob('file*')
        self.assertEqual(g.match(src_file_txt), True)
        self.assertEqual(g.match(src_dir), False)
        self.assertEqual(g.match(src_dir_file_txt), True)
        self.assertEqual(g.match(build_file_txt), True)

    def test_star(self):
        g = NameGlob('*')
        self.assertEqual(g.match(src_file_txt), True)
        self.assertEqual(g.match(src_dir), False)
        self.assertEqual(g.match(src_dir_file_txt), True)
        self.assertEqual(g.match(build_file_txt), True)

        g = NameGlob('*/')
        self.assertEqual(g.match(src_file_txt), False)
        self.assertEqual(g.match(src_dir), True)
        self.assertEqual(g.match(src_dir_file_txt), False)
        self.assertEqual(g.match(build_file_txt), False)

        g = NameGlob('*', type='*')
        self.assertEqual(g.match(src_file_txt), True)
        self.assertEqual(g.match(src_dir), True)
        self.assertEqual(g.match(src_dir_file_txt), True)
        self.assertEqual(g.match(build_file_txt), True)
