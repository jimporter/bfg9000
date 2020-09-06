import os

from . import *

from bfg9000.environment import Environment, LibraryMode
from bfg9000.exceptions import ToolNotFoundError
from bfg9000.file_types import SourceFile
from bfg9000.path import Path, Root, InstallRoot
from bfg9000.tools import rm, lex, scripts  # noqa

this_dir = os.path.abspath(os.path.dirname(__file__))
test_data_dir = os.path.join(this_dir, '..', 'data')


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
