import os.path

from . import *

is_mingw = (env.host_platform.family == 'windows' and
            env.builder('c++').flavor == 'cc')


class TestPackage(IntegrationTest):
    def __init__(self, *args, **kwargs):
        super().__init__(os.path.join(examples_dir, '04_package'), *args,
                         **kwargs)

    def test_build(self):
        self.build()
        # XXX: This fails on MinGW (not sure why)...
        if not is_mingw:
            self.assertOutput([executable('program')], '')


class TestSystemPackage(IntegrationTest):
    def __init__(self, *args, **kwargs):
        super().__init__(os.path.join(examples_dir, '04_package'),
                         extra_env={'PKG_CONFIG': 'nonexist'}, *args, **kwargs)

    def test_build(self):
        self.build()
        # XXX: This fails on MinGW (not sure why)...
        if not is_mingw:
            self.assertOutput([executable('program')], '')


@skip_if(is_mingw, 'xfail on mingw')
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


class TestOpenGLSystemPackage(IntegrationTest):
    def __init__(self, *args, **kwargs):
        super().__init__('opengl', extra_env={'PKG_CONFIG': 'nonexist'}, *args,
                         **kwargs)

    def test_build(self):
        self.build()
        self.assertOutput([executable('program')], '')
