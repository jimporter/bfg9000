import subprocess
import unittest

from integration import IntegrationTest

class TestExternalLibrary(IntegrationTest):
    def __init__(self, *args, **kwargs):
        IntegrationTest.__init__(self, 'external_library', *args, **kwargs)

    def test_all(self):
        subprocess.check_call([self.backend])
        self.assertEqual(subprocess.check_output(['bin/program']), '')

if __name__ == '__main__':
    unittest.main()
