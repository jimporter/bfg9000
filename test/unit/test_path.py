import os
import unittest

from bfg9000.path import *
from bfg9000.platforms import platform_name

path_variables = {
    Root.srcdir: '$(srcdir)',
    Root.builddir: None,
    InstallRoot.prefix: '$(prefix)',
}


class TestPath(unittest.TestCase):
    def test_realize_srcdir(self):
        p = Path('foo', Root.srcdir)
        self.assertEqual(p.realize(path_variables),
                         os.path.join('$(srcdir)', 'foo'))
        self.assertEqual(p.realize(path_variables, executable=True),
                         os.path.join('$(srcdir)', 'foo'))

        p = Path('foo/bar', Root.srcdir)
        self.assertEqual(p.realize(path_variables),
                         os.path.join('$(srcdir)', 'foo', 'bar'))
        self.assertEqual(p.realize(path_variables, executable=True),
                         os.path.join('$(srcdir)', 'foo', 'bar'))

    def test_realize_builddir(self):
        p = Path('foo', Root.builddir)
        self.assertEqual(p.realize(path_variables), 'foo')
        self.assertEqual(p.realize(path_variables, executable=True),
                         os.path.join('.', 'foo'))

        p = Path('foo/bar', Root.builddir)
        self.assertEqual(p.realize(path_variables), os.path.join('foo', 'bar'))
        self.assertEqual(p.realize(path_variables, executable=True),
                         os.path.join('foo', 'bar'))

    def test_realize_absolute(self):
        p = Path('/foo/bar', Root.builddir)
        self.assertEqual(p.realize(path_variables),
                         os.path.join(os.path.sep, 'foo', 'bar'))
        self.assertEqual(p.realize(path_variables, executable=True),
                         os.path.join(os.path.sep, 'foo', 'bar'))

        if platform_name() == 'windows':
            p = Path(r'C:\foo\bar', Root.builddir)
            self.assertEqual(p.realize(path_variables),
                             os.path.join('C:', os.path.sep, 'foo', 'bar'))
            self.assertEqual(p.realize(path_variables, executable=True),
                             os.path.join('C:', os.path.sep, 'foo', 'bar'))

    def test_realize_srcdir_empty(self):
        p = Path('', Root.srcdir)
        self.assertEqual(p.realize(path_variables), '$(srcdir)')
        self.assertEqual(p.realize(path_variables, executable=True),
                         '$(srcdir)')

    def test_realize_builddir_empty(self):
        p = Path('', Root.builddir)
        self.assertEqual(p.realize(path_variables), '.')
        self.assertEqual(p.realize(path_variables, executable=True), '.')

    def test_parent(self):
        p = Path('foo/bar', Root.srcdir)
        self.assertEqual(p.parent(), Path('foo', Root.srcdir))

        p = Path('bar', Root.srcdir)
        self.assertEqual(p.parent(), Path('', Root.srcdir))

        p = Path('', Root.srcdir)
        self.assertRaises(ValueError, p.parent)

    def test_append(self):
        p = Path('foo', Root.srcdir)
        self.assertEqual(p.append('bar'), Path('foo/bar', Root.srcdir))

    def test_addext(self):
        p = Path('foo', Root.srcdir)
        self.assertEqual(p.addext('.txt'), Path('foo.txt', Root.srcdir))

    def test_basename(self):
        p = Path('foo/bar', Root.srcdir)
        self.assertEqual(p.basename(), 'bar')

    def test_install_path_srcdir(self):
        p = Path('foo/bar', Root.srcdir)
        self.assertEqual(install_path(p, InstallRoot.bindir),
                         Path('bar', InstallRoot.bindir))

    def test_install_path_builddir(self):
        p = Path('foo/bar', Root.builddir)
        self.assertEqual(install_path(p, InstallRoot.bindir),
                         Path('foo/bar', InstallRoot.bindir))


class TestCommonPrefix(unittest.TestCase):
    def test_empty(self):
        self.assertEqual(commonprefix([]), None)

    def test_single(self):
        p = Path('foo/bar')
        self.assertEqual(commonprefix([p]), p)

    def test_multi_same(self):
        p = Path('foo/bar')
        self.assertEqual(commonprefix([p, p]), p)

    def test_multi_partial_match(self):
        p = Path('foo/bar')
        q = Path('foo/baz')
        self.assertEqual(commonprefix([p, q]), p.parent())

    def test_multi_subset(self):
        p = Path('foo/bar')
        q = Path('foo/bar/baz')
        self.assertEqual(commonprefix([p, q]), p)

    def test_multi_no_match(self):
        p = Path('foo/bar')
        q = Path('baz/quux')
        self.assertEqual(commonprefix([p, q]), Path(''))
