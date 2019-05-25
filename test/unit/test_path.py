import errno
import mock
import os
from collections import namedtuple

from . import *

from bfg9000 import path
from bfg9000.platforms import target
from bfg9000.safe_str import jbos

MockEnv = namedtuple('MockEnv', ['target_platform'])

path_variables = {
    path.Root.srcdir: '$(srcdir)',
    path.Root.builddir: None,
    path.InstallRoot.prefix: '$(prefix)',
    path.InstallRoot.bindir: '$(bindir)',
}


class TestPath(PathTestCase):
    def test_construct(self):
        p = self.Path('foo/bar', path.Root.srcdir)
        self.assertEqual(p.suffix, 'foo/bar')
        self.assertEqual(p.root, path.Root.srcdir)
        self.assertEqual(p.destdir, False)

        p = self.Path(r'foo\bar', path.Root.srcdir)
        self.assertEqual(p.suffix, 'foo/bar')
        self.assertEqual(p.root, path.Root.srcdir)
        self.assertEqual(p.destdir, False)

        p = self.Path('foo/.././bar', path.Root.srcdir)
        self.assertEqual(p.suffix, 'bar')
        self.assertEqual(p.root, path.Root.srcdir)
        self.assertEqual(p.destdir, False)

        p = self.Path('.', path.Root.srcdir)
        self.assertEqual(p.suffix, '')
        self.assertEqual(p.root, path.Root.srcdir)
        self.assertEqual(p.destdir, False)

        p = self.Path('foo/../.', path.Root.srcdir)
        self.assertEqual(p.suffix, '')
        self.assertEqual(p.root, path.Root.srcdir)
        self.assertEqual(p.destdir, False)

    def test_construct_absolute(self):
        p = self.Path('/foo/bar', path.Root.absolute)
        self.assertEqual(p.suffix, '/foo/bar')
        self.assertEqual(p.root, path.Root.absolute)
        self.assertEqual(p.destdir, False)

        p = self.Path('/foo/bar', path.Root.srcdir)
        self.assertEqual(p.suffix, '/foo/bar')
        self.assertEqual(p.root, path.Root.absolute)
        self.assertEqual(p.destdir, False)

        p = self.Path('C:/foo/bar', path.Root.srcdir)
        self.assertEqual(p.suffix, 'C:/foo/bar')
        self.assertEqual(p.root, path.Root.absolute)
        self.assertEqual(p.destdir, False)

        p = self.Path(r'C:\foo\bar', path.Root.srcdir)
        self.assertEqual(p.suffix, 'C:/foo/bar')
        self.assertEqual(p.root, path.Root.absolute)
        self.assertEqual(p.destdir, False)

        p = self.Path('C:/.', path.Root.srcdir)
        self.assertEqual(p.suffix, 'C:/')
        self.assertEqual(p.root, path.Root.absolute)
        self.assertEqual(p.destdir, False)

        p = self.Path('//server/mount/foo/bar', path.Root.srcdir)
        self.assertEqual(p.suffix, '//server/mount/foo/bar')
        self.assertEqual(p.root, path.Root.absolute)
        self.assertEqual(p.destdir, False)

        p = self.Path(r'\\server\mount\foo\bar', path.Root.srcdir)
        self.assertEqual(p.suffix, '//server/mount/foo/bar')
        self.assertEqual(p.root, path.Root.absolute)
        self.assertEqual(p.destdir, False)

        self.assertRaises(ValueError, self.Path, 'foo/bar', path.Root.absolute)
        self.assertRaises(ValueError, self.Path, 'c:foo')

    def test_construct_destdir(self):
        p = self.Path('foo/bar', path.InstallRoot.bindir, True)
        self.assertEqual(p.suffix, 'foo/bar')
        self.assertEqual(p.root, path.InstallRoot.bindir)
        self.assertEqual(p.destdir, True)

        self.assertRaises(ValueError, self.Path, 'foo/bar', path.Root.srcdir,
                          True)

    def test_equality(self):
        self.assertTrue(self.Path('a', path.Root.srcdir) ==
                        self.Path('a', path.Root.srcdir))
        self.assertFalse(self.Path('a', path.Root.srcdir) !=
                         self.Path('a', path.Root.srcdir))
        self.assertTrue(self.Path('a', path.InstallRoot.bindir, True) ==
                        self.Path('a', path.InstallRoot.bindir, True))
        self.assertFalse(self.Path('a', path.InstallRoot.bindir, True) !=
                         self.Path('a', path.InstallRoot.bindir, True))

        self.assertFalse(self.Path('a', path.Root.srcdir) ==
                         self.Path('a', path.Root.builddir))
        self.assertTrue(self.Path('a', path.Root.srcdir) !=
                        self.Path('a', path.Root.builddir))
        self.assertFalse(self.Path('a', path.Root.srcdir) ==
                         self.Path('b', path.Root.srcdir))
        self.assertTrue(self.Path('a', path.Root.srcdir) !=
                        self.Path('b', path.Root.srcdir))
        self.assertFalse(self.Path('a', path.InstallRoot.bindir, True) ==
                         self.Path('a', path.InstallRoot.bindir, False))
        self.assertTrue(self.Path('a', path.InstallRoot.bindir, True) !=
                        self.Path('a', path.InstallRoot.bindir, False))

    def test_cross(self):
        for name in ('winnt', 'linux'):
            platform = target.platform_info(name)
            env = MockEnv(platform)

            p = self.Path('foo/bar', path.Root.srcdir)
            self.assertEqual(
                p.cross(env), platform.Path('foo/bar', path.Root.srcdir)
            )

    def test_parent(self):
        p = self.Path('foo/bar', path.Root.srcdir)
        self.assertEqual(p.parent(), self.Path('foo', path.Root.srcdir))

        p = self.Path('bar', path.Root.srcdir)
        self.assertEqual(p.parent(), self.Path('', path.Root.srcdir))

        p = self.Path('', path.Root.srcdir)
        self.assertRaises(ValueError, p.parent)

        p = self.Path('foo/bar', path.InstallRoot.bindir, True)
        self.assertEqual(
            p.parent(), self.Path('foo', path.InstallRoot.bindir, True)
        )

    def test_append(self):
        Root = path.Root
        p = self.Path('foo', Root.srcdir)
        self.assertEqual(p.append('bar'),
                         self.Path('foo/bar', Root.srcdir))
        self.assertEqual(p.append('.'), self.Path('foo', Root.srcdir))
        self.assertEqual(p.append('..'), self.Path('', Root.srcdir))
        self.assertEqual(p.append('../bar'), self.Path('bar', Root.srcdir))
        self.assertEqual(p.append(r'..\bar'), self.Path('bar', Root.srcdir))

        self.assertEqual(p.append('/bar'), self.Path('/bar', Root.absolute))
        self.assertEqual(p.append('C:/bar'),
                         self.Path('C:/bar', Root.absolute))
        self.assertEqual(p.append(r'C:\bar'),
                         self.Path('C:/bar', Root.absolute))
        self.assertEqual(p.append('//server/mount/bar'),
                         self.Path('//server/mount/bar', Root.absolute))
        self.assertEqual(p.append(r'\\server\mount\bar'),
                         self.Path('//server/mount/bar', Root.absolute))

        p = self.Path('foo', path.InstallRoot.bindir, True)
        self.assertEqual(p.append('bar'),
                         self.Path('foo/bar', path.InstallRoot.bindir, True))

        p = self.Path('foo', Root.srcdir)

    def test_ext(self):
        p = self.Path('foo.txt', path.Root.srcdir)
        self.assertEqual(p.ext(), '.txt')

    def test_addext(self):
        p = self.Path('foo', path.Root.srcdir)
        self.assertEqual(p.addext('.txt'),
                         self.Path('foo.txt', path.Root.srcdir))

        p = self.Path('foo', path.InstallRoot.bindir, True)
        self.assertEqual(p.addext('.txt'),
                         self.Path('foo.txt', path.InstallRoot.bindir, True))

    def test_stripext(self):
        p = self.Path('foo.txt', path.Root.srcdir)
        self.assertEqual(p.stripext(), self.Path('foo', path.Root.srcdir))
        p = self.Path('foo.txt', path.Root.srcdir)
        self.assertEqual(p.stripext('.cpp'),
                         self.Path('foo.cpp', path.Root.srcdir))

        p = self.Path('foo', path.Root.srcdir)
        self.assertEqual(p.stripext(), self.Path('foo', path.Root.srcdir))
        p = self.Path('foo', path.Root.srcdir)
        self.assertEqual(p.stripext('.cpp'),
                         self.Path('foo.cpp', path.Root.srcdir))

        p = self.Path('foo.txt', path.InstallRoot.bindir, True)
        self.assertEqual(p.stripext(),
                         self.Path('foo', path.InstallRoot.bindir, True))

    def test_splitleaf(self):
        p = self.Path('foo/bar/baz', path.Root.srcdir)
        self.assertEqual(p.splitleaf(),
                         (self.Path('foo/bar', path.Root.srcdir), 'baz'))

    def test_split(self):
        p = self.Path('foo/bar/baz', path.Root.srcdir)
        self.assertEqual(p.split(), ['foo', 'bar', 'baz'])

    def test_basename(self):
        p = self.Path('foo/bar', path.Root.srcdir)
        self.assertEqual(p.basename(), 'bar')

    def test_relpath_relative(self):
        p = self.Path('foo/bar', path.Root.srcdir)
        self.assertEqual(p.relpath(p), '.')
        self.assertEqual(p.relpath(p, 'pre'), 'pre')

        self.assertEqual(p.relpath(self.Path('foo', path.Root.srcdir)), 'bar')
        self.assertEqual(p.relpath(self.Path('foo', path.Root.srcdir), 'pre'),
                         self.ospath.join('pre', 'bar'))

        self.assertEqual(p.relpath(self.Path('baz', path.Root.srcdir)),
                         self.ospath.join('..', 'foo', 'bar'))
        self.assertEqual(p.relpath(self.Path('baz', path.Root.srcdir), 'pre'),
                         self.ospath.join('pre', '..', 'foo', 'bar'))

        self.assertEqual(p.relpath(self.Path('.', path.Root.srcdir)),
                         self.ospath.join('foo', 'bar'))
        self.assertEqual(p.relpath(self.Path('.', path.Root.srcdir), 'pre'),
                         self.ospath.join('pre', 'foo', 'bar'))

        p = self.Path('.', path.Root.srcdir)
        self.assertEqual(p.relpath(path.Path('foo', path.Root.srcdir)), '..')
        self.assertEqual(p.relpath(path.Path('foo', path.Root.srcdir), 'pre'),
                         self.ospath.join('pre', '..'))

        p = self.Path('foo/bar', path.Root.srcdir)
        self.assertRaises(
            ValueError, lambda: p.relpath(self.Path('foo', path.Root.builddir))
        )

    def test_relpath_absolute(self):
        p = self.Path('/foo/bar', path.Root.srcdir)
        self.assertEqual(
            p.relpath(self.Path('start', path.Root.srcdir)),
            self.ospath.join(self.ospath.sep, 'foo', 'bar')
        )
        self.assertEqual(
            p.relpath(self.Path('start', path.Root.srcdir), 'pre'),
            self.ospath.join(self.ospath.sep, 'foo', 'bar')
        )

        self.assertEqual(
            p.relpath(self.Path('/start', path.Root.srcdir)),
            self.ospath.join(self.ospath.sep, 'foo', 'bar')
        )
        self.assertEqual(
            p.relpath(self.Path('/start', path.Root.srcdir), 'pre'),
            self.ospath.join(self.ospath.sep, 'foo', 'bar')
        )

        p = self.Path(r'C:\foo\bar', path.Root.srcdir)
        self.assertEqual(
            p.relpath(self.Path(r'C:\start', path.Root.srcdir)),
            'C:' + self.ospath.sep + self.ospath.join('foo', 'bar')
        )
        self.assertEqual(
            p.relpath(self.Path(r'C:\start', path.Root.srcdir), 'pre'),
            'C:' + self.ospath.sep + self.ospath.join('foo', 'bar')
        )

    def test_reroot(self):
        p = self.Path('foo/bar', path.Root.srcdir)
        self.assertEqual(p.reroot(path.Root.builddir),
                         self.Path('foo/bar', path.Root.builddir))

        p = self.Path('foo/bar', path.InstallRoot.bindir, True)
        self.assertEqual(p.reroot(path.InstallRoot.libdir),
                         self.Path('foo/bar', path.InstallRoot.libdir, True))

    def test_to_json(self):
        p = self.Path('foo', path.Root.srcdir)
        self.assertEqual(p.to_json(), ('foo', 'srcdir', False))

        p = self.Path('foo', path.InstallRoot.bindir, True)
        self.assertEqual(p.to_json(), ('foo', 'bindir', True))

    def test_from_json(self):
        p = self.Path.from_json(['foo', 'srcdir', False])
        self.assertEqual(p, self.Path('foo', path.Root.srcdir))

        p = self.Path.from_json(['foo', 'bindir', True])
        self.assertEqual(p, self.Path('foo', path.InstallRoot.bindir, True))

    def test_realize_srcdir(self):
        p = self.Path('foo', path.Root.srcdir)
        self.assertEqual(p.realize(path_variables),
                         self.ospath.join('$(srcdir)', 'foo'))
        self.assertEqual(p.realize(path_variables, executable=True),
                         self.ospath.join('$(srcdir)', 'foo'))

        p = self.Path('foo/bar', path.Root.srcdir)
        self.assertEqual(p.realize(path_variables),
                         self.ospath.join('$(srcdir)', 'foo', 'bar'))
        self.assertEqual(p.realize(path_variables, executable=True),
                         self.ospath.join('$(srcdir)', 'foo', 'bar'))

    def test_realize_builddir(self):
        p = self.Path('foo', path.Root.builddir)
        self.assertEqual(p.realize(path_variables), 'foo')
        self.assertEqual(p.realize(path_variables, executable=True),
                         self.ospath.join('.', 'foo'))

        p = self.Path('foo/bar', path.Root.builddir)
        self.assertEqual(p.realize(path_variables),
                         self.ospath.join('foo', 'bar'))
        self.assertEqual(p.realize(path_variables, executable=True),
                         self.ospath.join('foo', 'bar'))

    def test_realize_absolute(self):
        ospath = self.ospath
        p = self.Path('/foo/bar', path.Root.builddir)
        self.assertEqual(p.realize(path_variables),
                         ospath.join(ospath.sep, 'foo', 'bar'))
        self.assertEqual(p.realize(path_variables, executable=True),
                         ospath.join(ospath.sep, 'foo', 'bar'))

        p = self.Path(r'C:\foo\bar', path.Root.builddir)
        self.assertEqual(p.realize(path_variables),
                         'C:' + ospath.sep + ospath.join('foo', 'bar'))
        self.assertEqual(p.realize(path_variables, executable=True),
                         'C:' + ospath.sep + ospath.join('foo', 'bar'))

    def test_realize_srcdir_empty(self):
        p = self.Path('', path.Root.srcdir)
        self.assertEqual(p.realize(path_variables), '$(srcdir)')
        self.assertEqual(p.realize(path_variables, executable=True),
                         '$(srcdir)')

    def test_realize_builddir_empty(self):
        p = self.Path('', path.Root.builddir)
        self.assertEqual(p.realize(path_variables), '.')
        self.assertEqual(p.realize(path_variables, executable=True), '.')

    def test_realize_destdir(self):
        path_vars_with_destdir = path_variables.copy()
        path_vars_with_destdir[path.DestDir.destdir] = '$(destdir)'

        p = self.Path('foo', path.InstallRoot.bindir, True)
        self.assertEqual(p.realize(path_variables),
                         self.ospath.join('$(bindir)', 'foo'))
        self.assertEqual(p.realize(path_vars_with_destdir),
                         self.ospath.join('$(destdir)$(bindir)', 'foo'))

    def test_string(self):
        ospath = self.ospath
        paths = {path.Root.srcdir: self.Path('/srcdir', path.Root.absolute)}

        p = self.Path('/foo/bar', path.Root.absolute)
        self.assertEqual(p.string(), ospath.join(ospath.sep, 'foo', 'bar'))

        p = self.Path('foo/bar', path.Root.srcdir)
        self.assertEqual(
            p.string(paths), ospath.join(ospath.sep, 'srcdir', 'foo', 'bar')
        )

        p = self.Path('.', path.Root.srcdir)
        self.assertEqual(p.string(paths), ospath.join(ospath.sep, 'srcdir'))

    def test_hash(self):
        d = {self.Path('.', path.Root.srcdir),
             self.Path('.', path.Root.builddir),
             self.Path('foo', path.Root.srcdir),
             self.Path('bar', path.InstallRoot.bindir),
             self.Path('bar', path.InstallRoot.bindir, destdir=True)}
        self.assertEqual(len(d), 5)

    def test_bool(self):
        self.assertEqual(bool(self.Path('.', path.Root.builddir)), False)
        self.assertEqual(bool(self.Path('.', path.Root.srcdir)), True)
        self.assertEqual(bool(self.Path('.', path.InstallRoot.bindir)), True)
        self.assertEqual(bool(self.Path('foo', path.Root.builddir)), True)
        self.assertEqual(bool(self.Path('foo', path.Root.srcdir)), True)
        self.assertEqual(bool(self.Path('foo', path.InstallRoot.bindir)), True)

    def test_add(self):
        p = self.Path('foo/bar', path.Root.srcdir)
        result = p + 'baz'
        self.assertEqual(type(result), jbos)
        self.assertEqual(result.bits, (p, 'baz'))

        result = 'baz' + p
        self.assertEqual(type(result), jbos)
        self.assertEqual(result.bits, ('baz', p))


