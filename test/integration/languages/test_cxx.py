import os.path

from ..integration import *


class TestCxx(IntegrationTest):
    def __init__(self, *args, **kwargs):
        IntegrationTest.__init__(
            self, os.path.join('languages', 'cxx'), *args, **kwargs
        )

    def test_build(self):
        self.build(executable('program'))
        self.assertOutput([executable('program')], 'hello from c++!\n')
