import os.path

from .. import *


class TestMixed(IntegrationTest):
    def __init__(self, *args, **kwargs):
        IntegrationTest.__init__(
            self, os.path.join('languages', 'mixed'), *args, **kwargs
        )

    def test_build(self):
        self.build(executable('program'))
        self.assertOutput([executable('program')], 'hello from c++!\n')


class TestMixedLibrary(IntegrationTest):
    def __init__(self, *args, **kwargs):
        IntegrationTest.__init__(
            self, os.path.join('languages', 'mixed_library'), *args, **kwargs
        )

    def test_build(self):
        self.build(executable('program'))
        self.assertOutput([executable('program')], 'hello, library!\n')


# This fails on OS X, probably because of a version mismatch somewhere.
@unittest.skipIf(env.platform.name == 'windows', 'no fortran on windows')
@unittest.skipIf(env.platform.name == 'darwin', 'fortran on os x is weird')
class TestMixedFortran(IntegrationTest):
    def __init__(self, *args, **kwargs):
        IntegrationTest.__init__(
            self, os.path.join('languages', 'mixed_fortran'), *args, **kwargs
        )

    def test_build(self):
        self.build(executable('program'))
        self.assertOutput([executable('program')], 'hello from f77!\n')
