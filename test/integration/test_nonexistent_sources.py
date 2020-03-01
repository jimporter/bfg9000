from . import *


class TestNonexistentSources(IntegrationTest):
    def __init__(self, *args, **kwargs):
        super().__init__('nonexistent_sources', *args, **kwargs)

    def test_build(self):
        self.build(executable('simple'))
        self.assertOutput([executable('simple')], 'hello, world!\n')

    def test_default(self):
        self.build()
        self.assertOutput([executable('simple')], 'hello, world!\n')
