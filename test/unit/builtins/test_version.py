from .. import *

from bfg9000.builtins.version import bfg9000_required_version, bfg9000_version
from bfg9000.versioning import bfg_version, VersionError


class TestRequiredVersion(TestCase):
    def test_bfg_version(self):
        bfg9000_required_version('>=0.1.0')
        self.assertRaises(VersionError, bfg9000_required_version, '<=0.1.0')

    def test_python_version(self):
        bfg9000_required_version(python_version='>=2.7.0')
        self.assertRaises(VersionError, bfg9000_required_version, None,
                          '<=2.0.0')

    def test_both_versions(self):
        bfg9000_required_version('>=0.1.0', '>=2.7.0')
        self.assertRaises(VersionError, bfg9000_required_version, '<=0.1.0',
                          '<=2.0.0')


class TestVersion(TestCase):
    def test_version(self):
        self.assertEqual(bfg9000_version(), bfg_version)
