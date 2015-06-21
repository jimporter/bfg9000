import os.path
import unittest

from integration import *

class TestOptions(IntegrationTest):
    def __init__(self, *args, **kwargs):
        IntegrationTest.__init__(
            self, os.path.join(examples_dir, '03_options'), *args, **kwargs
        )

    def test_build(self):
        self.build()
        self.assertOutput([executable('program')], 'hello, world!\n')

if __name__ == '__main__':
    unittest.main()
