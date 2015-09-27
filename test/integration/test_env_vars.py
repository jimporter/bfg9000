import os.path
import unittest

from integration import *

class TestTests(IntegrationTest):
    def __init__(self, *args, **kwargs):
        IntegrationTest.__init__(self, 'env_vars', *args, **kwargs)

    @skip_if_backend('msbuild')
    def test_test(self):
        self.build('test')

if __name__ == '__main__':
    unittest.main()
