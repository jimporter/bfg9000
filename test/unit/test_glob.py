from . import *

from bfg9000.glob import *
from bfg9000.path import Path, Root

src_file_txt = Path('file.txt', Root.srcdir)
src_dir = Path('dir/', Root.srcdir)
src_dir_file_txt = Path('dir/file.txt', Root.srcdir)
build_file_txt = Path('file.txt', Root.builddir)


class TestPathGlobResult(TestCase):
    def test_bool(self):
        R = PathGlob.Result
        self.assertTrue(bool(R.yes))
        self.assertFalse(bool(R.no))
        self.assertFalse(bool(R.never))

    def test_and(self):
        R = PathGlob.Result
        self.assertEqual(R.yes & R.yes, R.yes)
        self.assertEqual(R.yes & R.no, R.no)
        self.assertEqual(R.yes & R.never, R.never)

        self.assertEqual(R.no & R.yes, R.no)
        self.assertEqual(R.no & R.no, R.no)
        self.assertEqual(R.no & R.never, R.never)

        self.assertEqual(R.never & R.yes, R.never)
        self.assertEqual(R.never & R.no, R.never)
        self.assertEqual(R.never & R.never, R.never)

    def test_or(self):
        R = PathGlob.Result
        self.assertEqual(R.yes | R.yes, R.yes)
        self.assertEqual(R.yes | R.no, R.yes)
        self.assertEqual(R.yes | R.never, R.yes)

        self.assertEqual(R.no | R.yes, R.yes)
        self.assertEqual(R.no | R.no, R.no)
        self.assertEqual(R.no | R.never, R.no)

        self.assertEqual(R.never | R.yes, R.yes)
        self.assertEqual(R.never | R.no, R.no)
        self.assertEqual(R.never | R.never, R.never)


class TestPathGlob(TestCase):
    def assertMatch(self, glob, path, result, skip_base=False):
        self.assertEqual(glob.match(path, skip_base), PathGlob.Result[result])

    def test_simple(self):
        g = PathGlob('file*')
        self.assertPathEqual(g.base, Path('', Root.srcdir))
        self.assertMatch(g, src_file_txt, 'yes')
        self.assertMatch(g, src_dir, 'never')
        self.assertMatch(g, src_dir_file_txt, 'never')
        self.assertMatch(g, build_file_txt, 'no')

    def test_base_dir(self):
        g = PathGlob('dir/*')
        self.assertPathEqual(g.base, Path('dir/', Root.srcdir))
        self.assertMatch(g, src_file_txt, 'never')
        self.assertMatch(g, src_dir, 'no')
        self.assertMatch(g, src_dir_file_txt, 'yes')
        self.assertMatch(g, build_file_txt, 'no')

        g = PathGlob('dir/sub/*')
        self.assertPathEqual(g.base, Path('dir/sub/', Root.srcdir))
        self.assertMatch(g, src_file_txt, 'never')
        self.assertMatch(g, src_dir, 'no')

    def test_star(self):
        g = PathGlob('*')
        self.assertMatch(g, src_file_txt, 'yes')
        self.assertMatch(g, src_dir, 'no')
        self.assertMatch(g, src_dir_file_txt, 'never')
        self.assertMatch(g, build_file_txt, 'no')

        g = PathGlob('*/')
        self.assertMatch(g, src_file_txt, 'no')
        self.assertMatch(g, src_dir, 'yes')
        self.assertMatch(g, src_dir_file_txt, 'never')
        self.assertMatch(g, build_file_txt, 'no')

        g = PathGlob('*', type='*')
        self.assertMatch(g, src_file_txt, 'yes')
        self.assertMatch(g, src_dir, 'yes')
        self.assertMatch(g, src_dir_file_txt, 'never')
        self.assertMatch(g, build_file_txt, 'no')

    def test_starstar(self):
        g = PathGlob('**')
        self.assertMatch(g, src_file_txt, 'yes')
        self.assertMatch(g, src_dir, 'no')
        self.assertMatch(g, src_dir_file_txt, 'yes')
        self.assertMatch(g, build_file_txt, 'no')

        g = PathGlob('**/')
        self.assertMatch(g, src_file_txt, 'no')
        self.assertMatch(g, src_dir, 'yes')
        self.assertMatch(g, src_dir_file_txt, 'no')
        self.assertMatch(g, build_file_txt, 'no')

        g = PathGlob('**', type='*')
        self.assertMatch(g, src_file_txt, 'yes')
        self.assertMatch(g, src_dir, 'yes')
        self.assertMatch(g, src_dir_file_txt, 'yes')
        self.assertMatch(g, build_file_txt, 'no')

    def test_starstar_prefix(self):
        g = PathGlob('**/file.txt')
        self.assertMatch(g, src_file_txt, 'yes')
        self.assertMatch(g, src_dir, 'no')
        self.assertMatch(g, src_dir_file_txt, 'yes')
        self.assertMatch(g, build_file_txt, 'no')

        g = PathGlob('**/*')
        self.assertMatch(g, src_file_txt, 'yes')
        self.assertMatch(g, src_dir, 'no')
        self.assertMatch(g, src_dir_file_txt, 'yes')
        self.assertMatch(g, build_file_txt, 'no')

    def test_complicated(self):
        g = PathGlob('**/*a*/**/*.txt')
        self.assertMatch(g, Path('bar/file.txt', Root.srcdir), 'yes')
        self.assertMatch(g, Path('foo/bar/file.txt', Root.srcdir), 'yes')

        g = PathGlob('**/*a*/baz/**/*.txt')
        self.assertMatch(g, Path('foo/bar/baz/file.txt', Root.srcdir), 'yes')
        self.assertMatch(g, Path('a/foo/bar/baz/file.txt', Root.srcdir), 'yes')
        self.assertMatch(g, Path('baz/bar/file.txt', Root.srcdir), 'no')

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
        self.assertMatch(g, srcpath('dir/sub/file.txt'), 'yes', True)
        self.assertMatch(g, srcpath('foo/bar/file.txt'), 'yes', True)
        self.assertMatch(g, srcpath('file.txt'), 'no', True)

        self.assertMatch(g, Path('dir/sub/file.txt'), 'yes', True)
        self.assertMatch(g, Path('foo/bar/file.txt'), 'yes', True)
        self.assertMatch(g, Path('file.txt'), 'no', True)

    def test_normalize(self):
        g = PathGlob('**/**')
        self.assertEqual(g.glob, [([], 0), ([], 0)])
        self.assertMatch(g, src_file_txt, 'yes')
        self.assertMatch(g, src_dir, 'no')
        self.assertMatch(g, src_dir_file_txt, 'yes')
        self.assertMatch(g, build_file_txt, 'no')

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
