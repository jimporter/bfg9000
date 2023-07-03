from .. import AttrDict, make_env, TestCase  # noqa: F401

from bfg9000 import file_types
from bfg9000.builtins import builtin
from bfg9000.build_inputs import BuildInputs
from bfg9000.path import Path, Root


class FileTest(TestCase):
    def assertSameFile(self, a, b, exclude=set(), seen=None):
        if seen is None:
            seen = set()
        seen.add(id(a))

        self.assertEqual(type(a), type(b))
        keys = ((set(a.__dict__.keys()) | set(b.__dict__.keys())) -
                exclude - {'creator', 'post_install'})

        for i in keys:
            ai, bi = getattr(a, i, None), getattr(b, i, None)
            if ( isinstance(ai, file_types.Node) and
                 isinstance(bi, file_types.Node) ):
                if not id(ai) in seen:
                    self.assertSameFile(ai, bi, exclude, seen)
            else:
                self.assertEqual(
                    ai, bi, '{!r}: {!r} != {!r}'.format(i, ai, bi)
                )


class BuiltinTest(FileTest):
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
