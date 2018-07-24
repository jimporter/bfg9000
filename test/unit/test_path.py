import errno
import mock
import os
import unittest

from bfg9000.path import *
from bfg9000.platforms import platform_name
from bfg9000.safe_str import jbos

path_variables = {
    Root.srcdir: '$(srcdir)',
    Root.builddir: None,
    InstallRoot.prefix: '$(prefix)',
    InstallRoot.bindir: '$(bindir)',
}


class TestPath(unittest.TestCase):
    def test_construct(self):
        p = Path('foo/bar', Root.srcdir)
        self.assertEqual(p.suffix, os.path.join('foo', 'bar'))
        self.assertEqual(p.root, Root.srcdir)
        self.assertEqual(p.destdir, False)

    def test_construct_absolute(self):
        p = Path('/foo/bar', Root.absolute)
        self.assertEqual(p.suffix, os.path.join(os.path.sep, 'foo', 'bar'))
        self.assertEqual(p.root, Root.absolute)
        self.assertEqual(p.destdir, False)

        p = Path('/foo/bar', Root.srcdir)
        self.assertEqual(p.suffix, os.path.join(os.path.sep, 'foo', 'bar'))
        self.assertEqual(p.root, Root.absolute)
        self.assertEqual(p.destdir, False)

        self.assertRaises(ValueError, Path, 'foo/bar', Root.absolute)

    def test_construct_destdir(self):
        p = Path('foo/bar', InstallRoot.bindir, True)
        self.assertEqual(p.suffix, os.path.join('foo', 'bar'))
        self.assertEqual(p.root, InstallRoot.bindir)
        self.assertEqual(p.destdir, True)

        self.assertRaises(ValueError, Path, 'foo/bar', Root.srcdir, True)

    def test_equality(self):
        self.assertTrue(Path('a', Root.srcdir) == Path('a', Root.srcdir))
        self.assertFalse(Path('a', Root.srcdir) != Path('a', Root.srcdir))
        self.assertTrue(Path('a', InstallRoot.bindir, True) ==
                        Path('a', InstallRoot.bindir, True))
        self.assertFalse(Path('a', InstallRoot.bindir, True) !=
                         Path('a', InstallRoot.bindir, True))

        self.assertFalse(Path('a', Root.srcdir) == Path('a', Root.builddir))
        self.assertTrue(Path('a', Root.srcdir) != Path('a', Root.builddir))
        self.assertFalse(Path('a', Root.srcdir) == Path('b', Root.srcdir))
        self.assertTrue(Path('a', Root.srcdir) != Path('b', Root.srcdir))
        self.assertFalse(Path('a', InstallRoot.bindir, True) ==
                         Path('a', InstallRoot.bindir, False))
        self.assertTrue(Path('a', InstallRoot.bindir, True) !=
                        Path('a', InstallRoot.bindir, False))

    def test_parent(self):
        p = Path('foo/bar', Root.srcdir)
        self.assertEqual(p.parent(), Path('foo', Root.srcdir))

        p = Path('bar', Root.srcdir)
        self.assertEqual(p.parent(), Path('', Root.srcdir))

        p = Path('', Root.srcdir)
        self.assertRaises(ValueError, p.parent)

        p = Path('foo/bar', InstallRoot.bindir, True)
        self.assertEqual(p.parent(), Path('foo', InstallRoot.bindir, True))

    def test_append(self):
        p = Path('foo', Root.srcdir)
        self.assertEqual(p.append('bar'), Path('foo/bar', Root.srcdir))

        p = Path('foo', InstallRoot.bindir, True)
        self.assertEqual(p.append('bar'),
                         Path('foo/bar', InstallRoot.bindir, True))

    def test_ext(self):
        p = Path('foo.txt', Root.srcdir)
        self.assertEqual(p.ext(), '.txt')

    def test_addext(self):
        p = Path('foo', Root.srcdir)
        self.assertEqual(p.addext('.txt'), Path('foo.txt', Root.srcdir))

        p = Path('foo', InstallRoot.bindir, True)
        self.assertEqual(p.addext('.txt'),
                         Path('foo.txt', InstallRoot.bindir, True))

    def test_stripext(self):
        p = Path('foo.txt', Root.srcdir)
        self.assertEqual(p.stripext(), Path('foo', Root.srcdir))
        p = Path('foo.txt', Root.srcdir)
        self.assertEqual(p.stripext('.cpp'), Path('foo.cpp', Root.srcdir))

        p = Path('foo', Root.srcdir)
        self.assertEqual(p.stripext(), Path('foo', Root.srcdir))
        p = Path('foo', Root.srcdir)
        self.assertEqual(p.stripext('.cpp'), Path('foo.cpp', Root.srcdir))

        p = Path('foo.txt', InstallRoot.bindir, True)
        self.assertEqual(p.stripext(), Path('foo', InstallRoot.bindir, True))

    def test_split(self):
        p = Path('foo/bar/baz', Root.srcdir)
        self.assertEqual(p.split(), ['foo', 'bar', 'baz'])

    def test_basename(self):
        p = Path('foo/bar', Root.srcdir)
        self.assertEqual(p.basename(), 'bar')

    def test_relpath_relative(self):
        p = Path('foo/bar', Root.srcdir)
        self.assertEqual(p.relpath(Path('foo', Root.srcdir)), 'bar')

        p = Path('foo/bar', Root.srcdir)
        self.assertEqual(p.relpath(Path('baz', Root.srcdir)),
                         os.path.join('..', 'foo', 'bar'))

        p = Path('foo/bar', Root.srcdir)
        self.assertEqual(p.relpath(Path('.', Root.srcdir)),
                         os.path.join('foo', 'bar'))

        p = Path('.', Root.srcdir)
        self.assertEqual(p.relpath(Path('foo', Root.srcdir)), '..')

        p = Path('foo/bar', Root.srcdir)
        self.assertRaises(
            ValueError, lambda: p.relpath(Path('foo', Root.builddir))
        )

    def test_relpath_absolute(self):
        p = Path('/foo/bar', Root.srcdir)
        self.assertEqual(p.relpath(Path('/start', Root.srcdir)),
                         os.path.join(os.path.sep, 'foo', 'bar'))

        if platform_name() == 'windows':
            p = Path(r'C:\foo\bar', Root.srcdir)
            self.assertEqual(p.relpath(Path(r'C:\start', Root.srcdir)),
                             r'C:\foo\bar')

    def test_reroot(self):
        p = Path('foo/bar', Root.srcdir)
        self.assertEqual(p.reroot(Root.builddir),
                         Path('foo/bar', Root.builddir))

        p = Path('foo/bar', InstallRoot.bindir, True)
        self.assertEqual(p.reroot(InstallRoot.libdir),
                         Path('foo/bar', InstallRoot.libdir, True))

    def test_to_json(self):
        p = Path('foo', Root.srcdir)
        self.assertEqual(p.to_json(), ('foo', 'srcdir', False))

        p = Path('foo', InstallRoot.bindir, True)
        self.assertEqual(p.to_json(), ('foo', 'bindir', True))

    def test_from_json(self):
        p = Path.from_json(['foo', 'srcdir', False])
        self.assertEqual(p, Path('foo', Root.srcdir))

        p = Path.from_json(['foo', 'bindir', True])
        self.assertEqual(p, Path('foo', InstallRoot.bindir, True))

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

    def test_realize_destdir(self):
        path_vars_with_destdir = path_variables.copy()
        path_vars_with_destdir[DestDir.destdir] = '$(destdir)'

        p = Path('foo', InstallRoot.bindir, True)
        self.assertEqual(p.realize(path_variables),
                         os.path.join('$(bindir)', 'foo'))
        self.assertEqual(p.realize(path_vars_with_destdir),
                         os.path.join('$(destdir)$(bindir)', 'foo'))

    def test_string(self):
        paths = {Root.srcdir: Path('/srcdir', Root.absolute)}

        p = Path('/foo/bar', Root.absolute)
        self.assertEqual(p.string(), os.path.join(os.path.sep, 'foo', 'bar'))

        p = Path('foo/bar', Root.srcdir)
        self.assertEqual(
            p.string(paths), os.path.join(os.path.sep, 'srcdir', 'foo', 'bar')
        )

        p = Path('.', Root.srcdir)
        self.assertEqual(p.string(paths), os.path.join(os.path.sep, 'srcdir'))

    def test_hash(self):
        d = {Path('.', Root.srcdir), Path('.', Root.builddir),
             Path('foo', Root.srcdir), Path('bar', InstallRoot.bindir),
             Path('bar', InstallRoot.bindir, destdir=True)}
        self.assertEqual(len(d), 5)

    def test_bool(self):
        self.assertEqual(bool(Path('.', Root.builddir)), False)
        self.assertEqual(bool(Path('.', Root.srcdir)), True)
        self.assertEqual(bool(Path('.', InstallRoot.bindir)), True)
        self.assertEqual(bool(Path('foo', Root.builddir)), True)
        self.assertEqual(bool(Path('foo', Root.srcdir)), True)
        self.assertEqual(bool(Path('foo', InstallRoot.bindir)), True)

    def test_add(self):
        p = Path('foo/bar', Root.srcdir)
        result = p + 'baz'
        self.assertEqual(type(result), jbos)
        self.assertEqual(result.bits, (p, 'baz'))

        result = 'baz' + p
        self.assertEqual(type(result), jbos)
        self.assertEqual(result.bits, ('baz', p))


