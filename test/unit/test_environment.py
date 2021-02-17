import os

from . import *

from bfg9000.environment import Environment, EnvVarDict, LibraryMode
from bfg9000.exceptions import ToolNotFoundError
from bfg9000.file_types import SourceFile
from bfg9000.path import Path, Root, InstallRoot
from bfg9000.tools import rm, lex, scripts  # noqa

this_dir = os.path.abspath(os.path.dirname(__file__))
test_data_dir = os.path.join(this_dir, '..', 'data')


class TestEnvVarDict(TestCase):
    def test_setitem(self):
        d = EnvVarDict()
        d['foo'] = 'fooval'
        self.assertEqual(d, {'foo': 'fooval'})
        self.assertEqual(d.initial, {})
        self.assertEqual(d.changes, {'foo': 'fooval'})

        d = EnvVarDict(foo='fooval', bar='barval')
        d['foo'] = 'foochange'
        self.assertEqual(d, {'foo': 'foochange', 'bar': 'barval'})
        self.assertEqual(d.initial, {'foo': 'fooval', 'bar': 'barval'})
        self.assertEqual(d.changes, {'foo': 'foochange'})

        with self.assertRaises(TypeError):
            d['foo'] = None

    def test_delitem(self):
        d = EnvVarDict(foo='fooval', bar='barval')
        del d['foo']
        self.assertEqual(d, {'bar': 'barval'})
        self.assertEqual(d.initial, {'foo': 'fooval', 'bar': 'barval'})
        self.assertEqual(d.changes, {'foo': None})

    def test_clear(self):
        d = EnvVarDict(foo='fooval', bar='barval')
        d.clear()
        self.assertEqual(d, {})
        self.assertEqual(d.initial, {'foo': 'fooval', 'bar': 'barval'})
        self.assertEqual(d.changes, {'foo': None, 'bar': None})

    def test_pop(self):
        d = EnvVarDict(foo='fooval', bar='barval')
        self.assertEqual(d.pop('foo'), 'fooval')
        self.assertEqual(d, {'bar': 'barval'})
        self.assertEqual(d.initial, {'foo': 'fooval', 'bar': 'barval'})
        self.assertEqual(d.changes, {'foo': None})

        self.assertEqual(d.pop('foo', 'default'), 'default')
        self.assertEqual(d, {'bar': 'barval'})
        self.assertEqual(d.initial, {'foo': 'fooval', 'bar': 'barval'})
        self.assertEqual(d.changes, {'foo': None})

        with self.assertRaises(KeyError):
            self.assertEqual(d.pop('foo'))

        self.assertEqual(d.pop('bar', 'default'), 'barval')
        self.assertEqual(d, {})
        self.assertEqual(d.initial, {'foo': 'fooval', 'bar': 'barval'})
        self.assertEqual(d.changes, {'foo': None, 'bar': None})

    def test_popitem(self):
        d = EnvVarDict(foo='fooval')
        self.assertEqual(d.popitem(), ('foo', 'fooval'))
        self.assertEqual(d, {})
        self.assertEqual(d.initial, {'foo': 'fooval'})
        self.assertEqual(d.changes, {'foo': None})

        with self.assertRaises(KeyError):
            self.assertEqual(d.popitem())

    def test_setdefault(self):
        d = EnvVarDict()
        self.assertEqual(d.setdefault('foo', 'fooval'), 'fooval')
        self.assertEqual(d, {'foo': 'fooval'})
        self.assertEqual(d.initial, {})
        self.assertEqual(d.changes, {'foo': 'fooval'})

        self.assertEqual(d.setdefault('foo', 'foo2'), 'fooval')
        self.assertEqual(d, {'foo': 'fooval'})
        self.assertEqual(d.initial, {})
        self.assertEqual(d.changes, {'foo': 'fooval'})

        with self.assertRaises(TypeError):
            d.setdefault('bar', None)

    def test_update(self):
        d = EnvVarDict(foo='fooval', bar='barval')
        d.update(foo='foochange', baz='bazval')
        self.assertEqual(d, {'foo': 'foochange', 'bar': 'barval',
                             'baz': 'bazval'})
        self.assertEqual(d.initial, {'foo': 'fooval', 'bar': 'barval'})
        self.assertEqual(d.changes, {'foo': 'foochange', 'baz': 'bazval'})

        d.update({'foo': 'foochange2'})
        self.assertEqual(d, {'foo': 'foochange2', 'bar': 'barval',
                             'baz': 'bazval'})
        self.assertEqual(d.initial, {'foo': 'fooval', 'bar': 'barval'})
        self.assertEqual(d.changes, {'foo': 'foochange2', 'baz': 'bazval'})

    def test_to_json(self):
        d = EnvVarDict(foo='fooval', bar='barval')
        d.update(foo='foochange', baz='bazval')
        self.assertEqual(d.to_json(), {
            'initial': {'foo': 'fooval', 'bar': 'barval'},
            'current': {'foo': 'foochange', 'bar': 'barval',
                        'baz': 'bazval'},
        })

    def test_from_json(self):
        d = EnvVarDict.from_json({
            'initial': {'foo': 'fooval', 'bar': 'barval'},
            'current': {'foo': 'foochange', 'bar': 'barval',
                        'baz': 'bazval'},
        })
        self.assertEqual(d, {'foo': 'foochange', 'bar': 'barval',
                             'baz': 'bazval'})
        self.assertEqual(d.initial, {'foo': 'fooval', 'bar': 'barval'})
        self.assertEqual(d.changes, {'foo': 'foochange', 'baz': 'bazval'})

        d = EnvVarDict.from_json({
            'initial': {'foo': 'fooval', 'bar': 'barval'},
            'current': {'bar': 'barval', 'baz': 'bazval'},
        })
        self.assertEqual(d, {'bar': 'barval', 'baz': 'bazval'})
        self.assertEqual(d.initial, {'foo': 'fooval', 'bar': 'barval'})
        self.assertEqual(d.changes, {'foo': None, 'baz': 'bazval'})

    def test_reset(self):
        d = EnvVarDict(foo='fooval', bar='barval')
        d.update(foo='foochange', baz='bazval')
        d.reset()
        self.assertEqual(d, {'foo': 'fooval', 'bar': 'barval'})
        self.assertEqual(d.initial, {'foo': 'fooval', 'bar': 'barval'})
        self.assertEqual(d.changes, {})


