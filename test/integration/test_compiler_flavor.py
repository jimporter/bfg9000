from .integration import *
from bfg9000.environment import Environment

env = Environment(None, None, None, None, None, None)
flavor = env.compiler('c++').flavor


class TestCompilerFlavor(IntegrationTest):
    def __init__(self, *args, **kwargs):
        IntegrationTest.__init__(self, 'compiler_flavor', *args, **kwargs)

    def test_build(self):
        self.build(executable('program'))
        self.assertOutput([executable('program')],
                          'hello, {}!\n'.format(flavor))
