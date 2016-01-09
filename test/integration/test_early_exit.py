from .integration import *


class TestEarlyExit(IntegrationTest):
    def __init__(self, *args, **kwargs):
        IntegrationTest.__init__(self, 'early_exit', *args, **kwargs)

    def test_build(self):
        self.build(executable('program'))
        self.assertOutput([executable('program')], 'hello, world!\n')

    def test_postexit(self):
        with self.assertRaises(SubprocessError):
            self.build('postexit')
