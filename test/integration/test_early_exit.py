from . import *


class TestEarlyExit(IntegrationTest):
    def __init__(self, *args, **kwargs):
        super().__init__('early_exit', *args, **kwargs)

    def test_build(self):
        self.build(executable('program'))
        self.assertOutput([executable('program')], 'hello, world!\n')

    def test_postexit(self):
        with self.assertRaises(SubprocessError):
            self.build('postexit')


class TestEarlyExitFail(IntegrationTest):
    def __init__(self, *args, **kwargs):
        super().__init__('early_exit_fail', configure=False, *args, **kwargs)

    def test_configure(self):
        self.configure(returncode=42)
        with self.assertRaises(SubprocessError):
            self.build()