class TestAbsPath(TestCase):
    def test_abspath(self):
        self.assertEqual(
            path.abspath('/foo/bar'),
            path.Path(os.path.abspath('/foo/bar'), path.Root.absolute)
        )


class TestInstallPath(TestCase):
    def test_install_path_file(self):
        p = path.Path('foo/bar', path.Root.srcdir)
        self.assertEqual(path.install_path(p, path.InstallRoot.bindir),
                         path.Path('bar', path.InstallRoot.bindir, True))

        p = path.Path('foo/bar', path.Root.builddir)
        self.assertEqual(path.install_path(p, path.InstallRoot.bindir),
                         path.Path('foo/bar', path.InstallRoot.bindir, True))

        p = path.abspath('/foo/bar')
        with self.assertRaises(TypeError):
            path.install_path(p, path.InstallRoot.bindir)

    def test_install_path_directory(self):
        p = path.Path('foo/bar', path.Root.srcdir)
        self.assertEqual(path.install_path(p, path.InstallRoot.bindir, True),
                         path.Path('', path.InstallRoot.bindir, True))

        p = path.Path('foo/bar', path.Root.builddir)
        self.assertEqual(path.install_path(p, path.InstallRoot.bindir, True),
                         path.Path('foo/bar', path.InstallRoot.bindir, True))

        p = path.abspath('/foo/bar')
        with self.assertRaises(TypeError):
            path.install_path(p, path.InstallRoot.bindir, True)

    def test_install_path_cross(self):
        for name in ('winnt', 'linux'):
            platform = target.platform_info(name)
            env = MockEnv(platform)

            p = path.Path('foo/bar', path.Root.srcdir)
            self.assertEqual(
                path.install_path(p, path.InstallRoot.bindir, cross=env),
                platform.Path('bar', path.InstallRoot.bindir)
            )

            p = path.Path('foo/bar', path.Root.builddir)
            self.assertEqual(
                path.install_path(p, path.InstallRoot.bindir, cross=env),
                platform.Path('foo/bar', path.InstallRoot.bindir)
            )

            p = path.Path('/foo/bar', path.Root.absolute)
            self.assertEqual(
                path.install_path(p, path.InstallRoot.bindir, cross=env),
                platform.Path('/foo/bar', path.Root.absolute)
            )

    def test_install_path_cross_directory(self):
        for name in ('winnt', 'linux'):
            platform = target.platform_info(name)
            env = MockEnv(platform)

            p = path.Path('foo/bar', path.Root.srcdir)
            self.assertEqual(path.install_path(p, path.InstallRoot.bindir,
                                               True, cross=env),
                             platform.Path('', path.InstallRoot.bindir))

            p = path.Path('foo/bar', path.Root.builddir)
            self.assertEqual(path.install_path(p, path.InstallRoot.bindir,
                                               True, cross=env),
                             platform.Path('foo/bar', path.InstallRoot.bindir))

            p = path.Path('/foo/bar', path.Root.absolute)
            self.assertEqual(path.install_path(p, path.InstallRoot.bindir,
                                               True, cross=env),
                             platform.Path('/foo/bar', path.Root.absolute))


