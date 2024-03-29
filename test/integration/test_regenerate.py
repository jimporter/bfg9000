import os.path
import re
import shutil

from . import *
pjoin = os.path.join

regen_ex = re.compile('^info: regenerating build files$', re.MULTILINE)


@skip_if_backend('msbuild')
class TestRegenerate(IntegrationTest):
    def __init__(self, *args, **kwargs):
        super().__init__('regenerate', stage_src=True, *args, **kwargs)

    def test_build(self):
        self.assertNotRegex(self.build('foo'), regen_ex)
        self.assertExists(pjoin(self.builddir, 'foo'))

    def test_regenerate(self):
        self.wait()
        with open(pjoin(self.srcdir, 'build.bfg'), 'a') as out:
            out.write("command('bar', cmd=['touch', 'bar'])\n")

        self.assertRegex(self.build('bar'), regen_ex)
        self.assertExists(pjoin(self.builddir, 'bar'))


@skip_pred(lambda x: x.backend == 'msbuild' or
           (x.backend in 'make' and env.host_platform.family == 'windows'),
           'xfail on msbuild, windows + make')
class TestRegenerateGlob(IntegrationTest):
    def __init__(self, *args, **kwargs):
        self.extradir = pjoin(test_data_dir, 'regenerate_glob')
        super().__init__(pjoin(examples_dir, '05_find_files'), stage_src=True,
                         *args, **kwargs)

    def copyfile(self, src, dest=None):
        if dest is None:
            dest = src
        shutil.copy(pjoin(self.extradir, src),
                    pjoin(self.srcdir, dest))

    def test_modify_build_bfg(self):
        self.wait()
        with open(pjoin(self.srcdir, 'build.bfg'), 'a') as out:
            out.write('# hello\n')

        self.assertRegex(self.build(executable('hello')), regen_ex)
        self.assertOutput([executable('hello')], 'Hello, world!\n')

    def test_add_file(self):
        self.wait()
        self.copyfile(pjoin('src', 'hello', 'bonjour.hpp'))
        self.copyfile(pjoin('src', 'hello', 'bonjour.cpp'))
        self.copyfile(pjoin('src', 'hello', 'main_added.cpp'),
                      pjoin('src', 'hello', 'main.cpp'))

        self.assertRegex(self.build(executable('hello')), regen_ex)
        self.assertOutput([executable('hello')],
                          'Hello, world!\nBonjour le monde!\n')

    def test_add_irrelevant_file(self):
        self.wait()
        with open(pjoin(self.srcdir, 'src', 'hello', 'misc.txt'), 'w') as out:
            out.write('hello\n')

        self.assertNotRegex(self.build(executable('hello')), regen_ex)
        self.assertOutput([executable('hello')], 'Hello, world!\n')

    def test_add_dir(self):
        self.wait()
        shutil.copytree(pjoin(self.extradir, 'src', 'goodbye', 'french'),
                        pjoin(self.srcdir, 'src', 'goodbye', 'french'))
        self.copyfile(pjoin('src', 'goodbye', 'main_added.cpp'),
                      pjoin('src', 'goodbye', 'main.cpp'))

        self.assertRegex(self.build(executable('goodbye')), regen_ex)
        self.assertOutput([executable('goodbye')],
                          'Goodbye!\nAuf Wiedersehen!\nAu revoir!\n')

    def test_remove_file(self):
        self.wait()
        os.unlink(pjoin(self.srcdir, 'src', 'hello', 'hello.cpp'))
        self.copyfile(pjoin('src', 'hello', 'main_removed.cpp'),
                      pjoin('src', 'hello', 'main.cpp'))

        self.assertRegex(self.build(executable('hello')), regen_ex)
        self.assertOutput([executable('hello')], '')

    def test_remove_dir(self):
        self.wait()
        cleandir(pjoin(self.srcdir, 'src', 'goodbye', 'german'),
                 recreate=False)
        self.copyfile(pjoin('src', 'goodbye', 'main_removed.cpp'),
                      pjoin('src', 'goodbye', 'main.cpp'))

        self.assertRegex(self.build(executable('goodbye')), regen_ex)
        self.assertOutput([executable('goodbye')], 'Goodbye!\n')
