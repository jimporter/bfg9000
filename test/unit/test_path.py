import os
from collections import namedtuple
from unittest import mock

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
        self.assertEqual(p.directory, False)
        self.assertEqual(p.destdir, False)

        p = self.Path(r'foo\bar', path.Root.srcdir)
        self.assertEqual(p.suffix, 'foo/bar')
        self.assertEqual(p.root, path.Root.srcdir)
        self.assertEqual(p.directory, False)
        self.assertEqual(p.destdir, False)

        p = self.Path('foo/bar/../.', path.Root.srcdir)
        self.assertEqual(p.suffix, 'foo')
        self.assertEqual(p.root, path.Root.srcdir)
        self.assertEqual(p.directory, False)
        self.assertEqual(p.destdir, False)

        p = self.Path('foo/.././bar', path.Root.srcdir)
        self.assertEqual(p.suffix, 'bar')
        self.assertEqual(p.root, path.Root.srcdir)
        self.assertEqual(p.directory, False)
        self.assertEqual(p.destdir, False)

        self.assertRaises(ValueError, self.Path, '..', path.Root.srcdir)
        self.assertRaises(ValueError, self.Path, 'foo/../..', path.Root.srcdir)
        self.assertRaises(ValueError, self.Path, 'foo/../../bar',
                          path.Root.srcdir)

        self.assertRaises(ValueError, self.Path, 'foo', None)
        self.assertRaises(ValueError, self.Path, 'foo', 'root')

    def test_construct_absolute(self):
        p = self.Path('/foo/bar', path.Root.absolute)
        self.assertEqual(p.suffix, '/foo/bar')
        self.assertEqual(p.root, path.Root.absolute)
        self.assertEqual(p.directory, False)
        self.assertEqual(p.destdir, False)

        p = self.Path('/foo/bar', path.Root.srcdir)
        self.assertEqual(p.suffix, '/foo/bar')
        self.assertEqual(p.root, path.Root.absolute)
        self.assertEqual(p.directory, False)
        self.assertEqual(p.destdir, False)

        p = self.Path('C:/foo/bar', path.Root.srcdir)
        self.assertEqual(p.suffix, 'C:/foo/bar')
        self.assertEqual(p.root, path.Root.absolute)
        self.assertEqual(p.directory, False)
        self.assertEqual(p.destdir, False)

        p = self.Path(r'C:\foo\bar', path.Root.srcdir)
        self.assertEqual(p.suffix, 'C:/foo/bar')
        self.assertEqual(p.root, path.Root.absolute)
        self.assertEqual(p.directory, False)
        self.assertEqual(p.destdir, False)

        p = self.Path('//server/mount/foo/bar', path.Root.srcdir)
        self.assertEqual(p.suffix, '//server/mount/foo/bar')
        self.assertEqual(p.root, path.Root.absolute)
        self.assertEqual(p.directory, False)
        self.assertEqual(p.destdir, False)

        p = self.Path(r'\\server\mount\foo\bar', path.Root.srcdir)
        self.assertEqual(p.suffix, '//server/mount/foo/bar')
        self.assertEqual(p.root, path.Root.absolute)
        self.assertEqual(p.directory, False)
        self.assertEqual(p.destdir, False)

        self.assertRaises(ValueError, self.Path, 'foo/bar', path.Root.absolute)
        self.assertRaises(ValueError, self.Path, 'c:foo')

    def test_construct_directory(self):
        p = self.Path('foo/bar/', path.Root.srcdir)
        self.assertEqual(p.suffix, 'foo/bar')
        self.assertEqual(p.root, path.Root.srcdir)
        self.assertEqual(p.directory, True)
        self.assertEqual(p.destdir, False)

        p = self.Path('foo\\bar\\', path.Root.srcdir)
        self.assertEqual(p.suffix, 'foo/bar')
        self.assertEqual(p.root, path.Root.srcdir)
        self.assertEqual(p.directory, True)
        self.assertEqual(p.destdir, False)

        p = self.Path('.', path.Root.srcdir)
        self.assertEqual(p.suffix, '')
        self.assertEqual(p.root, path.Root.srcdir)
        self.assertEqual(p.directory, True)
        self.assertEqual(p.destdir, False)

        p = self.Path('./', path.Root.srcdir)
        self.assertEqual(p.suffix, '')
        self.assertEqual(p.root, path.Root.srcdir)
        self.assertEqual(p.directory, True)
        self.assertEqual(p.destdir, False)

        p = self.Path('foo/../.', path.Root.srcdir)
        self.assertEqual(p.suffix, '')
        self.assertEqual(p.root, path.Root.srcdir)
        self.assertEqual(p.directory, True)
        self.assertEqual(p.destdir, False)

        p = self.Path('foo/bar', path.Root.srcdir, directory=True)
        self.assertEqual(p.suffix, 'foo/bar')
        self.assertEqual(p.root, path.Root.srcdir)
        self.assertEqual(p.directory, True)
        self.assertEqual(p.destdir, False)

        p = self.Path('/foo/bar/', path.Root.absolute)
        self.assertEqual(p.suffix, '/foo/bar')
        self.assertEqual(p.root, path.Root.absolute)
        self.assertEqual(p.directory, True)
        self.assertEqual(p.destdir, False)

        p = self.Path('/', path.Root.absolute)
        self.assertEqual(p.suffix, '/')
        self.assertEqual(p.root, path.Root.absolute)
        self.assertEqual(p.directory, True)
        self.assertEqual(p.destdir, False)

        p = self.Path('/.', path.Root.absolute)
        self.assertEqual(p.suffix, '/')
        self.assertEqual(p.root, path.Root.absolute)
        self.assertEqual(p.directory, True)
        self.assertEqual(p.destdir, False)

        p = self.Path('C:/', path.Root.srcdir)
        self.assertEqual(p.suffix, 'C:/')
        self.assertEqual(p.root, path.Root.absolute)
        self.assertEqual(p.directory, True)
        self.assertEqual(p.destdir, False)

        p = self.Path('C:/.', path.Root.srcdir)
        self.assertEqual(p.suffix, 'C:/')
        self.assertEqual(p.root, path.Root.absolute)
        self.assertEqual(p.directory, True)
        self.assertEqual(p.destdir, False)

        self.assertRaises(ValueError, self.Path, 'foo/', path.Root.srcdir,
                          directory=False)

    def test_construct_destdir(self):
        p = self.Path('foo/bar', path.InstallRoot.bindir, True)
        self.assertEqual(p.suffix, 'foo/bar')
        self.assertEqual(p.root, path.InstallRoot.bindir)
        self.assertEqual(p.directory, False)
        self.assertEqual(p.destdir, True)

        p = self.Path('/foo/bar', path.Root.absolute, True)
        self.assertEqual(p.suffix, '/foo/bar')
        self.assertEqual(p.root, path.Root.absolute)
        self.assertEqual(p.directory, False)
        self.assertEqual(p.destdir, True)

        p = self.Path('/foo/bar', path.InstallRoot.bindir, True)
        self.assertEqual(p.suffix, '/foo/bar')
        self.assertEqual(p.root, path.Root.absolute)
        self.assertEqual(p.directory, False)
        self.assertEqual(p.destdir, True)

        self.assertRaises(ValueError, self.Path, 'foo/bar', path.Root.srcdir,
                          True)

    def test_construct_relative(self):
        for base in (self.Path('foo', path.Root.srcdir),
                     self.Path('/foo', path.Root.absolute),
                     self.Path('foo', path.InstallRoot.bindir, True)):
            p = self.Path('bar', base)
            self.assertEqual(p.suffix, base.suffix + '/bar')
            self.assertEqual(p.root, base.root)
            self.assertEqual(p.directory, False)
            self.assertEqual(p.destdir, base.destdir)

            p = self.Path('bar/', base)
            self.assertEqual(p.suffix, base.suffix + '/bar')
            self.assertEqual(p.root, base.root)
            self.assertEqual(p.directory, True)
            self.assertEqual(p.destdir, base.destdir)

            p = self.Path('..', base)
            self.assertEqual(p.suffix, base.suffix.replace('foo', ''))
            self.assertEqual(p.root, base.root)
            self.assertEqual(p.directory, True)
            self.assertEqual(p.destdir, base.destdir)

            p = self.Path('bar', base, True)
            self.assertEqual(p.suffix, base.suffix + '/bar')
            self.assertEqual(p.root, base.root)
            self.assertEqual(p.directory, False)
            self.assertEqual(p.destdir, True)

            p = self.Path('bar', base, False)
            self.assertEqual(p.suffix, base.suffix + '/bar')
            self.assertEqual(p.root, base.root)
            self.assertEqual(p.directory, False)
            self.assertEqual(p.destdir, False)

            p = self.Path('/bar', base)
            self.assertEqual(p.suffix, '/bar')
            self.assertEqual(p.root, path.Root.absolute)
            self.assertEqual(p.directory, False)
            self.assertEqual(p.destdir, False)

            if base.root != path.Root.absolute:
                self.assertRaises(ValueError, self.Path, '../..', base)

    def test_ensure(self):
        self.assertPathEqual(self.Path.ensure('foo'), self.Path('foo'))
        self.assertPathEqual(self.Path.ensure('foo', path.Root.srcdir),
                             self.Path('foo', path.Root.srcdir))
        self.assertPathEqual(self.Path.ensure('foo', directory=True),
                             self.Path('foo/'))
        self.assertPathEqual(
            self.Path.ensure('foo', path.InstallRoot.bindir, True),
            self.Path('foo', path.InstallRoot.bindir, True)
        )

        p = self.Path('foo')
        self.assertIs(self.Path.ensure(p), p)
        self.assertIs(self.Path.ensure(p, path.Root.srcdir), p)
        self.assertIs(self.Path.ensure(p, path.InstallRoot.bindir, True), p)
        self.assertRaises(ValueError, self.Path.ensure, p, path.Root.srcdir,
                          strict=True)
        self.assertRaises(ValueError, self.Path.ensure, '/foo',
                          path.Root.srcdir, strict=True)

        base = self.Path('base')
        self.assertPathEqual(self.Path.ensure('foo', base),
                             self.Path('base/foo'))
        self.assertPathEqual(self.Path.ensure('foo', base),
                             self.Path('base/foo'))
        self.assertPathEqual(self.Path.ensure('/foo', base), self.Path('/foo'))
        self.assertIs(self.Path.ensure(p, base), p)
        self.assertRaises(ValueError, self.Path.ensure,
                          self.Path('foo', path.Root.srcdir), strict=True)
        self.assertRaises(ValueError, self.Path.ensure, '/foo', strict=True)

    def test_equality(self):
        self.assertTrue(self.Path('a', path.Root.srcdir) ==
                        self.Path('a', path.Root.srcdir))
        self.assertFalse(self.Path('a', path.Root.srcdir) !=
                         self.Path('a', path.Root.srcdir))
        self.assertTrue(self.Path('a', path.InstallRoot.bindir, True) ==
                        self.Path('a', path.InstallRoot.bindir, True))
        self.assertFalse(self.Path('a', path.InstallRoot.bindir, True) !=
                         self.Path('a', path.InstallRoot.bindir, True))

        self.assertTrue(self.Path('a', path.Root.srcdir) ==
                        self.Path('a/', path.Root.srcdir))
        self.assertFalse(self.Path('a', path.Root.srcdir) !=
                         self.Path('a/', path.Root.srcdir))

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

        winpath = target.platform_info('winnt').Path
        linuxpath = target.platform_info('linux').Path
        self.assertFalse(winpath('a') == linuxpath('a'))
        self.assertTrue(winpath('a') != linuxpath('a'))

        self.assertFalse(self.Path('a', path.Root.srcdir) == 'a')
        self.assertTrue(self.Path('a', path.Root.srcdir) != 'a')

    def test_cross(self):
        for name in ('winnt', 'linux'):
            platform = target.platform_info(name)
            env = MockEnv(platform)

            p = self.Path('foo/bar', path.Root.srcdir)
            self.assertPathEqual(p.cross(env),
                                 platform.Path('foo/bar', path.Root.srcdir))

            p = self.Path('foo/bar/', path.Root.srcdir)
            self.assertPathEqual(p.cross(env),
                                 platform.Path('foo/bar/', path.Root.srcdir))

            p = self.Path('foo/bar', path.InstallRoot.bindir, destdir=True)
            self.assertPathEqual(
                p.cross(env),
                platform.Path('foo/bar', path.InstallRoot.bindir)
            )

    def test_as_directory(self):
        f = self.Path('foo', path.Root.srcdir)
        d = self.Path('foo/', path.Root.srcdir)
        self.assertPathEqual(f.as_directory(), d)
        self.assertIs(d.as_directory(), d)

    def test_parent(self):
        p = self.Path('foo/bar', path.Root.srcdir)
        self.assertPathEqual(p.parent(), self.Path('foo/', path.Root.srcdir))

        p = self.Path('bar', path.Root.srcdir)
        self.assertPathEqual(p.parent(), self.Path('./', path.Root.srcdir))

        p = self.Path('', path.Root.srcdir)
        self.assertRaises(ValueError, p.parent)

        p = self.Path('foo/bar', path.InstallRoot.bindir, True)
        self.assertPathEqual(
            p.parent(), self.Path('foo/', path.InstallRoot.bindir, True)
        )

    def test_append(self):
        Root = path.Root
        p = self.Path('foo', Root.srcdir)
        self.assertPathEqual(p.append('bar'),
                             self.Path('foo/bar', Root.srcdir))
        self.assertPathEqual(p.append('bar/baz'),
                             self.Path('foo/bar/baz', Root.srcdir))
        self.assertPathEqual(p.append(r'bar\baz'),
                             self.Path('foo/bar/baz', Root.srcdir))

        self.assertPathEqual(p.append('.'), self.Path('foo', Root.srcdir))
        self.assertPathEqual(p.append('..'), self.Path('', Root.srcdir))
        self.assertPathEqual(p.append('../bar'), self.Path('bar', Root.srcdir))
        self.assertPathEqual(p.append(r'..\bar'),
                             self.Path('bar', Root.srcdir))

        self.assertPathEqual(p.append('bar/'),
                             self.Path('foo/bar/', Root.srcdir))
        self.assertPathEqual(p.append('./'), self.Path('foo/', Root.srcdir))

        self.assertPathEqual(p.append('/bar'),
                             self.Path('/bar', Root.absolute))
        self.assertPathEqual(p.append('C:/bar'),
                             self.Path('C:/bar', Root.absolute))
        self.assertPathEqual(p.append(r'C:\bar'),
                             self.Path('C:/bar', Root.absolute))
        self.assertPathEqual(p.append('//server/mount/bar'),
                             self.Path('//server/mount/bar', Root.absolute))
        self.assertPathEqual(p.append(r'\\server\mount\bar'),
                             self.Path('//server/mount/bar', Root.absolute))

        p = self.Path('foo', path.InstallRoot.bindir, True)
        self.assertPathEqual(
            p.append('bar'),
            self.Path('foo/bar', path.InstallRoot.bindir, True)
        )

        p = self.Path('foo', Root.srcdir)
        self.assertRaises(ValueError, p.append, '../..')

    def test_ext(self):
        p = self.Path('foo.txt', path.Root.srcdir)
        self.assertEqual(p.ext(), '.txt')

    def test_addext(self):
        p = self.Path('foo', path.Root.srcdir)
        self.assertPathEqual(p.addext('.txt'),
                             self.Path('foo.txt', path.Root.srcdir))

        p = self.Path('foo/', path.Root.srcdir)
        self.assertPathEqual(p.addext('.txt'),
                             self.Path('foo.txt/', path.Root.srcdir))

        p = self.Path('foo', path.InstallRoot.bindir, True)
        self.assertPathEqual(
            p.addext('.txt'),
            self.Path('foo.txt', path.InstallRoot.bindir, True)
        )

    def test_stripext(self):
        p = self.Path('foo.txt', path.Root.srcdir)
        self.assertPathEqual(p.stripext(), self.Path('foo', path.Root.srcdir))
        p = self.Path('foo.txt', path.Root.srcdir)
        self.assertPathEqual(p.stripext('.cpp'),
                             self.Path('foo.cpp', path.Root.srcdir))

        p = self.Path('foo.txt/', path.Root.srcdir)
        self.assertPathEqual(p.stripext(),
                             self.Path('foo/', path.Root.srcdir))
        p = self.Path('foo.txt/', path.Root.srcdir)
        self.assertPathEqual(p.stripext('.cpp'),
                             self.Path('foo.cpp/', path.Root.srcdir))

        p = self.Path('foo', path.Root.srcdir)
        self.assertPathEqual(p.stripext(), self.Path('foo', path.Root.srcdir))
        p = self.Path('foo', path.Root.srcdir)
        self.assertPathEqual(p.stripext('.cpp'),
                             self.Path('foo.cpp', path.Root.srcdir))

        p = self.Path('foo.txt', path.InstallRoot.bindir, True)
        self.assertPathEqual(p.stripext(),
                             self.Path('foo', path.InstallRoot.bindir, True))

    def test_splitleaf(self):
        p = self.Path('foo/bar/baz', path.Root.srcdir)
        par, leaf = p.splitleaf()
        self.assertPathEqual(par, self.Path('foo/bar/', path.Root.srcdir))
        self.assertEqual(leaf, 'baz')

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
        self.assertEqual(p.relpath(p, localize=False), '.')
        self.assertEqual(p.relpath(p, 'pre', False), 'pre')

        self.assertEqual(p.relpath(self.Path('foo', path.Root.srcdir)), 'bar')
        self.assertEqual(p.relpath(self.Path('foo', path.Root.srcdir), 'pre'),
                         self.ospath.join('pre', 'bar'))
        self.assertEqual(p.relpath(self.Path('foo', path.Root.srcdir),
                                   localize=False), 'bar')
        self.assertEqual(p.relpath(self.Path('foo', path.Root.srcdir), 'pre',
                                   False), 'pre/bar')

        self.assertEqual(p.relpath(self.Path('baz', path.Root.srcdir)),
                         self.ospath.join('..', 'foo', 'bar'))
        self.assertEqual(p.relpath(self.Path('baz', path.Root.srcdir), 'pre'),
                         self.ospath.join('pre', '..', 'foo', 'bar'))
        self.assertEqual(p.relpath(self.Path('baz', path.Root.srcdir),
                                   localize=False), '../foo/bar')
        self.assertEqual(p.relpath(self.Path('baz', path.Root.srcdir), 'pre',
                                   False), 'pre/../foo/bar')

        self.assertEqual(p.relpath(self.Path('.', path.Root.srcdir)),
                         self.ospath.join('foo', 'bar'))
        self.assertEqual(p.relpath(self.Path('.', path.Root.srcdir), 'pre'),
                         self.ospath.join('pre', 'foo', 'bar'))
        self.assertEqual(p.relpath(self.Path('.', path.Root.srcdir),
                                   localize=False), 'foo/bar')
        self.assertEqual(p.relpath(self.Path('.', path.Root.srcdir), 'pre',
                                   False), 'pre/foo/bar')

        p = self.Path('.', path.Root.srcdir)
        self.assertEqual(p.relpath(path.Path('foo', path.Root.srcdir)), '..')
        self.assertEqual(p.relpath(path.Path('foo', path.Root.srcdir), 'pre'),
                         self.ospath.join('pre', '..'))
        self.assertEqual(p.relpath(path.Path('foo', path.Root.srcdir),
                                   localize=False), '..')
        self.assertEqual(p.relpath(path.Path('foo', path.Root.srcdir), 'pre',
                                   False), 'pre/..')

        p = self.Path('foo/bar', path.Root.srcdir)
        self.assertRaises(
            ValueError, lambda: p.relpath(self.Path('foo', path.Root.builddir))
        )

    def test_relpath_absolute(self):
        p = self.Path('/foo/bar')
        self.assertEqual(p.relpath(self.Path('start')),
                         self.ospath.join(self.ospath.sep, 'foo', 'bar'))
        self.assertEqual(p.relpath(self.Path('start'), 'pre'),
                         self.ospath.join(self.ospath.sep, 'foo', 'bar'))
        self.assertEqual(p.relpath(self.Path('start'), localize=False),
                         '/foo/bar')
        self.assertEqual(p.relpath(self.Path('start'), 'pre', False),
                         '/foo/bar')

        self.assertEqual(p.relpath(self.Path('/start')),
                         self.ospath.join(self.ospath.sep, 'foo', 'bar'))
        self.assertEqual(p.relpath(self.Path('/start'), 'pre'),
                         self.ospath.join(self.ospath.sep, 'foo', 'bar'))
        self.assertEqual(p.relpath(self.Path('/start'), localize=False),
                         '/foo/bar')
        self.assertEqual(p.relpath(self.Path('/start'), 'pre', False),
                         '/foo/bar')

        p = self.Path(r'C:\foo\bar')
        self.assertEqual(
            p.relpath(self.Path(r'C:\start')),
            'C:' + self.ospath.sep + self.ospath.join('foo', 'bar')
        )
        self.assertEqual(
            p.relpath(self.Path(r'C:\start'), 'pre'),
            'C:' + self.ospath.sep + self.ospath.join('foo', 'bar')
        )
        self.assertEqual(p.relpath(self.Path(r'C:\start'), localize=False),
                         'C:/foo/bar')
        self.assertEqual(p.relpath(self.Path(r'C:\start'), 'pre', False),
                         'C:/foo/bar')

    def test_reroot(self):
        p = self.Path('foo/bar', path.Root.srcdir)
        self.assertPathEqual(p.reroot(path.Root.builddir),
                             self.Path('foo/bar', path.Root.builddir))

        p = self.Path('foo/bar/', path.Root.srcdir)
        self.assertPathEqual(p.reroot(path.Root.builddir),
                             self.Path('foo/bar/', path.Root.builddir))

        p = self.Path('foo/bar', path.InstallRoot.bindir, True)
        self.assertPathEqual(
            p.reroot(path.InstallRoot.libdir),
            self.Path('foo/bar', path.InstallRoot.libdir, True)
        )

    def test_to_json(self):
        p = self.Path('foo', path.Root.srcdir)
        self.assertEqual(p.to_json(), ('foo', 'srcdir', False))

        p = self.Path('foo/', path.Root.srcdir)
        self.assertEqual(p.to_json(), ('foo/', 'srcdir', False))

        p = self.Path('./', path.Root.srcdir)
        self.assertEqual(p.to_json(), ('./', 'srcdir', False))

        p = self.Path('/', path.Root.absolute)
        self.assertEqual(p.to_json(), ('/', 'absolute', False))

        p = self.Path('foo', path.InstallRoot.bindir, True)
        self.assertEqual(p.to_json(), ('foo', 'bindir', True))

    def test_from_json(self):
        p = self.Path.from_json(['foo', 'srcdir', False])
        self.assertPathEqual(p, self.Path('foo', path.Root.srcdir))

        p = self.Path.from_json(['foo', 'bindir', True])
        self.assertPathEqual(
            p, self.Path('foo', path.InstallRoot.bindir, True)
        )

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

        p = self.Path('/foo', path.Root.absolute, True)
        self.assertEqual(p.realize(path_variables),
                         self.ospath.join(self.ospath.sep, 'foo'))
        self.assertEqual(p.realize(path_vars_with_destdir),
                         self.ospath.join('$(destdir)', 'foo'))

    def test_realize_no_variable_sep(self):
        p = self.Path('foo', path.Root.srcdir)
        self.assertEqual(p.realize(path_variables, variable_sep=False),
                         '$(srcdir)foo')

        p = self.Path('foo/bar', path.Root.srcdir)
        self.assertEqual(p.realize(path_variables, variable_sep=False),
                         self.ospath.join('$(srcdir)foo', 'bar'))

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
        with mock.patch('os.getcwd', return_value=r'/base'):
            self.assertPathEqual(path.abspath('foo'),
                                 path.Path('/base/foo', path.Root.absolute))
            self.assertPathEqual(path.abspath('/foo/bar'),
                                 path.Path('/foo/bar', path.Root.absolute))

            self.assertPathEqual(path.abspath('foo/'),
                                 path.Path('/base/foo/', path.Root.absolute))
            self.assertPathEqual(path.abspath('/foo/bar/'),
                                 path.Path('/foo/bar/', path.Root.absolute))

            self.assertPathEqual(path.abspath('foo', directory=True),
                                 path.Path('/base/foo/', path.Root.absolute))
            self.assertRaises(ValueError, path.abspath, 'foo/',
                              directory=False)

    def test_drive(self):
        with mock.patch('os.getcwd', return_value=r'C:\base'):
            self.assertPathEqual(path.abspath('foo'),
                                 path.Path('C:/base/foo', path.Root.absolute))
            self.assertPathEqual(path.abspath('/foo/bar'),
                                 path.Path('C:/foo/bar', path.Root.absolute))
            self.assertPathEqual(path.abspath('D:/foo/bar'),
                                 path.Path('D:/foo/bar', path.Root.absolute))


