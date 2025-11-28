from .. import AttrDict, FileTestCase, make_env, TestCase  # noqa: F401

from bfg9000 import file_types
from bfg9000.builtins import builtin
from bfg9000.build_inputs import BuildInputs
from bfg9000.options import option_list
from bfg9000.packages import Package
from bfg9000.path import Path, Root


class BuiltinTestCase(FileTestCase):
    clear_variables = False

    def setUp(self):
        self.env = make_env()
        self.build, self.context = self._make_context(self.env)
        self.bfgfile = file_types.File(self.build.bfgpath)

    def _make_context(self, env):
        build = BuildInputs(env, Path('build.bfg', Root.srcdir))
        context = builtin.BuildContext(env, build, None)
        context.path_stack.append(
            builtin.BuildContext.PathEntry(build.bfgpath)
        )
        return build, context


class MockPackage(Package):
    def __init__(self, name, submodules=None, version=None, *, format,
                 compile_options=None, link_options=None):
        super().__init__(name, submodules, format=format)
        self.version = version
        self._compile_options = compile_options or option_list()
        self._link_options = link_options or option_list()

    def compile_options(self, compiler, *, raw=False):
        return self._compile_options

    def link_options(self, linker, *, raw=False):
        return self._link_options
