import unittest

from integration import *

class TestDefaults(IntegrationTest):
    def __init__(self, *args, **kwargs):
        IntegrationTest.__init__(self, 'defaults', *args, **kwargs)

    def test_default(self):
        self.build()
        self.assertOutput([executable('a')], 'hello, a!\n')
        self.assertOutput([executable('b')], 'hello, b!\n')

if __name__ == '__main__':
    unittest.main()
