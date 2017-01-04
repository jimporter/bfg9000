from . import *


@skip_if_backend('msbuild')
class TestExplicitDefaults(IntegrationTest):
    def __init__(self, *args, **kwargs):
        IntegrationTest.__init__(self, 'explicit_defaults', *args, **kwargs)

    def test_default(self):
        self.build()
        self.assertOutput([executable('a')], 'hello, a!\n')
        self.assertNotExists(executable('b'))


@skip_if_backend('msbuild')
class TestImplicitDefaults(IntegrationTest):
    def __init__(self, *args, **kwargs):
        IntegrationTest.__init__(self, 'implicit_defaults', *args, **kwargs)

    def test_default(self):
        self.build()
        self.assertOutput([executable('a')], 'hello, a!\n')
        self.assertOutput([executable('b')], 'hello, b!\n')
        self.assertNotExists(executable('test'))
