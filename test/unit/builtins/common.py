from six import iterkeys

from .. import make_env, TestCase

from bfg9000 import file_types
from bfg9000.builtins import builtin
from bfg9000.build_inputs import BuildInputs
from bfg9000.path import Path, Root


class BuiltinTest(TestCase):
    def setUp(self):
        self.env = make_env()
        self.build = BuildInputs(self.env, Path('build.bfg', Root.srcdir))
        self.builtin_dict = self.bind()
        self.bfgfile = file_types.File(self.build.bfgpath)

    def bind(self):
        return builtin.build.bind(
            build_inputs=self.build, env=self.env, argv=None
        )

    def assertSame(self, a, b, exclude=set()):
        self.assertEqual(type(a), type(b))
        keys = set(iterkeys(a.__dict__)) & set(iterkeys(b.__dict__)) - exclude
        for i in keys:
            ai, bi = getattr(a, i), getattr(b, i)
            self.assertEqual(ai, bi, '{!r}: {!r} != {!r}'.format(i, ai, bi))
