import subprocess
import unittest

from integration import *

class TestSimple(IntegrationTest):
    def __init__(self, *args, **kwargs):
        IntegrationTest.__init__(self, 'simple', *args, **kwargs)

    def test_build(self):
        self.build(executable('simple'))
        self.assertOutput([executable('simple')], 'hello, world!\n')

    def test_default(self):
        self.build()
        self.assertOutput([executable('simple')], 'hello, world!\n')

if __name__ == '__main__':
    unittest.main()
