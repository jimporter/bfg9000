import subprocess
import unittest

from integration import *

class TestSharedLibrary(IntegrationTest):
    def __init__(self, *args, **kwargs):
        IntegrationTest.__init__(self, 'shared_library', *args, **kwargs)

    def test_all(self):
        self.build()
        self.assertOutput([executable('program')], 'hello, library!\n')

if __name__ == '__main__':
    unittest.main()
