import os.path

from .integration import *

is_mingw = platform_name() == 'windows' and env.compiler('c++').flavor == 'cc'


@unittest.skipIf(is_mingw, 'xfail on mingw')
class TestSystemPackage(IntegrationTest):
    def __init__(self, *args, **kwargs):
        IntegrationTest.__init__(
            self, os.path.join(examples_dir, '04_package'),
            *args, **kwargs
        )

    def test_build(self):
        self.build()
        self.assertOutput([executable('program')], '')


@unittest.skipIf(is_mingw, 'xfail on mingw')
class TestBoostPackage(IntegrationTest):
    def __init__(self, *args, **kwargs):
        IntegrationTest.__init__(self, 'boost', *args, **kwargs)

    def test_build(self):
        self.build()
        self.assertOutput([executable('program'), '--hello'],
                          'Hello, world!\n')


@unittest.skipIf(platform_name() == 'windows', 'xfail on windows')
class TestPkgConfigPackage(IntegrationTest):
    def __init__(self, *args, **kwargs):
        IntegrationTest.__init__(self, 'pkgconfig_package', *args, **kwargs)

    def test_build(self):
        self.build()
        self.assertOutput([executable('program'), '--hello'], '')
