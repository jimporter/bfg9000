from .integration import *


class TestDefaults(IntegrationTest):
    def __init__(self, *args, **kwargs):
        IntegrationTest.__init__(self, 'defaults', *args, **kwargs)

    @skip_if_backend('msbuild')
    def test_default(self):
        self.build()
        self.assertOutput([executable('a')], 'hello, a!\n')
        self.assertOutput([executable('b')], 'hello, b!\n')
