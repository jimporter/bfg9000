import subprocess
import unittest

from integration import IntegrationTest

class TestDefaults(IntegrationTest):
    def __init__(self, *args, **kwargs):
        IntegrationTest.__init__(self, 'defaults', *args, **kwargs)

    def test_default(self):
        subprocess.check_call([self.backend])
        self.assertEqual(subprocess.check_output(['./a']),
                         'hello, a!\n')
        self.assertEqual(subprocess.check_output(['./b']),
                         'hello, b!\n')

if __name__ == '__main__':
    unittest.main()
