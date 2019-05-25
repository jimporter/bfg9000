import os
import sys
from six import iteritems

from . import *

from bfg9000.environment import Environment, LibraryMode
from bfg9000.path import Path, Root, InstallRoot
from bfg9000.platforms.host import platform_info

this_dir = os.path.abspath(os.path.dirname(__file__))
test_data_dir = os.path.join(this_dir, '..', 'data')


class TestEnvironment(TestCase):
    def assertDictsEqual(self, a, b):
        self.assertEqual(len(a), len(b))
        for i in a:
            self.assertEqual(a[i], b[i])

    def test_upgrade_from_v4(self):
        env = Environment.load(
            os.path.join(test_data_dir, 'environment', 'v4')
        )

        self.assertEqual(env.bfgdir, Path('/path/to', Root.absolute))
        self.assertEqual(env.backend, 'make')

        self.assertEqual(env.srcdir, Path('/root/srcdir', Root.absolute))
        self.assertEqual(env.builddir, Path('/root/builddir', Root.absolute))
        self.assertDictsEqual(env.install_dirs, {
            InstallRoot.prefix: Path('/root/prefix', Root.absolute),
            InstallRoot.exec_prefix: Path('', InstallRoot.prefix),
            InstallRoot.bindir: Path('bin', InstallRoot.exec_prefix),
            InstallRoot.libdir: Path('lib', InstallRoot.exec_prefix),
            InstallRoot.includedir: Path('include', InstallRoot.prefix),
        })

        self.assertEqual(env.library_mode, LibraryMode(True, False))
        self.assertEqual(env.extra_args, [])

        variables = {u'HOME': u'/home/user'}
        if platform_info().family == 'windows' and sys.version_info[0] == 2:
            variables = {str(k): str(v) for k, v in iteritems(variables)}
        self.assertEqual(env.variables, variables)

        self.assertEqual(env.host_platform.name, 'linux')
        self.assertEqual(env.target_platform.name, 'linux')
