import subprocess
import unittest

from integration import *

class TestExternalLibrary(IntegrationTest):
    def __init__(self, *args, **kwargs):
        IntegrationTest.__init__(self, 'external_library', *args, **kwargs)

    def test_all(self):
        self.build()
        self.assertOutput([executable('program')], '')

if __name__ == '__main__':
    unittest.main()
