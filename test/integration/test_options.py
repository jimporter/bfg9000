import os.path

from . import *


class TestOptions(IntegrationTest):
    def __init__(self, *args, **kwargs):
        IntegrationTest.__init__(
            self, os.path.join(examples_dir, '03_options'), *args, **kwargs
        )

    def test_build(self):
        self.build()
        self.assertOutput([executable('program')], 'hello, world!\n')
        if env.host_platform.genus == 'linux':
            output = self.assertPopen(['readelf', '-s', executable('program')])
            assertNotRegex(self, output, r"Symbol table '\.symtab'")
