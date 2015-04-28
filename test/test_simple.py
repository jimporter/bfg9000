import subprocess
import unittest

from integration import IntegrationTest

class TestSimple(IntegrationTest):
    def __init__(self, *args, **kwargs):
        IntegrationTest.__init__(self, 'simple', *args, **kwargs)

    def test_build(self):
        subprocess.check_call([self.backend, 'bin/simple'])
        self.assertEqual(subprocess.check_output(['bin/simple']),
                         'hello, world!\n')

    def test_default(self):
        subprocess.check_call([self.backend])
        self.assertEqual(subprocess.check_output(['bin/simple']),
                         'hello, world!\n')

if __name__ == '__main__':
    unittest.main()
