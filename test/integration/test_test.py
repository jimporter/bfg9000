import subprocess
import unittest

from integration import *

class TestTest(IntegrationTest):
    def __init__(self, *args, **kwargs):
        IntegrationTest.__init__(self, 'test', *args, **kwargs)

    def test_test(self):
        self.build('test')

if __name__ == '__main__':
    unittest.main()
