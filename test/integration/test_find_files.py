import posixpath
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
            src = posixpath.join('06_find_files', 'src')
            self.assertEqual(set(t.getnames()), {
                posixpath.join('06_find_files', 'build.bfg'),
                posixpath.join(src, 'hello', 'hello.cpp'),
                posixpath.join(src, 'hello', 'hello.hpp'),
                posixpath.join(src, 'hello', 'main.cpp'),
                posixpath.join(src, 'goodbye'),
                posixpath.join(src, 'goodbye', 'main.cpp'),
                posixpath.join(src, 'goodbye', 'english'),
                posixpath.join(src, 'goodbye', 'english', 'goodbye.cpp'),
                posixpath.join(src, 'goodbye', 'english', 'goodbye.hpp'),
                posixpath.join(src, 'goodbye', 'german'),
                posixpath.join(src, 'goodbye', 'german', 'goodbye.cpp'),
                posixpath.join(src, 'goodbye', 'german', 'goodbye.hpp'),
            })
