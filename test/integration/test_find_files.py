import os.path
import unittest

from integration import *

class TestFindFiles(IntegrationTest):
    def __init__(self, *args, **kwargs):
        IntegrationTest.__init__(
            self, os.path.join(examples_dir, '07_find_files'), *args, **kwargs
        )

    def test_default(self):
        self.build()
        self.assertOutput([executable('hello')], 'Hello, world!\n')
        self.assertOutput(
            [executable('goodbye')],
            'Goodbye!\nAuf Wiedersehen!\n'
        )

if __name__ == '__main__':
    unittest.main()
