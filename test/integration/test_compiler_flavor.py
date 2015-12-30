import unittest

from .integration import *


class TestCompilerFlavor(IntegrationTest):
    def __init__(self, *args, **kwargs):
        IntegrationTest.__init__(self, 'compiler_flavor', *args, **kwargs)

    def test_build(self):
        self.build(executable('program'))
        self.assertOutput([executable('program')], 'hello, cc!\n')


if __name__ == '__main__':
    unittest.main()
