from . import *


class TestExplicitDefaults(IntegrationTest):
    def __init__(self, *args, **kwargs):
        IntegrationTest.__init__(self, 'explicit_defaults', *args, **kwargs)

    @skip_if_backend('msbuild')
    def test_default(self):
        self.build()
        self.assertOutput([executable('a')], 'hello, a!\n')
        self.assertNotExists(executable('b'))


class TestImplicitDefaults(IntegrationTest):
    def __init__(self, *args, **kwargs):
        IntegrationTest.__init__(self, 'implicit_defaults', *args, **kwargs)

    @skip_if_backend('msbuild')
    def test_default(self):
        self.build()
        self.assertOutput([executable('a')], 'hello, a!\n')
        self.assertOutput([executable('b')], 'hello, b!\n')
        self.assertNotExists(executable('test'))
