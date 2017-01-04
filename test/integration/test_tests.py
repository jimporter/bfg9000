import os.path

from . import *


@skip_if_backend('msbuild')
class TestTests(IntegrationTest):
    def __init__(self, *args, **kwargs):
        IntegrationTest.__init__(
            self, os.path.join(examples_dir, '08_tests'), *args, **kwargs
        )

    def test_test(self):
        self.build('test')
