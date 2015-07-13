import os
import unittest

from bfg9000.path import Path, install_path

path_variables = {
    Path.srcdir: '$(srcdir)',
    Path.builddir: None,
    Path.prefix: '$(prefix)',
}

class TestPath(unittest.TestCase):
    def test_realize_srcdir(self):
        p = Path('foo', Path.srcdir)
        self.assertEqual(p.realize(path_variables),
                         os.path.join('$(srcdir)', 'foo'))
        self.assertEqual(p.realize(path_variables, executable=True),
                         os.path.join('$(srcdir)', 'foo'))

        p = Path('foo/bar', Path.srcdir)
        self.assertEqual(p.realize(path_variables),
                         os.path.join('$(srcdir)', 'foo', 'bar'))
        self.assertEqual(p.realize(path_variables, executable=True),
                         os.path.join('$(srcdir)', 'foo', 'bar'))

    def test_realize_builddir(self):
        p = Path('foo', Path.builddir)
        self.assertEqual(p.realize(path_variables), 'foo')
        self.assertEqual(p.realize(path_variables, executable=True),
                         os.path.join('.', 'foo'))

        p = Path('foo/bar', Path.builddir)
        self.assertEqual(p.realize(path_variables), os.path.join('foo', 'bar'))
        self.assertEqual(p.realize(path_variables, executable=True),
                         os.path.join('foo', 'bar'))

    def test_realize_absolute(self):
        p = Path('/foo/bar', Path.builddir)
        self.assertEqual(p.realize(path_variables),
                         os.path.join('/', 'foo', 'bar'))
        self.assertEqual(p.realize(path_variables, executable=True),
                         os.path.join('/', 'foo', 'bar'))

    def test_parent(self):
        p = Path('foo/bar', Path.srcdir)
        self.assertEqual(p.parent(), Path('foo', Path.srcdir))

        p = Path('bar', Path.srcdir)
        self.assertEqual(p.parent(), Path('', Path.srcdir))

        p = Path('', Path.srcdir)
        self.assertRaises(ValueError, p.parent)

    def test_append(self):
        p = Path('foo', Path.srcdir)
        self.assertEqual(p.append('bar'), Path('foo/bar', Path.srcdir))

    def test_addext(self):
        p = Path('foo', Path.srcdir)
        self.assertEqual(p.addext('.txt'), Path('foo.txt', Path.srcdir))

    def test_basename(self):
        p = Path('foo/bar', Path.srcdir)
        self.assertEqual(p.basename(), 'bar')

    def test_install_path_srcdir(self):
        p = Path('foo/bar', Path.srcdir)
        self.assertEqual(install_path(p, Path.bindir),
                         Path('bin/bar', Path.prefix))

    def test_install_path_builddir(self):
        p = Path('foo/bar', Path.builddir)
        self.assertEqual(install_path(p, Path.bindir),
                         Path('bin/foo/bar', Path.prefix))

if __name__ == '__main__':
    unittest.main()