class TestAbsPath(unittest.TestCase):
    def test_abspath(self):
        self.assertEqual(abspath('/foo/bar'),
                         Path(os.path.abspath('/foo/bar'), Root.absolute))


class TestInstallPath(unittest.TestCase):
    def test_install_path_file(self):
        p = Path('foo/bar', Root.srcdir)
        self.assertEqual(install_path(p, InstallRoot.bindir),
                         Path('bar', InstallRoot.bindir, True))

        p = Path('foo/bar', Root.builddir)
        self.assertEqual(install_path(p, InstallRoot.bindir),
                         Path('foo/bar', InstallRoot.bindir, True))

    def test_install_path_directory(self):
        p = Path('foo/bar', Root.srcdir)
        self.assertEqual(install_path(p, InstallRoot.bindir, True),
                         Path('', InstallRoot.bindir, True))

        p = Path('foo/bar', Root.builddir)
        self.assertEqual(install_path(p, InstallRoot.bindir, True),
                         Path('foo/bar', InstallRoot.bindir, True))

    def test_install_path_no_destdir(self):
        p = Path('foo/bar', Root.srcdir)
        self.assertEqual(install_path(p, InstallRoot.bindir, destdir=False),
                         Path('bar', InstallRoot.bindir))
        self.assertEqual(install_path(p, InstallRoot.bindir, True, False),
                         Path('', InstallRoot.bindir))

        p = Path('foo/bar', Root.builddir)
        self.assertEqual(install_path(p, InstallRoot.bindir, destdir=False),
                         Path('foo/bar', InstallRoot.bindir))
        self.assertEqual(install_path(p, InstallRoot.bindir, True, False),
                         Path('foo/bar', InstallRoot.bindir))

    def test_install_path_absolute_ok(self):
        p = abspath('/foo/bar')
        self.assertEqual(install_path(p, InstallRoot.bindir,
                                      absolute_ok=True), p)
        self.assertEqual(install_path(p, InstallRoot.bindir, True,
                                      absolute_ok=True), p)

    def test_install_path_absolute_not_ok(self):
        p = abspath('/foo/bar')
        self.assertRaises(TypeError, install_path, p, InstallRoot.bindir)
        self.assertRaises(TypeError, install_path, p, InstallRoot.bindir, True)


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


