from . import *


class TestUserArgs(IntegrationTest):
    def __init__(self, *args, **kwargs):
        IntegrationTest.__init__(
            self, os.path.join(examples_dir, '10_custom_args'),
            configure=False, *args, **kwargs
        )

    def test_build_default(self):
        self.configure()
        self.build(executable('simple'))
        self.assertOutput([executable('simple')], 'hello from unnamed!\n')

    def test_build_with_args(self):
        self.configure(['--name=foo'])
        self.build(executable('simple'))
        self.assertOutput([executable('simple')], 'hello from foo!\n')
