from .. import make_env, TestCase

from bfg9000.builtins import builtin
from bfg9000.build_inputs import BuildInputs
from bfg9000.path import Path, Root


class BuiltinTest(TestCase):
    def setUp(self):
        self.env = make_env()
        self.build = BuildInputs(self.env, Path('build.bfg', Root.srcdir))
        self.builtin_dict = self.bind()

    def bind(self):
        return builtin.build.bind(
            build_inputs=self.build, env=self.env, argv=None
        )
