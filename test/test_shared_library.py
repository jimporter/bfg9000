import subprocess
import unittest

from integration import IntegrationTest

class TestSharedLibrary(IntegrationTest):
    def __init__(self, *args, **kwargs):
        IntegrationTest.__init__(self, 'shared_library', *args, **kwargs)

    def test_all(self):
        subprocess.check_call([self.backend])
        self.assertEqual(subprocess.check_output(['./program']),
                         'hello, library!\n')

if __name__ == '__main__':
    unittest.main()