class TestExists(unittest.TestCase):
    def test_exists(self):
        with mock.patch('os.path.exists', lambda x: True):
            self.assertEqual(exists(Path('/foo/bar')), True)


class TestSamefile(unittest.TestCase):
    def test_real(self):
        with mock.patch('os.path.samefile', lambda x, y: x == y, create=True):
            self.assertEqual(samefile(Path('/foo/bar'), Path('/foo/bar')),
                             True)

    def test_polyfill(self):
        class OsPath(object):
            def __init__(self):
                for i in ('isabs', 'normpath', 'realpath'):
                    setattr(self, i, getattr(os.path, i))

        with mock.patch('os.path', OsPath()):
            self.assertEqual(samefile(Path('/foo/bar'), Path('/foo/bar')),
                             True)


class TestMakedirs(unittest.TestCase):
    def test_success(self):
        with mock.patch('os.makedirs') as os_makedirs:
            makedirs('foo')
            makedirs('bar', 0o666)
            self.assertEqual(os_makedirs.mock_calls, [
                mock.call('foo', 0o777),
                mock.call('bar', 0o666),
            ])

    def test_exists(self):
        def mock_makedirs(path, mode):
            raise OSError(errno.EEXIST, 'msg')

        with mock.patch('os.makedirs', mock_makedirs), \
             mock.patch('os.path.isdir', lambda x: x == 'dir'):  # noqa
            self.assertRaises(OSError, makedirs, 'file')
            self.assertRaises(OSError, makedirs, 'file', exist_ok=True)
            self.assertRaises(OSError, makedirs, 'dir')
            makedirs('dir', exist_ok=True)

    def test_other_error(self):
        def mock_makedirs(path, mode):
            raise OSError(errno.EPERM, 'msg')

        with mock.patch('os.makedirs', mock_makedirs):
            self.assertRaises(OSError, makedirs, 'file')


class TestPushd(unittest.TestCase):
    def test_basic(self):
        with mock.patch('os.getcwd', lambda: 'cwd'), \
             mock.patch('os.chdir') as os_chdir:  # noqa
            with pushd('foo'):
                self.assertEqual(os_chdir.mock_calls, [mock.call('foo')])
            self.assertEqual(os_chdir.mock_calls, [
                mock.call('foo'), mock.call('cwd')
            ])

    def test_makedirs(self):
        with mock.patch('os.makedirs') as os_makedirs, \
             mock.patch('os.getcwd', lambda: 'cwd'), \
             mock.patch('os.chdir') as os_chdir:  # noqa
            with pushd('foo', makedirs=True):
                self.assertEqual(os_makedirs.mock_calls, [
                    mock.call('foo', 0o777)
                ])
                self.assertEqual(os_chdir.mock_calls, [mock.call('foo')])
            self.assertEqual(os_chdir.mock_calls, [
                mock.call('foo'), mock.call('cwd')
            ])
