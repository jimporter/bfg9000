import unittest

from ... import make_env

from bfg9000.builtins import builtin
from bfg9000.build_inputs import BuildInputs
from bfg9000.path import Path, Root


class BuiltinTest(unittest.TestCase):
    def setUp(self):
        self.env = make_env()
        self.build = BuildInputs(self.env, Path('build.bfg', Root.srcdir))
        self.builtin_dict = builtin.build.bind(
            build_inputs=self.build, env=self.env, argv=None
        )
