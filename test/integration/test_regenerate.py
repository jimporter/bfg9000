import os.path
import shutil
import unittest

from integration import *

def stagedir(path):
    dest = os.path.join(test_stage_dir, os.path.basename(path))
    cleandir(dest, recreate=False)
    shutil.copytree(os.path.join(test_data_dir, path), dest)
    return dest

class TestRegenerate(IntegrationTest):
    def __init__(self, *args, **kwargs):
        stage = stagedir('regenerate')
        IntegrationTest.__init__(self, stage, *args, **kwargs)

    def test_build(self):
        self.build('foo')
        self.assertTrue(os.path.exists(os.path.join(self.builddir, 'foo')))

    def test_regenerate(self):
        with open(os.path.join(self.srcdir, 'build.bfg'), 'a') as out:
            out.write("command('bar', cmd=['touch', 'bar'])\n")

        self.build('bar')
        self.assertTrue(os.path.exists(os.path.join(self.builddir, 'bar')))

if __name__ == '__main__':
    unittest.main()
