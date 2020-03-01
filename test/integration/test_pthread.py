from . import *


@skip_if(env.target_platform.family == 'windows', hide=True)
class TestPthread(IntegrationTest):
    def __init__(self, *args, **kwargs):
        super().__init__('pthread', *args, **kwargs)

    def test_build(self):
        self.build(executable('program'))
        self.assertOutput([executable('program')], 'hello from thread!\n')
