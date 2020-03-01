import os.path

from . import *


@skip_if_backend('msbuild')
class TestTests(IntegrationTest):
    def __init__(self, *args, **kwargs):
        super().__init__(os.path.join(examples_dir, '07_tests'), *args,
                         **kwargs)

    def test_test(self):
        self.build('test')
