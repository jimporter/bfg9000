from .common import BuiltinTest

from bfg9000.builtins import default, install  # noqa
from bfg9000 import file_types
from bfg9000.path import Path, Root


class TestInstall(BuiltinTest):
    def test_install_none(self):
        self.assertEqual(self.builtin_dict['install'](), None)

    def test_install_single(self):
        exe = file_types.Executable(Path('exe', Root.srcdir), None)
        self.assertEqual(self.builtin_dict['install'](exe), exe)

    def test_install_multiple(self):
        exe1 = file_types.Executable(Path('exe1', Root.srcdir), None)
        exe2 = file_types.Executable(Path('exe2', Root.srcdir), None)
        self.assertEqual(self.builtin_dict['install'](exe1, exe2),
                         (exe1, exe2))
