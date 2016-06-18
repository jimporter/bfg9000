import os.path

from .. import *


@unittest.skipIf(env.platform.name == 'windows',
                 'no objective c on windows')
class TestObjC(IntegrationTest):
    def __init__(self, *args, **kwargs):
        IntegrationTest.__init__(
            self, os.path.join('languages', 'objc'), *args, **kwargs
        )

    def test_build(self):
        self.build(executable('program'))
        self.assertOutput([executable('program')], 'hello from objective c!\n')
