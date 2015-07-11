import os.path
import shutil
import time
import unittest

from integration import *

def stagedir(path):
    dest = os.path.join(test_stage_dir, os.path.basename(path))
    cleandir(dest, recreate=False)
    shutil.copytree(os.path.join(test_data_dir, path), dest)
    return dest

class RegenerateBaseTest(IntegrationTest):
    def _sleep(self, t=1):
        # XXX: This sleep call is needed for ninja, which seems to have low
        # granularity when checking the mtime of files.
        if self.backend == 'ninja':
            time.sleep(t)

class TestRegenerate(RegenerateBaseTest):
    def __init__(self, *args, **kwargs):
        stage = stagedir('regenerate')
        IntegrationTest.__init__(self, stage, *args, **kwargs)

    def test_build(self):
        self.build('foo')
        self.assertTrue(os.path.exists(os.path.join(self.builddir, 'foo')))

    def test_regenerate(self):
        self._sleep()
        with open(os.path.join(self.srcdir, 'build.bfg'), 'a') as out:
            out.write("command('bar', cmd=['touch', 'bar'])\n")

        self.build('bar')
        self.assertTrue(os.path.exists(os.path.join(self.builddir, 'bar')))

class TestRegenerateGlob(RegenerateBaseTest):
    def __init__(self, *args, **kwargs):
        stage = stagedir(os.path.join(examples_dir, '08_find_files'))
        self.extradir = os.path.join(test_data_dir, 'regenerate-glob')
        IntegrationTest.__init__(self, stage, *args, **kwargs)

    def _copy(self, src, dest=None):
        if dest is None:
            dest = src
        shutil.copy(os.path.join(self.extradir, src),
                    os.path.join(self.srcdir, dest))

    def test_add_file(self):
        self._sleep()
        self._copy(os.path.join('hello', 'bonjour.hpp'))
        self._copy(os.path.join('hello', 'bonjour.cpp'))
        self._copy(os.path.join('hello', 'main_added.cpp'),
                   os.path.join('hello', 'main.cpp'))

        self.build(executable('hello'))
        self.assertOutput([executable('hello')],
                          'Hello, world!\nBonjour le monde!\n')

    def test_add_dir(self):
        self._sleep()
        shutil.copytree(os.path.join(self.extradir, 'goodbye', 'french'),
                        os.path.join(self.srcdir, 'goodbye', 'french'))
        self._copy(os.path.join('goodbye', 'main_added.cpp'),
                   os.path.join('goodbye', 'main.cpp'))

        self.build(executable('goodbye'))
        self.assertOutput([executable('goodbye')],
                          'Goodbye!\nAuf Wiedersehen!\nAu revoir!\n')

    def test_remove_file(self):
        self._sleep()
        os.unlink(os.path.join(self.srcdir, 'hello', 'hello.cpp'))
        self._copy(os.path.join('hello', 'main_removed.cpp'),
                   os.path.join('hello', 'main.cpp'))
        self.build(executable('hello'))
        self.assertOutput([executable('hello')], '')

    def test_remove_dir(self):
        self._sleep()
        cleandir(os.path.join(self.srcdir, 'goodbye', 'german'), recreate=False)
        self._copy(os.path.join('goodbye', 'main_removed.cpp'),
                   os.path.join('goodbye', 'main.cpp'))

        self.build(executable('goodbye'))
        self.assertOutput([executable('goodbye')], 'Goodbye!\n')

if __name__ == '__main__':
    unittest.main()
