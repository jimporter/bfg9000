import os.path
import tarfile

from .integration import *


class TestExecutable(IntegrationTest):
    def __init__(self, *args, **kwargs):
        IntegrationTest.__init__(
            self, os.path.join(examples_dir, '01_executable'), *args, **kwargs
        )

    def test_build(self):
        self.build(executable('simple'))
        self.assertOutput([executable('simple')], 'hello, world!\n')

    @skip_if_backend('msbuild')
    def test_all(self):
        self.build('all')
        self.assertOutput([executable('simple')], 'hello, world!\n')

    def test_default(self):
        self.build()
        self.assertOutput([executable('simple')], 'hello, world!\n')

    @skip_if_backend('msbuild')
    def test_dist(self):
        dist = output_file('simple-1.0.tar.gz')
        self.build('dist')
        self.assertExists(dist)
        with tarfile.open(self.target_path(dist)) as t:
            self.assertEqual(set(t.getnames()), {'build.bfg', 'simple.cpp'})
