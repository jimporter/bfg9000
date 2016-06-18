from . import *


class TestExtraDeps(IntegrationTest):
    def __init__(self, *args, **kwargs):
        IntegrationTest.__init__(self, 'extra_deps', *args, **kwargs)

    def test_build(self):
        self.build(executable('program'))
        self.assertOutput([executable('program')], 'hello, world!\n')

        self.assertExists(output_file('1'))
        self.assertExists(output_file('2'))
        self.assertExists(output_file('3'))

    def test_touch_3(self):
        self.build('touch3')

        self.assertNotExists(output_file('1'))
        self.assertExists(output_file('2'))
        self.assertExists(output_file('3'))
