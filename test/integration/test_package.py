import os.path

from .integration import *

is_mingw = platform_name() == 'windows' and env.compiler('c++').flavor == 'cc'


class TestSystemPackage(IntegrationTest):
    def __init__(self, *args, **kwargs):
        IntegrationTest.__init__(
            self, os.path.join(examples_dir, '04_package'),
            *args, **kwargs
        )

    @unittest.skipIf(is_mingw, 'xfail on mingw')
    def test_build(self):
        self.build()
        self.assertOutput([executable('program')], '')


class TestBoostPackage(IntegrationTest):
    def __init__(self, *args, **kwargs):
        IntegrationTest.__init__(self, 'boost', *args, **kwargs)

    @unittest.skipIf(is_mingw, 'xfail on mingw')
    def test_build(self):
        self.build()
        self.assertOutput([executable('program'), '--hello'],
                          'Hello, world!\n')
