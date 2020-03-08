from .common import BuiltinTest
from bfg9000 import file_types
from bfg9000.builtins import alias as alias_  # noqa
from bfg9000.path import Path, Root


class TestAlias(BuiltinTest):
    def test_alias(self):
        expected = file_types.Phony('foo')
        alias = self.context['alias']('foo')
        self.assertSameFile(alias, expected)
        self.assertEqual(alias.creator.extra_deps, [])

    def test_deps(self):
        dep = self.context['generic_file']('dep.txt')
        expected = file_types.Phony('foo')
        alias = self.context['alias']('foo', dep)
        self.assertSameFile(alias, expected)
        self.assertEqual(alias.creator.extra_deps, [dep])

    def test_submodule(self):
        with self.context.push_path(Path('dir/build.bfg', Root.srcdir)):
            expected = file_types.Phony('foo')
            alias = self.context['alias']('foo')
            self.assertSameFile(alias, expected)
