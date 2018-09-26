from .common import BuiltinTest
from bfg9000 import exceptions


class TestExceptions(BuiltinTest):
    def test_exceptions(self):
        for name in dir(exceptions):
            t = getattr(exceptions, name)
            if isinstance(t, type):
                self.assertTrue(self.builtin_dict[name] is t)
