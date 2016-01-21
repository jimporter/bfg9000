import os.path

from .integration import *

is_mingw = platform_name() == 'windows' and env.compiler('c++').flavor == 'cc'


class TestSystemLibrary(IntegrationTest):
    def __init__(self, *args, **kwargs):
        IntegrationTest.__init__(
            self, os.path.join(examples_dir, '04_external_library'),
            *args, **kwargs
        )

    @unittest.skipIf(is_mingw, 'xfail on mingw')
    def test_build(self):
        self.build()
        self.assertOutput([executable('program')], '')


class TestBoostLibrary(IntegrationTest):
    def __init__(self, *args, **kwargs):
        IntegrationTest.__init__(self, 'boost', *args, **kwargs)

    @unittest.skipIf(is_mingw, 'xfail on mingw')
    def test_build(self):
        self.build()
        self.assertOutput([executable('program'), '--hello'],
                          'Hello, world!\n')
