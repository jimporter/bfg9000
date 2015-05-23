import os
import sys
import unittest

basedir = os.path.abspath(os.path.dirname(__file__))
sys.path.append(os.path.join(basedir, '..', '..', 'src'))

from path import Path, VarPath

class TestPath(unittest.TestCase):
    def test_src_base(self):
        p = Path('foo/bar', Path.srcdir, Path.basedir)
        self.assertEqual(p.local_path(), VarPath('srcdir', 'foo/bar'))
        self.assertEqual(p.install_path(), VarPath('prefix', 'bar'))

    def test_build_base(self):
        p = Path('foo/bar', Path.builddir, Path.basedir)
        self.assertEqual(p.local_path(), VarPath(None, 'foo/bar'))
        self.assertEqual(p.install_path(), VarPath('prefix', 'foo/bar'))

    def test_src_bin(self):
        p = Path('foo/bar', Path.srcdir, Path.bindir)
        self.assertEqual(p.local_path(), VarPath('srcdir', 'foo/bar'))
        self.assertEqual(p.install_path(), VarPath('prefix', 'bin/bar'))

    def test_build_bin(self):
        p = Path('foo/bar', Path.builddir, Path.bindir)
        self.assertEqual(p.local_path(),  VarPath(None, 'bin/foo/bar'))
        self.assertEqual(p.install_path(), VarPath('prefix', 'bin/foo/bar'))

if __name__ == '__main__':
    unittest.main()
