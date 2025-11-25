from .common import BuiltinTestCase
from bfg9000 import builtins
from bfg9000.builtins.builtin import BuildContext


class TestBuiltin(BuiltinTestCase):
    def test_init(self):
        builtins.init()
        context = BuildContext(self.env, self.build, None)
        self.assertTrue('project' in context.builtins)
        self.assertTrue('executable' in context.builtins)
