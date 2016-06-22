import tarfile

from . import *


class TestCustomSteps(IntegrationTest):
    def __init__(self, *args, **kwargs):
        IntegrationTest.__init__(
            self, os.path.join(examples_dir, '09_custom_steps'), *args,
            **kwargs
        )

    def test_hello(self):
        self.build(executable('hello'))
        self.assertOutput([executable('hello')], 'hello from python!\n')

    def test_goodbye(self):
        self.build(executable('goodbye'))
        self.assertOutput([executable('goodbye')], 'goodbye from python!\n')
