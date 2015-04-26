import subprocess
import unittest

from integration import IntegrationTest

class TestOptions(IntegrationTest):
    def __init__(self, *args, **kwargs):
        IntegrationTest.__init__(self, 'options', *args, **kwargs)

    def test_build(self):
        subprocess.check_call([self.backend, 'program'])
        self.assertEqual(subprocess.check_output(['./program']),
                         'hello, world!\n')

if __name__ == '__main__':
    unittest.main()
