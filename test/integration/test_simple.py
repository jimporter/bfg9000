import os.path
import unittest

from integration import *

class TestSimple(IntegrationTest):
    def __init__(self, *args, **kwargs):
        IntegrationTest.__init__(self, os.path.join(examples_dir, '01_simple'),
                                 *args, **kwargs)

    def test_build(self):
        self.build(executable('simple'))
        self.assertOutput([executable('simple')], 'hello, world!\n')

    @skip_if_backend('msbuild')
    def test_all(self):
        self.build('all')
        self.assertOutput([executable('simple')], 'hello, world!\n')

    def test_default(self):
        self.build()
        self.assertOutput([executable('simple')], 'hello, world!\n')

if __name__ == '__main__':
    unittest.main()
