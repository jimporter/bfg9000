from . import *


class TestWholeArchive(IntegrationTest):
    def __init__(self, *args, **kwargs):
        IntegrationTest.__init__(self, 'whole_archive', *args, **kwargs)

    @skip_if(env.builder('c++').flavor != 'cc', 'requires cc builder',
             hide=True)
    def test_build(self):
        self.build()
        self.assertOutput([executable('program')], 'hello, library!\n')
