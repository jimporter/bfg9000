import os.path
import unittest

from integration import *

class TestExternalLibrary(IntegrationTest):
    def __init__(self, *args, **kwargs):
        IntegrationTest.__init__(
            self, os.path.join(examples_dir, '05_external_library'),
            *args, **kwargs
        )

    def test_build(self):
        self.build()
        self.assertOutput([executable('program')], '')

if __name__ == '__main__':
    unittest.main()
