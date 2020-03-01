import os.path

from .. import *


@skip_if('fortran' not in test_features, 'skipping fortran tests')
class TestF77(IntegrationTest):
    def __init__(self, *args, **kwargs):
        super().__init__(os.path.join('languages', 'f77'), *args, **kwargs)

    def test_build(self):
        self.build(executable('program'))
        self.assertOutput([executable('program')], ' hello from f77!\n')


@skip_if('fortran' not in test_features, 'skipping fortran tests')
class TestF95(IntegrationTest):
    def __init__(self, *args, **kwargs):
        super().__init__(os.path.join('languages', 'f95'), *args, **kwargs)

    def test_build(self):
        self.build(executable('program'))
        self.assertOutput([executable('program')], ' hello from f95!\n')
