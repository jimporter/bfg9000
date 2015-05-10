import subprocess
import unittest

from integration import *

class TestStaticLibrary(IntegrationTest):
    def __init__(self, *args, **kwargs):
        IntegrationTest.__init__(self, 'static_library', *args, **kwargs)

    def test_all(self):
        self.build()
        self.assertOutput([executable('program')], 'hello, library!\n')

if __name__ == '__main__':
    unittest.main()
