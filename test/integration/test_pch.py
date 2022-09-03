from . import *


@skip_if('pch' not in test_features, 'skipping pch tests')
class TestPch(IntegrationTest):
    def __init__(self, *args, **kwargs):
        super().__init__('pch', *args, **kwargs)

    def test_build(self):
        self.build(executable('program'))
        self.assertOutput([executable('program')], 'hello from pch!\n')


@skip_if('pch' not in test_features, 'skipping pch tests')
class TestPchNoSource(IntegrationTest):
    def __init__(self, *args, **kwargs):
        super().__init__('pch_no_source', *args, **kwargs)

    def test_build(self):
        self.build(executable('program'))
        self.assertOutput([executable('program')], 'hello from pch!\n')