class TestCommonPrefix(TestCase):
    def test_empty(self):
        self.assertEqual(path.commonprefix([]), None)

    def test_single(self):
        p = path.Path('foo/bar')
        self.assertEqual(path.commonprefix([p]), p)

    def test_multi_same(self):
        p = path.Path('foo/bar')
        self.assertEqual(path.commonprefix([p, p]), p)

    def test_multi_partial_match(self):
        p = path.Path('foo/bar')
        q = path.Path('foo/baz')
        self.assertEqual(path.commonprefix([p, q]), p.parent())

    def test_multi_subset(self):
        p = path.Path('foo/bar')
        q = path.Path('foo/bar/baz')
        self.assertEqual(path.commonprefix([p, q]), p)

    def test_multi_no_match(self):
        p = path.Path('foo/bar')
        q = path.Path('baz/quux')
        self.assertEqual(path.commonprefix([p, q]), path.Path(''))


class TestWrappedOsPath(TestCase):
    def test_wrap(self):
        mocked = mock.MagicMock(return_value=True)
        mocked.__name__ = 'foo'
        f = path._wrap_ospath(mocked)
        f(path.Path('/foo/bar'))
        mocked.assert_called_once_with(os.path.join(os.path.sep, 'foo', 'bar'))


class TestSamefile(TestCase):
    def test_real(self):
        with mock.patch('os.path.samefile', lambda x, y: x == y, create=True):
            self.assertEqual(path.samefile(path.Path('/foo/bar'),
                                           path.Path('/foo/bar')), True)

    def test_polyfill(self):
        class OsPath(object):
            def __init__(self):
                for i in ('isabs', 'normpath', 'realpath', 'expanduser'):
                    setattr(self, i, getattr(os.path, i))

        with mock.patch('os.path', OsPath()):
            self.assertEqual(path.samefile(path.Path('/foo/bar'),
                                           path.Path('/foo/bar')), True)


