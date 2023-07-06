from . import *


class TestSubmoduleScope(IntegrationTest):
    def __init__(self, *args, **kwargs):
        super().__init__('submodule_scope', configure=False, *args, **kwargs)

    def test_configure(self):
        self.assertRegex(self.configure(),
                         r'info: \[child\] value = <unset>\n' +
                         r'info: \[parent\] value = parent\n')
