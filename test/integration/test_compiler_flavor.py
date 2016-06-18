from . import *


class TestCompilerFlavor(IntegrationTest):
    def __init__(self, *args, **kwargs):
        IntegrationTest.__init__(self, 'compiler_flavor', *args, **kwargs)

    def test_build(self):
        self.build(executable('program'))
        self.assertOutput(
            [executable('program')],
            'hello, {}!\n'.format(env.builder('c++').flavor)
        )