class TestEnvironment(TestCase):
    def assertDictsEqual(self, a, b):
        self.assertEqual(len(a), len(b))
        for i in a:
            self.assertEqual(a[i], b[i])

    def make_env(self):
        env = Environment(Path('bfgdir', Root.srcdir), None, None,
                          Path('/srcdir'), Path('/builddir'))
        env.install_dirs[InstallRoot.prefix] = Path('/prefix/')
        env.install_dirs[InstallRoot.exec_prefix] = Path('/exec-prefix/')
        return env

    def test_supports_destdir(self):
        env = self.make_env()
        env.install_dirs = {
            InstallRoot.prefix: Path('/root/prefix/'),
            InstallRoot.exec_prefix: Path('', InstallRoot.prefix),
            InstallRoot.bindir: Path('bin/', InstallRoot.exec_prefix),
            InstallRoot.libdir: Path('lib/', InstallRoot.exec_prefix),
            InstallRoot.includedir: Path('include/', InstallRoot.prefix),
        }
        self.assertTrue(env.supports_destdir)

        env = self.make_env()
        env.install_dirs = {
            InstallRoot.prefix: Path('C:/root/prefix/'),
            InstallRoot.exec_prefix: Path('', InstallRoot.prefix),
            InstallRoot.bindir: Path('bin/', InstallRoot.exec_prefix),
            InstallRoot.libdir: Path('lib/', InstallRoot.exec_prefix),
            InstallRoot.includedir: Path('include/', InstallRoot.prefix),
        }
        self.assertFalse(env.supports_destdir)

        env = self.make_env()
        env.install_dirs = {
            InstallRoot.prefix: None,
            InstallRoot.exec_prefix: Path('', InstallRoot.prefix),
            InstallRoot.bindir: Path('bin/', InstallRoot.exec_prefix),
            InstallRoot.libdir: Path('lib/', InstallRoot.exec_prefix),
            InstallRoot.includedir: Path('include/', InstallRoot.prefix),
        }
        self.assertFalse(env.supports_destdir)

    def test_builder(self):
        env = self.make_env()
        self.assertIsInstance(env.builder('lex'), lex.LexBuilder)
        with self.assertRaises(ToolNotFoundError):
            env.builder('nonexist')

    def test_tool(self):
        env = self.make_env()
        self.assertIsInstance(env.tool('rm'), rm.Rm)
        with self.assertRaises(ToolNotFoundError):
            env.tool('nonexist')

    def test_run_arguments(self):
        env = self.make_env()
        src = SourceFile(Path('foo.py'), 'python')
        self.assertEqual(env.run_arguments([src]), [env.tool('python'), src])
        with self.assertRaises(TypeError):
            env.run_arguments(src, 'nonexist')

    def test_upgrade_from_v4(self):
        env = Environment.load(
            os.path.join(test_data_dir, 'environment', 'v4')
        )

        self.assertPathEqual(env.bfgdir, Path('/path/to/'))
        self.assertEqual(env.backend, 'make')

        self.assertPathEqual(env.srcdir, Path('/root/srcdir/'))
        self.assertPathEqual(env.builddir, Path('/root/builddir/'))
        self.assertPathDictEqual(env.install_dirs, {
            InstallRoot.prefix: Path('/root/prefix/'),
            InstallRoot.exec_prefix: Path('', InstallRoot.prefix),
            InstallRoot.bindir: Path('bin/', InstallRoot.exec_prefix),
            InstallRoot.libdir: Path('lib/', InstallRoot.exec_prefix),
            InstallRoot.includedir: Path('include/', InstallRoot.prefix),
        })

        self.assertEqual(env.library_mode, LibraryMode(True, False))
        self.assertEqual(env.extra_args, [])

        variables = {u'HOME': u'/home/user'}
        self.assertEqual(env.variables, variables)

        self.assertEqual(env.host_platform.name, 'linux')
        self.assertEqual(env.target_platform.name, 'linux')

    def test_finalize(self):
        env = self.make_env()
        env.finalize({}, (True, False))
        self.assertEqual(env.library_mode, LibraryMode(True, False))
        self.assertPathEqual(env.install_dirs[InstallRoot.prefix],
                             Path('/prefix/'))
        self.assertPathEqual(env.install_dirs[InstallRoot.exec_prefix],
                             Path('/exec-prefix/'))

        env = self.make_env()
        env.finalize({
            InstallRoot.prefix: Path('/foo'),
            InstallRoot.exec_prefix: None,
        }, (True, False))
        self.assertPathEqual(env.install_dirs[InstallRoot.prefix],
                             Path('/foo/'))
        self.assertPathEqual(env.install_dirs[InstallRoot.exec_prefix],
                             Path('/exec-prefix/'))
