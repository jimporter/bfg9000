import os.path

from .. import *


@skip_if(env.host_platform.family == 'windows', 'no objective c on windows')
class TestObjCxx(IntegrationTest):
    def __init__(self, *args, **kwargs):
        super().__init__(os.path.join('languages', 'objcxx'), *args, **kwargs)

    def test_build(self):
        self.build(executable('program'))
        self.assertOutput([executable('program')],
                          'hello from objective c++!\n')
