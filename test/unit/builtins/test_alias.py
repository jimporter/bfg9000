from .common import BuiltinTest
from bfg9000 import file_types
from bfg9000.builtins import alias as alias_  # noqa


class TestAlias(BuiltinTest):
    def test_alias(self):
        expected = file_types.Phony('foo')
        alias = self.builtin_dict['alias']('foo')
        self.assertSameFile(alias, expected)
        self.assertEqual(alias.creator.extra_deps, [])

    def test_deps(self):
        dep = self.builtin_dict['generic_file']('dep.txt')
        expected = file_types.Phony('foo')
        alias = self.builtin_dict['alias']('foo', dep)
        self.assertSameFile(alias, expected)
        self.assertEqual(alias.creator.extra_deps, [dep])