class TestMakedirs(TestCase):
    def test_success(self):
        with mock.patch('os.makedirs') as os_makedirs:
            path.makedirs('foo')
            path.makedirs('bar', 0o666)
            self.assertEqual(os_makedirs.mock_calls, [
                mock.call('foo', 0o777),
                mock.call('bar', 0o666),
            ])

    def test_exists(self):
        def mock_makedirs(path, mode):
            raise OSError(errno.EEXIST, 'msg')

        with mock.patch('os.makedirs', mock_makedirs), \
             mock.patch('os.path.isdir', lambda x: x == 'dir'):  # noqa
            self.assertRaises(OSError, path.makedirs, 'file')
            self.assertRaises(OSError, path.makedirs, 'file', exist_ok=True)
            self.assertRaises(OSError, path.makedirs, 'dir')
            path.makedirs('dir', exist_ok=True)

    def test_other_error(self):
        def mock_makedirs(path, mode):
            raise OSError(errno.EPERM, 'msg')

        with mock.patch('os.makedirs', mock_makedirs):
            self.assertRaises(OSError, path.makedirs, 'file')


class TestPushd(TestCase):
    def test_basic(self):
        with mock.patch('os.getcwd', return_value='cwd'), \
             mock.patch('os.chdir') as os_chdir:  # noqa
            with path.pushd('foo'):
                self.assertEqual(os_chdir.mock_calls, [mock.call('foo')])
            self.assertEqual(os_chdir.mock_calls, [
                mock.call('foo'), mock.call('cwd')
            ])

    def test_makedirs(self):
        with mock.patch('os.makedirs') as os_makedirs, \
             mock.patch('os.getcwd', return_value='cwd'), \
             mock.patch('os.chdir') as os_chdir:  # noqa
            with path.pushd('foo', makedirs=True):
                self.assertEqual(os_makedirs.mock_calls, [
                    mock.call('foo', 0o777)
                ])
                self.assertEqual(os_chdir.mock_calls, [mock.call('foo')])
            self.assertEqual(os_chdir.mock_calls, [
                mock.call('foo'), mock.call('cwd')
            ])
