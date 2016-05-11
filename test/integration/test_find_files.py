import os.path
import tarfile

from .integration import *


class TestFindFiles(IntegrationTest):
    def __init__(self, *args, **kwargs):
        IntegrationTest.__init__(
            self, os.path.join(examples_dir, '06_find_files'), *args, **kwargs
        )

    def test_hello(self):
        self.build(executable('hello'))
        self.assertOutput([executable('hello')], 'Hello, world!\n')

    def test_goodbye(self):
        self.build(executable('goodbye'))
        self.assertOutput([executable('goodbye')],
                          'Goodbye!\nAuf Wiedersehen!\n')

    @skip_if_backend('msbuild')
    def test_dist(self):
        dist = output_file('06_find_files.tar.gz')
        self.build('dist')
        self.assertExists(dist)
        with tarfile.open(self.target_path(dist)) as t:
            self.assertEqual(set(t.getnames()), {
                'build.bfg',
                'src/hello/hello.cpp',
                'src/hello/hello.hpp',
                'src/hello/main.cpp',
                'src/goodbye/main.cpp',
                'src/goodbye/english/goodbye.cpp',
                'src/goodbye/english/goodbye.hpp',
                'src/goodbye/german/goodbye.cpp',
                'src/goodbye/german/goodbye.hpp',
            })
