import os
import unittest

from bfg9000.path import Path, real_path

class TestPath(unittest.TestCase):
    def test_src_base(self):
        p = Path('foo/bar', Path.srcdir, Path.basedir)
        self.assertEqual(
            p.local_path(), real_path('srcdir', os.path.join('foo', 'bar'))
        )
        self.assertEqual(p.install_path(), real_path('prefix', 'bar'))

    def test_build_base(self):
        p = Path('foo/bar', Path.builddir, Path.basedir)
        self.assertEqual(
            p.local_path(), real_path('builddir', os.path.join('foo', 'bar'))
        )
        self.assertEqual(
            p.install_path(), real_path('prefix', os.path.join('foo', 'bar'))
        )

    def test_src_bin(self):
        p = Path('foo/bar', Path.srcdir, Path.bindir)
        self.assertEqual(
            p.local_path(), real_path('srcdir', os.path.join('foo', 'bar'))
        )
        self.assertEqual(
            p.install_path(), real_path('prefix', os.path.join('bin', 'bar'))
        )

    def test_build_bin(self):
        p = Path('foo/bar', Path.builddir, Path.bindir)
        self.assertEqual(
            p.local_path(),
            real_path('builddir', os.path.join('bin', 'foo', 'bar'))
        )
        self.assertEqual(
            p.install_path(),
            real_path('prefix', os.path.join('bin', 'foo', 'bar'))
        )

if __name__ == '__main__':
    unittest.main()
