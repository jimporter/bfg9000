from . import *


class TestCustomSteps(IntegrationTest):
    def __init__(self, *args, **kwargs):
        super().__init__(os.path.join(examples_dir, '11_custom_steps'), *args,
                         **kwargs)

    def test_hello(self):
        self.build(executable('hello'))
        self.assertOutput([executable('hello')], 'hello from python!\n')

    def test_goodbye(self):
        self.build(executable('goodbye'))
        self.assertOutput([executable('goodbye')], 'goodbye from python!\n')

        # Ensure that cleaning multitarget make rules removes the .stamp file.
        if self.backend == 'make':
            self.clean()
            self.assertDirectory('.', {
                '.bfg_environ', 'Makefile',
                os.path.join('goodbye.int', '.dir'),
            })
