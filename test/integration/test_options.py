import os.path

from . import *


class TestOptions(IntegrationTest):
    def __init__(self, *args, **kwargs):
        super().__init__(os.path.join(examples_dir, '03_options'), *args,
                         **kwargs)

    def test_build(self):
        self.build()
        self.assertOutput([executable('program')], 'hello, world!\n')
        if env.host_platform.genus == 'linux':
            output = self.assertPopen(['readelf', '-s', executable('program')])
            self.assertNotRegex(output, r"Symbol table '\.symtab'")
