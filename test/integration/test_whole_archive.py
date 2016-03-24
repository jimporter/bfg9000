from .integration import *


class TestWholeArchive(IntegrationTest):
    def __init__(self, *args, **kwargs):
        IntegrationTest.__init__(self, 'whole_archive', *args, **kwargs)

    @unittest.skipIf(env.builder('c++').flavor != 'cc', 'requires cc builder')
    def test_build(self):
        self.build()
        self.assertOutput([executable('program')], 'hello, library!\n')
