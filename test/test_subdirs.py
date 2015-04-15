import subprocess

from integration import IntegrationTest

class TestSubdirs(IntegrationTest):
    def __init__(self, *args, **kwargs):
        IntegrationTest.__init__(self, 'subdirs', *args, **kwargs)

    def test_all(self):
        subprocess.check_call([self.backend])
        self.assertEqual(subprocess.check_output(['bin/program']),
                         'hello, library!\n')

if __name__ == '__main__':
    unittest.main()
