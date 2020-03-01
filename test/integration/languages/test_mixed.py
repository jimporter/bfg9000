import os.path

from .. import *


class TestMixed(IntegrationTest):
    def __init__(self, *args, **kwargs):
        super().__init__(os.path.join('languages', 'mixed'), *args, **kwargs)

    def test_build(self):
        self.build(executable('program'))
        self.assertOutput([executable('program')], 'hello from c++!\n')


class TestMixedLibrary(IntegrationTest):
    def __init__(self, *args, **kwargs):
        super().__init__(os.path.join('languages', 'mixed_library'), *args,
                         **kwargs)

    def test_build(self):
        self.build(executable('program'))
        self.assertOutput([executable('program')], 'hello, library!\n')


# This fails on OS X, probably because of a version mismatch somewhere.
@skip_if(env.host_platform.family == 'windows', 'no fortran on windows')
@skip_if(env.host_platform.genus == 'darwin', 'fortran on os x is weird')
class TestMixedFortran(IntegrationTest):
    def __init__(self, *args, **kwargs):
        super().__init__(os.path.join('languages', 'mixed_fortran'), *args,
                         **kwargs)

    def test_build(self):
        self.build(executable('program'))
        self.assertOutput([executable('program')], 'hello from f77!\n')
