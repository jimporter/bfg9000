import subprocess
import unittest

from integration import *

class TestExtraDeps(IntegrationTest):
    def __init__(self, *args, **kwargs):
        IntegrationTest.__init__(self, 'extra_deps', *args, **kwargs)

    def test_build(self):
        self.build(executable('program'))
        self.assertOutput([executable('program')], 'hello, world!\n')

        self.assertTrue(os.path.exists(os.path.join(self.builddir, '1')))
        self.assertTrue(os.path.exists(os.path.join(self.builddir, '2')))
        self.assertTrue(os.path.exists(os.path.join(self.builddir, '3')))

    def test_touch_3(self):
        self.build('touch3')

        self.assertTrue(os.path.exists(os.path.join(self.builddir, '2')))
        self.assertTrue(os.path.exists(os.path.join(self.builddir, '3')))

if __name__ == '__main__':
    unittest.main()
