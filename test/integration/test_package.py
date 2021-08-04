import os.path

from . import *


class TestPackage(IntegrationTest):
    def __init__(self, *args, **kwargs):
        super().__init__(os.path.join(examples_dir, '06_package'), *args,
                         **kwargs)

    def test_build(self):
        self.build()
        self.assertOutput([executable('program')], '')


@skip_if('boost' not in test_features, 'skipping boost tests')
class TestBoostPackage(IntegrationTest):
    def __init__(self, *args, **kwargs):
        super().__init__('boost', *args, **kwargs)

    def test_build(self):
        self.build()
        self.assertOutput([executable('program'), '--hello'],
                          'Hello, world!\n')


class TestOpenGLPackage(IntegrationTest):
    def __init__(self, *args, **kwargs):
        super().__init__('opengl', *args, **kwargs)

    def test_build(self):
        self.build()
        self.assertOutput([executable('program')], '')
