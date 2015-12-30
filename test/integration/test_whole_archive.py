import unittest

from .integration import *
from bfg9000.environment import Environment

env = Environment(None, None, None, None, None)
flavor = env.compiler('c++').flavor


class TestWholeArchive(IntegrationTest):
    def __init__(self, *args, **kwargs):
        IntegrationTest.__init__(self, 'whole_archive', *args, **kwargs)

    @unittest.skipIf(flavor != 'cc', 'requires cc builder')
    def test_build(self):
        self.build()
        self.assertOutput([executable('program')], 'hello, library!\n')


if __name__ == '__main__':
    unittest.main()