class TestCommonPrefix(TestCase):
    def test_empty(self):
        self.assertEqual(path.commonprefix([]), None)

    def test_single(self):
        p = path.Path('foo/bar')
        self.assertPathEqual(path.commonprefix([p]), p)

    def test_multi_same(self):
        p = path.Path('foo/bar')
        self.assertPathEqual(path.commonprefix([p, p]), p)

    def test_multi_partial_match(self):
        p = path.Path('foo/bar')
        q = path.Path('foo/baz')
        self.assertPathEqual(path.commonprefix([p, q]), path.Path('foo/'))

    def test_multi_subset(self):
        p = path.Path('foo/bar')
        q = path.Path('foo/bar/baz')
        self.assertPathEqual(path.commonprefix([p, q]), path.Path('foo/bar/'))

    def test_multi_no_match(self):
        p = path.Path('foo/bar')
        q = path.Path('baz/quux')
        self.assertPathEqual(path.commonprefix([p, q]), path.Path(''))


class TestWrappedOsPath(TestCase):
    def test_wrap(self):
        mocked = mock.MagicMock(return_value=True)
        mocked.__name__ = 'foo'
        f = path._wrap_ospath(mocked)
        f(path.Path('/foo/bar'))
        mocked.assert_called_once_with(os.path.join(os.path.sep, 'foo', 'bar'))


class TestSamefile(TestCase):
    def test_samefile(self):
        with mock.patch('os.path.samefile', lambda x, y: x == y, create=True):
            self.assertEqual(path.samefile(path.Path('/foo/bar'),
                                           path.Path('/foo/bar')), True)


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
                    mock.call('foo', 0o777, False)
                ])
                self.assertEqual(os_chdir.mock_calls, [mock.call('foo')])
            self.assertEqual(os_chdir.mock_calls, [
                mock.call('foo'), mock.call('cwd')
            ])

    def test_exception(self):
        with mock.patch('os.getcwd', return_value='cwd'), \
             mock.patch('os.chdir') as os_chdir:  # noqa
            with self.assertRaises(ValueError):
                with path.pushd('foo'):
                    self.assertEqual(os_chdir.mock_calls, [mock.call('foo')])
                    raise ValueError('uh oh!')
            self.assertEqual(os_chdir.mock_calls, [
                mock.call('foo'), mock.call('cwd')
            ])
