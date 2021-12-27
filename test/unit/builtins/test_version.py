from .common import BuiltinTest

from bfg9000.builtins import version  # noqa: F401
from bfg9000.versioning import bfg_version, VersionError


class TestRequiredVersion(BuiltinTest):
    def test_bfg_version(self):
        self.context['bfg9000_required_version']('>=0.1.0')
        with self.assertRaises(VersionError):
            self.context['bfg9000_required_version']('<=0.1.0')

    def test_python_version(self):
        self.context['bfg9000_required_version'](python_version='>=2.7.0')
        with self.assertRaises(VersionError):
            self.context['bfg9000_required_version'](python_version='<=2.0.0')

    def test_both_versions(self):
        self.context['bfg9000_required_version']('>=0.1.0', '>=2.7.0')
        with self.assertRaises(VersionError):
            self.context['bfg9000_required_version']('<=0.1.0', '<=2.0.0')


class TestVersion(BuiltinTest):
    def test_version(self):
        self.assertEqual(self.context['bfg9000_version'], bfg_version)
